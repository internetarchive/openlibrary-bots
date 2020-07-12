"""
normalize ISBNs
NOTE: This script assumes the Open Library Dump passed only contains editions with an isbn_10 or isbn_13
"""
import argparse
import datetime
import isbnlib
import gzip
import json
import logging
import sys

from olclient.openlibrary import OpenLibrary
from os import makedirs


class NormalizeISBNbot(OpenLibrary):
    """Useful class to normalize ISBN"""
    def __init__(self, dry_run=True, limit=1, *args, **kwargs):
        """Create logger and class variables then initialize as normal"""
        self.changed = 0
        self.dry_run = dry_run
        self.limit = limit

        job_name = sys.argv[0]
        self.logger = logging.getLogger("jobs.%s" % job_name)
        self.logger.setLevel(logging.DEBUG)
        log_formatter = logging.Formatter('%(name)s;%(levelname)-8s;%(asctime)s %(message)s')
        self.console_handler = logging.StreamHandler()
        self.console_handler.setLevel(logging.WARN)
        self.console_handler.setFormatter(log_formatter)
        self.logger.addHandler(self.console_handler)
        log_dir = 'logs/jobs/%s' % job_name
        makedirs(log_dir, exist_ok=True)
        log_file_datetime = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir + '/%s_%s.log' % (job_name, log_file_datetime)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(log_formatter)
        self.logger.addHandler(file_handler)
        super(NormalizeISBNbot, self).__init__(*args, **kwargs)

    def run(self, dump_filepath: str) -> None:
        """
        dump_filepath -- path to *.txt.gz dump containing editions that need to be operated on
        """
        if self.dry_run:
            self.logger.info('dry_run set to TRUE. Script will run, but no data will be modified.')

        header = {'type': 0,
                  'key': 1,
                  'revision': 2,
                  'last_modified': 3,
                  'JSON': 4}
        comment = 'normalize ISBN'
        with gzip.open(dump_filepath, 'rb') as fin:
            for row_num, row in enumerate(fin):
                if row_num < 9373:
                    continue
                row = row.decode().split('\t')
                _json = json.loads(row[header['JSON']])
                if _json['type']['key'] != '/type/edition':
                    continue
                isbns = dict()
                if 'isbn_10' in _json:
                    isbns['isbn_10'] = _json.get('isbn_10', None)
                if 'isbn_13' in _json:
                    isbns['isbn_13'] = _json.get('isbn_13', None)
                if isbns:
                    olid = _json['key'].split('/')[-1]
                    edition_obj = self.Edition.get(olid)
                    if edition_obj.type['key'] != '/type/edition':
                        continue
                    for isbn_type, isbn_value in isbns.items():
                        isbn = getattr(edition_obj, isbn_type, [])
                        for n in isbn:
                            normalized_isbn = isbnlib.get_canonical_isbn(n)
                            if normalized_isbn and normalized_isbn != n:  # get_canonical_isbn returns None if given invalid ISBN
                                setattr(edition_obj, isbn_type, [normalized_isbn])
                                self.logger.info('\t'.join([olid, n, normalized_isbn]))
                                self.save(edition_obj, **{'comment': comment})

    def save(self, ol_obj, *args, **kwargs):
        """Modify default save behavior based on 'limit' and 'dry_run' parameters"""
        if not self.dry_run:
            ol_obj.save(*args, **kwargs)
        else:
            self.logger.info('Modification not made because dry_run is True')
        self.changed += 1
        if self.changed >= self.limit:
            self.logger.info('Modification limit reached. Exiting script.')
            sys.exit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dump_path', type=str, default=None,
                        help='Path to *.txt.gz containing OpenLibrary editions data')
    parser.add_argument('--limit', type=int, default=1,
                        help='Limit number of edits performed on OpenLibrary data. Set to zero to allow unlimited edits')
    parser.add_argument('--dry-run', action='store_false',
                        help="Don't actually perform edits on Open Library")
    _args = parser.parse_args()

    bot = NormalizeISBNbot(dry_run=_args.dry_run, limit=_args.limit)
    bot.console_handler.setLevel(logging.INFO)

    try:
        bot.run(_args.dump_path)
    except Exception as e:
        bot.logger.exception("")
        raise e
