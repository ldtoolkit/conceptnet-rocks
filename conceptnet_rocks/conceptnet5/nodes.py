from conceptnet_rocks.conceptnet5.uri import uri_to_label, is_term, split_uri, get_uri_language, uri_prefix
from urllib.parse import urlparse


def ld_node(uri, label=None):
    """
    Convert a ConceptNet URI into a dictionary suitable for Linked Data.
    """
    if label is None:
        label = uri_to_label(uri)
    ld = {'@id': uri, 'label': label}
    if is_term(uri):
        pieces = split_uri(uri)
        ld['language'] = get_uri_language(uri)

        # Get a reasonably-distinct sense label for the term.
        # Usually it will be the part of speech, but when we have fine-grained
        # information from Wikipedia or WordNet, it'll include the last
        # component as well.
        if len(pieces) > 3:
            ld['sense_label'] = pieces[3]

        if len(pieces) > 4 and pieces[4] in ('wp', 'wn'):
            ld['sense_label'] += ', ' + pieces[-1]

        ld['term'] = uri_prefix(uri)
        ld['@type'] = 'Node'
    elif uri.startswith('http'):
        domain = urlparse(uri).netloc
        ld['site'] = domain
        ld['term'] = uri

        # OpenCyc is down and UMBEL doesn't host their vocabulary on the
        # Web. This property indicates whether you can follow a link
        # via HTTP and retrieve more information.
        ld['site_available'] = True
        if domain in {'sw.opencyc.org', 'umbel.org', 'wikidata.dbpedia.org'}:
            ld['site_available'] = False
        ld['path'] = urlparse(uri).path
        ld['@type'] = 'Node'
    elif uri.startswith('/r/'):
        ld['@type'] = 'Relation'
    return ld
