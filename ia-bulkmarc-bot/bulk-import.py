#!/usr/bin/env python3

""" 
    Iterates over an archive.org bulk MARC item, such as OpenLibraries-Trent-MARCs,
    and imports all records in all of its MARC files to Open Library.

    USAGE: ./bulk-import.py <archive.org item id>

    Logs results to STDOUT
"""

import internetarchive as ia
import re, sys
from olclient.openlibrary import OpenLibrary
from collections import namedtuple

LIVE = True # False to test against a local dev OL instance
BULK_API = '/api/import/ia'
item = "trent_test_marc"
item = "OpenLibraries-Trent-MARCs"

Credentials = namedtuple('Credentials', ['username', 'password'])

if len(sys.argv) > 1:
    item = sys.argv[1]

if LIVE:
    ol = OpenLibrary()
    #ol = OpenLibrary(base_url='https://dev.openlibrary.org')
else:
    local_dev = 'http://localhost:8080'
    c = Credentials('openlibrary@example.com', 'admin123')
    ol = OpenLibrary(base_url=local_dev, credentials=c)

limit = 50000 # if non-zero, a limit to only process this many records from each file
count = 0

completed_mrc = [
        'lbrn.mrc',
        'multi1.mrc',
        'tier1.mrc',    # DONE
        'tier2.mrc',    # DONE
        'tier3.mrc',    # DONE
        'tier4.mrc',    # DONE
        'multi2.mrc',   # NOT DONE, skipping 2nd multi for now in case there are issues
        ]

for f in ia.get_files(item):
    if f.name.endswith('.mrc'):
        print('FILENAME: %s' % f.name)
        if f.name in completed_mrc:
            continue
        offset = 0
        if f.name == 'tier5.mrc':
            offset = 19885954
        length = 5 # we only need to get the length of the first record (first 5 bytes), the API will seek to the end.

        while length:
            count += 1
            if limit and count >= limit:
                # Stop if a limit has been set, and we are over it.
                break
            identifier = '{}/{}:{}:{}'.format(item, f.name, offset, length)
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
        if limit and count >= limit:
            break
