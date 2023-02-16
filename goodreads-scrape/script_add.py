#!/usr/local/bin/python
import sys
import xml.etree.ElementTree as ET

import olclient.common as common
import requests
from olclient.openlibrary import OpenLibrary

isbn_13 = str(sys.argv[1])
API_KEY = ""
r = requests.get(f"https://www.goodreads.com/search.xml?key={API_KEY}q={isbn_13}")

root = ET.fromstring(r.content)  # Parsing XML response from Goodreads
title = (root[1][6][0][8][1]).text  # Deeply attributed title of the book
author = (root[1][6][0][8][2][1]).text  # author name
image_url = (root[1][6][0][8][3]).text
ol = OpenLibrary()
book = common.Book(title=title, authors=[common.Author(name=author)])
book.add_id("isbn_13", isbn_13)
new_book = ol.create_book(book)
new_book.add_bookcover(image_url)
