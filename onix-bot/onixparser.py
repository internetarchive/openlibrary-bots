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

class TestOnixParser(unittest.TestCase):

    # TEST_ONIX_FEED_URL = 'https://storage.googleapis.com/support-kms-prod/SNP_EFDA74818D56F47DE13B6FF3520E468126FD_3285388_en_v2'
    TEST_ONIX_FEED_URL = 'https://ia801503.us.archive.org/2/items/onix-bot/SampleONIX.xml'

    def setUp(self):
        self.op = OnixFeedParser(io.BytesIO(requests.get(self.TEST_ONIX_FEED_URL).content))

    # def test_onix_file(self):
    #     byte_str = io.BytesIO(requests.get(TestOnixParser.TEST_ONIX_FEED_URL).content).read()
    #     text_obj = byte_str.decode('UTF-8')

    #     errors = onixcheck.validate(io.StringIO(text_obj).getvalue())
    #     for error in errors:
    #         print(error.short)

    #     self.assertTrue(len(errors) == 0)

    def test_title(self):
        title = self.op.products[0].title
        expected_title = "Roman Art"
        self.assertTrue(expected_title == title)

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


class OnixFeedParser(object):

    # def __init__(self, filename, ns="http://www.editeur.org/onix/2.1/reference"):
    def __init__(self, filename, ns=""):
        parser = etree.XMLParser(ns_clean=True)
        self.onix = etree.parse(filename, parser).getroot()
        self.ns = ns
        # self.products = [OnixProductParser(product, ns) for product in self.onix.findall('{%s}Product' % ns)]
        self.products = [OnixProductParser(product, ns) for product in self.onix.findall('Product')]


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

if __name__ == "__main__":
    onix_filename = (sys.argv[1] if len(sys.argv) == 2 else io.BytesIO(requests.get(TestOnixParser.TEST_ONIX_FEED_URL).content))
    
    print(OnixFeedParser(onix_filename).products[0].title)
    print(OnixFeedParser(onix_filename).products[0].publication_country)
    print(OnixFeedParser(onix_filename).products[0].publication_city)

    unittest.main()
