import isbnlib
import re
import requests


class ISBNFinder:

    SERVICES = ["amazon", "goodreads"]

    @staticmethod
    def amazon(url):
        try:
            return (
                re.findall("/dp/([0-9X]{10})/?", url) or
                re.findall("/product/([0-9X]{10})/?", url)
            )
        except Exception as e:
            print(e)

    @staticmethod
    def goodreads(url):
        if re.findall("/book/show/([0-9]+)", url):
            return re.findall("ISBN13.*>([0-9X-]+)", requests.get(url).text)
        return []

    @classmethod
    def find_isbns(cls, text):
        isbns = []
        for token in text.split():
            if token.startswith("http"):
                url = requests.head(token).headers.get("Location") or token
                for service_name in cls.SERVICES:
                    _isbns = getattr(cls, service_name)(url)
                    isbns.extend(_isbns)
            else:
                isbns.extend(isbnlib.get_isbnlike(token, level="normal"))
        return [isbnlib.canonical(isbn) for isbn in isbns
                if isbnlib.is_isbn10(isbn) or isbnlib.is_isbn13(isbn)]


class InternetArchive:

    IA_URL = "https://archive.org"
    OL_URL = "https://openlibrary.org"
    OL_DEV = "https://dev.openlibrary.org"
    MODES = ["is_readable", "is_lendable", "is_printdisabled"]

    @classmethod
    def get_edition(cls, isbn):
        try:
            ed = requests.get("%s/isbn/%s.json" % (cls.OL_DEV, isbn)).json()
            ed["availability"] = ed and ed.get("ocaid") and cls.get_availability(ed["ocaid"])
            ed["isbn"] = ed and isbn
            return ed
        except Exception as e:
            print("Failed to fetch openlibrary edition for: %s" % isbn)
        return {}

    @classmethod
    def get_availability(cls, identifier):
        try:
            url = "%s/services/loans/loan/" % cls.IA_URL
            status = requests.get("%s?&action=availability&identifier=%s" % (
                url, identifier)).json().get("lending_status")
            for mode in cls.MODES:
                if status.get(mode):
                    return mode
        except Exception as e:
            print("Failed to fetch availability for: %s" % identifier)

    @classmethod
    def find_available_work(cls, book):
        try:
            url = "%s/advancedsearch.php" % cls.IA_URL
            work_id = book["works"][0]["key"].split("/")[-1]
            query = (
                "openlibrary_work:%s AND" % work_id +
                "(lending___is_lendable:true OR" +
                " lending___is_readable:true OR" +
                " lending___is_printdisabled:true" +
                ")"
            )
            params = [
                ("q", query),
                ("fl[]", "identifier"),
                ("fl[]", "openlibrary_work"),
                ("fl[]", "lending___is_lendable"),
                ("fl[]", "lending___is_readable"),
                ("fl[]", "lending___is_printdisabled"),
                ("rows", "50"),
                ("page", "1"),
                ("output", "json")
            ]
            matches = requests.get(url, params=params).json()
            if matches and matches["response"]["docs"]:
                books = matches["response"]["docs"]
                return next(book for book in books if book.get("openlibrary_work"))
        except Exception:
            print("Error fetching IA work")
        return {}
