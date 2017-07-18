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
from slack import getSlackUserById

headers = {'content-type': 'application/json'}
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

with open('.context', 'r') as f:
    env = json.loads(f.read())

es_host = env['es_host']
es_port = env['es_port']

es = Elasticsearch(hosts=[{'host': es_host, 'port': int(es_port)}])

def RunbookID(value):
    if value is not None:
        print('validator RunbookId='+value)
        result = es.count(index="aws-chatbot-runbook", doc_type="runbook", body={"query": {"match": {"id": value}}})
        print('found '+str(result)+' for runbookid='+value)
        if result['count']==1:
            return value
        else:
            raise Invalid('Contact Administrator, multiple Runbooks with id='+value)
    else:
        raise Invalid("Not a valid value")


def validate(runbook_id, team_member):
    runbook_id_validator=Schema(RunbookID)
    try:
        runbook_id_validator(runbook_id)
    except Invalid:
        return build_validation_result(False,
                                       'RunbookId',
                                       'Invalid runbook identifier, contact administrator')
									   
    if team_member is None or not team_member.startswith('@'):
        return build_validation_result(False,
                                       'SlackUser',
                                       'Invalid TeamMemberName')
   
    return build_validation_result(True, None, None)
	

""" --- Functions that control the bot's behavior --- """
def respond(intent_request):
    """
    Performs dialog management for assigning runbook to a user
    """
    intent = intent_request['currentIntent']['name']    
    source = intent_request['invocationSource']
    userInput = intent_request['inputTranscript'] if 'inputTranscript' in intent_request else None
    output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}


    #get runbook_id from user input or session
    if userInput is not None and re.search('R[0-9]+', userInput) is not None:
        #check if user has specified runbook id in utterance
        intent_request['currentIntent']['slots']["RunbookId"]=re.search('R[0-9]+', userInput).group(0)
    elif 'selected_runbook' in output_session_attributes:
        # get runbook from session if present
        runbook=json.loads(output_session_attributes['selected_runbook'])
        intent_request['currentIntent']['slots']["RunbookId"]=runbook['id']
    
    #get slack user from user input
    if userInput is not None and re.search('@\w+', userInput) is not None:
        #check if user has specified @user in utterance
        assignee=re.search('@\w+', userInput).group(0)
        intent_request['currentIntent']['slots']["SlackUser"]=assignee    

    
    if source == 'DialogCodeHook':
        slots = get_slots(intent_request)
        print('respond intentName={}, slots={}'.format(str(intent_request['currentIntent']['name']), str(slots)))

        runbook_id=slots['RunbookId'] if 'RunbookId' in slots else None
        assignee=slots["SlackUser"] if 'SlackUser' in slots else None

        validation_result = validate(runbook_id, assignee)
        print('respond validation result={}, invalid slot={}'.format(str(validation_result['isValid']),str(validation_result['violatedSlot'])))
        
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
   
            if validation_result['violatedSlot']=='RunbookId':
                print('respond elicit-slot session={}, invalid slot={}'.format(str(output_session_attributes),str(validation_result['violatedSlot'])))
                return elicit_slot_with_text_message(output_session_attributes, intent, slots, validation_result['violatedSlot'], 'Invalid Runbook, please provide a valid Runbook ID')                
         
            if validation_result['violatedSlot']=='SlackUser':
                print('respond elicit-slot session={}, invalid slot={}'.format(str(output_session_attributes),str(validation_result['violatedSlot'])))
                return elicit_slot_with_text_message(output_session_attributes, intent, slots, validation_result['violatedSlot'], 'Invalid slack user, mention slack users with \'@\' prefix')                

    print('respond output_session_attributes={}, slots={}'.format(str(output_session_attributes), str(slots)))
    return delegate(output_session_attributes, get_slots(intent_request))
                  
""" --- Intents --- """
def dispatch(intent_request):
    print('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))
    return respond(intent_request)


""" --- Main handler --- """
def lambda_handler(event, context):
    print('event.bot.name={}'.format(event['bot']['name']))
    return dispatch(event)
	