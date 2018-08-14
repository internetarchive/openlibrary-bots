#IA Sync Bot



##extract-isbn.py

Takes an Open Library edition dump as input and outputs tsv of:

<ISBN13> <Edition-OLID> (<Work-OLID> | NONE)
  OR
'BAD-ISBN:' <bad isbn> <Edition-OLID> (<Work-OLID> | NONE)

if the isbn does not validate.

Examples:
9780107805401   OL10000135M     OL7925046W
BAD-ISBN:       u'0000000002'   OL25422504M     OL16800386W

