##### Introduction
Less of a bot and more a script to resolve [openlibrary/2651](https://github.com/internetarchive/openlibrary/issues/2651).
This set of scripts searches for editions with a valid Internet Archive scan but no `ocaid` attribute. 
The `olid` and `ocaid` are stored as the first and second column respectively of a tab-separated csv file.
Since only admins can add `ocaid`s to editions, someone on the OL team can later use this tsv file to correct the ~58k malformed editions as of 2020-02-29.

##### How To Use
######Store editions that have a valid Internet Archive scan but no `ocaid` attribute.
```bash
$ bash main.sh path/to/edition/dump.txt.gz path/to/missing/ocaid/output/dump.tsv.gz path/to/validated/output/file.tsv.gz
```

###### Store editions with Internet Archive scans but no `ocaid`, regardless of the validity of the scan.
Editions found in this script **are not necessarily malformed**.
The output of this file should be passed to `missing_ocaid_finder.py` to confirm which editions are malformed.
```bash
$ bash no_ocaid_filter.sh path/to/edition/dump.txt.gz
```

######Store editions with a valid Internet Archive scan but no `ocaid` property.

_NOTE_: this is _**slow**_ since it makes repeated requests to the IA API, with retries and exponential rate-limiting.
```bash
$ python missing_ocaid_finder.py path/to/mising/ocaid/dump.tsv.gz path/to/output/file.tsv.gz
```