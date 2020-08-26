from isbnlib import notisbn
from isbnbot.normalize_isbns import NormalizeISBNJob


def test_isbn_needs_normalization():  # TODO: Add some isbn's that need normalization
    for isbn in "0 1234567890  Bob".split():
        assert notisbn(isbn)
        assert not NormalizeISBNJob.isbn_needs_normalization(isbn)

    for isbn in "0123456789 0425016013 9780425016015 0441788386 9780441788385".split():
        assert not notisbn(isbn)  # double negative
        assert not NormalizeISBNJob.isbn_needs_normalization(isbn)
