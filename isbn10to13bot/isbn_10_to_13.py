"""
isbn 10 to isbn 13
NOTE: This script ideally works on an Open Library Dump that only contains editions with an isbn_10 and no isbn_13
"""
import gzip
import json

import isbnlib
import olclient


class ConvertISBN10to13Job(olclient.AbstractBotJob):
    def run(self) -> None:
        """Looks for any ISBN 10s to convert to 13"""
        self.write_changes_declaration()
        header = {"type": 0, "key": 1, "revision": 2, "last_modified": 3, "JSON": 4}
        comment = "convert ISBN 10 to 13 using isbnlib"
        with gzip.open(self.args.file, "rb") as fin:
            for row_num, row in enumerate(fin):
                row = row.decode().split("\t")
                _json = json.loads(row[header["JSON"]])
                if _json["type"]["key"] != "/type/edition":
                    continue

                if "isbn_10" in _json:
                    isbns_10 = _json.get("isbn_10", None)
                else:
                    # we only update editions with existing isbn 10s
                    continue

                if "isbn_13" in _json:
                    # we only update editions with no existing isbn 13s (for now at least)
                    continue

                olid = _json["key"].split("/")[-1]
                edition = self.ol.Edition.get(olid)
                if edition.type["key"] != "/type/edition":
                    continue

                if hasattr(edition, "isbn_13"):
                    # we only update editions with no existing isbn 13s (for now at least)
                    continue

                isbns_13 = []
                for isbn in isbns_10:
                    canonical = isbnlib.canonical(isbn)
                    if isbnlib.is_isbn10(canonical):
                        isbn_13 = isbnlib.to_isbn13(canonical)
                    if isbnlib.is_isbn13(canonical):
                        isbn_13 = canonical
                    if isbn_13:
                        isbns_13.append(isbn_13)

                if len(isbns_13) > 1:
                    isbns_13 = dedupe(
                        isbns_13
                    )  # remove duplicates, shouldn't normally be necessary

                setattr(edition, "isbn_13", isbns_13)
                self.logger.info("\t".join([olid, str(isbns_10), str(isbns_13)]))
                self.save(lambda: edition.save(comment=comment))


def dedupe(input_list: list) -> list:
    """Remove duplicate elements in a list and return the new list"""
    output = []
    for i in input_list:
        if i not in output:
            output.append(i)
    return output


if __name__ == "__main__":
    job = ConvertISBN10to13Job()

    try:
        job.run()
    except Exception as e:
        job.logger.exception(e)
        raise e
