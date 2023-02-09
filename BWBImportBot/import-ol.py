import json
import os
import sys

import requests
from olclient import OpenLibrary
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

ol = OpenLibrary()
url = "https://openlibrary.org/api/import"

adapter = HTTPAdapter(max_retries=Retry(total=5, read=5, connect=5, backoff_factor=0.3))
ol.session.mount("https://", adapter)

if __name__ == "__main__":
    fname = sys.argv[1]
    start = None

    # Retrieve start point from logfile if one exists
    logfile = os.path.join(fname.rsplit(os.path.sep, 1)[0], "import.log")
    if os.path.exists(logfile):
        with open(logfile) as lin:
            for line in lin:
                pass
            try:
                start = int(line.replace("\n", "").split(":")[0])
            except:
                pass

    with open(fname) as fin:
        for i, raw_data in enumerate(fin):
            # Resume from start if available
            if not start or i > start:
                data = json.loads(raw_data)
                if "error" not in data:
                    if data.get("pagination"):
                        data["number_of_pages"] = data.pop("pagination", None)
                    r = ol.session.post(url, data=json.dumps(data))
                    if r.status_code == 200:
                        print(f"{i}: SUCCESS: {r.content}")
                    else:
                        print(f"{i}: ERROR: {r.content}")
