A set of scripts to add isbn_13 values to editions with IA/ocaid references containing one.
### How To Use
```bash
# Find Editions with IA ISBN, but no ISBN 13
 ./find_editions_with_isbnianot13.sh /path/to/ol_dump.txt.gz /path/to/filtered_dump.txt.gz
# Add ISBN 13s converted from the ia ocaid source
python isbn_ia_to_13.py --dump_path=/path/to/filtered_dump.txt.gz --dry_run=<bool> --limit=<init>
```
If `dry_run` is True, the script will run as normal, but no changes will be saved to OpenLibrary.
This is for debugging purposes. By default, `dry_run` is `True`.
`limit` is the maximum number of changes to OpenLibrary that will occur before the script quits.
By default, `limit` is set to `1`. Setting `limit` to `0` allows unlimited edits.
A log is automatically generated whenever `isbn_ia_to_13.py` executes.
