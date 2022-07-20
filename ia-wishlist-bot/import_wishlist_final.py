"""
Python Script to add books to Open Library 

Input: 'wishlist_works_may_2018.csv'

Output: 'Adding books to the Open Library'
* Open Library Objects put up on Open Library
"""

# Used to convert list in the form of
# string back into a list
import ast
import csv
import json
import string

import olclient.common as common
import requests

# Using the Open Library Client
from olclient.openlibrary import OpenLibrary

# File used in the whole script
FILE = 'data/wishlist_works_may_2018.csv'

# Creating an object of the Open Library Client
ol = OpenLibrary()

# reader = csv.reader(open(FILE, "rt"))
# Count of books added to Open Library
count = 0

# Array to add unduplicated books
value = []

with open(FILE, "rt") as infile:
    reader = csv.reader(infile)
    next(reader, None)
    for row in reader:
        # print(row[6])

        # Calls using the Open Library Client
        work = ol.Edition.get(isbn=row[5], oclc=row[4])
        work1 = ol.Edition.get(isbn=row[6])
        # correct_title = row[0].replace(".", "").replace("'", "").replace(",","").replace("!","")
        # new_title = '"' + correct_title.split(":")[0].replace(" ", "+") + '"'
        correct_title = str.maketrans('', '', string.punctuation)
        new_title = (
            '"'
            + row[0].split(':')[0].translate(correct_title).strip().replace(' ', '+')
            + '"'
        )

        correct_title = row[0].split(":")[0].translate(correct_title).lower().strip()

        # Author List
        author_list = ast.literal_eval(row[1])
        new_author = ''

        for author in author_list:
            # Concatenate to form one big string
            new_author = new_author + '"' + author.split(",")[0] + '"' + "OR"

        # Remove the last OR at the end of the string
        new_author = new_author[:-2]

        if len(author_list):
            url = (
                "http://openlibrary.org/search.json?q=title:"
                + str(new_title)
                + "+author:"
                + str(new_author)
            )
        else:
            url = "http://openlibrary.org/search.json?q=title:" + str(new_title)

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

            if work is None and work1 is None and not match and count != 1000:
                count = count + 1
                value.append(row)
                print("Count: " + str(count))
                print(row[0])
            elif count == 1000:
                with open("data/new_wishlist_salman_1000.csv", "w") as outfile:
                    csvwriter = csv.writer(outfile)
                    for out_data in value:
                        csvwriter.writerow(out_data)
                exit(0)
            else:
                print("Work already exists")
                # print(row[0])
        else:
            print(str(row[0]) + " has been skipped")
