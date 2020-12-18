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
            r = requests.get(url)
            return [str(isbn) for isbn in re.findall(b"ISBN13.*>([0-9X-]+)", r.content)]
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
        return filter(
            lambda isbn: isbnlib.is_isbn10(isbn) or isbnlib.is_isbn13(isbn),
            [isbnlib.canonical(isbn) for isbn in isbns]
        )

class Objectify(dict):
    def __getattr__(self, name):
        if name in self:
            return self[name]
        else:
            raise AttributeError("No such attribute: " + name)

    def __setattr__(self, name, value):
        self[name] = value
        
    def __delattr__(self, name):
        if name in self:
            del self[name]
        else:
            raise AttributeError("No such attribute: " + name)
    
class InternetArchive:

    IA_URL = "https://archive.org"
    OL_URL = "http://openlibrary.org"
    MODES = ["is_readable", "is_lendable", "is_printdisabled"]

    @classmethod
    def get_edition(cls, isbn):
        class Edition(Objectify):
            def __init__(self, kwargs):
                super().__init__(kwargs)
        #try:
        ed = Edition(requests.get("https://dev.openlibrary.org/isbn/%s.json" % isbn).json())
        ed.availability = ed and ed.get("ocaid") and cls.get_availability(ed["ocaid"])
        ed.isbn = ed and isbn
        return ed
        #except Exception as e:
        #    print("Failed to fetch openlibrary edition for: %s" % isbn)

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
        except:
            print("Error fetching IA work")
        return {}
