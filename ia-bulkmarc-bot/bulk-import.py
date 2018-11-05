#!/usr/bin/env python3

""" 
    Iterates over an archive.org bulk MARC item, such as OpenLibraries-Trent-MARCs,
    and imports all records in all of its MARC files to Open Library.

    USAGE: ./bulk-import.py <archive.org item id>

    Logs results to STDOUT
"""

import internetarchive as ia
import sys
from olclient.openlibrary import OpenLibrary
from collections import namedtuple

LIVE = True # False to test against a local dev OL instance
BULK_API = '/api/import/ia'
item = "trent_test_marc"
item = "OpenLibraries-Trent-MARCs"

if len(sys.argv) > 1:
    item = sys.argv[1]

if LIVE:
    ol = OpenLibrary()
else:
    local_dev = 'http://localhost:8080'
    Credentials = namedtuple('Credentials', ['username', 'password'])
    c = Credentials('openlibrary@example.com', 'admin123')
    ol = OpenLibrary(base_url=local_dev, credentials=c)

limit = 20 # if non-zero, a limit to only process this many records from each file, for testing
count = 0

for f in ia.get_files(item):
    if f.name.endswith('.mrc'):
        print('FILENAME: %s' % f.name)
        offset = 0
        length = 5 # we only need to get the length of the first record (first 5 bytes), the API will seek to the end.

        while length:
            identifier = '{}/{}:{}:{}'.format(item, f.name, offset, length)
            data = {'identifier': identifier, 'bulk_marc': 'true'}
            r = ol.session.post(ol.base_url + BULK_API + '?debug=true', data=data)
            try:
                result = r.json()
            except:
                result = {}
                print("UNEXPECTED ERROR WRITTEN TO: debug_%s.html" % count)
                with open('debug_%s.html' % count, 'w') as dout:
                    dout.write(r.content.decode())
            # log results to stdout
            print('{}: {} -- {}'.format(identifier, r.status_code, result))
            offset = result.get('next_record_offset')
            length = result.get('next_record_length')
            count += 1
            if limit and count >= limit:
                # Stop if a limit has been set, and we are over it.
                length = False
        if limit and count >= limit:
            break
