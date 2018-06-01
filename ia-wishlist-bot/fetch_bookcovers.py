"""
Python Script to fetch Bookcovers from 
1. Google Books API
2. Amazon Scraping Bookcovers
3. Betterworld Books Page
"""

import argparse
import requests
import json

# Method to fetch Bookcovers from Google
def fetch_bookcovers_google(isbn):
	url = "https://www.googleapis.com/books/v1/volumes?q=isbn:"+str(isbn)
	
	print(url)
	r = requests.get(url)
	data = json.loads(r.text)
	print(r.text)
	return data['items'][0]['volumeInfo']['imageLinks']['thumbnail']

# 
if __name__ == '__main__':
	parser = argparse.ArgumentParser()

	parser.add_argument("--google", help="Enter the ISBN Number to get Bookcovers using Google Books API")
	args = parser.parse_args()

	parser.add_argument("--amazon", help="Enter the ISBN Number to scrape Bookcovers using Amazon Website")
	args = parser.parse_args()

	parser.add_argument("--betterworld", help="Enter the ISBN Number to get bookcovers using Betterworld Books")
	args = parser.parse_args()

	print(fetch_bookcovers_google(args.isbn))