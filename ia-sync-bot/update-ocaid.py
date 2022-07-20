#!/usr/bin/env python3
import json

from olclient.openlibrary import OpenLibrary

ol = OpenLibrary()

infile = "olids-to-update.txt"

# Takes an infile and writes ocaids to Open Library items and performs a sync.

# infile is the json output of an archive.org search query
# containing 'openlibrary' (edition olid) and 'identifier' (ocaid) fields


def sync_ol_to_ia(olid):
    r = ol.session.get(ol.base_url + "/admin/sync?edition_id=" + olid)
    if r.status_code == 500:
        content = {"error": "HTTP 500"}
    else:
        content = r.json()
    if (
        "error" in content and "no changes to _meta.xml" not in content["error"]
    ):  # and r.json()['error'] == 'No qualifying edition':
        print(f"{olid}, {ocaid}: {content}")
    return r.status_code


# start and end are False or line numbers in infile to begin and stop processing
# Used in case there is a need to resume or re-run part of a batch.
start = False
end = False
with open(infile) as f:
    for count, line in enumerate(f):
        # OLD TSV FORMAT: ocaid, olid = line.split()
        data = json.loads(line)
        ocaid = data.get("identifier")
        olid = data.get("openlibrary")
        if start and count < start:
            continue
        if end and count > end:
            break
        # check and add ocaid to OL edition
        print(f"Adding {ocaid} to {olid}")
        edition = ol.get(olid)
        assert edition.title, "Missing title in %s!" % olid

        if hasattr(edition, "ocaid"):
            print("  OCAID already found: %s" % edition.ocaid)
        else:
            edition.ocaid = ocaid
            edition.save("add ocaid")
        # sync the edition
        r = sync_ol_to_ia(olid)
        if r == 500:
            edition.ocaid = ocaid
            edition.save("update ocaid")
            sync_ol_to_ia(olid)
