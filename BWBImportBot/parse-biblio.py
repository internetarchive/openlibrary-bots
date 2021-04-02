#!/usr/bin/env python3
import sys
import json

"""
   Process bibliographic data file and output JSON suitable for importing
   into the Open Library JSON import API
   https://openlibrary.org/api/import
"""


class Biblio:
    def __init__(self, data):
        self.data = data
        self.title = data[10]
        #self.author = data[21]
        #self.author_role = data[22]
        self.publisher = data[135]
        self.publication_date = data[20][:4]  # YYYY, YYYYMMDD
        self.copyright = data[19]
        self.isbn = data[124]
       
        self.pages = data[36]
        self.language = data[37].lower()
        self.issn = data[54]

        self.doi = data[145]
        self.lccn = data[146]
        self.lc_class = data[147]
        self.dewey = data[49]

        self.weight = data[39]
        self.length = data[40]
        self.width  = data[41]
        self.height = data[42]

        self.subjects = self.subjects()
        assert self.isbn

    def subjects(self):
        subjects = data[91:100]
        subjects = [s.capitalize().replace('_', ', ') for s in subjects if s]
        # subjects += data[101:120]
        # subjects += data[153:158]
        return subjects

    def contributors(self):
        contributors = []
        for i in range(5):
            contributors.append([self.data[21+i*3], self.data[22+i*3], self.data[23+i*3]])

        # form list of author dicts
        authors = [self.make_author(c) for c in contributors if c[0]]
        return authors

    def make_author(self, contributor):
        author = {'name': contributor[0]}
        if contributor[2] == 'X':
            # set corporate contributor
            author['entity_type'] = 'org'
        # TODO: sort out contributor types
        # AU = author
        # ED = editor
        return author

    def json(self, decode=False):
        a = {'title': self.title,
             'isbn_13': [self.isbn],
             'publish_date': self.publication_date,
             'publishers': [self.publisher],
             'authors': self.contributors(),


             'lc_classifications': [self.lc_class],
             'pagination': self.pages,
             'languages': [self.language],
             'subjects': self.subjects,
             'source_records': ['bwb:%s' % self.isbn],
        }
        return a



if __name__ == '__main__':
    fnames = sys.argv[1:]

    seen_isbns = set()

    for fname in fnames:
        with open(fname, 'r') as f:
            for line in f:
                data = line.strip().split('|')
                b = Biblio(data)
                isbn = b.isbn
                if isbn in seen_isbns:
                    print(json.dumps({
                        "isbn": isbn,
                        "status": "error",
                        "reason": "duplicate_isbn"
                    }))
                else:
                    try:
                        print(json.dumps(b.json()))
                    except UnicodeDecodeError:
                        pass  # for now
                    seen_isbns.add(isbn)



