A set of scripts to filter a complete Open Library dump for editions with an Internet Archive ID but now cover id in the edition metadata.
Solves internetarchive/openlibrary/issues/2550. As of 2020-03-31 there are 727810
 borrowable editions with no cover.

##### How To Use
###### Add Covers to Borrowable Editions From Complete Open Library Dump
```bash
bash main.sh /path/to/full/ol/dump.txt.gz /path/to/filtered/edition/dump.txt.gz /path/to/fixed/editions/dump.txt.gz
```
###### Find Borrowable Editions with No Cover
```bash
bash find_coverless_editions_in_library.sh /path/to/full/ol/dump.txt.gz /path/to/filtered/edition/dump.txt.gz
```

###### Add Covers to Borrowable Editions from Filtered Open Library Dump
```bash
python cover_updater.py /path/to/filtered/edition/dump.txt.gz /path/to/fixed/editions/dump.txt.gz
```