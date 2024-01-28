"""
normalize ISBNs
NOTE: This script assumes the Open Library Dump passed only contains editions with an isbn_10 or isbn_13
"""

import gzip
import json

import isbnlib
import olclient


class NormalizeISBNJob(olclient.AbstractBotJob):
    @staticmethod
    def isbn_needs_normalization(isbn: str) -> bool:
        """
        Returns True if the given string contains one or two unformatted isbns
        Returns False otherwise
        """
        if len(isbn) > 10 and parse_isbns(isbn):
            return True
        else:
            return False

    def run(self) -> None:
        """Looks for any ISBNs with extra non-numeric characters"""
        self.write_changes_declaration()
        header = {"type": 0, "key": 1, "revision": 2, "last_modified": 3, "JSON": 4}
        comment = "normalize ISBN"
        with gzip.open(self.args.file, "rb") as fin:
            for row_num, row in enumerate(fin):
                row = row.decode().split("\t")
                _json = json.loads(row[header["JSON"]])
                if _json["type"]["key"] != "/type/edition":
                    continue

                isbns_by_type = {}
                if "isbn_10" in _json:
                    isbns_by_type["isbn_10"] = _json.get("isbn_10", None)
                if "isbn_13" in _json:
                    isbns_by_type["isbn_13"] = _json.get("isbn_13", None)

                if not isbns_by_type:
                    continue

                needs_normalization = any(
                    self.isbn_needs_normalization(isbn)
                    for isbns in isbns_by_type.values()
                    for isbn in isbns
                )
                if not needs_normalization:
                    continue

                olid = _json["key"].split("/")[-1]
                edition = self.ol.Edition.get(olid)
                if edition.type["key"] != "/type/edition":
                    continue

                for isbn_type, isbns in isbns_by_type.items():
                    # if an ISBN is in the wrong field this script will not move it to the appropriate one
                    normalized_isbns = []
                    isbns = getattr(edition, isbn_type, [])
                    for isbn in isbns:
                        parsed = parse_isbns(isbn)
                        if parsed:
                            normalized_isbns.extend(parsed)
                        else:
                            normalized_isbns.append(isbn)

                    normalized_isbns = dedupe(normalized_isbns)  # remove duplicates
                    if normalized_isbns != isbns and normalized_isbns != []:
                        setattr(edition, isbn_type, normalized_isbns)
                        self.logger.info(
                            "\t".join([olid, str(isbns), str(normalized_isbns)])
                        )
                        self.save(lambda: edition.save(comment=comment))


def dedupe(input_list: list) -> list:
    """Remove duplicate elements in a list and return the new list"""
    output = []
    for i in input_list:
        if i not in output:
            output.append(i)
    return output


def chop(string: str, length: int) -> tuple[str]:
    return tuple(string[i : i + length] for i in range(0, len(string), length))


def parse_isbns(string: str) -> tuple:
    """Find isbns in a string on the assumption that if you strip all non-isbn
    characters and all that is left is valid isbns then it's unlikely to be random chance
    if that doesn't work it will use a reasonably strict regex to look for an isbn13
    formatted string within the full text, which should help when other numbers are present
    """

    # pass one: strip all non isbn characters, and see if what remains looks like an ISBN
    isbnchars = [c for c in string if c in "0123456789Xx"]
    if len(isbnchars) < 10:
        return ()

    isbnchars = "".join(isbnchars).upper()
    # X is tricky, but can only appear at the end of an isbn10 so remove if not where expected
    x_idx = isbnchars.find("X")
    if (x_idx + 1) % 10 != 0 and (x_idx + 1) % 23 != 0:
        isbnchars = isbnchars.replace("X", "")

    if len(isbnchars) % 10 == 0:
        if all(isbnlib.is_isbn10(isbn) for isbn in chop(isbnchars, 10)):
            return chop(isbnchars, 10)
    elif len(isbnchars) % 13 == 0:
        if all(isbnlib.is_isbn13(isbn) for isbn in chop(isbnchars, 13)):
            return chop(isbnchars, 13)
    elif (
        len(isbnchars) == 23
        and isbnlib.is_isbn13(isbnchars[:13])
        and isbnlib.is_isbn10(isbnchars[13:])
    ):
        return isbnchars[:13], isbnchars[13:]
    elif (
        len(isbnchars) == 23
        and isbnlib.is_isbn10(isbnchars[:10])
        and isbnlib.is_isbn13(isbnchars[10:])
    ):
        return isbnchars[:10], isbnchars[10:]

    # if we get this far then  we have 10+ string, but it's not a ISBN 10, 13 or a basic combination of the two. This is
    # beyond the scope of this bot job
    return ()


if __name__ == "__main__":
    job = NormalizeISBNJob()

    try:
        job.run()
    except Exception as e:
        job.logger.exception(e)
        raise e
