# -*- coding: utf-8 -*-
"""
Created on Fri Jul 07 10:10:39 2017

@author: 160229
"""
from __future__ import print_function

import re
import json
import logging
from voluptuous import Schema, Invalid
from elasticsearch import Elasticsearch 

from helper import build_validation_result, get_slots, elicit_slot_with_text_message, delegate
from runbook import getRunbookById
from runlog import getRunbookIdForRunlog, Runlog, save
from slack import getSlackUserById

headers = {'content-type': 'application/json'}
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

with open('.context', 'r') as f:
    env = json.loads(f.read())

es_host = env['es_host']
es_port = env['es_port']

es = Elasticsearch(hosts=[{'host': es_host, 'port': int(es_port)}])

def RunlogID(value):
    if value is not None:
        print('validator RunlogId='+value)
        result = es.count(index="aws-chatbot-runlog", doc_type="runlog", body={"query": {"match": {"id": value}}})
        print('found '+str(result)+' for RunlogId='+value)
        if result['count']==1:
            return value
        else:
            raise Invalid('Contact Administrator, multiple runlogs with id='+value)
    else:
        raise Invalid("Not a valid value")


def validate(runlog_id, team_member):
    runlog_id_validator=Schema(RunlogID)
    try:
        runlog_id_validator(runlog_id)
    except Invalid:
        return build_validation_result(False,
                                       'RunlogId',
                                       'Invalid runlog identifier, contact administrator')
									   
    if team_member is None or not team_member.startswith('@'):
        return build_validation_result(False,
                                       'SlackUser',
                                       'Invalid TeamMemberName')
   
    return build_validation_result(True, None, None)
	

""" --- Functions that control the bot's behavior --- """
def respond(intent_request):
    """
    Performs dialog management for delegating runlog to a user
    """
    intent = intent_request['currentIntent']['name']
    current_user = getSlackUserById(intent_request['userId'])
    source = intent_request['invocationSource']
    userInput = intent_request['inputTranscript'] if 'inputTranscript' in intent_request else None
    output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}

    #get runlog_id from user input or session
    runlog = None
    if userInput is not None and re.search('RL[0-9]+', userInput) is not None:
        #check if user has specified runbook id in utterance
        runlog_id=re.search('RL[0-9]+', userInput).group(0)
        intent_request['currentIntent']['slots']["RunlogId"]=runlog_id            
    elif 'runlog' in output_session_attributes:
        # get runlog from session if present
        runlog=json.loads(output_session_attributes['runlog'])
        runlog_id=runlog['runlogId']
        intent_request['currentIntent']['slots']["RunlogId"]=runlog['runlogId']
        
    #get slack user from user input or from slot (unlikely this will work)
    if re.search('@\w+', userInput) is not None:
        #check if user has specified @user in utterance
        intent_request['currentIntent']['slots']["SlackUser"]=re.search('@\w+', userInput).group(0)
    
    runbook_id=intent_request['currentIntent']['slots']['RunbookId'] if 'RunbookId' in intent_request['currentIntent']['slots'] else None
    assignee=intent_request['currentIntent']['slots']["SlackUser"] if 'SlackUser' in intent_request['currentIntent']['slots'] else None
    
    print('respond intentName={}, slots={}'.format(str(intent_request['currentIntent']['name']), str(get_slots(intent_request))))

    if source == 'DialogCodeHook':
        slots = get_slots(intent_request)

        validation_result = validate(runlog_id, assignee)
        print('respond validation result={}, invalid slot={}'.format(str(validation_result['isValid']),str(validation_result['violatedSlot'])))
        
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None            
            
            if validation_result['violatedSlot']=='RunlogId':
                print('respond elicit-slot session={}, invalid slot={}'.format(str(output_session_attributes),str(validation_result['violatedSlot'])))
                return elicit_slot_with_text_message(output_session_attributes, intent, slots, validation_result['violatedSlot'], 'Invalid Runbook, please provide a valid Runbook ID')                
            else:
                print('respond elicit-slot session={}, invalid slot={}'.format(str(output_session_attributes),str(validation_result['violatedSlot'])))
                return elicit_slot_with_text_message(output_session_attributes, intent, slots, validation_result['violatedSlot'], 'Invalid slack user, mention slack users with \'@\' prefix')                
        else:
            runbook_id=getRunbookIdForRunlog(runlog_id, current_user)
            runbook=getRunbookById(runbook_id)
            runlog_entry = Runlog.assign(runbook_id, runbook['name'], current_user, assignee)
            save(runlog_entry)
            print('respond save runlog={}'.format(str(runlog_entry)))
            output_session_attributes['runlog']=json.dumps(runlog_entry.__dict__)

    print('respond intentName={}, slots={}, output_session_attributes={}'.format(str(intent_request['currentIntent']['name']), str(slots), str(output_session_attributes)))
    return delegate(output_session_attributes, get_slots(intent_request))
                  
""" --- Intents --- """
def dispatch(intent_request):
    print('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))
    return respond(intent_request)


""" --- Main handler --- """
def lambda_handler(event, context):
    print('event.bot.name={}'.format(event['bot']['name']))
    return dispatch(event)
	