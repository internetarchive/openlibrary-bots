# IA Sync Bot



## extract-isbn.py

Takes an Open Library edition dump as input and outputs tsv of:

`<ISBN13> <Edition-OLID> (<Work-OLID> | 'NONE')`

  OR
  
`'BAD-ISBN:' <bad isbn> <Edition-OLID> (<Work-OLID> | 'NONE')`

if the isbn does not validate.

Examples:
```
9780107805401   OL10000135M     OL7925046W
BAD-ISBN:       u'0000000002'   OL25422504M     OL16800386W
```

## legacy-openlibrary-id-check.sh
collects data from https://archive.org and https://openlibrary.org and creates lists and stats on archive.org
items that have old-style `openlibrary` IDs, but no `openlibrary-edition`

## update-ocaid.py
Takes results of archive.org json search results and writes ocaids to Open Library items, and performs a sync.
