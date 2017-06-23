import re
# ocaid python module ocaid.py
# for working with and cleaning up Internet Archive ids

def extract(bad_id):
    # basic archive.org urls
    output = re.sub("(http(s)?://)?(www.)?archive.org/details/", "", bad_id)
    output = re.sub("^.*archive.org/(download|stream|[0-9]+/items)/([^/]+).*", r'\2', output)
    return output
