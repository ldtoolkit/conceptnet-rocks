from arango import ArangoClient
from conceptnet_rocks import arangodb
from conceptnet_rocks.conceptnet5.edges import transform_for_linked_data
from hashlib import sha1
from pathlib import Path
from tqdm import tqdm
from typing import Optional, Any, Dict, List
import dask.dataframe as dd
import orjson
import os
import subprocess


DEFAULT_DATABASE = "conceptnet"


def convert_uri_to_ascii(uri: str) -> str:
    return sha1(uri.encode()).hexdigest()


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


def load_dump_into_database(
        dump_path: Path,
        edge_count: Optional[int] = None,
        connection_uri: str = arangodb.DEFAULT_CONNECTION_URI,
        database: str = DEFAULT_DATABASE,
        root_password: str = arangodb.DEFAULT_ROOT_PASSWORD,
        arangodb_exe_path: Path = arangodb.DEFAULT_INSTALL_PATH,
        data_path: Path = arangodb.DEFAULT_DATA_PATH,
):
    with arangodb.instance(
        connection_uri=connection_uri,
        root_password=root_password,
        arangodb_exe_path=arangodb_exe_path,
        data_path=data_path,
    ):
        client = ArangoClient(hosts=connection_uri)

        root_credentials = {
            "username": "root",
            "password": root_password,
        }

        sys_db = client.db(arangodb.SYSTEM_DATABASE, **root_credentials)
        if sys_db.has_database(database):
            raise RuntimeError(f"Database {database} already exist")

        sys_db.create_database(database)

        db = client.db(database, **root_credentials)

        graph = db.create_graph("conceptnet")

        graph.create_vertex_collection("nodes")

        graph.create_edge_definition(
            edge_collection="edges",
            from_vertex_collections=["nodes"],
            to_vertex_collections=["nodes"]
        )

        dump_path = Path(dump_path).expanduser().resolve()

        df = dd.read_csv(dump_path, sep="\t", header=None)
        batch_size = 2**10

        if edge_count is None:
            edge_count = line_count(dump_path)

        edge_list = []
        node_list = []

        nodes_path = data_path / "nodes.jsonl"
        edges_path = data_path / "edges.jsonl"

        if not nodes_path.is_file() or not edges_path.is_file():
            with open(nodes_path, "wb") as nodes_file, open(edges_path, "wb") as edges_file:
                for row in tqdm(df.itertuples(), unit=' edges', total=edge_count):
                    i, assertion_uri, relation_uri, start_uri, end_uri, edge_data = row

                    start_uri += "/"
                    end_uri += "/"

                    edge_data_dict = orjson.loads(edge_data)
                    edge_data_dict["dataset"] += "/"

                    def source_with_trailing_slash(source: Dict[str, str]) -> Dict[str, str]:
                        result = {}
                        for field in ["activity", "contributor", "process"]:
                            if field in source:
                                result[field] = source[field] + "/"
                        return result

                    edge_data_dict["sources"] = [
                        source_with_trailing_slash(source)
                        for source in edge_data_dict["sources"]
                    ]

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

                    finished = i == edge_count - 1
                    if i % batch_size == 0 or finished:
                        for node in node_list:
                            nodes_file.write(orjson.dumps(node))
                            nodes_file.write(b"\n")
                        for edge in edge_list:
                            edges_file.write(orjson.dumps(edge))
                            edges_file.write(b"\n")
                        node_list.clear()
                        edge_list.clear()
                        if finished:
                            break

        arangoimport_path = arangodb.get_exe_path(path=arangodb_exe_path, program_name="arangoimport")
        for file_path, collection in [(nodes_path, "nodes"), (edges_path, "edges")]:
            subprocess.run([
                arangoimport_path,
                "--threads", f"{os.cpu_count()}",
                "--file", file_path,
                "--type", "jsonl",
                "--server.database", database,
                "--server.endpoint", connection_uri.replace("http", "tcp"),
                "--server.username", "root",
                "--server.password", root_password,
                "--collection", collection,
                "--on-duplicate", "ignore",
            ])
            file_path.unlink()

        nodes = db.collection("nodes")
        edges = db.collection("edges")
        nodes.add_persistent_index(["uri"], unique=True)
        edges.add_persistent_index(["dataset"])
        edges.add_persistent_index(["rel"])
        edges.add_persistent_index(["uri"], unique=True)

        # Docs (https://www.arangodb.com/docs/stable/indexing-index-basics.html#indexing-array-values):
        # Please note that filtering using array indexes only works from within AQL queries and only if the query
        # filters on the indexed attribute using the IN operator. The other comparison operators (==, !=, >, >=, <, <=,
        # ANY, ALL, NONE) cannot use array indexes currently.
        # edges.add_persistent_index(["sources[*].activity"])
        # edges.add_persistent_index(["sources[*].contributor"])
        # edges.add_persistent_index(["sources[*].process"])


class AssertionFinder:
    def __init__(
            self,
            database: str = DEFAULT_DATABASE,
            connection_uri: str = arangodb.DEFAULT_CONNECTION_URI,
            root_password: str = arangodb.DEFAULT_ROOT_PASSWORD,
            arangodb_exe_path: Path = arangodb.DEFAULT_INSTALL_PATH,
            data_path: Path = arangodb.DEFAULT_DATA_PATH,
            close_stdout_and_stderr: bool = False,
    ):
        self._arangodb_arbiter = arangodb.start_if_not_running(
            connection_uri=connection_uri,
            root_password=root_password,
            arangodb_exe_path=arangodb_exe_path,
            data_path=data_path,
            close_stdout_and_stderr=close_stdout_and_stderr,
        )
        self._client = ArangoClient(hosts=connection_uri)
        self._db = self._client.db(database, username="root", password=root_password)

    def __del__(self):
        arangodb.stop_arbiter(self._arangodb_arbiter)

    def lookup(self, uri: str, limit: int = 100, offset: int = 0):
        # noinspection PyShadowingNames
        def perform_query(query: str, query_vars: Dict[str, Any]) -> List[Dict[str, Any]]:
            return [
                transform_for_linked_data(data)
                for data in self._db.aql.execute(query, bind_vars=query_vars)
            ]

        limit_and_merge = """
            limit @offset, @limit
            let trimmed_sources = (
              for source in edge.sources
                return merge(
                  has(source, "activity") ? {activity: rtrim(source.activity, "/")} : {},
                  has(source, "contributor") ? {contributor: rtrim(source.contributor, "/")} : {},
                  has(source, "process") ? {process: rtrim(source.process, "/")} : {}
                )
            )
            return distinct merge({
              start: rtrim(document(edge._from).uri, "/"),
              end: rtrim(document(edge._to).uri, "/"),
              dataset: rtrim(edge.dataset, "/"),
              sources: trimmed_sources,
            }, unset(edge, "_from", "_to", "_key", "_id", "_rev", "dataset", "sources"))
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
        elif uri.startswith('/s/'):
            query = f"""
                for edge in edges
                  for s in edge.sources
                    filter (
                      (s.activity >= concat(@source, "/") and s.activity < concat(@source, "0"))
                      or
                      (s.contributor >= concat(@source, "/") and s.contributor < concat(@source, "0"))
                      or
                      (s.process >= concat(@source, "/") and s.process < concat(@source, "0"))
                    )
                    {limit_and_merge}
            """
            query_vars = {"limit": limit, "offset": offset, "source": uri}
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

    def clear_cache(self) -> None:
        self._db.aql.cache.clear()


if __name__ == "__main__":
    af = AssertionFinder()
