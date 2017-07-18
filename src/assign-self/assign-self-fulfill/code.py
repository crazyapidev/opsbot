# -*- coding: utf-8 -*-
"""
Created on Fri Jul 07 10:10:39 2017

@author: 160229
"""

import json
import logging

from helper import close, get_slots, build_response_card, elicit_intent_with_response_card
from runbook import getRunbookById
from runlog import Runlog, save
from slack import getSlackUserById

headers = {'content-type': 'application/json'}
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


""" --- Functions that control the bot's behavior --- """
def respond(intent_request):
    """
    fulfill assign intent
    """
    output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    
    runbook_id = get_slots(intent_request)["RunbookId"]
    current_user = getSlackUserById(intent_request['userId'])

    print('respond::fulfill intentName={}, slots={}'.format(str(intent_request['currentIntent']['name']), str(get_slots(intent_request))))

    runbook=getRunbookById(runbook_id)
    runlog_entry = Runlog.create(runbook_id, runbook['name'], current_user, current_user)
    save(runlog_entry)
    print('respond save runlog={}'.format(str(runlog_entry)))
    output_session_attributes['runlog']=json.dumps(runlog_entry.__dict__)

    print('respond elicit_intent session={}, slots={}'.format(str(output_session_attributes), str(get_slots(intent_request))))
    buttons = [ 
        {"text":"Execute","value": "execute "+runlog_entry.runlogId}
    ]
    response_card = build_response_card('Execute '+runbook_id, runbook['name'], buttons)
    print('response elicit_intent_with_response_card = {}'.format(str(response_card)))

    return elicit_intent_with_response_card(output_session_attributes, 'Added \''+runbook_id+'\' to your TODOs, click Execute to run through now.', response_card)
        
""" --- Intents --- """
def dispatch(intent_request):
    print('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))
    return respond(intent_request)


""" --- Main handler --- """
def lambda_handler(event, context):
    logger.debug('event.bot.name={}'.format(event['bot']['name']))
    return dispatch(event)
	