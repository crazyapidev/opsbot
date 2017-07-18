# -*- coding: utf-8 -*-
from __future__ import print_function
"""
Created on Sun Jul 09 20:38:43 2017

@author: 160229
"""

""" --- Helpers to build responses which match the structure of the necessary dialog actions --- """
def get_slots(intent_request):
    return intent_request['currentIntent']['slots']


def elicit_slot_with_text_message(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': {
                "contentType" : "PlainText",
                "content" : message,
            },
        }
    }
    
def elicit_slot_with_response_card(session_attributes, intent_name, slots, slot_to_elicit, message, response_card):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': {
                "contentType" : "PlainText",
                "content" : message,
            },
            'responseCard': response_card
        }
    }   
    
def elicit_intent_with_response_card(session_attributes, message, response_card):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitIntent',
            'message': {
                "contentType" : "PlainText",
                "content" : message,
            },
            'responseCard': response_card
        }
    }       

def confirm_intent_with_response_card(session_attributes, message, response_card):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ConfirmIntent',
            'message': {
                "contentType" : "PlainText",
                "content" : message,
            },
            'responseCard': response_card
        }
    }
    
def build_response_card(title, subtitle, options, url=None):
    """
    Build a responseCard with a title, subtitle, and an optional set of options which should be displayed as buttons.
    """
   
    buttons = None
    if options is not None:
        buttons = []
        for i in range(min(5, len(options))):
            buttons.append(options[i])
 
    return {
        'contentType': 'application/vnd.amazonaws.card.generic',
        'version': 1,
        'genericAttachments': [{
            'title': title,
            'subTitle': subtitle,
            #'attachmentLinkUrl': url,
            'buttons': buttons
       }]
    }

def build_multiple_response_cards(cards):
    """
    Build multiple responseCards with a title, subtitle, and an optional set of options which should be displayed as buttons.
    """
    
    attachments=[]
    for card in cards: 
        buttons = None
        if card['options'] is not None:
            buttons = []
            for i in range(min(5, len(card['options']))):
                buttons.append(card['options'][i])
                
        attachments.append({
            'title': card['title'],
            'subTitle': card['subTitle'],
            'buttons' : buttons
        }) 
        
    return {
        'contentType': 'application/vnd.amazonaws.card.generic',
        'version': 1,
        'genericAttachments': attachments
    }


def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


""" --- Helper Functions --- """

def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot,
        }

    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content }
    }
    
def try_ex(func):
    """
    Call passed in function in try block. If KeyError is encountered return None.
    This function is intended to be used to safely access dictionary.

    Note that this function would have negative impact on performance.
    """

    try:
        return func()
    except KeyError:
        return None
