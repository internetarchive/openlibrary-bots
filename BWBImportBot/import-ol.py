import sys
import json
import requests
from olclient import OpenLibrary

ol = OpenLibrary()
url = 'https://openlibrary.org/api/import'

if __name__ == '__main__':
    fname = sys.argv[1]
    with open(fname) as fin:
        for i, raw_data in enumerate(fin):
            data = json.loads(raw_data)
            if 'error' not in data:
                if data.get('pagination'):
                    data['number_of_pages'] = data.pop('pagination', None)
                r = ol.session.post(url, data=json.dumps(data))
                if r.status_code == 200:
                    print('SUCCESS: ' + r.content)
                else:
                    print('ERROR: ' + r.content)

