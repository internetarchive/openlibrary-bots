#! /usr/bin/env python3
import argparse

from apiclient.discovery import build
from olclient.openlibrary import OpenLibrary
import olclient.common as ol_common

NUMBER_OF_BOOK_CHOICES = 10


def _isbn_matches(ol_book, isbn):
    return [isbn] in ol_book.identifiers.values()


def _ol_identifiers_from_google_identifiers(google_identifiers):
    identifiers = {identifier["type"].lower(): [identifier["identifier"]] for identifier in google_identifiers}
    if "isbn_10" not in identifiers and "isbn_13" not in identifiers:
        raise KeyError
    return identifiers


def _ol_book_from_google_book(google_book):
    google_book_info = google_book["volumeInfo"]

    # Extract fields that we expect to always exist
    title = google_book_info["title"]
    authors = [ol_common.Author(name=author_name) for author_name in google_book_info["authors"]]
    industry_identifiers = _ol_identifiers_from_google_identifiers(google_book_info["industryIdentifiers"])

    # Extract fields that may not exist
    number_of_pages = google_book_info.get("pageCount")
    publisher = google_book_info.get("publisher")
    publish_date = google_book_info.get("publishedDate")
    cover_url = google_book_info["imageLinks"].get("thumbnail")

    return ol_common.Book(title=title,
                          number_of_pages=number_of_pages,
                          identifiers=industry_identifiers,
                          authors=authors,
                          publisher=publisher,
                          publish_date=publish_date,
                          cover=cover_url)


def _ol_books_from_google_books(google_books, max_books):
    ol_books = []
    for google_book in google_books:
        try:
            ol_books.append(_ol_book_from_google_book(google_book))
        except KeyError:
            continue

        if len(ol_books) == max_books:
            break

    return ol_books


def _upload_ol_book(ol_book):
    existing_book = OL.Work.search(title=ol_book.title, author=ol_book.primary_author.name)
    if existing_book is not None:
        raise ValueError("It looks like this book already exists on Open Library. "
                         "This script doesn't yet support updating existing books -- sorry!")

    edition = OL.Work.create(ol_book)
    print("Upload of {} successful".format(edition.olid))


def main():
    global OL
    OL = OpenLibrary()

    parser = argparse.ArgumentParser()
    parser.add_argument("--query", help="Your Google Books query (title, author, ISBN, etc)", required=True)
    parser.add_argument("--google_api_key", help="Your Google API key", required=True)
    args = parser.parse_args()

    google_books_service = build('books', 'v1', developerKey=args.google_api_key)
    google_books_request = google_books_service.volumes().list(source='public', q=args.query)
    google_books_response = google_books_request.execute()

    number_of_google_books = google_books_response["totalItems"]
    number_of_considered_books = min(number_of_google_books, NUMBER_OF_BOOK_CHOICES)
    if number_of_google_books == 0:
        raise ValueError("The Google Books API returned no results for your query. Aborting.")

    google_books = google_books_response["items"]
    ol_books = _ol_books_from_google_books(google_books, number_of_considered_books)

    # If query is an ISBN and Google finds a match, go ahead and upload
    if _isbn_matches(ol_books[0], args.query):
        ol_book = _ol_book_from_google_book(google_books[0])
        return _upload_ol_book(ol_book)

    # Else, let the user choose from a list
    print("Google Books found {} results for this query. Here are the first {}:".format(number_of_google_books,
                                                                                        number_of_considered_books))
    for i, ol_book in enumerate(ol_books):
        isbn_10 = ol_book.identifiers["isbn_10"][0]
        print("\t{}: '{}' by {} - ISBN {}".format(i, ol_book.title, ol_book.primary_author.name, isbn_10))

    chosen_index = int(input("Which of these would you like to upload? "))
    if chosen_index > number_of_considered_books:
        raise ValueError("Invalid choice. Aborting.")

    _upload_ol_book(ol_books[chosen_index])


if __name__ == "__main__":
    main()
