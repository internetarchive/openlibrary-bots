import onixcheck
from lxml import etree

from olclient.openlibrary import OpenLibrary
import olclient.common as common
import string
import ast
import requests
import json

FILE = 'data/SampleONIX.xml' 
ol = OpenLibrary()

class OnixParser(object):
    """
    ONIX Parser which parses through an ONIX File and returns valid attributes
    Attributes:
        products: An xml object representing all the Products in the ONIX File  
    """

    def __init__(self, filename):
        """
        1. Checks if there are any errors in the ONIX File 
        2. Returns an etree object called products which allows you to parse the file
        """
        errors = onixcheck.validate(filename)
        for error in errors:
            print(error.short)

        if errors:
            print("Your ONIX Record has a mistake. Kindly check the ONIX File again before parsing.")
            exit(0)

        tree = etree.parse(filename)

        self.products = tree.xpath('/ONIXMessage/Product')
        self.onix_records = [[]]

    def parse_product(self, product):
        product = etree.fromstring(etree.tostring(product))
        identifiers = product.xpath('/Product/ProductIdentifier')

        isbn10 = None
        isbn13 = None
        book_cover = None

        IDENTIFIER_TYPES = {'02': 'isbn10', '15': 'isbn13'}

        found_identifiers = {}
        for identifier in identifiers:
            found_identifiers[IDENTIFIER_TYPES.get(identifier[0].text)] = identifier[1].text

        titles = product.xpath('/Product/Title')

        for title in titles:
            book_title = title[1].text

        authors = product.xpath('/Product/Title')

        book_authors = []

        for author in authors:
            book_authors.append(author[1].text)

        publishers = product.xpath('/Product/Publisher')

        for publisher in publishers:
            book_publisher = publisher[1].text

        publication_country = product.xpath(
            '/Product/CountryOfPublication')[0].text
        publication_city = product.xpath('/Product/CityOfPublication')[0].text

        media_files = product.xpath('/Product/MediaFile')

        for media_file in media_files:
            book_cover = media_file[3].text

        languages = product.xpath('/Product/Language')

        for language in languages:
            book_language = language[1].text

        return [book_title, book_publisher, publication_city, publication_country, found_identifiers.get('isbn10'), found_identifiers.get('isbn13'), book_cover, book_language, book_authors]

    def get_attributes(self):
        for product in self.products:
            onix_record = self.parse_product(product)

            self.onix_records.append(onix_record)

    def check_duplicates(self):
        count = 0

        for record in self.onix_records:

            try:
                work_isbn10 = ol.Edition.get(isbn=record[4])
            except (IndexError, ValueError):
                print("Index Error for ISBN 10")

            try:
                work_isbn13 = ol.Edition.get(isbn=record[5])
            except (IndexError, ValueError):
                print("Index Error for ISBN 13")

            try:
                correct_title = str.maketrans('', '', string.punctuation)
                new_title = '"' + record[0].split(':')[0].translate(
                    correct_title).strip().replace(' ', '+') + '"'

                correct_title = record[0].split(":")[0].translate(
                    correct_title).lower().strip()
            except (IndexError, ValueError):
                print("Index Error FOR Title")

            try:
                author_list = record[8]
                new_author = ''

                for author in author_list:
                    # Concatenate to form one big string
                    new_author = new_author + '"' + author.split(",")[0] + '"' + "OR"

                # Remove the last OR at the end of the string
                new_author = new_author[:-2]

                if len(author_list):
                    url = "http://openlibrary.org/search.json?q=title:" + str(new_title) + "+author:" + str(new_author)
                else:
                    url = "http://openlibrary.org/search.json?q=title:" + str(new_title)
            except (IndexError, ValueError):
                print("Index Error for Authors")

            try:
                print(url)
                r = requests.get(url)
                if r.status_code == 200:
                    j = json.loads(r.text)

                    match = False
                    for doc in j['docs']:
                        # Takes into account only title
                        # if doc['title_suggest'].lower() == correct_title.split(":")[0].lower().strip():
                        if doc['title_suggest'].lower() == correct_title:
                            match = True

                    if work_isbn10 is None and work_isbn13 is None and not match and count != 1000:
                        count = count + 1
                        final_onix_records.append(record)
                        print("Count: " + str(count))
                        print(record[0])
            except Exception as e:
                print("URL Exception: URL can't be created")

        return final_onix_records

if __name__ == '__main__':

    onix = OnixParser(FILE)
    onix.get_attributes()
    print(onix.onix_records)

    final_onix_records = onix.check_duplicates()
