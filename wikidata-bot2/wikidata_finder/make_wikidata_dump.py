"""saves all wikidata items with Open Librarr ids to disk"""

import gzip
import sys

from SPARQLWrapper import SPARQLWrapper, JSON

if __name__ == '__main__':
    filename = sys.argv[1]

    '''get SPARQL results from Wikidata'''
    endpoint_url = 'https://query.wikidata.org/sparql'
    query = '''SELECT ?item ?olid WHERE {
      ?item wdt:P648 ?olid.
    }'''
    user_agent = 'WDQS-example Python/%s.%s' % (sys.version_info[0], sys.version_info[1])
    sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    '''Store SPARQL results in a gz file'''
    with gzip.open(filename, 'w') as fout:
        for result in results['results']['bindings']:
            wikidata_id = result['item']['value'].split('/')[-1]
            fout.write('\t'.join([result['olid']['value'], wikidata_id, '\n']).encode())
