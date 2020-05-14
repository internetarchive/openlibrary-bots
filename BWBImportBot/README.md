This bot takes partner data from Better World Books and imports (creates or updates) metadat records on OpenLibrary.org using the /api/import json endpoint.

## Cadence

This bot is/should-be run on an ongoing, rolling basis on books-lists VM.

## Data source

Please check books-lists:/bwb-monthly/README.md for info on how source data is processed.

Processing is done internally at the Internet Archive on the books-lists VM in /bwb-monthly.

An example of the raw source data is located in examples.csv.

parse-biblio.py may be used to convert the pipe seperated values into
compatible Open Library json key-vals.

An example of the prepared source data (after parse-biblio) is examples.json.

## Authentication

The account is run as BWBImportBot (login email: openlibrary+bwbimportbot@archive.org)

@mekarpeles + @charles + @cdrini can assist with credentials, see: books-lists:/bwb-monthly/bwbimportbot-creds.txt

## Usage

1. Run `ol --configure` to configure `olclient` prior to use, using BWBImportBot credentials
2. Run `import-ol.py example.json` where example.json is a file containing your json records.
