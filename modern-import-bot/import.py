#!/usr/bin/env python
from olclient.openlibrary import OpenLibrary
import sys
import time
ol = OpenLibrary()

fname = sys.argv[1]
delay = 3

with open(fname) as f:
    for line in f:
        isbn = line.strip()
        time.sleep(delay)
        r = ol.session.get(ol.base_url + "/isbn/" + isbn)
        if r.status_code == 404:
            status = "NOT FOUND"
            olid   = ''
        elif r.status_code == 200:
            olid = r.url
            if 'milliseconds ago' in str(r.content) and '?m=history">1 revision</a>' in str(r.content):
                status = 'CREATED'
            else:
                status = 'FOUND'
        else:
            status = 'ERROR'
        print("{}: {}{}".format(isbn, status, " AS %s" % olid if olid else ''))

