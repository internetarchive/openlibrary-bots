#!/usr/bin/python

import catharbot
import json
import re

dupe_list = "../ocaid_dupes.txt"
filename = dupe_list

bot = catharbot.CatharBot()


def is_skippable(doc):
    ''' Skip if the record has already been deleted, redirected
        or had an invalid OCAID removed.
    '''
    if doc['type']['key'] in ['/type/delete', '/type/redirect']:
        return True
    if 'ocaid' in doc:
        return False
    else:
        return True

def extract_edition(line):
    return re.search(r'OL.+M', line).group(0)

def extract_work(line):
    return re.search(r'OL.+W', line).group(0)

def extract_ids(line):
    m = re.match(r'(^.+) (OL.+M) (OL.+W)?', line)
    return m.groups()

def clear_invalid_ocaid(olid):
    data = bot.load_doc(olid) 
    del data['ocaid']
    return bot.save_one(data, "remove invalid ia id")

def merge_group(group):
    if len(group) > 2:
         raise Exception("Not implemented yet!")
    merge_if_same_edition(group)

def normalise(doc):
    if 'works' in doc:
        doc.pop('works')
    doc.pop('created')
    doc.pop('revision')
    return doc

def get_olid(doc):
    return doc['key'].replace('/works/', '').replace('/books/', '')

def get_work(doc):
    if 'works' in doc:
        return get_olid(doc['works'][0])
    return None

def merge_if_same_edition(group):
    a = normalise(bot.load_doc(group[0][0]))
    b = normalise(bot.load_doc(group[1][0]))
    a_set = set(a)
    b_set = set(b)
    if a_set == b_set:
        print("  IDENTICAL EDITIONS FOUND!")
        docs = []
        docs.append(bot.get_redirect(get_olid(b), get_olid(a)))
        docs.append(bot.get_redirect(group[1][1], group[0][1]))
        print(" Merging editions and works:")
        print(bot.save_many(docs, "Merged duplicate OCAIDs"))
        print("  DEBUG: %s" % docs)
    else:
        print(a_set - b_set)
        print(b_set - a_set)

def orphan_check(group):
    works = [ e[1] for e in group if e[1] ]
    for e in group:
        if e[1] is None:
             print("  ORPHAN FOUND! %s" % e[0])
             if len(works) > 1:
                 raise Exception("Multiple works to choose from!")
             else:
                 print("  Associating %s with %s" % (e[0], works[0]))
                 doc = bot.get_move_edition(e[0], works[0])
                 print(bot.save_one(doc, "Associate with work")) 
                

def debug_group(group):
    output = ""
    for e in group:
        output += "%s/books/%s , " % (bot.base_url, e[0])
    editions = [ e[0] for e in group ]
    works = [e[1] for e in group ]
    return "%s \n Editions %s\n Works %s" % (output, editions, works)

start_line = 320
end_line   = 900 

with open(filename, 'r') as infile: 
    last_id = None
    group   = []
    for i, line in enumerate(infile): 
        if i > end_line: 
            break 
        if i >= start_line:
            ocaid, olid, work = extract_ids(line)
            if last_id and ocaid != last_id:
                # end of group, operate on complete group
                if len(group) < 2:
                   print("Nothing to do, length %i Group [%s]" % (len(group), last_id))
                else:
                   works = [ed[1] for ed in group]
                   if len(set(works)) == 1:
                       print("Duplicate Editions only in group [%s]" % last_id)
                   else:
                       # Group has duplicate works and editions
          
                       print("%s: %s" % (last_id, group))
                       print("%i: %s" % (i, debug_group(group)))
                       try:
                           merge_group(group)
                           # check for orphans:
                           orphan_check(group)
                       except Exception as e:
                           print("EXCEPTION %s" % e)

                group = []
            # else:
            #    print("[%s] %s -> %s" % (ocaid, olid, work))
            last_id = ocaid
            data = bot.load_doc(olid) 
            if not is_skippable(data) and data['ocaid'] == ocaid:
                group.append([olid, get_work(data)])