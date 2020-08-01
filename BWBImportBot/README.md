This bot takes monthly partner data from Better World Books and imports (creates or updates) metadata records on OpenLibrary.org using the monthly.sh runner, the parse-biblio.py processor, and the import-ol.py wrapper of the /api/import json endpoint.

## Cadence

This bot is/should-be run on an ongoing, rolling basis on books-lists VM by the monthly.sh cron task.

## Data Pipeline

Processing is done internally at the Internet Archive on the books-lists VM in /bwb-monthly.

Data is fetched from BWB via ftp as <Type>.zip Where <Type> is of the set: { Annotations,  Awards,  Bibliographic,  Bios,  Pub }. Bibliographic.zip contains book records to be imported into OL.

1. On the 17th of each month, the latest BWB data should be fetched via FTP using monthly.sh into a directory of the form YYYY-MM/.
2. The files are zipped into a YYYY-MM-DD.zip and uploaded to archive.org/details/book-private for archiving / long-term storage
3. YYYY-MM/Bibliographic.zip is unzipped to YYYY-MM/Bibliographic/YYYY-MM-DD/ which contains Bibliographic source files named by the form: bettworldbks<COUNTRY>*. An example of the raw source data may be found in examples.csv.
4. `parse-biblio.py bettworldbks*` is used to process these Bibliographic source files. This identifies duplicate records (by isbn) and converts BWB pipe seperated source values into import-compatible Open Library json records. An example of the processed source data (after parse-biblio) is examples.json.
5. import-ol.py is used to upload resulting json records into Open Library

IMPORTANT: In order to run monthly.sh, you will need ~/.netrc in @charles or @mek's home dir (containing credentials)

## Authentication

The account is run as BWBImportBot (login email: openlibrary+bwbimportbot@archive.org)

@mekarpeles + @charles + @cdrini can assist with credentials, see: books-lists:/bwb-monthly/bwbimportbot-creds.txt

## Usage

1. Run `ol --configure` to configure `olclient` prior to use, using BWBImportBot credentials
2. Run `import-ol.py example.json` where example.json is a file containing your json records.
