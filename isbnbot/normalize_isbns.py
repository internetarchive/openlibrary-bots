"""
normalize ISBNs
NOTE: This script assumes the Open Library Dump passed only contains editions with an isbn_10 or isbn_13
"""
import isbnlib
import gzip
import json

import olclient

ALLOWED_ISBN_CHARS = {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "X", "x", "-"}


class NormalizeISBNJob(olclient.AbstractBotJob):
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

    def run(self) -> None:
        """
        Performs ISBN normalization (removes hyphens and capitalizes letters)

        dump_filepath -- path to *.txt.gz dump containing editions that need to be operated on
        """
        if self.dry_run:
            self.logger.info(
                "dry_run set to TRUE. Script will run, but no data will be modified."
            )
        header = {'type': 0,
                  'key': 1,
                  'revision': 2,
                  'last_modified': 3,
                  'JSON': 4}
        comment = 'normalize ISBN'
        with gzip.open(self.args.file, 'rb') as fin:
            for row_num, row in enumerate(fin):
                row = row.decode().split('\t')
                _json = json.loads(row[header['JSON']])
                if _json['type']['key'] != '/type/edition':
                    continue

                isbns_by_type = dict()
                if 'isbn_10' in _json:
                    isbns_by_type['isbn_10'] = _json.get('isbn_10', None)
                if 'isbn_13' in _json:
                    isbns_by_type['isbn_13'] = _json.get('isbn_13', None)

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
                if edition.type['key'] != '/type/edition':
                    continue

                for isbn_type, isbns in isbns_by_type.items():
                    # if an ISBN is in the wrong field this script will not move it to the appropriate one
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


def dedupe(input_list: list) -> list:
    """Remove duplicate elements in a list and return the new list"""
    output = list()
    for i in input_list:
        if i not in output:
            output.append(i)
    return output


if __name__ == '__main__':
    job = NormalizeISBNJob()

    try:
        job.run()
    except Exception as e:
        job.logger.exception(e)
        raise e
