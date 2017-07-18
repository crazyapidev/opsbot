# -*- coding: utf-8 -*-
"""
Created on Fri Jul 07 10:10:39 2017

@author: 160229
"""
from __future__ import print_function

import re
import json
import logging

from helper import get_slots, build_response_card, elicit_slot_with_response_card, close
from runlog import getLastRunlogEntryById, Runlog, getLastRunlogEntry,save, Issue
from slack import getSlackUserById

headers = {'content-type': 'application/json'}
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

""" --- Functions that control the bot's behavior --- """
def respond(intent_request):
    """
    Performs dialog management for listing runlogs querying for resolution
    """
    intent = intent_request['currentIntent']['name']    
    current_user = getSlackUserById(intent_request['userId'])
    userInput = intent_request['inputTranscript']
    source = intent_request['invocationSource']
    output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    
    runlog_id = get_slots(intent_request)['RunlogId'] if 'RunlogId' in get_slots(intent_request) else None
    if runlog_id is None:
        if re.search('RL[0-9]+', userInput) is not None:
            #check if user has specified runlog id in utterance
            runlog_id=re.search('RL[0-9]+', userInput).group(0)
            intent_request['currentIntent']['slots']["RunlogId"]=runlog_id
        elif 'runlog' in output_session_attributes:
            # get runlog from session if present
            runlog=json.loads(output_session_attributes['runlog'])
            runlog_id=runlog['runlogId']
            intent_request['currentIntent']['slots']["RunlogId"]=runlog_id 
            
    resolve_issue = get_slots(intent_request)['ResolveIssue'] if 'ResolveIssue' in get_slots(intent_request) else None
    add_resolution = get_slots(intent_request)['AddResolution'] if 'AddResolution' in get_slots(intent_request) else None        

    if source == 'DialogCodeHook':        
        log = getLastRunlogEntryById(runlog_id) #search for last runlog entry with issue description              
        
        if  not resolve_issue:
            buttons = [{"text":"Mark Resolved","value":"resolve-issue"}]
            response_card = build_response_card(log['runlogId'] 
                                                +"-"+log['resolution']['summary']
                                                ,log['resolution']['description'],buttons)
            
            return elicit_slot_with_response_card(output_session_attributes,
                intent,
                get_slots(intent_request),
                'ResolveIssue',
                Issue(log['resolution']['issueType'], 
                    log['resolution']['severity'], 
                    log['resolution']['environment'], 
                    log['resolution']['summary'], 
                    log['resolution']['description'],
                    add_resolution).__dict__,
                response_card)
                               
        if resolve_issue == "resolve-issue":                        
            last_task_entry = getLastRunlogEntry(runlog_id, 'TASK', current_user)
            runlog_entry = Runlog.resolve(runlog_id, last_task_entry.id, last_task_entry.name, 'TASK', current_user, last_task_entry.originator, 'Resolution found for issue :\n'+log['resolution']['summary'], 
                                          None,
                                          json.dumps(Issue(log['resolution']['issueType'], 
                                            log['resolution']['severity'], 
                                            log['resolution']['environment'], 
                                            log['resolution']['summary'], 
                                            log['resolution']['description'],
                                            add_resolution).__dict__
                                        ),
                                        last_task_entry.resolutionCount)
            save(runlog_entry)
            print('respond save runlog={}'.format(str(runlog_entry)))
            output_session_attributes['runlog']=json.dumps(runlog_entry.__dict__)
            return close(output_session_attributes, 'Fulfilled',
                                     {'contentType': 'PlainText',
                                      'content': '''Resolution has been added'''})
                  
""" --- Intents --- """
def dispatch(intent_request):
    print('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))
    return respond(intent_request)


""" --- Main handler --- """
def lambda_handler(event, context):
    print('event.bot.name={}'.format(event['bot']['name']))
    return dispatch(event)
    