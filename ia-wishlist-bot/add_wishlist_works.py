"""
Python Script to create a list of books to add on Open Library

Input: 'ol_works.csv'
Parameters include `isbn_13` of all books which are not included in Open Library

Output: 'wishlist_works_may_2018.csv'
* Parameters include `isbn_10`, `isbn_13`, `author`, `title`, `language`, `oclc`, `date`
"""

import csv
import ndjson 
import time

isbn_data = []

new_data = []

# Fetches all ISBNs which are currently not added to Open Library
with open('ol_works.csv', 'r') as csvfile:
    csvreader = csv.reader(csvfile)
    for row in csvreader:
	    isbn_data.append(row[0])

# ISBNs are added as a set to avoid any duplication
isbn_set = set(isbn_data)

# Wishlist books are fetched and loaded
with open('/storage/openlibrary/wishlist/wish_list_march_2018.ndjson') as f:
	dataset = ndjson.load(f)

# Time is recorded for the function to execute
start_time = time.time()

# Iterating over the dataset
for data in dataset:
	# Checking if ISBN-13 for a particular data is Nonetype or not
	if data['isbn13'] != None:
		y = set([data['isbn13']])
		# Intersection of set of dataset ISBN-13 and wishlist ISBN-13 is taken
		if isbn_set.intersection(y):
			new_data.append(data)

print("--- %s seconds to process all the works ---" % (time.time() - start_time))

# A new CSV file is chosen to write into the Wishlist
with open('wishlist_works_may_2018.csv', 'w') as csvfile:
    csvwriter = csv.writer(csvfile)
    
	# CSV File Header is Written
	# csvwriter.writerow(['book_title', 'book_authors', 'book_language', 'book_date', 'book_oclc', 'book_isbn10', 'book_isbn13'])

	# CSV File Contents are being written 
    for out_data in new_data:
	    csvwriter.writerow([out_data])