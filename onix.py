import onixcheck
import xml.etree.ElementTree as ET
from lxml import etree

# File 
FILE = 'data/SampleONIX.xml'

# Check 1: Check if there are any errors in the XML file
errors = onixcheck.validate(FILE)
for error in errors:
    print(error.short)

# EXit the script in case there are errors
if errors:
    print("Kindly use a correct XML File to parse")
    exit(0)

tree = etree.parse(FILE)

products = tree.xpath('/ONIXMessage/Product')

onix_record = [['Title','Publisher','City Of Publication','Country of Publication','isbn10', 'isbn13', 'Boocover Link', 'Language']]

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

    publishers = product.xpath('/Product/Publisher')
    
    for publisher in publishers:
        book_publisher = publisher[1].text 

    publication_country = product.xpath('/Product/CountryOfPublication')
    publication_city = product.xpath('/Product/CityOfPublication')
    
    media_files = product.xpath('/Product/MediaFile')

    for media_file in media_files:
        book_cover = media_file[3].text

    languages = product.xpath('/Product/Language')

    for language in languages:
        book_language = language[2].text

    onix_record.append([isbn10, isbn13])

print(onix_record)
