import csv
import json
import requests
import sys


if __name__ == '__main__':
    csv.field_size_limit(sys.maxsize)
    filepath = sys.argv[1]
    with open(filepath, 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter='\t', quoting=csv.QUOTE_NONE)
        header = {'type': 0,
                  'key': 1,
                  'revision': 2,
                  'last_modified': 3,
                  'JSON': 4}
        with open('need_ocaids.csv', 'w') as fout:
            for row in reader:
                skip_row = False
                _json = json.loads(row[header['JSON']])
                if 'ia_loaded_id' in _json and 'ocaid' not in _json:
                    for ocaid in _json['ia_loaded_id']:
                        ocaid_status_code = requests.get('https://archive.org/details/%s' % ocaid).status_code
                        if ocaid_status_code == 200:
                            olid = _json['key'].split('/')[-1]
                            fout.write(olid + '\t' + ocaid + '\n')
                            fout.flush()
                            skip_row = True
                            break
                if skip_row:
                    continue
                if 'source_records' in _json:
                    for source_record in _json['source_records']:
                        if source_record is not None:
                            if 'ia:' in source_record and 'ocaid' not in _json:
                                ocaid = source_record.split(':')[-1]
                                ocaid_status_code = requests.get('https://archive.org/details/%s' % ocaid).status_code
                                if ocaid_status_code == 200:
                                    olid = _json['key'].split('/')[-1]
                                    fout.write(olid + '\t' + ocaid + '\n')
                                    fout.flush()
                                    break
# 25908 missing ocaids
