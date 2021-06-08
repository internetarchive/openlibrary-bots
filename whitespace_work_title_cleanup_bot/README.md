A remix of making_a_bot.py for works
### How To Use
```bash
# Normalize ISBNs from Work Filtered Data Dump
python whitespace_work_title_cleanup.py --dump_path=/path/to/filtered_dump.txt.gz --dry_run=<bool> --limit=<init>
```
If `dry_run` is True, the script will run as normal, but no changes will be saved to OpenLibrary.
This is for debugging purposes. By default, `dry_run` is `True`.
`limit` is the maximum number of changes to OpenLibrary that will occur before the script quits.
By default, `limit` is set to `1`. A log is automatically generated whenever `whitespace_work_title_cleanup.py` executes in logs folder.
