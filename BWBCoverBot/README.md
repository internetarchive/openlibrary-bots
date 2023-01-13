* What bot account does one use with bwbcoverbot?
=======
# BWBCoverBot
A script to update covers on Open Library using zips of covers from BWB.

# Use
`python main.py bwbcoverfile.zip`. E.g. `python main.py Apr2021_17_lc_13.zip`.

# How it works
Each zip file from BWB contains hundreds of `.jpg` files, each prefixed with an ISBN 13 (e.g. `9781483457550.jpg`).

BWBCoverBot goes through the zip and for each file it checks `./bwb-cover-bot.sqlite` to see if the ISBN 13 is in the DB, and if `cover_exists` is 1.

If the cover is already in the DB, BWBCoverBot moves on, but if it's not, it will query the Open Library API, check if there is a cover, add the cover if necessary, and update `cover_exists`.

# Seed BWBCoverBot's database
To avoid unnecessary API calls to see if Open Library already has a cover for each ISBN in the BWB zip, [Reconcile](https://github.com/scottbarnes/reconcile/) can generate a pre-seeded database with cover information based on the monthly data dumps. Get the complete data dump, run `poetry run python reconcile/main.py create-db`, and `poetry run python reconcile/main.py create-cover-db`. Then copy the generated `./bwb-cover-bot.sqlite` into the directory with BWBCoverBot.
