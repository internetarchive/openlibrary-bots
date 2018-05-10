from olclient.openlibrary import OpenLibrary
import json
import olid
#ol = OpenLibrary()

# Importing Base String for Python 2 and 3
try:
  basestring
except NameError:
  basestring = str

DEBUG=True

class CatharBot(OpenLibrary):

    def get_editions_from_work(self, id):
        if DEBUG:
            print(id)
        editions = [e.olid for e in self.Work.get(id).editions]
        return editions

    def get_move_edition(self, edition, work):
        url = self._generate_url_from_olid(edition)
        ed = self.session.get(url).json()
        ed['works'] = [{'key': "/works/" + work}]
        return ed

    def get_redirect(self, from_olid, to_olid):
        ''' 
        from OLID, to OLID
        '''
        assert olid.get_type(from_olid) == olid.get_type(to_olid)
        data = {
            'key': olid.full_key(from_olid),
            'location': olid.full_key(to_olid),
            'type': { 'key': '/type/redirect' }
        }
        return data

    def merge_works(self, duplicate_works, master):
        docs = []
        for w in duplicate_works:
            editions = self.get_editions_from_work(w)
            for e in editions:
                docs.append(self.get_move_edition(e, master))
            docs.append(self.get_redirect(w, master))
        return self.save_many(docs, "Merged duplicate works")

    def merge_editions(self, duplicate_editions, master):
        docs = []
        for e in duplicate_editions:
            docs.append(self.get_redirect(e, master))
        return self.save_many(docs, "Merged duplicate editions")

    def delete_list(self, ids, comment):
        docs = []
        for d in ids:
            docs.append({
                'key': olid.full_key(d),
                'type': '/type/delete'
            })
        return self.save_many(docs, comment)

    def save_many(self, docs, comment):
        headers = {
            'Opt': '"http://openlibrary.org/dev/docs/api"; ns=42',
            '42-comment': comment
        }
        return self.session.post(self.base_url+'/api/save_many', json.dumps(docs), headers=headers)

    def save_one(self, doc, comment):
        doc['_comment'] = comment
        return self.session.put(self.base_url + doc['key'] + ".json", json.dumps(doc))

    def is_modified(self, a, b):
        ''' Check if a string or doc has been modified
        '''
        return a != b

    def recurse_fix(self, data, fix_function, changed=False):
        ''' pass every field in a doc through a function
        '''
        if isinstance(data, basestring):  # only transforming strings at the moment
             return fix_function(data) 
        if isinstance(data, dict):
             output = {}
             for k, v in data.iteritems():
                 output[k] = self.recurse_fix(v, fix_function, changed)
             return output
        if isinstance(data, list):
             output = []
             for item in data:
                 output.append(self.recurse_fix(item, fix_function, changed))
             return output
        # no transform to do, return data
        return data 

    def load_doc(self, id):
        return self.session.get(olid.full_url(id)).json()

