"""
Python Script to fetch Bookcovers from 
1. Google Books API
2. Amazon Scraping Bookcovers
3. Betterworld Books Page
"""

import argparse
import requests
import json
from bs4 import BeautifulSoup
from random import choice

# Random Desktop Agents to avoid detection
desktop_agents = ['Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
                  'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
                  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
                  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/602.2.14 (KHTML, like Gecko) Version/10.0.1 Safari/602.2.14',
                  'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
                  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36',
                  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36',
                  'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
                  'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
                  'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0']

# Random Headers to add to the application
def random_headers():
    return {'User-Agent': choice(desktop_agents), 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}

# Method to fetch bookcovers by Amazon
def fetch_bookcovers_amazon(isbn):
	url = "https://www.amazon.com/~/dp/"+str(isbn)+"/"
	r = requests.get(url, headers=random_headers())
	data = r.text
	soup = BeautifulSoup(data, "lxml")
	bookcover = soup.find_all("img", {"id": "imgBlkFront"})
	print(bookcover[0].attr["data-a-dynamic-image"])
	image_url = bookcover[0].attr["data-a-dynamic-image"]

	return image_url

# Bookcover URLs for Betterworld Books
def fetch_bookcovers_betterworld(isbn10,isbn13):
	url = "https://images.betterworldbooks.com/"+isbn10[0:3]+"/"+isbn13+".jpg"
	return url	

# Method to fetch Bookcovers from Google
def fetch_bookcovers_google(isbn):
	url = "https://www.googleapis.com/books/v1/volumes?q=isbn:"+str(isbn)
	
	print(url)
	r = requests.get(url)
	data = json.loads(r.text)
	print(r.text)
	return data['items'][0]['volumeInfo']['imageLinks']['thumbnail']

# Main Method
if __name__ == '__main__':
	parser = argparse.ArgumentParser()

	parser.add_argument("--google", help="Enter the ISBN Number to get Bookcovers using Google Books API")
	args = parser.parse_args()

	parser.add_argument("--amazon", help="Enter the ISBN Number to scrape Bookcovers using Amazon Website")
	args = parser.parse_args()

	parser.add_argument("--betterworld", help="Enter the ISBN Number to get bookcovers using Betterworld Books")
	args = parser.parse_args()

	isbn10 = input("Value of ISBN 10")
	isbn13 = input("Value of ISBN 13")

	if args.google:
		fetch_bookcovers_google(isbn13)
	if args.amazon:
		fetch_bookcovers_amazon(isbn13)
	if args.betterworld:
		fetch_bookcovers_betterworld(isbn10, isbn13)