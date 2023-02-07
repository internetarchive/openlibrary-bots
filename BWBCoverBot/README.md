* What bot account does one use with bwbcoverbot?
=======
# BWBCoverBot
A script to update covers on Open Library using a zip of covers from BWB.

# Setup
Export `OL_ACCESS_KEY` and `OL_SECRET_KEY` (s3) used by the [BWBImportBot](https://openlibrary.org/people/bwbimportbot) account to import.

# Use
Run `python main.py bwbcoverfile.zip`. E.g. `python main.py Apr2021_17_lc_13.zip`.

# How it works
Each zip file from BWB contains hundreds of `.jpg` files. The root of each filename is an ISBN 13 (e.g. `9781483457550.jpg`).

BWBCoverBot goes through the zip and for each `.jpg` file it checks `./bwb-cover-bot.sqlite` to see if the associated ISBN 13 from the `.jpg`'s filename is in the DB, and if `cover_exists` is not 1.

If the cover is not already in the DB, BWBCoverBot it will query the Open Library API, check if there is a cover, add the cover if necessary, and set `cover_exists` to 1.

# Seed BWBCoverBot's database
To avoid unnecessary API calls to see if Open Library already has a cover for each ISBN in the BWB zip, pending a purpose-made dump for this task, [Reconcile](https://github.com/scottbarnes/reconcile/) can generate a pre-seeded database with cover information based on the monthly data dumps. Get the complete data dump, run `poetry run python reconcile/main.py create-db`, and `poetry run python reconcile/main.py create-cover-db`. Then copy the generated `./bwb-cover-bot.sqlite` into the directory with BWBCoverBot.

# Testing
Though testing isn't complete, the majority of BWBCoverBot's interaction with the Open Library API is mocked to make it easier to test script changes without needing to worry about calls to the live Open Library API. Install [pytest](https://pytest.org) and run `python -m pytest ./tests` to test.
