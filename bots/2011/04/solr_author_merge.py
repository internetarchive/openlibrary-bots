#!/usr/bin/python

import _init_path

import sys
from openlibrary import config
from time import time, sleep
import argparse, simplejson, re
from urllib2 import URLError, urlopen
from openlibrary.catalog.utils.query import withKey, set_query_host
from openlibrary.solr.update_work import update_author, update_work, get_work_subjects, add_field, solr_update, AuthorRedirect
from collections import defaultdict
from lxml.etree import tostring, Element
from openlibrary.solr.update import subject_count, subject_need_update

parser = argparse.ArgumentParser(description='solr author merge')
parser.add_argument('--config', default='openlibrary.yml')
parser.add_argument('--state_file', default='author_merge')
args = parser.parse_args()

config_file = args.config
config.load(config_file)

base = 'http://%s/openlibrary.org/log/' % config.runtime_config['infobase_server']
set_query_host('openlibrary.org')

state_file = config.runtime_config['state_dir'] + '/' + args.state_file
offset = open(state_file).readline()[:-1]

#out = open('author_merge_logs', 'w')

re_author_key = re.compile(r'^/(?:a|authors)/(OL\d+A)$')

update_times = []

subjects_to_update = set()
authors_to_update = []

def solr_update_authors(authors_to_update):
    for a in authors_to_update:
        try:
            author_updates = ['<delete>' + ''.join('<id>%s</id>' % re_author_key.match(akey).group(1) for akey in a['redirects']) + '</delete>']
        except:
            print 'redirects'
            print a['redirects']
            raise
        author_updates += update_author(a['master_key'], a=a['master'], handle_redirects=False)
    solr_update(author_updates, debug=False)
    solr_update(['<commit/>'], debug=True)

def solr_update_subjects():
    global subjects_to_update
    print subjects_to_update

    subject_add = Element("add")
    for subject_type, subject_name in subjects_to_update:
        key = subject_type + '/' + subject_name
        count = subject_count(subject_type, subject_name)

        if not subject_need_update(key, count):
            print 'no updated needed:', (subject_type, subject_name, count)
            continue
        print 'updated needed:', (subject_type, subject_name, count)

        doc = Element("doc")
        add_field(doc, 'key', key)
        add_field(doc, 'name', subject_name)
        add_field(doc, 'type', subject_type)
        add_field(doc, 'count', count)
        subject_add.append(doc)

    if len(subject_add):
        print 'updating subjects'
        add_xml = tostring(subject_add).encode('utf-8')
        solr_update([add_xml], debug=False)
        solr_update(['<commit />'], debug=True)

    subjects_to_update = set()

def solr_updates(i):
    global subjects_to_update, authors_to_update
    t0 = time()
    d = i['data']
    changeset = d['changeset']
    print 'author:', d['author']
    try:
        assert len(changeset['data']) == 2 and 'master' in changeset['data'] and 'duplicates' in changeset['data']
    except:
        print d['changeset']
        raise
    master_key = changeset['data']['master']
    dup_keys = changeset['data']['duplicates']
    assert dup_keys
    print 'timestamp:', i['timestamp']
    print 'dups:', dup_keys
    print 'records to update:', len(d['result'])

    master = None
    obj_by_key = {}
    works = []
    editions_by_work = defaultdict(list)
    for obj in d['query']:
        obj_type = obj['type']['key']
        k = obj['key']
        if obj_type == '/type/work':
            works.append(obj['key'])
        elif obj_type == '/type/edition':
            if 'works' not in obj:
                continue
            for w in obj['works']:
                editions_by_work[w['key']].append(obj)
        obj_by_key[k] = obj
    master = obj_by_key.get(master_key)
    #print 'master:', master

    if len(d['result']) == 0:
        print i

    work_updates = []
    for wkey in works:
            #print 'editions_by_work:', editions_by_work
            work = obj_by_key[wkey]
            work['editions'] = editions_by_work[wkey]
            subjects = get_work_subjects(work)
            for subject_type, values in subjects.iteritems():
                subjects_to_update.update((subject_type, v) for v in values)
            try:
                ret = update_work(work, obj_cache=obj_by_key, debug=True)
            except AuthorRedirect:
                work = withKey(wkey)
                work['editions'] = editions_by_work[wkey]
                ret = update_work(work, debug=True, resolve_redirects=True)
            work_updates += ret
    if work_updates:
        solr_update(work_updates, debug=False)

    authors_to_update.append({ 'redirects': dup_keys, 'master_key': master_key, 'master': master})
    print 'authors to update:', len(authors_to_update)

    t1 = time() - t0
    update_times.append(t1)
    print 'update takes: %d seconds' % t1
    print

while True:
    url = base + offset
#out = open('author_redirects', 'w')
#for url in open('author_merge_logs'):
    print url,

    try:
        data = urlopen(url).read()
    except URLError as inst:
        if inst.args and inst.args[0].args == (111, 'Connection refused'):
            print 'make sure infogami server is working, connection refused from:'
            print url
            sys.exit(0)
        print 'url:', url
        raise
    try:
        ret = simplejson.loads(data)
    except:
        open('bad_data.json', 'w').write(data)
        raise

    offset = ret['offset']
    data_list = ret['data']
    if len(data_list) == 0:
        if authors_to_update:
            print 'commit'
            solr_update(['<commit/>'], debug=True)
            solr_update_authors(authors_to_update)
            authors_to_update = []
            solr_update_subjects()

        print 'waiting'
        sleep(10)
        continue
    else:
        print
    for i in data_list:
        action = i.pop('action')
        if action != 'save_many':
            continue
        if i['data']['comment'] != 'merge authors':
            continue
        if 'changeset' not in i['data']:
            print i
        if i['data']['changeset']['kind'] == 'edit-book':
            continue
        if i['timestamp'] == '2010-08-05T14:37:25.139418':
            continue # bad author redirect
        if len(i['data']['result']) == 0:
            continue # no change
        solr_updates(i)

        print "average update time: %.1f seconds" % (float(sum(update_times)) / float(len(update_times)))
    print >> open(state_file, 'w'), offset

#out.close()
