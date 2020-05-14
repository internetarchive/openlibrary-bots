"""
BWBImportBot
Import BWB metadata into OpenLibrary.org

Original import used books-lists:/bwb-monthly/books-published-in-2020.csv
"""

import sys
import json
import requests
from olclient import OpenLibrary

url = 'https://openlibrary.org/api/import'
input_file = sys.argv[1] 
ol = OpenLibrary()

with open(input_file) as fin:
    for i, raw_data in enumerate(fin):

        # If you only want to run
        
        #if i < 1000:
        #    continue
        #if i > 10000:
        #    break

        # keep track of index, in case we break --
        # later, write this to log (to/and enable graceful restart)
        print('=' * 10)
        print(i)
        print('=' * 10)

        # this is a fix for legacy data which incorrectly used
        # `pagination` as a key instead of `number_of_pages`
        data = json.loads(raw_data)
        if data.get('pagination'):
            data['number_of_pages'] = data.pop('pagination', None)
            
        r = ol.session.post(url, data=json.dumps(data))

        # hacky reporting
        print(r)
        if r.status_code == 400:
            print('X' * 10)
            print(raw_data)
        print(r.content)
