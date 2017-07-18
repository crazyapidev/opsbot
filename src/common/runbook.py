# -*- coding: utf-8 -*-
"""
Created on Sun Jul 09 20:38:43 2017

@author: 160229
"""
from __future__ import print_function

import logging

from elasticsearch import Elasticsearch 

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

with open('.context', 'r') as f:
    env = json.loads(f.read())

es_host = env['es_host']
es_port = env['es_port']

""" --------- Query templates --------------- """

query_match_all={
    "query": {
        "match_all": {}
    },
    "aggs" : {
        "type" : {
            "terms" : { "field" : "type.keyword" },
            "aggs" : {
                "products" : { "terms" : { "field" : "product.keyword" } }
            }
        }
        ,"product" : {
            "terms" : { "field" : "product.keyword" },
            "aggs" : {
                "types": { "terms" : { "field" : "type.keyword" } },
                "actions": { "terms" : { "field" : "action.keyword" } }
            }
        }
        ,"action" : { "terms" : { "field" : "action.keyword" } }
    },
    "size":5
}


query_by_name={
    "query": {
        "dis_max": {
            "queries": []
        }
    },
    "aggs" : {
        "type" : { "terms" : { "field" : "type.keyword" } }
        ,"product" : { "terms" : { "field" : "product.keyword" } }
        ,"action" : { "terms" : { "field" : "action.keyword" } }
    },
    "size":5
}


""" --- Helpers to access runbook details --- """

def getRunbookById(value):
    result = es.search(index="aws-chatbot-runbook", doc_type="runbook", body={"query": {"match": {"id": value}}})
    return result['hits']['hits'][0]['_source']

def getAllRunbooks():
    result = es.search(index="aws-chatbot-runbook", doc_type="runbook", body=query_match_all)
    runbooks = [r['_source'] for r in result['hits']['hits']]	
    return { "runbooks": runbooks, "facets": result['aggregations']} # facets['product']['buckets'] = [ {"key":"EC2", "doc_count":10}, {"key":"S3", "doc_count":2}]

def searchByName(name,product,runbook_type,action_type):    
    query_by_name["query"]["dis_max"]["queries"]=[] #reset

    if name is not None:
        query_by_name["query"]["dis_max"]["queries"].append({"term": {"name": name} })
    
    if product is not None:
        query_by_name["query"]["dis_max"]["queries"].append({"match_phrase":{"product.keyword":product}})

    if runbook_type is not None:
        query_by_name["query"]["dis_max"]["queries"].append({"match_phrase":{"type.keyword":runbook_type}})

    if action_type is not None:
        query_by_name["query"]["dis_max"]["queries"].append({"match_phrase":{"action.keyword":action_type}})
        
        
    if name is None and product is None and runbook_type is None and action_type is None:
        query_by_name["query"]["dis_max"]["queries"].append({"match_all":{}})
        
    print('searchByName query={}'.format(query_by_name))
    result = es.search(index="aws-chatbot-runbook", doc_type="runbook", body=query_by_name)
    print('searchByName result={}'.format(str(result)))
        
    runbooks = [r['_source'] for r in result['hits']['hits']]	
    print('searchByName runbooks={}'.format(str(runbooks)))
    return { "runbooks": runbooks, "facets": result['aggregations']}


""" --- Helper Functions --- """

if __name__=='__main__':
    print(searchByName(name="lex",product='aws lambda',runbook_type=None,action_type=None))
    #print([{"key":f['key']+'('+str(f['doc_count'])+')',"value":f['key']} for f in getAllRunbooks()['facets']['type']['buckets'] ])
