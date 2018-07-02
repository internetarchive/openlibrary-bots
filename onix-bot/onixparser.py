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
"""

import sys
from lxml import etree
import requests
import unittest
import io
import onixcheck

class TestOnixParser(unittest.TestCase):

    TEST_ONIX_FEED_URL = 'https://storage.googleapis.com/support-kms-prod/SNP_EFDA74818D56F47DE13B6FF3520E468126FD_3285388_en_v2'

    def setUp(self):
        self.op = OnixFeedParser(io.BytesIO(requests.get(self.TEST_ONIX_FEED_URL).content))


    def test_title(self):
        title = self.op.products[0].title
        expected_title = "This is my distinctive title."
        self.assertTrue(expected_title == title)

class OnixFeedParser(object):

    def __init__(self, filename, ns="http://www.editeur.org/onix/2.1/reference"):
        parser = etree.XMLParser(ns_clean=True)
        self.onix = etree.parse(filename, parser).getroot()
        self.ns = ns
        self.products = [OnixProductParser(product, ns) for product in
                         self.onix.findall('{%s}Product' % ns)]


class OnixProductParser(object):

    def __init__(self, product, ns):
        self.ns = ns
        self.product = product

    @property
    def title(self):
        title = self.product.xpath('//ns:Title', namespaces={'ns': self.ns})
        if title:
            title = title[0].xpath('//ns:TitleText', namespaces={'ns': self.ns})
        return title[0].text if title else ''


if __name__ == "__main__":
    onix_filename = (sys.argv[1] if len(sys.argv) == 2 else io.BytesIO(requests.get(TestOnixParser.TEST_ONIX_FEED_URL).content))
    
    print(OnixFeedParser(onix_filename).products[0].title)

    # unittest.main()
