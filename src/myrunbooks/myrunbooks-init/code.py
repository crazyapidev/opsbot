# -*- coding: utf-8 -*-
"""
Created on Fri Jul 07 10:10:39 2017

@author: 160229
"""
from __future__ import print_function

import logging

from helper import build_multiple_response_cards, elicit_intent_with_response_card
from runlog import getRunbookIdForRunlog,getAssignedRunlogs
from slack import getSlackUserById

headers = {'content-type': 'application/json'}
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

""" --- Functions that control the bot's behavior --- """
def respond(intent_request):
    """
    Performs dialog management for listing runlogs of a user
    """
    current_user = getSlackUserById(intent_request['userId'])
    source = intent_request['invocationSource']
    output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}

    attachments=[]
    if source == 'DialogCodeHook':        
        result = getAssignedRunlogs(current_user) #search for runlogs for current user
        
        if result:
            for log in result['runlogs']:
                buttons = [ {"text":"Start/Resume", "value":'execute '+ log.runlogId }, {"text":"Assign", "value":'delegate '+log.runlogId } ] 
                
                runbook_for_runlog_id=getRunbookIdForRunlog(log.runlogId, current_user)
                response_card = { 'title': (runbook_for_runlog_id.id +': '+runbook_for_runlog_id.name), 'subTitle' : runbook_for_runlog_id['status'], 'options': buttons }
                attachments.insert(0, response_card)

    if len(attachments)==0:
        attachments.append( {'title': 'No tasks found','subTitle': 'You don\'t have any tasks','options':None } )

    response_cards=build_multiple_response_cards(attachments)        
    print('respond elicit-intent response_cards={}'.format(str(response_cards)))
    return elicit_intent_with_response_card(output_session_attributes, 'Please select from below list', response_cards)

                  
""" --- Intents --- """
def dispatch(intent_request):
    print('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))
    return respond(intent_request)


""" --- Main handler --- """
def lambda_handler(event, context):
    print('event.bot.name={}'.format(event['bot']['name']))
    return dispatch(event)
    