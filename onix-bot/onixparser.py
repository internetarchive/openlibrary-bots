# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""
onixparser.py
~~~~~~~~~~~~~


Usage:
    >>> from onixparser import OnixFeedParser
    >>> op = OnixFeedParser('onix_test_data.xml')
    >>> p = op.products[0]
    >>> p.title
    >>> p.media_file_link
    >>> p.publication_country
    >>> p.publication_city
"""

import io
import json
import string
import sys
import tempfile
import unittest

import olclient.common as common
import onixcheck
import requests
from lxml import etree
from olclient.openlibrary import OpenLibrary

ol = OpenLibrary()


class TestOnixParser(unittest.TestCase):
    # TEST_ONIX_FEED_URL = 'https://storage.googleapis.com/support-kms-prod/SNP_EFDA74818D56F47DE13B6FF3520E468126FD_3285388_en_v2'
    TEST_ONIX_FEED_URL = (
        "https://ia801503.us.archive.org/2/items/onix-bot/SampleONIX.xml"
    )

    def setUp(self):
        self.op = OnixFeedParser(
            io.BytesIO(requests.get(self.TEST_ONIX_FEED_URL).content)
        )

    def test_onix_file(self):
        byte_str = io.BytesIO(requests.get(TestOnixParser.TEST_ONIX_FEED_URL).content)

        with tempfile.NamedTemporaryFile() as temp:
            temp.write(byte_str.getvalue())
            temp.flush()
            errors = onixcheck.validate(temp.name)

        for error in errors:
            print(error.short)

        self.assertTrue(len(errors) == 0)

    def test_title(self):
        title = self.op.products[0].title
        expected_title = "Roman Art"

        self.assertTrue(expected_title == title)

    def test_publisher(self):
        publisher = self.op.products[0].publisher
        expected_publisher = "Oxford University Press"

        self.assertTrue(expected_publisher == publisher)

    def test_authors(self):
        authors = self.op.products[0].authors
        expected_authors = ""

        self.assertTrue(expected_authors == authors)

    def test_languages(self):
        languages = self.op.products[0].languages
        expected_languages = "eng"

        self.assertTrue(expected_languages == languages)

    def test_identifiers(self):
        identifiers = self.op.products[0].identifiers

        expected_isbn10 = "0199223955"
        expected_isbn13 = "9780199223954"

        self.assertTrue(identifiers.get("isbn10") == expected_isbn10)
        self.assertTrue(identifiers.get("isbn13") == expected_isbn13)
        self.assertFalse(identifiers.get("isbn12") == expected_isbn13)

    def test_media_file_link(self):
        media_file_link = self.op.products[0].media_file_link
        expected_media_file_link = (
            "http://assets.cambridge.org/97801985/20818/cover/9780198520818.jpg"
        )

        self.assertTrue(expected_media_file_link == media_file_link)

    def test_publication_country(self):
        publication_country = self.op.products[0].publication_country
        expected_publication_country = "GB"

        self.assertTrue(expected_publication_country == publication_country)

    def test_publication_city(self):
        publication_city = self.op.products[0].publication_city
        expected_publication_city = "Oxford"

        self.assertTrue(expected_publication_city == publication_city)

    def test_json(self):
        onix_json = self.op.products[0].get_json
        expected_onix_json = json.dumps(
            {
                "title": "Roman Art",
                "publication_country": "GB",
                "publication_city": "Oxford",
                "identifiers": {"isbn10": "0199223955", "isbn13": "9780199223954"},
                "authors": "",
                "publishers": "Oxford University Press",
                "languages": "eng",
            }
        )

        self.assertTrue(expected_onix_json == onix_json)


class TestOnixProductBot(unittest.TestCase):
    TEST_ONIX_JSON = json.dumps(
        {
            "title": "Roman Art",
            "publication_country": "GB",
            "publication_city": "Oxford",
            "identifiers": {"isbn10": "0199223955", "isbn13": "9780199223954"},
            "authors": "",
            "publishers": "Oxford University Press",
            "languages": "eng",
        }
    )

    def setUp(self):
        self.opb = OnixProductBot(self.TEST_ONIX_JSON)
        self.data = self.opb.data

    def test_onix_identifiers(self):
        expected_status = 0
        self.opb.check_identifiers

        self.assertTrue(expected_status == self.opb.status)


class OnixFeedParser(object):
    def __init__(self, filename, ns=""):
        parser = etree.XMLParser(ns_clean=True)
        self.onix = etree.parse(filename, parser).getroot()
        self.ns = ns
        self.products = [
            OnixProductParser(product, ns) for product in self.onix.findall("Product")
        ]


class OnixProductParser(object):
    def __init__(self, product, ns):
        self.ns = ns
        self.product = product

    @property
    def title(self):
        """Returns title corresponding to that product

        Args:
            None

        Returns:
            Title as string or empty string

        Usage:
            >>> from onixparser import OnixFeedParser
            >>> op = OnixFeedParser('onix_test_data.xml')
            >>> p = op.products[0]
            >>> p.title
        """
        title = self.product.xpath("//Title")
        if title:
            title = title[0].xpath("//TitleText")
        return title[0].text if title else ""

    @property
    def publisher(self):
        """Returns publisher corresponding to that product

        Args:
            None

        Returns:
            Publisher as string or empty string

        Usage:
            >>> from onixparser import OnixFeedParser
            >>> op = OnixFeedParser('onix_test_data.xml')
            >>> p = op.products[0]
            >>> p.publisher
        """
        publisher = self.product.xpath("//Publisher")
        if publisher:
            publisher = publisher[0].xpath("//PublisherName")
        return publisher[0].text if publisher else ""

    @property
    def authors(self):
        """Returns authors corresponding to that product

        Args:
            None

        Returns:
            Book authors as an array of authors or empty string

        Usage:
            >>> from onixparser import OnixFeedParser
            >>> op = OnixFeedParser('onix_test_data.xml')
            >>> p = op.products[0]
            >>> p.authors
        """
        authors = self.product.xpath("//Author")

        book_authors = []

        if authors:
            for author in authors:
                book_authors.append(author[1].text)

        return book_authors if authors else ""

    @property
    def languages(self):
        """Returns languages corresponding to that product

        Args:
            None

        Returns:
            Language as string or empty string

        Usage:
            >>> from onixparser import OnixFeedParser
            >>> op = OnixFeedParser('onix_test_data.xml')
            >>> p = op.products[0]
            >>> p.languages
        """
        languages = self.product.xpath("//Language")

        if languages:
            languages = languages[0].xpath("//LanguageCode")

        return languages[0].text if languages else ""

    @property
    def identifiers(self):
        """Returns book identifiers corresponding to that product

        Args:
            None

        Returns:
            Identifiers:
                - ISBN 10
                - ISBN 13

        Usage:
            >>> from onixparser import OnixFeedParser
            >>> op = OnixFeedParser('onix_test_data.xml')
            >>> p = op.products[0]
            >>> p.identifiers
        """

        identifiers = self.product.xpath("//ProductIdentifier")

        if identifiers:
            IDENTIFIER_TYPES = {"02": "isbn10", "15": "isbn13"}

            found_identifiers = {}
            for identifier in identifiers:
                if IDENTIFIER_TYPES.get(identifier[0].text):
                    found_identifiers[
                        IDENTIFIER_TYPES.get(identifier[0].text)
                    ] = identifier[1].text

        return found_identifiers if identifiers else ""

    @property
    def media_file_link(self):
        """Returns book cover corresponding to that product

        Args:
            None

        Returns:
            URL of the bookcover corresponding to that book or blank string

        Usage:
            >>> from onixparser import OnixFeedParser
            >>> op = OnixFeedParser('onix_test_data.xml')
            >>> p = op.products[0]
            >>> p.media_file_link
        """
        bookcover = self.product.xpath("//MediaFile")
        if bookcover:
            bookcover = bookcover[0].xpath("//MediaFileLink")
        return bookcover[0].text if bookcover else ""

    @property
    def publication_country(self):
        """Returns publication country corresponding to that product

        TODO:
            Map the country code to the required country

        Args:
            None

        Returns:
            Publication country for that particular book

        Usage:
            >>> from onixparser import OnixFeedParser
            >>> op = OnixFeedParser('onix_test_data.xml')
            >>> p = op.products[0]
            >>> p.publication_country
        """
        publication_country = self.product.xpath("//CountryOfPublication")
        if publication_country:
            return publication_country[0].text
        else:
            return ""

    @property
    def publication_city(self):
        """Returns city corresponding to that product

        Args:
            None

        Returns:
            Publication City corresponding to that book

        Usage:
            >>> from onixparser import OnixFeedParser
            >>> op = OnixFeedParser('onix_test_data.xml')
            >>> p = op.products[0]
            >>> p.publication_city
        """
        publication_city = self.product.xpath("//CityOfPublication")
        if publication_city:
            return publication_city[0].text
        else:
            return ""

    @property
    def get_json(self):
        """Returns JSON of all the elements for a particular product

        Args:
            None

        Returns:
            JSON of all the identifiers of that book

        Usage:
            >>> from onixparser import OnixFeedParser
            >>> op = OnixFeedParser('onix_test_data.xml')
            >>> p = op.products[0]
            >>> p.get_json
        """
        data = {}

        data["title"] = self.title
        data["publication_country"] = self.publication_country
        data["publication_city"] = self.publication_city
        data["identifiers"] = self.identifiers
        data["authors"] = self.authors
        data["publishers"] = self.publisher
        data["languages"] = self.languages

        return json.dumps(data)


class OnixProductBot(object):
    def __init__(self, data):
        self.status = 1
        self.data = json.loads(data)

    @property
    def check_identifiers(self):
        try:
            work_isbn10 = ol.Edition.get(
                isbn=self.data.get("identifiers").get("isbn10")
            )
        except (IndexError, ValueError):
            print("Index Error for ISBN 10")

        try:
            work_isbn13 = ol.Edition.get(
                isbn=self.data.get("identifiers").get("isbn13")
            )
        except (IndexError, ValueError):
            print("Index Error for ISBN 13")

        if work_isbn10 or work_isbn13:
            self.status = 0

    @property
    def check_title_or_author(self):
        try:
            correct_title = str.maketrans("", "", string.punctuation)
            new_title = (
                '"'
                + self.data.get("title")
                .split(":")[0]
                .translate(correct_title)
                .strip()
                .replace(" ", "+")
                + '"'
            )

            correct_title = (
                self.data.get("title")
                .split(":")[0]
                .translate(correct_title)
                .lower()
                .strip()
            )
        except (IndexError, ValueError):
            print("Index Error for Title")

        try:
            author_list = self.data.get("authors")
            new_author = ""

            for author in author_list:
                # Concatenate to form one big string
                new_author = new_author + '"' + author.split(",")[0] + '"' + "OR"

            # Remove the last OR at the end of the string
            new_author = new_author[:-2]
        except (IndexError, ValueError):
            print("Index Error for Authors")

        if len(author_list):
            url = (
                "http://openlibrary.org/search.json?q=title:"
                + str(new_title)
                + "+author:"
                + str(new_author)
            )
        else:
            url = "http://openlibrary.org/search.json?q=title:" + str(new_title)

        try:
            print(url)
            r = requests.get(url)
            if r.status_code == 200:
                j = json.loads(r.text)
                match = False
                for doc in j["docs"]:
                    # Takes into account only title
                    # if doc['title_suggest'].lower() == correct_title.split(":")[0].lower().strip():
                    if doc["title_suggest"].lower() == correct_title:
                        match = True
                if not match:
                    print(self.data)

        except Exception as e:
            print("URL Exception: URL can't be created")
            print(e)


if __name__ == "__main__":
    onix_filename = (
        sys.argv[1]
        if len(sys.argv) == 2
        else io.BytesIO(requests.get(TestOnixParser.TEST_ONIX_FEED_URL).content)
    )

    data = OnixFeedParser(onix_filename).products[0].get_json

    unittest.main()
