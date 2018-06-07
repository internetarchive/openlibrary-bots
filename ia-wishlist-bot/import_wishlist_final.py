# Using the Open Library Client
from olclient.openlibrary import OpenLibrary
import olclient.common as common

import csv
import requests
import json 

# File used in the whole script
FILE = 'data/wishlist_works_may_2018.csv'

# Creating an object of the Open Library Client
ol = OpenLibrary()

# reader = csv.reader(open(FILE, "rt"))
count = 0
value = []

with open(FILE, "rt") as infile:
    reader = csv.reader(infile)
    next(reader, None)
    for row in reader:
        # print(row[6])

        # Calls using the Open Library Client
        work = ol.Edition.get(isbn=row[5], oclc=row[4])
        work1 = ol.Edition.get(isbn=row[6])
        
        new_title = row[0].replace(" ", "+")
        r = requests.get("http://openlibrary.org/search.json?q=title:"+str(new_title))
        if r.status_code == 200:
            j = json.loads(r.text)
        
            match = False
            for doc in j['docs']:
                if doc['title_suggest'].lower() == row[0].lower():
                    match = True

            if work is None and work1 is None and not match and count != 100:
                count = count + 1
                value.append(row)
                print("Count: "+str(count))
                print(row[0])
            elif count == 100:
                with open("data/new_wishlist_salman_10.csv", "w") as outfile:
                    csvwriter = csv.writer(outfile)
                    for out_data in value:
                        csvwriter.writerow(out_data)
                exit(0)
            else:
                print("No match found")
                # print(row[0])
        else:
            print(str(row[0])+" has been skipped")