#-*- coding: utf-8 -*-
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

import sys
from lxml import etree
import requests
import unittest
import io
import onixcheck
import json

class TestOnixParser(unittest.TestCase):

    # TEST_ONIX_FEED_URL = 'https://storage.googleapis.com/support-kms-prod/SNP_EFDA74818D56F47DE13B6FF3520E468126FD_3285388_en_v2'
    TEST_ONIX_FEED_URL = 'https://ia801503.us.archive.org/2/items/onix-bot/SampleONIX.xml'

    def setUp(self):
        self.op = OnixFeedParser(io.BytesIO(requests.get(self.TEST_ONIX_FEED_URL).content))

    def test_onix_file(self):
        byte_str = io.BytesIO(requests.get(TestOnixParser.TEST_ONIX_FEED_URL).content)

        errors = onixcheck.validate(byte_str.getvalue())
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
        expected_authors = ''
        
        self.assertTrue(expected_authors == authors)

    def test_languages(self):
        languages = self.op.products[0].languages
        expected_languages = 'eng'
        
        self.assertTrue(expected_languages == languages)

    def test_identifiers(self):
        identifiers = self.op.products[0].identifiers
        
        expected_isbn10 = "0199223955"
        expected_isbn13 = "9780199223954"

        self.assertTrue(identifiers.get('isbn10') == expected_isbn10)
        self.assertTrue(identifiers.get('isbn13') == expected_isbn13)
        self.assertFalse(identifiers.get('isbn12') == expected_isbn13)

    def test_media_file_link(self):
        media_file_link = self.op.products[0].media_file_link
        expected_media_file_link = "http://assets.cambridge.org/97801985/20818/cover/9780198520818.jpg"
        
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
        expected_onix_json = json.dumps({"title": "Roman Art", "publication_country": "GB", "publication_city": "Oxford", "identifiers": {"isbn10": "0199223955", "isbn13": "9780199223954"}, "authors": "", "publishers": "Oxford University Press", "languages": "eng"})

        self.assertTrue(expected_onix_json == onix_json)


class OnixFeedParser(object):

    # def __init__(self, filename, ns="http://www.editeur.org/onix/2.1/reference"):
    def __init__(self, filename, ns=""):
        parser = etree.XMLParser(ns_clean=True)
        self.onix = etree.parse(filename, parser).getroot()
        self.ns = ns
        # self.products = [OnixProductParser(product, ns) for product in self.onix.findall('{%s}Product' % ns)]
        self.products = [OnixProductParser(product, ns) for product in self.onix.findall('Product')]
        # self.errors = onixcheck.validate(filename.getvalue())


class OnixProductParser(object):

    def __init__(self, product, ns):
        self.ns = ns
        self.product = product

    @property
    def title(self):
        # title = self.product.xpath('//ns:Title', namespaces={'ns': self.ns})
        title = self.product.xpath('//Title')
        if title:
            # title = title[0].xpath('//ns:TitleText', namespaces={'ns': self.ns})
            title = title[0].xpath('//TitleText')
        return title[0].text if title else ''

    @property
    def publisher(self):
        # publisher = self.product.xpath('//ns:Publisher', namespaces={'ns': self.ns})
        publisher = self.product.xpath('//Publisher')
        if publisher:
            # publisher = publisher[0].xpath('//ns:PublisherName', namespaces={'ns': self.ns})
            publisher = publisher[0].xpath('//PublisherName')
        return publisher[0].text if publisher else ''

    @property
    def authors(self):
        # authors = self.product.xpath('//ns:Author', namespaces={'ns': self.ns})
        authors = self.product.xpath('//Author')
        
        book_authors = []

        if authors:
            for author in authors:
                book_authors.append(author[1].text)

        return book_authors if authors else ''

    @property
    def languages(self):
        # languages = self.product.xpath('//ns:Language', namespaces={'ns': self.ns})
        languages = self.product.xpath('//Language')
        
        if languages:
            languages = languages[0].xpath('//LanguageCode')
            
        return languages[0].text if languages else ''

    @property
    def identifiers(self):
        # identifiers = self.product.xpath('//ns:ProductIdentifier', namespaces={'ns': self.ns})
        identifiers = self.product.xpath('//ProductIdentifier')

        if identifiers:
            IDENTIFIER_TYPES = {'02': 'isbn10', '15': 'isbn13'}

            found_identifiers = {}
            for identifier in identifiers:
                if IDENTIFIER_TYPES.get(identifier[0].text):
                    found_identifiers[IDENTIFIER_TYPES.get(identifier[0].text)] = identifier[1].text
        
        return found_identifiers if identifiers else ''

    @property
    def media_file_link(self):
        # bookcover = self.product.xpath('//ns:MediaFile', namespaces={'ns': self.ns})
        bookcover = self.product.xpath('//MediaFile')
        if bookcover:
            # bookcover = bookcover[0].xpath('//ns:MediaFileLink', namespaces={'ns': self.ns})
            bookcover = bookcover[0].xpath('//MediaFileLink')
        return bookcover[0].text if bookcover else ''

    @property
    def publication_country(self):
        # publication_country = self.product.xpath('//ns:CountryOfPublication', namespaces={'ns': self.ns})
        publication_country = self.product.xpath('//CountryOfPublication')
        if publication_country:
            return publication_country[0].text
        else:
            return ''

    @property
    def publication_city(self):
        # publication_city = self.product.xpath('//ns:CityOfPublication', namespaces={'ns': self.ns})
        publication_city = self.product.xpath('//CityOfPublication')
        if publication_city:
            return publication_city[0].text
        else:
            return ''

    @property
    def get_json(self):
        data = {}

        data['title'] = self.title
        data['publication_country'] = self.publication_country
        data['publication_city'] = self.publication_city
        data['identifiers'] = self.identifiers
        data['authors'] = self.authors
        data['publishers'] = self.publisher
        data['languages'] = self.languages

        return json.dumps(data)

if __name__ == "__main__":
    onix_filename = (sys.argv[1] if len(sys.argv) == 2 else io.BytesIO(requests.get(TestOnixParser.TEST_ONIX_FEED_URL).content))
    
    print(OnixFeedParser(onix_filename).products[0].get_json)

    unittest.main()
