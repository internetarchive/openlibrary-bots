# Import simplejson for Python 2 else json for Python 3
try:
    import urllib2
except ImportError:
    # python 3.6
    import urllib2.request as urllib2

try:
    import urllib
except ImportError:
    # python 3.6
    import urllib.parse as urllib
# Import simplejson for Python 2 else json for Python 3
try:
    import simplejson
except ImportError:
    # python 3.6
    import json as simplejson

import collections
import datetime
import os
import re
import site
import sys

local_site = os.path.join(os.path.dirname(__file__), "..", "..", "..")
site.addsitedir(local_site)

import pprint
from optparse import OptionParser

from openlibrary.api import OpenLibrary

NYT_BEST_SELLERS_URL = "http://api.nytimes.com/svc/books/v2/lists"


def LOG(level, msg):
    print(f"{level}: {msg.encode('utf-8')}", file=sys.stderr)


def ensureUtf(s):
    try:
        if isinstance(s, str):
            return s.encode("utf8", "ignore")
    except NameError:
        return str(s)


def _request(request, parser=simplejson.loads):
    request = (
        urllib2.Request(
            request, None, headers={"Referrer": "http://www.openlibrary.org"}
        )
        if isinstance(request, str)
        else request
    )
    results = None
    conn = urllib2.urlopen(request)
    try:
        results = conn.read()
        results = ensureUtf(results)
        results = parser(results)
    except Exception as e:
        LOG("ERROR", f"error loading {request}: {e} results: {results}")
        raise
    finally:
        conn.close()
    return results


def get_nyt_bestseller_list_names():
    url = "{}/{}.json?{}".format(
        NYT_BEST_SELLERS_URL,
        "names",
        urllib.urlencode({"api-key": NYT_API_KEY}),
    )
    results = _request(url)
    assert "results" in results
    assert len(results["results"]) == results["num_results"]
    return [r["list_name"] for r in results["results"]]


def load_nyt_bestseller_list(list_name):
    url = "{}/{}.json?{}".format(
        NYT_BEST_SELLERS_URL,
        urllib.quote(list_name.replace(" ", "-")),
        urllib.urlencode({"api-key": NYT_API_KEY}),
    )

    results = _request(url)
    assert "results" in results

    if len(results["results"]) != results["num_results"]:
        LOG(
            "ERROR",
            "expected {} result for {}, got {}".format(
                results["num_results"], len(results["results"]), list_name
            ),
        )

    return results["results"]


def _do_ol_query(type="/type/edition", **query):
    query.setdefault("type", type)
    return OL.query(query)


def reconcile_authors(authors):
    result = set()
    result.update(_do_ol_query(type="/type/author", name=authors.upper()))
    authors = " ".join([a.capitalize() for a in authors.split()])
    result.update(_do_ol_query(type="/type/author", name=authors))
    return result


def reconcile_book(book):
    result = set()
    for isbn10 in (x["isbn10"] for x in book["isbns"]):
        for edition in _do_ol_query(works={"title": None}, isbn_10=isbn10):
            result.add(edition["key"])
            result.update([x["key"] for x in edition["works"] or []])

    if result:
        LOG("INFO", f"RECONCILED BY ISBN10: {result!s}")
        return result

    for isbn13 in (x["isbn13"] for x in book["isbns"]):
        for edition in _do_ol_query(works={"title": None}, isbn_13=str(isbn13)):
            result.add(edition["key"])
            result.update([x["key"] for x in edition["works"] or []])

    if result:
        LOG("INFO", f"RECONCILED BY ISBN13: {result!s}")
        return result

    authors = reconcile_authors(book["book_details"][0]["author"])
    if not authors:
        authors = set()
        for a in re.split(
            "(?: (?:and|with) )|(?:,|&)|(?:^edited|others$)",
            book["book_details"][0]["author"],
        ):
            authors.update(reconcile_authors(a))

    if not authors:
        LOG("INFO", f"NO AUTHOR: {pprint.pformat(book['book_details'])}")
        return []

    for a in authors:
        title = book["book_details"][0]["title"]
        r = []
        r.extend(
            _do_ol_query(
                type="/type/work", authors={"author": {"key": str(a)}}, title=title
            )
        )
        title = " ".join([t.capitalize() for t in title.split()])
        r.extend(
            _do_ol_query(
                type="/type/work", authors={"author": {"key": str(a)}}, title=title
            )
        )
        if r:
            result.update([x["key"] for x in r])
            LOG("INFO", f"RECONCILED BY AUTHOR: {result!s}")
            return result
    return result


def _get_first_bestseller_date(nyt):
    bd = nyt["bestsellers_date"]
    wol = nyt["weeks_on_list"]
    bd = datetime.datetime.strptime(bd, "%Y-%m-%d")
    wol = datetime.timedelta(days=wol * 7)
    result = bd - wol
    return result.date().isoformat()


def write_machine_tags(ln, books):
    key_to_nyt = {}
    for book in books:
        for work in book["ol:works"]:
            key_to_nyt[work] = book["nyt"]

    works = OL.get_many(list(set(key_to_nyt.keys())))
    write = {}
    for work in works.values():
        nyt = key_to_nyt[work["key"]]
        tags = (
            "New York Times bestseller",
            "nyt:{}={}".format(
                "_".join([s.lower() for s in ln.split()]),
                _get_first_bestseller_date(nyt),
            ),
        )
        if "subjects" not in work:
            work["subjects"] = list(tags)
            write[work["key"]] = work
        else:
            for tag in tags:
                if tag not in work["subjects"]:
                    work["subjects"].append(tag)
                    write[work["key"]] = work
        # clean up any broken tags
        work["subjects"] = [
            s
            for s in work["subjects"]
            if not s.startswith(("nyt:", "nytimes:")) or s in tags
        ]

        if work["key"] not in write:
            LOG(
                "INFO",
                "all tags already present, skipping {}: '{}' by {}".format(
                    work["key"],
                    nyt["book_details"][0]["title"],
                    nyt["book_details"][0]["author"],
                ),
            )
        else:
            LOG("DEBUG", f"Adding tags ({', '.join(tags)}) to {work['key']}")
    LOG("INFO", f"WRITING MACHINE TAGS FOR {len(write)} of {len(books)} works")
    if write:
        OL.save_many(
            write.values(), comment=f"Adding tags to New York Times {ln} bestsellers"
        )


if __name__ == "__main__":
    op = OptionParser(
        usage="%prog [-a HOST:PORT] [-k nyt_api_key] -u [bot_username] -p [bot_password]"
    )
    op.add_option(
        "-a",
        "--api-host",
        dest="openlibrary_host",
        default="openlibrary.org:80",
        help="The openlibrary API host",
    )
    op.add_option(
        "-k",
        "--nyt-api-key",
        dest="nyt_api_key",
        help="API key for use with the nyt bestsellers api",
    )
    op.add_option(
        "-u",
        "--bot-username",
        dest="username",
        default="nyt_bestsellers_bot",
        help="The bot username for accessing the Open Library API",
    )
    op.add_option(
        "-p",
        "--bot-password",
        dest="password",
        help="The bot password for accessing the Open Library API",
    )

    options, _ = op.parse_args()

    global NYT_API_KEY
    NYT_API_KEY = options.nyt_api_key
    global OL
    OL = OpenLibrary(f"http://{options.openlibrary_host}")
    OL.login(options.username, options.password)
    results = collections.defaultdict(list)
    for ln in get_nyt_bestseller_list_names():
        LOG("INFO", f"processing list {ln}")
        for i, book in enumerate(load_nyt_bestseller_list(ln)):
            ol_keys = reconcile_book(book)
            if not ol_keys:
                LOG(
                    "WARN",
                    "unable to reconcile '{}' by {} - no OL book found".format(
                        book["book_details"][0]["title"],
                        book["book_details"][0]["author"],
                    ),
                )
            if not (key for key in ol_keys if key.startswith("/works/")):
                LOG(
                    "WARN",
                    "only editions for '{}' by {}: {}".format(
                        book["book_details"][0]["title"],
                        book["book_details"][0]["author"],
                        ol_keys,
                    ),
                )
            results[ln].append(
                {
                    "nyt": book,
                    "ol:keys": ol_keys,
                    "ol:works": (key for key in ol_keys if key.startswith("/works/")),
                }
            )
        if results[ln]:
            LOG(
                "INFO",
                "RECONCILED {}% of {}".format(
                    int(
                        len([r for r in results[ln] if r["ol:works"]])
                        / float(len(results[ln]))
                        * 100
                    ),
                    ln,
                ),
            )
            write_machine_tags(ln, results[ln])
        else:
            LOG("WARN", f"No bestsellers for {ln}")
