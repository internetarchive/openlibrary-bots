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

with open('out1.csv', 'w') as csvfile:
    csvwriter = csv.writer(csvfile)
    for out_data in new_data:
	    csvwriter.writerow([out_data])
