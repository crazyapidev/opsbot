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

from helper import delegate, get_slots, build_validation_result, elicit_slot_with_text_message
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
        print('validator found '+str(result)+' for runbookid='+value)
        if result['count']==1:
            return value
        else:
            raise Invalid('Contact Administrator, multiple Runbooks with id='+value)
    else:
        raise Invalid("Invalid RunbookId, contact administrator")
            

def validate(runbook_id):
    runbook_id_validator=Schema(RunbookID)
    try:
        runbook_id_validator(runbook_id)
    except Invalid:
        return build_validation_result(False,
                                       'RunbookId',
                                       'Invalid runbook identifier, contact administrator')   
    return build_validation_result(True, None, None)


""" --- Functions that control the bot's behavior --- """
def respond(intent_request):
    """
    Performs dialog management for assigning runbook to self and creating a runlog.
    """
    source = intent_request['invocationSource']
    intent = intent_request['currentIntent']['name']    
    userInput = intent_request['inputTranscript']
    output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}

    #get runbook_id from user input or session
    if re.search('R[0-9]+', userInput) is not None:
        #check if user has specified runbook id in utterance
        runbook_id=re.search('R[0-9]+', userInput).group(0)
        intent_request['currentIntent']['slots']["RunbookId"]=runbook_id            
    elif 'selected_runbook' in output_session_attributes:
        # get runbook from session if present
        runbook=json.loads(output_session_attributes['selected_runbook'])
        intent_request['currentIntent']['slots']["RunbookId"]=runbook['id']
    
    print('respond intentName={}, slots={}'.format(str(intent_request['currentIntent']['name']), str(get_slots(intent_request))))
    if source == 'DialogCodeHook':
        slots = get_slots(intent_request)

        runbook_id=intent_request['currentIntent']['slots']["RunbookId"]
        validation_result = validate(runbook_id)
        print('respond validation result={}, invalid slot={}'.format(str(validation_result['isValid']),str(validation_result['violatedSlot'])))        
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            
            if validation_result['violatedSlot']=='RunbookId':
                print('respond elicit-slot session={}, invalid slot={}'.format(str(output_session_attributes),str(validation_result['violatedSlot'])))
                return elicit_slot_with_text_message(output_session_attributes, intent, slots, validation_result['violatedSlot'], 'Invalid Runbook, please provide a valid Runbook ID')                

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
	