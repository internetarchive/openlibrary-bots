from olclient.openlibrary import OpenLibrary
import olclient.common as common
import ndjson

ol = OpenLibrary()

with open('wish_list_march_2018.ndjson') as f:
	data = ndjson.load(f)

for i in range(100000):
	new_book = data[i]
	# Define a Book Object
	title = new_book['title'] if new_book['title'] else u''
	author = new_book['author'][0] if new_book['title'] else u''
	date = new_book['date'] if new_book['date'] else u''
	isbn10 = new_book['isbn10'] if new_book['isbn10'] else u''
	isbn13 = new_book['isbn13'] if new_book['isbn13'] else u''
	oclc = new_book['oclc'] if new_book['oclc'] else u''

	added_book = common.Book(title=title, authors=[common.Author(name=author)], publisher=u"", publish_date=date)

	# Add metadata like ISBN 10 and ISBN 13
	book.add_id(u'isbn_10', isbn10)
	book.add_id(u'isbn_13', isbn13)
	book.add_id(u'oclc', oclc)

	newly_added_book = ol.create_book(added_book)

	# Add Bookcover
	bookcover_added = True
	newly_added_book.add_bookcover(new_book['bookcover']) if new_book['bookcover'] else bookcover_added = False