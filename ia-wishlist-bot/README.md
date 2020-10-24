# IA Wishlist Bot

## Description

The IA Wishlist Bot allows users to add books to the Open Library Database where all books are part of a set of books which are added to the Open Library Database.

### General Scripts

1. `fetch_bookcovers.py` - Python Script to fetch bookcovers given ISBN Value either from Amazon, Google API or Betterworld Books.
2. `wishlist_isbn_data.py` - Python Script to interface with a SQLite Database.

### Data dependent Scripts

1. `get_wishlist_works_via_isbn.py` - Python Script to find Open Library Synonyms and works which aren't added to Open Library and outputs list of ISBNs which aren't added to Open Library.
2. `add_wishlist_works.py` - Python Script which inputs a list of ISBNs and outputs details of books to be added.
3. `add_works_via_wishist.py` - Python Script to add works to Open Library from the Metadata collected from the Wishlist using the Open Library Client.   

## Steps followed:

### Step 1: 
* Use the file, `import_wishlist_final.py` with the file, `ia-data/wishlist_works_may_2018.csv` to generate a file called `new_wishlist_july.csv`.

### Step 2: 
* Using the file `new_wishlist_july.csv` run it on the OpenJournal Server (contact Open Library Administrator for access), to add books to Open Library.

## Fetching Bookcovers
Bookcovers can be taken using the following methods: 
1. **Google Books API** - Allows the Open Library Bot to fetch a Bookcover via the Google Books API. Currently being tested with the Google API.
2. **BetterWorld Books** - Bookcovers are fetched from the BetterWorld Books website using Web Scraping.
3. **Amazon** - Bookcovers are directly fetched from the Amazon website using the bs4 Python Package to do web scraping.
