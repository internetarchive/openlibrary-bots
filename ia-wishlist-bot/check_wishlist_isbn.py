import csv
import ndjson 
import time

isbn_data = []

new_data = []
with open('ol_works.csv', 'r') as csvfile:
    csvreader = csv.reader(csvfile)
    for row in csvreader:
	    isbn_data.append(row[0])

isbn_set = set(isbn_data)

with open('/storage/openlibrary/wishlist/wish_list_march_2018.ndjson') as f:
	dataset = ndjson.load(f)


start_time = time.time()

for data in dataset:
	if data['isbn13'] != None:
		y = set([data['isbn13']])
		if isbn_set.intersection(y):
			#print("Yayyy")
			new_data.append(data)

print("--- %s seconds to process all the works ---" % (time.time() - start_time))


with open('wishlist_add_works_2018.csv', 'w') as csvfile:
    csvwriter = csv.writer(csvfile)
    
    for out_data in new_data:
	    csvwriter.writerow([out_data])
