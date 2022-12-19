"""
Adds a cover to a coverless edition if it has an ocaid
NOTE: This script assumes the Open Library Dump passed only contains coverless editions with an ocaid
"""

import gzip
import json
import sys

from olclient.openlibrary import OpenLibrary

if __name__ == "__main__":
    ol = OpenLibrary()
    filtered_ol_dump = sys.argv[1]
    output_filepath = sys.argv[2]
    with gzip.open(filtered_ol_dump, "rb") as fin:
        header = {"type": 0, "key": 1, "revision": 2, "last_modified": 3, "JSON": 4}
        with gzip.open(output_filepath, "a") as fout:
            for row in fin:
                row = row.decode().split("\t")
                _json = json.loads(row[header["JSON"]])
                olid = _json["key"].split("/")[-1]
                edition_obj = ol.Edition.get(olid)
                if not len(getattr(edition_obj, "covers", [])):
                    fout.write(f"{edition_obj.olid}\n".encode())
                    edition_obj.add_bookcover(
                        "https://archive.org/download/%s/page/cover" % _json["ocaid"]
                    )
