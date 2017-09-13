import re
from olclient.openlibrary import OpenLibrary

ol = OpenLibrary()

def get_type(olid):
    ol_types = {'OL..A': 'author', 'OL..M': 'book', 'OL..W': 'work'}
    kind = re.sub('\d+', '..', olid)
    return ol_types[kind]

def full_key(olid):
    return "/%ss/%s" % (get_type(olid), olid)

def full_url(olid):
    return "%s%s.json" % (ol.base_url, full_key(olid))

