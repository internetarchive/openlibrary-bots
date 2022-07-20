#!/usr/bin/env python3

""" 
    Iterates over an archive.org bulk MARC item, such as OpenLibraries-Trent-MARCs,
    and imports all records in all of its MARC files to Open Library.

    USAGE: ./bulk-import.py <archive.org item id>

    Logs results to STDOUT
"""

import argparse
import json
import os
import re
import sys
from collections import namedtuple
from glob import glob
from time import sleep

import internetarchive as ia
from olclient.openlibrary import OpenLibrary
from requests.adapters import HTTPAdapter
from requests.exceptions import ConnectionError, HTTPError

BULK_API = "/api/import/ia"
LOCAL_ID = re.compile(r"\/local_ids\/(\w+)")
MARC_EXT = re.compile(r".*\.(mrc|utf8)$")

SERVER_ISSUES_WAIT = (
    50 * 60
)  # seconds to wait if server is giving unexpected 5XXs likely to be resolved in time
SHORT_CONNECT_WAIT = 5 * 60  # seconds


def get_marc21_files(item):
    return [f.name for f in ia.get_files(item) if MARC_EXT.match(f.name)]


def log_error(response):
    n = 0
    current_errors = glob("error*.html")
    for f in current_errors:
        n = max(n, 1 + int(re.search(r"[0-9]+", os.path.splitext(f)[0]).group(0)))
    name = "error_%d.html" % n
    with open(name, "w") as error_log:
        error_log.write(response.content.decode())
    return name


def next_record(identifier, ol):
    """
    identifier: '{}/{}:{}:{}'.format(item, fname, offset, length)
    """
    current = ol.session.get(ol.base_url + "/show-records/" + identifier)
    m = re.search(
        r'<a href="\.\./[^/]+/[^:]+:([0-9]+):([0-9]+)".*Next</a>', current.text
    )
    next_offset, next_length = m.groups()
    # Follow redirect to get actual length (next_length is always 5 to trigger the redirect)
    r = ol.session.head(
        ol.base_url
        + "/show-records/"
        + re.search(r"^[^:]*", identifier).group(0)
        + f":{next_offset}:{next_length}"
    )
    next_length = re.search(r"[^:]*$", r.headers.get("Location", "5")).group(0)
    return int(next_offset), int(next_length)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bulk MARC importer.")
    parser.add_argument("item", help="Source item containing MARC records", nargs="?")
    parser.add_argument(
        "-i",
        "--info",
        help="List available MARC21 .mrc files on this item",
        action="store_true",
    )
    parser.add_argument(
        "-b",
        "--barcode",
        help="Barcoded local_id available for import",
        nargs="?",
        const=True,
        default=False,
    )
    parser.add_argument("-f", "--file", help="Bulk MARC file to import")
    parser.add_argument(
        "-n", "--number", help="Number of records to import", type=int, default=1
    )
    parser.add_argument(
        "-o",
        "--offset",
        help="Offset in BYTES from which to start importing",
        type=int,
        default=0,
    )
    parser.add_argument(
        "-l",
        "--local",
        help="Import to a locally running Open Library dev instance for testing (localhost:8080)",
        action="store_true",
    )
    parser.add_argument(
        "-d",
        "--dev",
        help="Import to dev.openlibrary.org Open Library dev instance for testing",
        action="store_true",
    )
    parser.add_argument(
        "-s",
        "--staging",
        help="Import to staging.openlibrary.org Open Library staging instance for testing",
        action="store_true",
    )

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()
    item = args.item
    fname = args.file
    local_testing = args.local
    dev_testing = args.dev
    staging_testing = args.staging
    barcode = args.barcode

    if local_testing:
        Credentials = namedtuple("Credentials", ["username", "password"])
        local_dev = "http://localhost:8080"
        c = Credentials("openlibrary@example.com", "admin123")
        ol = OpenLibrary(base_url=local_dev, credentials=c)
    elif staging_testing:
        ol = OpenLibrary(base_url="http://staging.openlibrary.org")
    elif dev_testing:
        ol = OpenLibrary(base_url="https://dev.openlibrary.org")
    else:
        ol = OpenLibrary()

    print("Importing to %s" % ol.base_url)
    print("ITEM: %s" % item)
    print("FILENAME: %s" % fname)

    if args.info:
        if barcode is True:
            # display available local_ids
            print("Available local_ids to import:")
            r = ol.session.get(ol.base_url + "/local_ids.json")
            print(LOCAL_ID.findall(r.json()["body"]["value"]))
        if item:
            # List MARC21 files, then quit.
            print("Item %s has the following MARC files:" % item)
            for f in get_marc21_files(item):
                print(f)
        ol.session.close()
        exit()

    limit = (
        args.number
    )  # if non-zero, a limit to only process this many records from each file
    count = 0
    offset = args.offset
    length = 5  # we only need to get the length of the first record (first 5 bytes), the API will seek to the end.

    ol.session.mount("https://", HTTPAdapter(max_retries=10))

    while length:
        if limit and count >= limit:
            # Stop if a limit has been set, and we are over it.
            break
        identifier = f"{item}/{fname}:{offset}:{length}"
        data = {"identifier": identifier, "bulk_marc": "true"}
        if barcode and barcode is not True:
            # A local_id key has been passed to import a specific local_id barcode
            data["local_id"] = barcode

        try:
            r = ol.session.post(ol.base_url + BULK_API + "?debug=true", data=data)
            r.raise_for_status()

        except HTTPError as e:
            result = {}
            status = r.status_code
            if status > 500:
                error_summary = ""
                # on 503, wait then retry
                if r.status_code == 503:
                    length = 5
                    offset = offset  # repeat current import
                    sleep(SERVER_ISSUES_WAIT)
                    continue
            elif status == 500:
                # In debug mode 500s produce HTML with details of the error
                m = re.search(r"<h1>(.*)</h1>", r.text)
                error_summary = m and m.group(1) or r.text
                # Write error log
                error_log = log_error(r)
                print(
                    "UNEXPECTED ERROR %s; [%s] WRITTEN TO: %s"
                    % (r.status_code, error_summary, error_log)
                )

                if length == 5:
                    # Two 500 errors in a row: skip to next record
                    offset, length = next_record(identifier, ol)
                    continue
                if (
                    m
                ):  # a handled, debugged, and logged error, unlikely to be resolved by retrying later:
                    # Skip this record and move to the next
                    offset = offset + length
                else:
                    sleep(SERVER_ISSUES_WAIT)
                length = 5
                print(f"{offset}:{length}")
                continue
            else:  # 4xx errors should have json content, to be handled in default 200 flow
                pass
        except ConnectionError as e:
            print("CONNECTION ERROR: %s" % e.args[0])
            sleep(SHORT_CONNECT_WAIT)
            continue
        # log results to stdout
        try:
            result = r.json()
            offset = result.get("next_record_offset")
            length = result.get("next_record_length")
        except json.decoder.JSONDecodeError:
            result = r.content
        print(f"{identifier}: {r.status_code} -- {result}")
        count += 1
