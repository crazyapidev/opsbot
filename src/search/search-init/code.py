# -*- coding: utf-8 -*-
"""
Created on Fri Jul 07 10:10:39 2017

@author: 160229
"""
from __future__ import print_function

import json
import logging
from voluptuous import Schema, Invalid
from elasticsearch import Elasticsearch 

from helper import get_slots, build_validation_result, build_response_card, elicit_slot_with_response_card, build_multiple_response_cards, elicit_intent_with_response_card
from runbook import getAllRunbooks, searchByName, getRunbookById
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
            
            
def Product(value):
    if value is not None:
        print('validator Product='+value)
        result = es.count(index="aws-chatbot-runbook", doc_type="runbook", body={"query": {"match_phrase": {"product.keyword": value.lower()}}})
        print('validator found '+str(result)+' for product='+value)
        if result['count']>0:
            return value
        else:
            raise Invalid('No such product exists')
    else:
        raise Invalid("Invalid product, contact administrator")


def validate(product, runbook_type, action, runbook_id):
    product_validator=Schema(Product)
    try:
        product_validator(product)
    except Invalid:
        return build_validation_result(False,
                                       'Product',
                                       'Invalid Product')
    
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
    Performs dialog management for searching and selecting a runbook.
    """
    product = get_slots(intent_request)["Product"]
    runbook_type = get_slots(intent_request)["RunbookType"]
    action = get_slots(intent_request)["ActionType"]
    runbook_id = get_slots(intent_request)["RunbookId"]
    
    print('respond intentName={}, slots={}'.format(str(intent_request['currentIntent']['name']), str(get_slots(intent_request))))

    source = intent_request['invocationSource']    
    intent = intent_request['currentIntent']['name']
    output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
	
    if source == 'DialogCodeHook':
        slots = get_slots(intent_request)

        validation_result = validate(product, runbook_type, action, runbook_id)
        print('respond validation result={}, invalid slot={}'.format(str(validation_result['isValid']),str(validation_result['violatedSlot'])))
        
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            
            # elicit slot for product            
            if validation_result['violatedSlot']=='Product':
                buttons = [ {"text":f['key'].upper()+' ('+str(f['doc_count'])+')',"value":f['key']} for f in getAllRunbooks()['facets']['product']['buckets'] ]
                response_card = build_response_card('Filter by Product/Platform','Select from the following products/platforms', buttons)
                
                print('respond elicit-slot response_card={}, invalid slot={}'.format(str(response_card),str(validation_result['violatedSlot'])))
                return elicit_slot_with_response_card(output_session_attributes,
                               intent,
                               slots,
                               validation_result['violatedSlot'],
                               'Please select from below products',
                               response_card)
                
    
            if validation_result['violatedSlot']=='RunbookId':                
                result = searchByName(None, product, runbook_type, action) #search for runbooks with current slots                
                attachments=[]
                for rbk in result['runbooks']:                    
                    buttons = [ {"text":"Select "+rbk['id'], "value":rbk['id']} ]
                    response_card = { 'title': (rbk['id']+': '+rbk['name']), 'subTitle' : rbk['description'][:75], 'options': buttons }
                    attachments.insert(0, response_card)
                
                response_cards=build_multiple_response_cards(attachments)
                
                print('respond elicit-slot response_cards={}, invalid slot={}'.format(str(response_cards),str(validation_result['violatedSlot'])))
                return elicit_slot_with_response_card(output_session_attributes,
                               intent,
                               slots,
                               validation_result['violatedSlot'],
                               'Please select from below list',
                               response_cards)


        if runbook_id:
            output_session_attributes['selected_runbook'] = json.dumps(getRunbookById(runbook_id)) # serialize runbook obj
            output_session_attributes['previous_intent'] = intent_request['currentIntent']['name']
                        
        print('respond elicit_intent session={}'.format(str(output_session_attributes)))
        # select runbook, and rely on the goodbye message of the bot to define the message to the end user.
        buttons = [ 
                    {"text":"View Details","value": "get "+runbook_id}, 
                    {"text":"Assign to","value": "assign "+runbook_id}, 
                    {"text":"Execute","value": "to do "+runbook_id}
        ]
        response_card = build_response_card('Runbook '+runbook_id, getRunbookById(runbook_id)['name'], buttons)
        print('response elicit_intent_with_response_card = {}'.format(str(response_card)))
    
        return elicit_intent_with_response_card(output_session_attributes, 'Now that you have selected a runbook, what do you want to do next?', response_card)

                  
""" --- Intents --- """
def dispatch(intent_request):
    print('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))
    return respond(intent_request)


""" --- Main handler --- """
def lambda_handler(event, context):
    print('event.bot.name={}'.format(event['bot']['name']))
    return dispatch(event)
	