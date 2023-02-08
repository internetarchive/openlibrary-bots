# `promise-bot`

A bot for correcting promise item records that were imported between November and December of 2022.

## What does it do, exactly?

For each affected record, `promise-bot` does the following:

1. Removes all but the first `local_id` that begin with `urn:bwbsku`.  The first `local_id` in this form is correct, and should not be removed.
2. Removes all `amazon` and `better_world_book` entries from the record's `identifiers` dictionary.
3. Updates associated `souce_records` entry, ensuring uniqueness.

We intend to re-import all affected records. This means that any data deleted by `promise-bot` will be added to the catalog at a later date, which will result in more than 300k new records being created.

Note that this bot is intended to fix records in batches.  The affected records will be read from an input file.  Once a batch has been processed, the line number of the next unprocessed input file line is written to a state file.

## How to use

### Initial Set-up
Run the following to create a virtual environment:
`python3 -m venv /path/to/new/virtual/environment`

Then, install dependencies:
```
source venv/bin/activate
python install -r requirements.txt
```

### Running the bot
This bot can be configured by a file, or from the command-line.  Regardless of how the bot is started, a configuration file containing the Open Library Client credentials in an `[s3]` section is required.

#### Running with file configuration
Create a new configuration file (or modify the existing one), and run the following:

`python fix_promise_items.py config /path/to/config/file`

If you are running the bot this way, and a state file exists, the `start_line` is overridden by the line number in the state file.

#### Running from the command-line
Run the following to start the bot with command-line configurations:

`python fix_promise_items.py cli /path/to/input/file [options]`

Unlike running the bot from a configuration file, `start_line` *is not* overridden by the contents of the state file.  This must be explicitly set if you want to start processing the input file from a specific line number.

For more information, run `python fix_promise_items.py cli -h`

### The Input File
This bot requires an input file containing all of the affected records.  The input file is expected to be tab-delimited, and each line will have the following format:
`{N number of skus} {edition_key} {sku 1} [...] {sku N}`

## Should I use this bot?

Probably not.  This bot is meant to fix a tranche of ~180k edition records which contain identifiers for multiple editions.  Once those records have been corrected and our import pipeline is processing promise items without error, this bot can be retired.
