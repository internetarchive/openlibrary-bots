A set of scripts to normalize (remove hypens and capitolize letters) in ISBNs.
Currently, this makes editions discoverable via search

### How To Use
#### Find Editions with ISBNs
```bash find_editions_with_isbns.sh /path/to/ol_dump.txt.gz /path/to/filtered_dump.txt.gz```
#### Normalize ISBNs from Filtered Data Damp
```python normalize_isbns.py --dump_path=/path/to/filtered_dump.txt.gz --dry_run=<bool> --limit=<init>```
If `dry_run` is True, the script will run as normal, but no changes will be saved to OpenLibrary.
This is for debugging purposes. By default, `dry_run` is `True`.
`limit` is the maximum number of changes to OpenLibrary that will occur before the script quits.
By default, `limit` is set to `1`. Setting `limit` to `0` allows unlimited edits.
A log is automatically generated whenever `normalize_isbns.py` executes.