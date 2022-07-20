"""
normalize ISBNs
NOTE: This script assumes the Open Library Dump passed only contains editions with an isbn_10 or isbn_13
"""
import argparse
import datetime
import gzip
import json
import logging
import sys
from os import makedirs

import isbnlib
from olclient.openlibrary import OpenLibrary

ALLOWED_ISBN_CHARS = {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "X", "x", "-"}


class NormalizeISBNJob:
    def __init__(self, ol=None, dry_run=True, limit=1):
        """Create logger and class variables"""
        if ol is None:
            self.ol = OpenLibrary()
        else:
            self.ol = ol

        self.changed = 0
        self.dry_run = dry_run
        self.limit = limit

        job_name = sys.argv[0].replace(".py", "")
        self.logger = logging.getLogger("jobs.%s" % job_name)
        self.logger.setLevel(logging.DEBUG)
        log_formatter = logging.Formatter(
            "%(name)s;%(levelname)-8s;%(asctime)s %(message)s"
        )
        self.console_handler = logging.StreamHandler()
        self.console_handler.setLevel(logging.WARN)
        self.console_handler.setFormatter(log_formatter)
        self.logger.addHandler(self.console_handler)
        log_dir = "logs/jobs/%s" % job_name
        makedirs(log_dir, exist_ok=True)
        log_file_datetime = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir + f"/{job_name}_{log_file_datetime}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(log_formatter)
        self.logger.addHandler(file_handler)

    @staticmethod
    def isbn_needs_normalization(isbn: str) -> bool:
        """
        Returns True if the given ISBN is valid and needs to be normalized (hyphens removed, letters capitalized, etc.)
        Returns False otherwise
        """
        if not set(isbn.strip()).issubset(ALLOWED_ISBN_CHARS):
            return False
        elif isbnlib.notisbn(isbn):
            return False
        else:
            normalized_isbn = isbnlib.get_canonical_isbn(
                isbn
            )  # get_canonical_isbn returns None if ISBN is invalid
            return normalized_isbn and normalized_isbn != isbn

    def run(self, dump_filepath: str) -> None:
        """
        Performs ISBN normalization (removes hyphens and capitalizes letters)

        dump_filepath -- path to *.txt.gz dump containing editions that need to be operated on
        """
        if self.dry_run:
            self.logger.info(
                "dry_run set to TRUE. Script will run, but no data will be modified."
            )

        header = {"type": 0, "key": 1, "revision": 2, "last_modified": 3, "JSON": 4}
        comment = "normalize ISBN"
        with gzip.open(dump_filepath, "rb") as fin:
            for row_num, row in enumerate(fin):
                row = row.decode().split("\t")
                _json = json.loads(row[header["JSON"]])
                if _json["type"]["key"] != "/type/edition":
                    continue

                isbns_by_type = dict()
                if "isbn_10" in _json:
                    isbns_by_type["isbn_10"] = _json.get("isbn_10", None)
                if "isbn_13" in _json:
                    isbns_by_type["isbn_13"] = _json.get("isbn_13", None)
                if not isbns_by_type:
                    continue

                needs_normalization = any(
                    [
                        self.isbn_needs_normalization(isbn)
                        for isbns in isbns_by_type.values()
                        for isbn in isbns
                    ]
                )
                if not needs_normalization:
                    continue

                olid = _json["key"].split("/")[-1]
                edition = self.ol.Edition.get(olid)
                if edition.type["key"] != "/type/edition":
                    continue

                for (
                    isbn_type,
                    isbns,
                ) in (
                    isbns_by_type.items()
                ):  # if an ISBN is in the wrong field this script will not move it to the appropriate one
                    normalized_isbns = list()
                    isbns = getattr(edition, isbn_type, [])
                    for isbn in isbns:
                        if self.isbn_needs_normalization(isbn):
                            normalized_isbn = isbnlib.get_canonical_isbn(isbn)
                            normalized_isbns.append(normalized_isbn)
                        else:
                            normalized_isbns.append(isbn)
                    normalized_isbns = dedupe(normalized_isbns)  # remove duplicates
                    if normalized_isbns != isbns and normalized_isbns != []:
                        setattr(edition, isbn_type, normalized_isbns)
                        self.logger.info(
                            "\t".join([olid, str(isbns), str(normalized_isbns)])
                        )
                        self.save(lambda: edition.save(comment=comment))

    def save(self, save_fn):
        """Modify default save behavior based on 'limit' and 'dry_run' parameters"""
        if not self.dry_run:
            save_fn()
        else:
            self.logger.info("Modification not made because dry_run is True")
        self.changed += 1
        if self.limit and self.changed >= self.limit:
            self.logger.info("Modification limit reached. Exiting script.")
            sys.exit()


def str2bool(value):
    if isinstance(value, bool):
        return value
    if value.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif value.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")


def dedupe(input: list) -> list:
    """Remove duplicate elements in a list and return the new list"""
    output = list()
    for i in input:
        if i not in output:
            output.append(i)
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dump_path",
        type=str,
        default=None,
        help="Path to *.txt.gz containing OpenLibrary editions data",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1,
        help="Limit number of edits performed on OpenLibrary data. Set to zero to allow unlimited edits",
    )
    parser.add_argument(
        "--dry-run",
        type=str2bool,
        default=True,
        help="Don't actually perform edits on Open Library",
    )
    _args = parser.parse_args()

    _ol = OpenLibrary()
    bot = NormalizeISBNJob(ol=_ol, dry_run=_args.dry_run, limit=_args.limit)
    bot.console_handler.setLevel(logging.INFO)

    try:
        bot.run(_args.dump_path)
    except Exception as e:
        bot.logger.exception("")
        raise e
