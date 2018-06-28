import onixcheck
import xml.etree.ElementTree as ET
from lxml import etree

# File 
FILE = 'data/SampleONIX.xml'

"""
Step 1: Check if there are any errors in the XML file
"""
errors = onixcheck.validate(FILE)
for error in errors:
    print(error.short)

# Exit the script in case there are errors
if errors:
    print("Kindly use a correct XML File to parse")
    exit(0)

"""
Step 2: Parse the XML file to get all relevant features from the dataset
"""
tree = etree.parse(FILE)

products = tree.xpath('/ONIXMessage/Product')

# onix_record = [['Title','Publisher','City Of Publication','Country of Publication','isbn10', 'isbn13', 'Boocover Link', 'Language']]
onix_records = [[]]

for product in products:
    product = etree.fromstring(etree.tostring(product))
    identifiers = product.xpath('/Product/ProductIdentifier')
    
    for identifier in identifiers:
        if identifier[0].text == "02":
            isbn10 = identifier[1].text 
        if identifier[0].text == "15":
            isbn13 = identifier[1].text 

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

    publication_country = product.xpath('/Product/CountryOfPublication')[0].text
    publication_city = product.xpath('/Product/CityOfPublication')[0].text
    
    media_files = product.xpath('/Product/MediaFile')

    for media_file in media_files:
        book_cover = media_file[3].text

    languages = product.xpath('/Product/Language')

    for language in languages:
        book_language = language[1].text

    onix_records.append([book_title, book_publisher, publication_city, publication_country, isbn10, isbn13, book_cover, book_language, book_authors])

# print(onix_records)
"""
0 -> Book Title
1 -> Book Publisher
2 -> Publication City
3- > Publication Country
4 -> ISBN-10
5 -> ISBN-13
6 -> Book Cover
7 -> Book Language
8 -> Author
"""

from olclient.openlibrary import OpenLibrary
import olclient.common as common
import string, ast
import requests, json

ol = OpenLibrary()
count = 0 
final_onix_records = []

"""
Step 3: Check for ISBN Match amongst all the books.
Step 4: Check for Author Match and Title Match
"""

for record in onix_records:
    work_isbn10 = ol.Edition.get(isbn=record[4])
    work_isbn13 = ol.Edition.get(isbn=record[5])

    correct_title = str.maketrans('', '', string.punctuation)
    new_title = '"' + record[0].split(':')[0].translate(
            correct_title).strip().replace(' ', '+') + '"'

    correct_title = record[0].split(":")[0].translate(
        correct_title).lower().strip()

    # Author List
    # author_list = ast.literal_eval(record[8])
    author_list = record[8]
    new_author = ''

    for author in author_list:
        # Concatenate to form one big string
        new_author = new_author + '"' + author.split(",")[0] + '"' + "OR"

    # Remove the last OR at the end of the string
    new_author = new_author[:-2]

    if len(author_list):
        url = "http://openlibrary.org/search.json?q=title:" + \
            str(new_title) + "+author:" + str(new_author)
    else:
        url = "http://openlibrary.org/search.json?q=title:" + \
            str(new_title)

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

"""
Step 5: Add books to Open Library using ol-client
Input: final_onix_records -> Array of ONIX Records
"""
