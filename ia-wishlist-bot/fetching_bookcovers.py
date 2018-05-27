import argparse
import requests
import json

def fetch_bookcovers(isbn):
	url = "https://www.googleapis.com/books/v1/volumes?q=isbn:"+str(isbn)
	
	print(url)
	r = requests.get(url)
	data = json.loads(r.text)
	print(r.text)
	return data['items'][0]['volumeInfo']['imageLinks']['thumbnail']


if __name__ == '__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument("isbn", help="Enter the ISBN Number")
	args = parser.parse_args()
	print(fetch_bookcovers(args.isbn))