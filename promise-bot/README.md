# `promise-bot`

A bot for correcting promise item records that were imported between November and December of 2022.

## What does it do, exactly?

For each affected record, `promise-bot` does the following:

1. Removes all but the first `local_id` that begin with `urn:bwbsku`.  The first `local_id` in this form is correct, and should not be removed.
2. Removes all `amazon` and `better_world_book` entries from the record's `identifiers` dictionary.
3. Updates associated `souce_records` entry, ensuring uniqueness.

We intend to re-import all affected records. This means that any data deleted by `promise-bot` will be added to the catalog at a later date, which will result in more than 300k new records being created.

## How to use

Info pending...

## Should I use this bot?

Probably not.  This bot is meant to fix a tranche of ~180k edition records which contain identifiers for multiple editions.  Once those records have been corrected and our import pipeline is processing promise items without error, this bot can be retired.
