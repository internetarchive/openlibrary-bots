import csv
import json
import requests
import sys

from olclient.openlibrary import OpenLibrary

if __name__ == '__main__':
    ol = OpenLibrary()
    csv.field_size_limit(sys.maxsize)
    filename = 'ol_dump_editions_2020-02-29.csv'
    with open(filename, 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t', quoting=csv.QUOTE_NONE)
        header = {'type': 0,
                  'key': 1,
                  'revision': 2,
                  'last_modified': 3,
                  'JSON': 4}
        with open('fixed_books.csv', 'a') as fout:
            for row in reader:
                _json = json.loads(row[header['JSON']])
                if 'ocaid' in _json and 'covers' not in _json:
                    olid = _json['key'].split('/')[-1]
                    edition_obj = ol.Edition.get(olid)
                    if not len(getattr(edition_obj, 'covers', [])):
                        fout.write(edition_obj.olid + '\n')
                        fout.flush()
                        edition_obj.add_bookcover('https://archive.org/download/%(ocaid)s/page/cover' % {'ocaid': _json['ocaid']})
# amount of coverless scans is: 643304
# 7125 coverless wikidata items
