"""
Python Script to get a list of ISBNs which aren't added to Open Library

Input: 'wishlist_works_edition.ndjson'
* Contains the parameters "oclc_synonyms",  "openlibrary_synonyms", "editions" -> {"isbn", "olid"}

Output: 'ol_works.csv'
* Contains the Parameter: 'isbn-13' for all the books which aren't added to Open Library
"""

import ndjson
import csv
import time

import os
import urllib.request

new_data = []

if not os.path.isdir("data"):
	os.mkdir('data')

if not os.path.exists('data/wishlist_works_editions.ndjson'):
	file_name = 'data/wishlist_works_editions.ndjson'
	urllib.request.urlretrieve(
		'https://archive.org/download/openlibrary-bots/wishlist_works_editions.ndjson', file_name)

with open('data/wishlist_works_editions.ndjson') as f:
	data = ndjson.load(f)

start_time = time.time()

for i in range(len(data)):
	flag = 0
	if not len(data[i]['openlibrary_synonyms']):
		for edition in data[i]['editions']:
			if edition['olid'] is None:
				flag = 1

		if flag:
			new_data.append(data[i]['editions'][0]['isbn'])

print("--- %s seconds ---" % (time.time() - start_time))

with open('data/ol_works.csv', 'w') as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(['ISBN-13'])
    for out_data in new_data:
	    csvwriter.writerow([out_data])