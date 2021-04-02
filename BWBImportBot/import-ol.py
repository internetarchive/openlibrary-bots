import os
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
    start = None

    # Retrieve start point from logfile if one exists
    logfile = os.path.join(fname.rsplit(os.path.sep, 1)[0], 'import.log')
    if os.path.exists(logfile):
        with open(logfile) as lin:
            for line in lin:
                pass
            try:
                start = int(line.replace('\n', '').split(':')[0])
            except:
                pass

    with open(fname) as fin:
        for i, raw_data in enumerate(fin):
            # Resume from start if available
            if not start or i > start:
                data = json.loads(raw_data)
                if 'error' not in data:
                    r = ol.session.post(url, data=json.dumps(data))
                    if r.status_code == 200:
                        print('%s: SUCCESS: %s' % (i, r.content))
                    else:
                        print('%s: ERROR: %s' % (i, r.content))
