import sys
import json
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from olclient import OpenLibrary

ol = OpenLibrary()
url = 'https://openlibrary.org/api/import'

adapter = HTTPAdapter(max_retries=Retry(
    total=5,
    read=5,
    connect=5,
    backoff_factor=0.3
))
ol.session.mount('https://', adapter)

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

