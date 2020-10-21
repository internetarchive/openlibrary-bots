#!/usr/bin/env python3

""" 
    Iterates over an archive.org bulk MARC item, such as OpenLibraries-Trent-MARCs,
    and imports all records in all of its MARC files to Open Library.

    USAGE: ./bulk-import.py <archive.org item id>

    Logs results to STDOUT
"""

import argparse
import internetarchive as ia
import os
import re
from collections import namedtuple
from olclient.openlibrary import OpenLibrary
from glob import glob


BULK_API = '/api/import/ia'
LOCAL_ID = re.compile(r'\/local_ids\/(\w+)')
MARC_EXT = re.compile(r'.*\.(mrc|utf8)$')


def get_marc21_files(item):
    return [f.name for f in ia.get_files(item) if MARC_EXT.match(f.name)]


def log_error(response):
    n = 0
    current_errors = glob('error*.html')
    for f in current_errors:
        n = max(n, 1 + int(re.search(r'[0-9]+', os.path.splitext(f)[0]).group(0)))
    name = 'error_%d.html' % n
    with open(name, 'w') as error_log:
        error_log.write(response.content.decode())
    return name


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Bulk MARC importer.')
    parser.add_argument('item', help='Source item containing MARC records', nargs='?')
    parser.add_argument('-i', '--info', help='List available MARC21 .mrc files on this item', action='store_true')
    parser.add_argument('-b', '--barcode', help='Barcoded local_id available for import', nargs='?', const=True, default=False)
    parser.add_argument('-f', '--file', help='Bulk MARC file to import')
    parser.add_argument('-n', '--number', help='Number of records to import', type=int, default=1)
    parser.add_argument('-o', '--offset', help='Offset in BYTES from which to start importing', type=int, default=0)
    parser.add_argument('-l', '--local', help='Import to a locally running Open Library dev instance for testing (localhost:8080)', action='store_true')
    parser.add_argument('-d', '--dev', help='Import to dev.openlibrary.org Open Library dev instance for testing', action='store_true')

    args = parser.parse_args()
    item = args.item
    fname = args.file
    local_testing = args.local
    dev_testing = args.dev
    barcode = args.barcode

    if local_testing:
        Credentials = namedtuple('Credentials', ['username', 'password'])
        local_dev = 'http://localhost:8080'
        c = Credentials('openlibrary@example.com', 'admin123')
        ol = OpenLibrary(base_url=local_dev, credentials=c)
    elif dev_testing:
        ol = OpenLibrary(base_url='https://dev.openlibrary.org')
    else:
        ol = OpenLibrary()

    print('Importing to %s' % ol.base_url)
    print('ITEM: %s' % item)
    print('FILENAME: %s' % fname)

    if args.info:
        if barcode is True:
            # display available local_ids
            print('Available local_ids to import:')
            r = ol.session.get(ol.base_url + '/local_ids.json')
            print(LOCAL_ID.findall(r.json()['body']['value']))
        if item:
            # List MARC21 files, then quit.
            print('Item %s has the following MARC files:' % item)
            for f in get_marc21_files(item):
                print(f)
        ol.session.close()
        exit()

    limit = args.number  # if non-zero, a limit to only process this many records from each file
    count = 0
    offset = args.offset
    length = 5  # we only need to get the length of the first record (first 5 bytes), the API will seek to the end.

    while length:
        if limit and count >= limit:
            # Stop if a limit has been set, and we are over it.
            break
        identifier = f'{item}/{fname}:{offset}:{length}'
        data = {'identifier': identifier, 'bulk_marc': 'true'}
        if barcode and barcode is not True:
            # A local_id key has been passed to import a specific local_id barcode
            data['local_id'] = barcode
        r = ol.session.post(ol.base_url + BULK_API + '?debug=true', data=data)
        try:
            result = r.json()
        except:
            result = {}
            if r.status_code < 500:
                error_summary = re.search(r'<h2>(.*)</h2>', r.content.decode()).group(1)
            else:
                error_summary = ''
            # Write error log
            error_log = log_error(r)
            print(f"UNEXPECTED ERROR {r.status_code}; [{error_summary}] WRITTEN TO: {error_log}")
            # Skip this record and move to the next
            # FIXME: this fails if there are 2 errors in a row :(
            if length == 5:
                # break out of everything, 2 errors in a row
                count = limit
                break
            offset = offset + length
            length = 5
            print(f"{offset}:{length}")
            continue
        # log results to stdout
        print(f'{identifier}: {r.status_code} -- {result}')
        offset = result.get('next_record_offset')
        length = result.get('next_record_length')
        count += 1
