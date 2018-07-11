import sys
from olclient.openlibrary import OpenLibrary
import olclient.common as common

import csv, ast
import requests
import json
import unittest

ol = OpenLibrary()
# Sample File to parse through the records
FILE = 'ia-data/sample_wishlist.csv'


class TestWishlistAddBook(unittest.TestCase):
    # Check: Parsing a CSV Row into a Dictionary
    def test_parse_wishlist_csv_row_to_dict(self):
        csv = ["Larks in a paradise: New Zealand portraits", "['McNeish, James', 'Friedlander, Marti']", "eng", "1974", "16289249", "0002114976", "9780002114974"]
        expected = {"title": "Larks in a paradise: New Zealand portraits", "authors": [
            'McNeish, James', 'Friedlander, Marti'], "language": "eng", "date": "1974", "oclc": "16289249", "isbn10": "0002114976", "isbn13": "9780002114974"}

        self.assertTrue(parse_wishlist_csv_row_to_dict(csv) == expected)

    # Check: Ensure Author Object
    def test_get_author_object(self):
        author = {'author_name': 'JK Rowling'}
        expected = common.Author(name='JK Rowling')
        author_obj = get_author_object(author.get('author_name'), author.get('author_birth_date'), author.get('author_death_date'))

        self.assertTrue(expected.name == author_obj.name and expected.identifiers == author_obj.identifiers)

    # Bookcover to be obtained
    def test_get_bookcover(self):
        csv = ["Mom Goes to War(Light)", "[' Irene Aparici Martin']","eng", "1974", "16289249", "8415503202", "9788415503200"]

        book = parse_wishlist_csv_row_to_dict(csv)
        expected_url = "https://images.betterworldbooks.com/841/9788415503200.jpg"

        self.assertTrue(expected_url == get_bookcover(book))

    # Empty Bookcover retained
    def test_empty_bookcover(self):
        csv = ["Alicia a trave s del espejo La caza del snark", "['Lewis Carroll']",
               "Spanish", "2002", "893562252", "9706664998", "9789706664990"]
        book = parse_wishlist_csv_row_to_dict(csv)
        expected_url = None

        self.assertTrue(expected_url == get_bookcover(book))


def process_csv(filename):
    """This function takes a csv file which was output from our whatever process created e.g. *new_wishlist_salman_1000.csv* and converts it into a python dictionary
    
    Args:
        filename - Parse through a valid CSV File

    Returns:
        (List) of book data

    Usage:
        >>> process_csv("data/sample_wishlist.csv")
        [["Eagle's Trees and shrubs of New Zealand.", "['Eagle, Audrey Lily']", 'English', '1982', '12334838', '0002165325', '9780002165327']]
    """
    with open(filename, mode='r') as infile:
        reader = csv.reader(infile)

        book_data = [row for row in reader]

        return book_data

def parse_wishlist_csv_row_to_dict(data):
    """This function takes a csv row which was output from our whatever process created e.g. *new_wishlist_salman_1000.csv* and converts it into a python dictionary

    Args:
        data - List of Book data

    Returns:
        Dictionary of Book Data

    Usage:
        >>> parse_wishlist_csv_row_to_dict(["Larks in a paradise: New Zealand portraits", "['McNeish, James', 'Friedlander, Marti']", 'English', '1974', '16289249', '0002114976', '9780002114974'])
        {"title": "Larks in a paradise: New Zealand portraits", "authors": ['McNeish, James', 'Friedlander, Marti'], "language": "eng", "date": "1974", "oclc": "16289249", "isbn10": "0002114976", "isbn13": "9780002114974"}    
    """
    book = {"title": data[0], "authors": ast.literal_eval(data[1]), "language": data[2], "date": data[3], "oclc": data[4], "isbn10": data[5], "isbn13": data[6]}
    return book


def get_author_object(author_name, author_birth_date=None, author_death_date=None):
    """This takes an author name which was output from our CSV row and then either retrieves an ol Object which was already created or creates a new OL Object

    Args:
        author_name -  (string) for Author Name
        author_birth_date - (string) in the format %d/%m/%y
        author_death_date - (string) in the format %d/%m/%y

    Returns:
        Open Library Author object

    Usage:
        >>> get_author_object('Dan Brown')
    """
    author_olid = ol.Author.get_olid_by_name(author_name)
    if author_olid:
        return ol.get(author_olid)
    else:
        return common.Author(name=author_name)

def get_bookcover(book):
    """This takes an book json and goes to Betterworld Books to get the correct Bookcover for that image

    Args:
        book - (json) containing isbn10 and isbn13

    Returns:
        URL to bookcover for that book

    Usage:
        >>> get_bookcover({'title': 'Mom Goes to War(Light)', 'authors': [' Irene Aparici Martin'], 'language': 'eng', 'date': '1974', 'oclc': '16289249', 'isbn10': '8415503202', 'isbn13': '9788415503200'})
        'https://images.betterworldbooks.com/841/9788415503200.jpg'
    """

    url = "https://images.betterworldbooks.com/" + book.get('isbn10')[0:3] + "/" + book.get('isbn13') + ".jpg"
    
    r =requests.get(url)

    if r.status_code == 200:
        return url
    return None

def add_book_via_olclient(book, author_list, bookcover=None):
    """This method takes a book json, list of author object and a bookcover(optional) and adds the given Book Record to Open Library

    Args:
        book - (json) containing title, langauge, date, oclc, isbn10 and isbn13
        author_list - (list) of Open Library Author Objects
        bookcover - (url) to bookcover of the related book

    Returns:
        None

    Usage:
        >>> add_book_via_olclient({'title': 'Mom Goes to War(Light)', 'authors': [' Irene Aparici Martin'], 'language': 'eng', 'date': '1974', 'oclc': '16289249', 'isbn10': '8415503202', 'isbn13': '9788415503200'},[' Irene Aparici Martin'], 'https://images.betterworldbooks.com/841/9788415503200.jpg')
    """

    # Define a Book Object
    new_book = common.Book(title=book.get("title"), authors=author_list, publish_date=book.get("date"), language=book.get("language"))


    # Add metadata like ISBN 10 and ISBN 13
    new_book.add_id(u'isbn_10', book.get("isbn10"))

    print(new_book)
    newer_book = ol.create_book(new_book)

    newer_book.add_id(u'isbn_13', book.get('isbn13'))
    newer_book.add_id(u'oclc', book.get('oclc'))

    if bookcover:
        newer_book.add_bookcover(bookcover)

def process_book(book):
    """This method takes a book json and calls other methods to add books to OL

    Args:
        book - (json) containing title, langauge, date, oclc, isbn10 and isbn13

    Returns:
        None

    Usage:
        >>> process_book({'title': 'Mom Goes to War(Light)', 'authors': [' Irene Aparici Martin'], 'language': 'eng', 'date': '1974', 'oclc': '16289249', 'isbn10': '8415503202', 'isbn13': '9788415503200'})
    """
    # make sure we've normalized the author name (e.g. first last?)
    author_list = []
    for author_name in book.get('authors'):
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

