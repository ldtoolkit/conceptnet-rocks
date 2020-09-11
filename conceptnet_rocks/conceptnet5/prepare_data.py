from conceptnet_rocks.conceptnet5.uri import uri_prefixes


def gin_indexable_edge(edge):
    """
    Convert an edge into a dictionary that can be matched with the JSONB @>
    operator, which tests if one dictionary includes all the information in
    another. This operator can be indexed by GIN.

    We replace the 'start', 'end', 'rel', and 'dataset' URIs with lists
    of their URI prefixes. We query those slots with a single-element list,
    which will be a sub-list of the prefix list if it's a match.

    As an example, a query for {'start': '/c/en'} will become the GIN
    query {'start': ['/c/en']}, which will match indexed edges such as
    {
        'start': ['/c/en', '/c/en/dog'],
        'end': ['/c/en', '/c/en/bark'],
        'rel': ['/r/CapableOf'],
        ...
    }
    """
    gin_edge = {}
    gin_edge['uri'] = edge['uri']
    gin_edge['start'] = uri_prefixes(edge['start'])
    gin_edge['end'] = uri_prefixes(edge['end'])
    gin_edge['rel'] = uri_prefixes(edge['rel'])
    gin_edge['dataset'] = uri_prefixes(edge['dataset'])
    flat_sources = set()
    for source in edge['sources']:
        for value in source.values():
            flat_sources.update(uri_prefixes(value, min_pieces=3))
    gin_edge['sources'] = sorted(flat_sources)
    return gin_edge
