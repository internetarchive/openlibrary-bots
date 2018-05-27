# Import the sqlite3 library
import sqlite3
import argparse

def general_info():
    db = sqlite3.connect("/storage/openlibrary/wishlist/isbn_data.db")
    cur = db.cursor
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    table = cur.fetchone()
    print("Table name is: " + str(table))

def find_books():
    db = sqlite3.connect("/storage/openlibrary/wishlist/isbn_data.db")
    cur = db.cursor
    id = (None, None)
    cur.execute("SELECT * FROM data WHERE ia_books_id=? AND ia_works_id=?;",id)
    data = cur.fetchall()
    print("Number of books not on Open Library are: " + len(data))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--general", help="Get General Information about the table")
    parser.add_argument(
        "--find", help="Find books which do not have `ia_books_id` or `ia_works_id`")
    args = parser.parse_args()
    if args.general:
        general_info()
    if args.find:
        find_books()