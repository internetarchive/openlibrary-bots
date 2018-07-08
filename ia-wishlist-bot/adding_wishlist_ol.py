import sys
from olclient.openlibrary import OpenLibrary
import olclient.common as common

import csv, ast
import requests
import json
import unittest

ol = OpenLibrary()
FILE = 'ia-data/new_wishlist_salman_1000.csv'

class TestWishlistAddBook(unittest.TestCase):
    def test_parse_wishlist_csv_row_to_dict(self):
        csv = "foo,bar,baz,qux"
        expected = {"author": "foo", "title": "bar"}
        self.assertTrue(parse_wishlist_csv_row_to_dict(csv) == expected)

    def test_check_if_author_exists(self):
        author = {'author_name': 'J. R. Tolkien',
                  'author_birth_date': 'XXX', 'author_death_date':'XXX'}  # replace XXX w/ valid date
        # great place to check that our code works if certain dates are missing!
        expected = 'OL123A'  # TODO: replace 123 w/ valid olid
        olid = check_if_author_exists(
            author['author_name'], author['author_birth_date'], author['author_death_date'])
        self.assertTrue(expected == olid)


def parse_wishlist_csv_row_to_dict(csv):
    """This function takes a csv row which was output from our whatever process created e.g. *new_wishlist_salman_1000.csv* and converts it into a python dictionary

    Usage:
        >>> parse_wishlist_csv_row_to_dict("foo,bar,baz,qux")
        { "author": "foo", "title": "bar", ...}
    """
    book = {"title": csv[0], "author_name": ast.literal_eval(csv[1]), "language": csv[2], "date": csv[3], "oclc": csv[4], "isbn10": csv[5], "isbn13": csv[6]}
    return book


def check_if_author_exists(author_name, author_birth_data, author_death_date):
    # TODO -- search for author or return None (using olclient's existing methods -- we did this already for our last step)
    author = ol.Author.get_olid_by_name(author_name)
    return author  # this may be None, that's OK


def process_book(book):
    # make sure we've normalized the author name (e.g. first last?)
    author = check_if_author_exists(
        book['author_name'], book['author_birth_date'], book['author_death_date'])
    # TODO: bookcover search, etc
    # TODO: add book to Open Library vie olclient

def process_csv(filename):
    """This function takes a csv file which was output from our whatever process created e.g. *new_wishlist_salman_1000.csv* and converts it into a python dictionary

    Usage:
        >>> parse_wishlist_csv_row_to_dict("foo,bar,baz,qux")
        { "author": "foo", "title": "bar", ...}
    """
    with open(filename, mode='r') as infile:
        reader = csv.reader(infile)

        book_data = [row for row in reader]

        return book_data
        # mydict = {rows[0]: rows[1] for rows in reader}

if __name__ == "__main__":
    # csv_row = sys.argv[1]
    book_data = process_csv(FILE)

    for data in book_data:
        book = parse_wishlist_csv_row_to_dict(data)
        process_book(book)
    # book = parse_wishlist_csv_row_to_dict("foo,bar,baz,qux")
