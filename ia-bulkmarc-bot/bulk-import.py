#!/usr/bin/env python3

""" 
    Iterates over an archive.org bulk MARC item, such as OpenLibraries-Trent-MARCs,
    and imports all records in all of its MARC files to Open Library.

    USAGE: ./bulk-import.py <archive.org item id>

    Logs results to STDOUT
"""

import argparse
import internetarchive as ia
import re
import sys
from collections import namedtuple
from olclient.openlibrary import OpenLibrary

LIVE = True  # False to test against a local dev OL instance
BULK_API = '/api/import/ia'

Credentials = namedtuple('Credentials', ['username', 'password'])


def get_marc21_files(item):
    return [f.name for f in ia.get_files(item) if f.name.endswith('.mrc')]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Bulk MARC importer.')
    parser.add_argument('item', help='Source item containing MARC records')
    parser.add_argument('-i', '--info', help='List available MARC21 .mrc files on this item', action='store_true')
    parser.add_argument('-f', '--file', help='Bulk MARC file to import')
    parser.add_argument('-l', '--limit', help='Number of records to import', type=int, default=1)
    parser.add_argument('-o', '--offset', help='Offset in BYTES from which to start importing', type=int, default=0)

    args = parser.parse_args()
    item = args.item
    fname = args.file

    if args.info:
        # List MARC21 files, then quit.
        for f in get_marc21_files(item):
            print(f)
        exit()

    if LIVE:
        ol = OpenLibrary()
        #ol = OpenLibrary(base_url='https://dev.openlibrary.org')
    else:
        local_dev = 'http://localhost:8080'
        c = Credentials('openlibrary@example.com', 'admin123')
        ol = OpenLibrary(base_url=local_dev, credentials=c)

    limit = args.limit  # if non-zero, a limit to only process this many records from each file
    count = 0

    print('FILENAME: %s' % fname)
    offset = args.offset
    length = 5  # we only need to get the length of the first record (first 5 bytes), the API will seek to the end.

    while length:
        if limit and count >= limit:
            # Stop if a limit has been set, and we are over it.
            break
        identifier = '{}/{}:{}:{}'.format(item, fname, offset, length)
        data = {'identifier': identifier, 'bulk_marc': 'true'}
        r = ol.session.post(ol.base_url + BULK_API + '?debug=true', data=data)
        try:
            result = r.json()
        except:
            result = {}
            error_summary = re.search(r'<h2>(.*)</h2>', r.content.decode()).group(1)
            print("UNEXPECTED ERROR %s; [%s] WRITTEN TO: debug_%s.html" % (r.status_code, error_summary, count))
            with open('debug_%s.html' % count, 'w') as dout:
                dout.write(r.content.decode())
            # Skip this record and move to the next
            # FIXME: this fails if there are 2 errors in a row :(
            if length == 5:
                # break out of everything, 2 errors in a row
                count = limit
                break
            offset = offset + length
            length = 5
            print("%s:%s" % (offset, length))
            continue
        # log results to stdout
        print('{}: {} -- {}'.format(identifier, r.status_code, result))
        offset = result.get('next_record_offset')
        length = result.get('next_record_length')
        count += 1
