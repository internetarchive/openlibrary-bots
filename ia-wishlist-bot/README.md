# IA Wishlist Bot

## Description

### General Scripts

1. `fetch_bookcovers.py` - Python Script to fetch bookcovers given ISBN Value.
2. `check_wishlist_isbn_data.py` - Python Script to interface with a SQLite Database.

### Data dependent Scripts

1. `get_wishlist_works_via_isbn.py` - Python Script to find Open Library Synonymns and works which aren't added to Open Library and outputs list of ISBNs which aren't added to Open Library.
2. `add_wishlist_works.py` - Python Script which inputs a list of ISBNs and outputs details of books to be added.
3. `add_works_via_wishist.py` - Python Script to add works to Open Library from the Metadata collected from the Wishlist using the Open Library Client.   

## Steps followed:
TODO

## Fetching Bookcovers
Bookcovers can be taken using the following methods: 
1. Google Books API - Allows you to fetch Bookcover via API.
2. BetterWorld Books - Can be done using Web Scraping.
3. Amazon - Can be fetched using Web Scraping.