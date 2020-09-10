from a_conceptnet.conceptnet5.edges import transform_for_linked_data
from arango import ArangoClient
from pathlib import Path
from tqdm import tqdm
from typing import Optional, Any, Dict, List
import base64
import csv
import json


def convert_uri_to_ascii(uri: str) -> str:
    return base64.b64encode(uri.encode(), altchars=b'+-').decode()


def get_node_id(uri_ascii: str) -> str:
    return f"nodes/{uri_ascii}"


def line_count(file_path):
    f = open(file_path, "rb")
    result = 0
    buf_size = 1024 * 1024
    read_f = f.raw.read

    buf = read_f(buf_size)
    while buf:
        result += buf.count(b"\n")
        buf = read_f(buf_size)

    return result


def load_dump_into_database(dump_path: Path, edge_count: Optional[int] = None):
    client = ArangoClient(hosts="http://localhost:8529")

    sys_db = client.db("_system", username="root", password="")
    if sys_db.has_database("conceptnet"):
        raise RuntimeError("Database conceptnet already exist")

    sys_db.create_database("conceptnet")

    db = client.db("conceptnet", username="root")

    graph = db.create_graph("conceptnet")

    graph.create_vertex_collection("nodes")

    graph.create_edge_definition(
        edge_collection="edges",
        from_vertex_collections=["nodes"],
        to_vertex_collections=["nodes"]
    )

    dump_path = Path(dump_path).expanduser().resolve()

    with open(str(dump_path), newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        batch_size = 2**10

        if edge_count is None:
            edge_count = line_count(dump_path)

        edge_list = []
        node_list = []

        edges = db.collection("edges")
        nodes = db.collection("nodes")

        for i, row in tqdm(enumerate(reader), unit=' edges', total=edge_count):
            finished = i == edge_count
            if i % batch_size == 0 or finished:
                edges.import_bulk(edge_list, on_duplicate="ignore")
                nodes.import_bulk(node_list, on_duplicate="ignore")
                edge_list.clear()
                node_list.clear()
                if finished:
                    break

            assertion_uri, relation_uri, start_uri, end_uri, edge_data = row

            start_uri += "/"
            end_uri += "/"

            edge_data_dict = json.loads(edge_data)
            edge_data_dict["dataset"] += "/"

            start_node_key = convert_uri_to_ascii(start_uri)
            node_list.append({"_key": start_node_key, "uri": start_uri})

            end_node_key = convert_uri_to_ascii(end_uri)
            node_list.append({"_key": end_node_key, "uri": end_uri})

            start_node_id = get_node_id(start_node_key)
            end_node_id = get_node_id(end_node_key)

            edge_list.append({
                "_from": start_node_id,
                "_to": end_node_id,
                "uri": assertion_uri,
                "rel": relation_uri,
                **edge_data_dict,
            })

    nodes.add_persistent_index(["uri"], unique=True)
    edges.add_persistent_index(["dataset"])
    edges.add_persistent_index(["rel"])
    edges.add_persistent_index(["uri"], unique=True)


class AssertionFinder:
    def __init__(self):
        self._client = ArangoClient(hosts="http://localhost:8529")
        self._db = self._client.db("conceptnet", username="root")

    def lookup(self, uri: str, limit: int = 100, offset: int = 0):
        def perform_query(query: str, query_vars: Dict[str, Any]) -> List[Dict[str, Any]]:
            return [
                transform_for_linked_data(data)
                for data in self._db.aql.execute(query, bind_vars=query_vars)
            ]

        limit_and_merge = """
            limit @offset, @limit
            return merge({
              start: rtrim(document(edge._from).uri, "/"),
              end: rtrim(document(edge._to).uri, "/"),
              dataset: rtrim(edge.dataset, "/")
            }, unset(edge, "_from", "_to", "_key", "_id", "_rev", "dataset"))
        """

        if uri.startswith('/c/') or uri.startswith('http'):
            query = f"""
                for start_node in nodes
                  filter start_node.uri >= concat(@uri, "/") and start_node.uri < concat(@uri, "0")
                  for node, edge in any start_node edges
                  {limit_and_merge}
            """
            query_vars = {"limit": limit, "offset": offset, "uri": uri}
            return perform_query(query=query, query_vars=query_vars)
        elif uri.startswith('/r/'):
            query = f"""
                for edge in edges
                  filter edge.rel == @rel
                  {limit_and_merge}
            """
            query_vars = {"limit": limit, "offset": offset, "rel": uri}
            return perform_query(query=query, query_vars=query_vars)
        elif uri.startswith('/d/'):
            query = f"""
                for edge in edges
                  filter edge.dataset >= concat(@dataset, "/") and edge.dataset < concat(@dataset, "0")
                  {limit_and_merge}
            """
            query_vars = {"limit": limit, "offset": offset, "dataset": uri}
            return perform_query(query=query, query_vars=query_vars)
        elif uri.startswith('/a/'):
            query = f"""
                for edge in edges
                  filter edge.uri == @uri
                  {limit_and_merge}
            """
            query_vars = {"limit": limit, "offset": offset, "uri": uri}
            return perform_query(query=query, query_vars=query_vars)
        else:
            raise ValueError(f"{uri} isn't a supported")
