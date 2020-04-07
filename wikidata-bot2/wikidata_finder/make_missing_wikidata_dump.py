"""Reads OpenLibrary IDs from a dump and outputs Open Library ids that do not have wikidata ids but should"""

import gzip
import sys

from olclient.openlibrary import OpenLibrary


if __name__ == '__main__':
    input_filepath = sys.argv[1]
    output_filepath = sys.argv[2]
    with gzip.open(input_filepath, 'r') as fin:
        header = {
            'olid': 0,
            'wikidata_id': 1
        }
        ol = OpenLibrary()
        with gzip.open(output_filepath, 'w') as fout:
            for row in fin:
                row = row.decode().split('\t')
                olid_type = row[header['olid']][-1].lower()
                if olid_type == 'a':
                    author = ol.Author.get(row[header['olid']])
                    try:
                        author.remote_ids['wikidata']
                        continue
                    except (KeyError, AttributeError):  # author has no wikidata id
                        fout.write('\t'.join([author.olid, row[header['wikidata_id']], '\n']).encode())
                elif olid_type == 'm':
                    edition = ol.Edition.get(row[header['olid']])
                    try:
                        edition.identifiers['wikidata']
                        continue
                    except (KeyError, AttributeError):  # edition has no wikidata id
                        fout.write('\t'.join([edition.olid, row[header['wikidata_id']], '\n']).encode())
                elif olid_type == 'w':
                    continue  # fixme is there a way to add a wikidata id to a Work?

