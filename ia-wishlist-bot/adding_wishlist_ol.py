import ast
import csv
import json
import sys
import unittest

import olclient.common as common
import requests
from olclient.openlibrary import OpenLibrary

ol = OpenLibrary()
FILE = "ia-data/new_wishlist_salman_1000.csv"


class TestWishlistAddBook(unittest.TestCase):
    def test_parse_wishlist_csv_row_to_dict(self):
        csv = [
            "Larks in a paradise: New Zealand portraits",
            "['McNeish, James', 'Friedlander, Marti']",
            "eng",
            "1974",
            "16289249",
            "0002114976",
            "9780002114974",
        ]
        expected = {
            "title": "Larks in a paradise: New Zealand portraits",
            "authors": ["McNeish, James", "Friedlander, Marti"],
            "language": "eng",
            "date": "1974",
            "oclc": "16289249",
            "isbn10": "0002114976",
            "isbn13": "9780002114974",
        }

        self.assertTrue(parse_wishlist_csv_row_to_dict(csv) == expected)

    def test_get_author_object(self):
        author = {"author_name": "JK Rowling"}
        expected = common.Author(name="JK Rowling")
        author_obj = get_author_object(
            author.get("author_name"),
            author.get("author_birth_date"),
            author.get("author_death_date"),
        )

        self.assertTrue(
            expected.name == author_obj.name
            and expected.identifiers == author_obj.identifiers
        )

    def test_get_bookcover(self):
        csv = [
            "Mom Goes to War(Light)",
            "[' Irene Aparici Martin']",
            "eng",
            "1974",
            "16289249",
            "8415503202",
            "9788415503200",
        ]

        book = parse_wishlist_csv_row_to_dict(csv)
        expected_url = "https://images.betterworldbooks.com/841/9788415503200.jpg"

        self.assertTrue(expected_url == get_bookcover(book))

    def test_empty_bookcover(self):
        csv = [
            "Alicia a trave s del espejo La caza del snark",
            "['Lewis Carroll']",
            "Spanish",
            "2002",
            "893562252",
            "9706664998",
            "9789706664990",
        ]
        book = parse_wishlist_csv_row_to_dict(csv)
        expected_url = None

        self.assertTrue(expected_url == get_bookcover(book))


def process_csv(filename):
    """This function takes a csv file which was output from our whatever process created e.g. *new_wishlist_salman_1000.csv* and converts it into a python dictionary

    Usage:
        >>> parse_wishlist_csv_row_to_dict("foo,bar,baz,qux")
        { "author": "foo", "title": "bar", ...}
    """
    with open(filename, mode="r") as infile:
        reader = csv.reader(infile)

        book_data = [row for row in reader]

        return book_data


def parse_wishlist_csv_row_to_dict(csv):
    """This function takes a csv row which was output from our whatever process created e.g. *new_wishlist_salman_1000.csv* and converts it into a python dictionary

    Usage:
        >>> parse_wishlist_csv_row_to_dict("foo,bar,baz,qux")
        { "author": "foo", "title": "bar", ...}
    """
    book = {
        "title": csv[0],
        "authors": ast.literal_eval(csv[1]),
        "language": csv[2],
        "date": csv[3],
        "oclc": csv[4],
        "isbn10": csv[5],
        "isbn13": csv[6],
    }
    return book


import re


def get_author_object(author_name, author_birth_date=None, author_death_date=None):
    """This takes an author name which was output from our CSV row and then either retrieves an ol Object which was already created or creates a new OL Object

    Usage:
        >>> get_author_object('Dan Brown')
    """
    if "," in author_name:
        author_name = author_name.split(",")
        author_name = author_name[1] + " " + author_name[0]

    while True:
        author_name_new = re.sub(r"\([^\(]*?\)", r"", author_name)
        if author_name_new == author_name:
            break
        author_name = author_name_new

    author_olid = ol.Author.get_olid_by_name(author_name)
    if author_olid:
        return ol.get(author_olid)
    else:
        return common.Author(name=author_name)


def get_bookcover(book):
    url = (
        "https://images.betterworldbooks.com/"
        + book.get("isbn10")[0:3]
        + "/"
        + book.get("isbn13")
        + ".jpg"
    )

    r = requests.get(url)

    if r.status_code == 200:
        return url
    return None


def add_book_via_olclient(book, author_list, bookcover=None):

    if len(author_list) != 0:
        # Define a Book Object
        new_book = common.Book(
            title=book.get("title"),
            authors=author_list,
            publish_date=book.get("date"),
            language=book.get("language"),
        )

        # Add metadata like ISBN 10 and ISBN 13
        new_book.add_id("isbn_10", book.get("isbn10"))
        new_book.add_id("isbn_13", book.get("isbn13"))
        new_book.add_id("oclc", book.get("oclc"))

        print(new_book)
        try:
            newer_book = ol.create_book(new_book)
            if bookcover:
                newer_book.add_bookcover(bookcover)
        except Exception as e:
            print("Book already exists!")

    else:
        print("No authors added. Work " + book.get("title") + " has been skipped.")


def process_book(book):
    # make sure we've normalized the author name (e.g. first last?)
    author_list = []
    for author_name in book.get("authors"):
        author_list.append(get_author_object(author_name))

    # Bookcover search, etc
    bookcover = get_bookcover(book)

    # Add book to Open Library via olclient
    add_book_via_olclient(book, author_list, bookcover)


if __name__ == "__main__":
    # csv_row = sys.argv[1]
    # unittest.main()

    book_data = process_csv(FILE)

    for data in book_data:
        book = parse_wishlist_csv_row_to_dict(data)
        process_book(book)

        print("Book has been processed")
    # book = parse_wishlist_csv_row_to_dict("foo,bar,baz,qux")
