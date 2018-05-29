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

new_data = []


with open('/storage/openlibrary/wishlist/wishlist_works_editions.ndjson') as f:
	data = ndjson.load(f)

start_time = time.time()

for i in range(len(data)):
	flag = 0
	if len(data[i]['openlibrary_synonyms']) == 0:
		for edition in data[i]['editions']:
			if edition['olid'] == None:
				flag = 1

		if flag:
			new_data.append(data[i]['editions'][0]['isbn'])

print("--- %s seconds ---" % (time.time() - start_time))

with open('ol_works.csv', 'w') as csvfile:
    csvwriter = csv.writer(csvfile)
    for out_data in new_data:
	    csvwriter.writerow([out_data])
