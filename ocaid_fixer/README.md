###### Introduction
Less of a bot and more a script to resolve [openlibrary/2651](https://github.com/internetarchive/openlibrary/issues/2651). The script searches for editions with Internet Archive scans but no `ocaid` attribute. The `olid` and `ocaid` are stored as the first and second column respectively of a tab-seperated csv file. Since only admins can add `ocaid`s to editions, somone on the OL team can later use this csv file to correct the ~20k malformed editions.

##### How To Use
```bash
$ python ocaid_fixer.py path/to/editions/dump.txt
```
###### Example
```bash
$ python ocaid_fixer.py ol_dump_editions_2020-02-29.txt
```
