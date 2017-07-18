# -*- coding: utf-8 -*-
"""
Created on Fri Jul 07 10:10:39 2017

@author: 160229
"""
from __future__ import print_function

import logging

from datetime import datetime
from elasticsearch import Elasticsearch 

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

with open('.context', 'r') as f:
    env = json.loads(f.read())

es_host = env['es_host']
es_port = env['es_port']

""" --------- Runlog class -------------- """
class Runlog:
    def __init__(self, runlogId, id, name, level, user, originator, recipient, status, message, issue, resolution, resolutionCount, logTime):
        self.runlogId=runlogId
        self.id=id
        self.name=name
        self.level=level
        self.user=user
        self.originator=originator
        self.recipient=recipient
        self.status=status
        self.message=message
        self.issue=issue
        self.resolution=resolution
        self.resolutionCount=resolutionCount
        self.logTime=logTime.strftime("%Y-%m-%dT%H:%M:%S.%fZ") #yyyy-MM-dd'T'HH:mm:ss.SSSZZ
    
    def __str__(self):
        return str(self.__dict__)
        
    @classmethod
    def create(cls, id, name, user, originator):
        return cls(getNextRunlogId(), id, name, 'RUNBOOK', user, originator, user, 'NEW', None, None, None, 0, datetime.now())
        
    @classmethod
    def start(cls, runlogId, id, name, level, user, originator):
        return cls(runlogId, id, name, level, user, originator, user, 'START', None, None, None, 0, datetime.now())

    @classmethod
    def finish(cls, runlogId, id, name, level, user, originator, message):
        return cls(runlogId, id, name, level, user, originator, user, 'FINISH', message, None, None, 0, datetime.now())

    @classmethod
    def raise_error(cls, runlogId, id, name, level, user, originator, message, issue,resolution):
        return cls(runlogId, id, name, level, user, originator, user, 'ERROR', message, issue, resolution, 0, datetime.now())

    @classmethod
    def resolve(cls, runlogId, id, name, level, user, originator, message, issue, resolution, resolutionCount):
        return cls(runlogId, id, name, level, user, originator, user, 'RESOLVE', message, issue, resolution, resolutionCount, datetime.now())

    @classmethod
    def assign(cls, runlogId, id, name, originator, recipient):
        return cls(runlogId, id, name, 'RUNBOOK', recipient, originator, recipient, 'ASSIGN', None, None, None, 0, datetime.now())


""" --------- Query templates --------------- """
query_for_user_runlogs={
	"query": {
		"bool": {
			"must": [
               {"match": {"user": "zafarkhan" } },
               {"match": {"level": "RUNBOOK" } }
			],
			"must_not": [{"match": {"status": "FINISHED"} } ]
		}
	},
	"sort": {"logTime": {"order": "desc"} },
    "size": 10
}

query_runlog_entry_for_resolution={
    "query": {
        "nested" : {
            "path" : "resolution",
            "score_mode" : "avg",
            "query" : {
                "bool" : {
                    "must" : [
                     {
                         "exists" : { "field" : "resolution.resolution" }
                     },
                     {
                         "multi_match": {
                            "query": "permission error",
                            "fields": ["resolution.summary","resolution.description"]
                        }
                     }
                    ]
                }
            }
        }
    },
    "sort":[ {"logTime": {"order": "desc"} },
             {"resolutionCount":{"order":"desc"}}],
    "size": 2
} 

all_runlog_entry_by_runlogId = {
    "query": {
        "match_phrase": { "runlogId": "" }
    },
	"sort": [ {"logTime":"desc"} ],
    "size": 20
}

query_for_user_runlogs_by_status={
	"query": {
		"bool": {
			"must": [
               {"match": {"user": "zafarkhan" } },
               {"match":{"status":"ASSIGN"}}
			]
		}
	},
	"sort": {"logTime": {"order": "desc"} }
}

last_runlog_entry_by_runlogId = {
    "query": {
        "match_phrase": { "runlogId": "" }
    },
	"sort": [ {"logTime":"desc"} ],
   "size":1
}

runlog_entry_by_runlogId_and_level_and_user = {
	"query": {
		"bool": {
			"must": [
				{ "match": {"runlogId": "RL2" } },
				{ "match": {"level": "RUNBOOK" } },
				{ "match": {"user": "@praveen.koduganty" } }
			]
		}
	},
	"sort": [ {"logTime":"desc"} ],
    "size": 1
}

""" --- Helpers to access runbook details --- """

update_runlog_entry_by_runlogId = {
   "doc" :{}
}


""" --- Helpers to access runlogs details --- """
def getNextRunlogId():
    result = es.search(index="aws-chatbot-runlog", doc_type="runlog", body={"query": {"match": { "status": "NEW"} }, "sort":[{ "logTime" : "desc" }], "size":1})
    if result['hits']['total']==0:
        return 'RL'+str(1000)
    else:
        current=result['hits']['hits'][0]['_source']['runlogId'][2:]
        return 'RL'+str(int(current)+1)

def save(runlog_entry):
    es.index(index="aws-chatbot-runlog", doc_type="runlog", body=runlog_entry.__dict__)


def getAllRunlogEntriesById(runlog_id):
    if runlog_id is not None:
        all_runlog_entry_by_runlogId['query']['match_phrase']['runlogId']=runlog_id
        result = es.search(index="aws-chatbot-runlog", doc_type="runlog", body=all_runlog_entry_by_runlogId)    
        if result['hits']['total']>0:            
            return [hit['_source'] for hit in result['hits']['hits']]
    

def getLastRunlogEntryById(runlog_id):
    if runlog_id is not None:
        last_runlog_entry_by_runlogId['query']['match_phrase']['runlogId']=runlog_id
        result = es.search(index="aws-chatbot-runlog", doc_type="runlog", body=last_runlog_entry_by_runlogId)    
        if result['hits']['total']>0:        
            return result['hits']['hits'][0]['_source']
            
            
def getLastRunlogEntry(runlog_id, level, user):
    if runlog_id is not None and level is not None and user is not None:
        runlog_entry_by_runlogId_and_level_and_user['query']['bool']['must'][0]['match']['runlogId']=runlog_id
        runlog_entry_by_runlogId_and_level_and_user['query']['bool']['must'][1]['match']['level']=level
        runlog_entry_by_runlogId_and_level_and_user['query']['bool']['must'][2]['match']['user']=user        
        result = es.search(index="aws-chatbot-runlog", doc_type="runlog", body=runlog_entry_by_runlogId_and_level_and_user)    
        if result['hits']['total']>0:        
            return result['hits']['hits'][0]['_source']


def getRunbookIdForRunlog(runlog_id, user):
    if runlog_id is not None:
        runlog_entry_by_runlogId_and_level_and_user['query']['bool']['must'][0]['match']['runlogId']=runlog_id
        runlog_entry_by_runlogId_and_level_and_user['query']['bool']['must'][1]['match']['level']='RUNBOOK'        
        runlog_entry_by_runlogId_and_level_and_user['query']['bool']['must'][2]['match']['user']=user        
        result = es.search(index="aws-chatbot-runlog", doc_type="runlog", body=runlog_entry_by_runlogId_and_level_and_user)    
        if result['hits']['total']>0:        
            return result['hits']['hits'][0]['_source']['id']
                        
def getAssignedRunlogs(user):
    
    if user is not None:
        query_for_user_runlogs["query"]["bool"]["must"][0]["match"]["user"]=user
        
        result = es.search(index="aws-chatbot-runlog", doc_type="runlog", body=query_for_user_runlogs)
        runlogs = [r['_source'] for r in result['hits']['hits']]    
        assignedRunlogIdList = []
        delegatedRunlogIdList = []
        assignedRunlogs = []
        
        for runlog in runlogs:
            if runlog['runlogId'] not in assignedRunlogIdList and runlog['runlogId']  not in delegatedRunlogIdList :                
                if runlog['status'] != None and runlog['status'].lower() != "assign" :
                        assignedRunlogIdList.append(runlog['runlogId'])
                        assignedRunlogs.append(runlog)
                else : 
                        delegatedRunlogIdList.append(runlog['runlogId'])
        return { "runlogs": assignedRunlogs}
    
def updateRunlog(runlog):
    if runlog is not None:
        update_runlog_entry_by_runlogId['doc'] = runlog
        result = es.search(index="aws-chatbot-runlog",doc_type="runlog",body=update_runlog_entry_by_runlogId)
        print(result)
            
    
""" To get results from stack overflow"""    
def getResolutionsStackOverflow(query):
   try:
       Report = []
       results = search_stackoverflow(
    query, "AIzaSyC4cu27sl3nCnkNPERaC16nvl-TP2TSxlY", "014029225622276855886:0kzby6kc9cw", num=5)
       for result in results:
                 jsonObject = {
                 'url':result['link'],
                 'desc':result['pagemap'],
                 'title':result['title']
                }
                 Report.append(jsonObject)
       answers = []   
       for item in Report:
           if 'answer' in item['desc']:
                for answer in item['desc']['answer']:
                    answerjson = {
                    "url":item['url'],
                    "resolution": answer['text'],
                    "resolutionCount":answer['upvotecount'],
                    "issue": item['title'],
                    "source" :"stackoverflow"
                    }
                    answers.append(answerjson)
       sorted(answers, key=lambda k: k['upvotecount'],reverse=True)
       return answers[:2]                  
   except Exception:
    return []
    
#sennds request to google and gives response back
def search_stackoverflow(query, api_key, cse_id, **kwargs):
    try:
        service = build("customsearch", "v1", developerKey=api_key)
        res = service.cse().list(q=query, cx=cse_id, **kwargs).execute()
        return res['items']
    except Exception,err:
        print(err)
        return []
        
def getResolution(runlog_id):    
    if runlog_id is not None:
        runlog = getLastRunlogEntryById(runlog_id)        
        query_runlog_entry_for_resolution["query"]["nested"]["query"]["bool"]["must"][1]["multi_match"]["query"]=runlog["resolution"]["summary"]        
        resolutions_from_runlogs = es.search(index="aws-chatbot-runlog",doc_type="runlog",body=query_runlog_entry_for_resolution)
        resolutionList = [] 
        
        for entry in [r['_source'] for r in resolutions_from_runlogs['hits']['hits']]:
            resolution = {}
            resolution['source'] = "runlog"
            resolution['resolution'] = entry['resolution']['resolution']
            resolution['resolutionCount'] = entry['resolutionCount']
            resolutionList.append(resolution)
            
        results_from_stackoverflow = getResolutionsStackOverflow(runlog['resolution']['summary'])        
        resolutionList= resolutionList + results_from_stackoverflow
        i=0
        for entry in resolutionList:
            resolution['id'] = ++i        
    return {"Resolutions":resolutionList}
   
    
""" --- Helper Functions --- """
if __name__=='__main__':
    #print(getResolution("RL1"))
    #print(getRunbookIdForRunlog('RL3','@praveen.koduganty'))
    print(getLastRunlogEntry('RL2','TASK','@praveen.koduganty'))