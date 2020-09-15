from conceptnet_rocks.conceptnet5.nodes import ld_node
from conceptnet_rocks.conceptnet5.uri import conjunction_uri


def transform_for_linked_data(edge):
    """
    Modify an edge (assertion) in place to contain values that are appropriate
    for a Linked Data API.

    Although this code isn't actually responsible for what an API returns
    (see the conceptnet-web repository for that), it helps to deal with what
    edge dictionaries should contain here.

    The relevant changes are:

    - Remove the 'features' list
    - Rename 'uri' to '@id'
    - Make 'start', 'end', and 'rel' into dictionaries with an '@id' and
      'label', removing the separate 'surfaceStart' and 'surfaceEnd'
      attributes
    - All dictionaries should have an '@id'. For the edge itself, it's the
      URI. Without this, we get RDF blank nodes, which are awful.
    - Set '@type' on objects representing edges and sources. (Nodes get their
      @type from the `ld_node` function.)
    """
    for source in edge['sources']:
        conj = conjunction_uri(*sorted(source.values()))
        source['@id'] = conj
        source['@type'] = 'Source'
    edge['@id'] = edge['uri']
    del edge['uri']
    edge['@type'] = 'Edge'

    start_uri = edge['start']
    end_uri = edge['end']
    rel_uri = edge['rel']
    start_label = edge.pop('surfaceStart', None)
    end_label = edge.pop('surfaceEnd', None)
    edge['start'] = ld_node(start_uri, start_label)
    edge['end'] = ld_node(end_uri, end_label)
    edge['rel'] = ld_node(rel_uri, None)
    if 'other' in edge:
        # TODO: Find out when we use this, or remove it if we don't use it
        if edge['other'] == start_uri:
            edge['other'] = edge['start']
        elif edge['other'] == end_uri:
            edge['other'] = edge['end']
        else:
            edge['rel'] = ld_node(rel_uri, None)

    if edge.get('surfaceText') is None:
        edge['surfaceText'] = None

    edge['weight'] = float(edge['weight'])

    return edge


