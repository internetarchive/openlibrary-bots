import gzip
import json
import requests
import sys

from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def add_line_to_gz(_fout, data, _ocaid):
    """writes 2 columns to a *.tsv and OLID and OCAID columns respectively"""
    olid = data['key'].split('/')[2]
    _fout.write('\t'.join((olid, _ocaid, '\n')).encode())


def is_ocaid_valid(_ocaid, _session):
    """Tries to connect to Internet Archive API a fixed amount times before giving up"""
    url = 'https://archive.org/details/%s' % _ocaid
    try:
        response = _session.get(url)
    except Exception:
        return False  # FIXME what's the logical thing to do here?
    return response.status_code == 200


if __name__ == '__main__':
    session = requests.Session()
    retry = Retry(connect=5, backoff_factor=0.1)
    ia_adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', ia_adapter)

    in_filepath = sys.argv[1]
    out_filepath = sys.argv[2]
    with gzip.open(in_filepath, 'rb') as fin:
        header = {'type': 0,
                  'key': 1,
                  'revision': 2,
                  'last_modified': 3,
                  'JSON': 4}
        with gzip.open(out_filepath, 'w') as fout:
            for row in fin:
                out = '.'
                skip_row = False
                raw_json = row.decode().split('\t')[header['JSON']]
                if 'ia_loaded_id' in raw_json:
                    _json = json.loads(row.decode().split('\t')[header['JSON']])
                    for ocaid in _json['ia_loaded_id']:
                        if is_ocaid_valid(ocaid, session):
                            add_line_to_gz(fout, _json, ocaid)
                            skip_row = True
                            out = 'F'
                            break
                if skip_row:
                    sys.stdout.write(out)
                    sys.stdout.flush()
                    continue
                if 'source_records' in raw_json:
                    _json = json.loads(row.decode().split('\t')[header['JSON']])
                    for source_record in _json['source_records']:
                        if 'ia:' in source_record:
                            ocaid = source_record.split(':')[1]
                            if is_ocaid_valid(ocaid, session):
                                add_line_to_gz(fout, _json, ocaid)
                                out = 'F'
                                break
                sys.stdout.write(out)
                sys.stdout.flush()
