"""
Python Script to query the Wishlist ISBN Data (SQLite Database)

Input: 'isbn_data.db'
* Parameters for the same can be found on https://docs.google.com/spreadsheets/d/1GDATWbgncmQzDaTJVdJU1kVcRhJIuMs0zHUnoCITED0/edit?usp=sharing

Output:
1. general_info() - Giving the list of columns in the `isbn_data` database.
2. find_books() - Finding Books which do not have an Open Library ID
"""

import argparse
import os

# Import the sqlite3 library
import sqlite3
import urllib.request


# General Information behind the SQLite Database
def general_info():
    db = sqlite3.connect("data/isbn_data.db")
    cur = db.cursor
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    table = cur.fetchone()
    print("Table name is: " + str(table))


# Allows users to search for books which do not have an Open Library ID
def find_books():
    db = sqlite3.connect("data/isbn_data.db")
    cur = db.cursor
    id = (None, None)
    cur.execute("SELECT * FROM data WHERE ia_books_id is ? AND ia_works_id is ?;", id)
    data = cur.fetchall()
    print("Number of books not on Open Library are: " + len(data))


if __name__ == "__main__":
    if not os.path.isdir("data"):
        os.mkdir("data")

    if not os.path.exists("data/isbn_data.db"):
        file_name = "data/isbn_data.db"
        urllib.request.urlretrieve(
            "https://archive.org/download/openlibrary-bots/isbn_data.db", file_name
        )

    parser = argparse.ArgumentParser()

    parser.add_argument("--general", help="Get General Information about the table")
    parser.add_argument(
        "--find", help="Find books which do not have `ia_books_id` or `ia_works_id`"
    )

    args = parser.parse_args()

    if args.general:
        general_info()
    if args.find:
        find_books()
