from olclient.openlibrary import OpenLibrary
import olclient.common as common
import ndjson
import jsonlines
import io

ol = OpenLibrary()

with open('wish_list_march_2018.ndjson') as f:
	data = ndjson.load(f)

	new_data = []

	count = 0
	for i in range(10):
		book = ol.Edition.get_olid_by_isbn((data[i]['isbn10']))
		if book is None:
			new_data.append(data)
			count = count + 1
			print(str(count)+" new books added")
		else:
			print("Old Book is found")


with jsonlines.open('wish_list_final.ndjson', mode='w') as writer:
	writer.write(new_data)

print(str(count) +" books have been added here")