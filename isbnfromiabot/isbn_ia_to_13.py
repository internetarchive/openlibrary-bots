"""
BWB isbn ref to isbn 13
NOTE: This script ideally works on an Open Library Dump that only contains editions with an BWB isbn ref and no isbn_13
"""
import gzip
import json
import re

import isbnlib
import olclient


class ConvertISBNiato13Job(olclient.AbstractBotJob):
    def run(self) -> None:
        """Looks for any IA ISBN to convert to 13"""
        self.write_changes_declaration()
        header = {"type": 0, "key": 1, "revision": 2, "last_modified": 3, "JSON": 4}
        comment = "extract ISBN 13 from IA source_record"
        with gzip.open(self.args.file, "rb") as fin:
            for row_num, row in enumerate(fin):
                row = row.decode().split("\t")
                _json = json.loads(row[header["JSON"]])
                if _json["type"]["key"] != "/type/edition":
                    continue

                if hasattr(_json, "isbn_13"):
                    # we only update editions with no existing isbn 13s (for now at least)
                    continue

                if "source_records" in _json:
                    source_records = _json.get("source_records", None)
                else:
                    continue
                regex = "ia:isbn_[0-9]{13}"
                isbn_13 = False
                for source_record in source_records:
                    if re.fullmatch(regex, source_record):
                        isbn_13 = source_record[8:]
                        break

                if not isbn_13:
                    continue

                if not isbnlib.is_isbn13(isbn_13):
                    continue

                olid = _json["key"].split("/")[-1]
                edition = self.ol.Edition.get(olid)
                if edition.type["key"] != "/type/edition":
                    continue

                if hasattr(edition, "isbn_13"):
                    # don't update editions that already have an isbn 13
                    continue

                isbns_13 = [isbn_13]

                setattr(edition, "isbn_13", isbns_13)
                self.logger.info("\t".join([olid, source_record, str(isbns_13)]))
                self.save(lambda: edition.save(comment=comment))


if __name__ == "__main__":
    job = ConvertISBNiato13Job()

    try:
        job.run()
    except Exception as e:
        job.logger.exception(e)
        raise e
