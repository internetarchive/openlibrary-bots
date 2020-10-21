#!/usr/bin/python

import isbnlib
import json
import sys

# Extracts ISBN_13 OLID W-WOLID from openlibrary edition data dumps.
#
# Takes an Open Library edition dump as input and outputs tsv of:
#
# <ISBN13> <Edition-OLID> (<Work-OLID> | NONE)
#   OR
# 'BAD-ISBN:' <bad isbn> <Edition-OLID> (<Work-OLID> | NONE)
# if the isbn does not validate.
#

infile = "/storage/openlibrary/ol_dump_editions_2018-06-30.txt"
infile = sys.argv[1] 

with open(infile) as f:
    for line in f:
        data = line.split("\t")
        book = json.loads(data[4])
        olid = book.get('key').replace('/books/', '')
        wolid = book.get('works', 'NONE')
        if wolid != 'NONE':
           wolid = wolid[0]['key'].replace('/works/', '')

        # get isbn
        good_isbn = []
        bad_isbn = []
        isbn_13 = book.get('isbn_13', [])
        isbn_10 = book.get('isbn_10', [])
        for isbn in isbn_13 + isbn_10:
            canonical = isbnlib.get_canonical_isbn(isbn)
            if canonical: 
                if len(canonical) == 10:
                    canonical = isbnlib.to_isbn13(canonical)
                good_isbn.append(canonical)
            else:
                bad_isbn.append(isbn)

        isbns = set(good_isbn)
        for isbn in isbns:
            try:
                assert isbnlib.get_canonical_isbn(isbn)
                print("\t".join([isbnlib.get_canonical_isbn(isbn), olid, wolid]))
            except Exception as e:
                bad_isbn.append(isbn)

        for bad in bad_isbn:
            print(u"\t".join([u'BAD-ISBN:', repr(bad), olid, wolid]))

