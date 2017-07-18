# -*- coding: utf-8 -*-
"""
Created on Fri Jul 07 10:10:39 2017

@author: 160229
"""
from __future__ import print_function

import re
import json
import logging

from helper import get_slots, delegate, close, elicit_slot_with_response_card, build_multiple_response_cards,build_response_card
from runlog import getLastRunlogEntry, Runlog, save, getResolution
from slack import getSlackUserById

headers = {'content-type': 'application/json'}
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

class Issue:
    def __init__(self, issue_type, severity, environment, issue, description):
        self.type=issue_type
        self.severity=severity
        self.environment=environment
        self.issue=issue
        self.description=description


""" --- Functions that control the bot's behavior --- """
def respond(intent_request):
    """
    Raises issue encountered while executing the runbook
    
    """
    intent = intent_request['currentIntent']['name']    
    current_user = getSlackUserById(intent_request['userId'])
    userInput = intent_request['inputTranscript']
    source = intent_request['invocationSource']    
    output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    
    #get runlog_id from user input or session or from slot
    runlog_id = get_slots(intent_request)["RunlogId"] if 'RunlogId' in get_slots(intent_request) else None
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
    
    issue_type = get_slots(intent_request)["IssueType"] if 'IssueType' in get_slots(intent_request) else None
    severity = get_slots(intent_request)["Severity"] if 'Severity' in get_slots(intent_request) else None
    environment = get_slots(intent_request)["Environment"] if 'Environment' in get_slots(intent_request) else None
    summary = get_slots(intent_request)["Summary"] if 'Summary' in get_slots(intent_request) else None
    description = get_slots(intent_request)["Description"] if 'Description' in get_slots(intent_request) else None
    
    resolution_id =get_slots(intent_request)["ResolutionId"]  if 'ResolutionId' in get_slots(intent_request) else None
    confirm_resolution = get_slots(intent_request)["ConfirmResolution"] if 'ConfirmResolution' in get_slots(intent_request) else None
    confirm_assign = get_slots(intent_request)["ConfirmAssign"] if 'ConfirmAssign' in get_slots(intent_request) else None
    
    assignee = get_slots(intent_request)["SlackUser"] if 'SlackUser' in get_slots(intent_request) else None
    if assignee is None and re.search('@\w+', userInput) is not None:
        #check if user has specified @user in utterance
        assignee=re.search('@\w+', userInput).group(0)
        intent_request['currentIntent']['slots']["SlackUser"]=assignee
       
    if source == 'DialogCodeHook':
        slots = get_slots(intent_request)        

        if issue_type and severity and environment and summary and description:
            last_task_entry = getLastRunlogEntry(runlog_id, 'TASK', current_user)
            runlog_entry = Runlog.raise_error(runlog_id, last_task_entry['id'], last_task_entry['name'], 'TASK', current_user, last_task_entry['originator'], summary, 
                                             None, json.dumps(Issue(issue_type, severity, environment, summary, description).__dict__))
            save(runlog_entry)
            print('respond save runlog={}'.format(str(runlog_entry)))
            output_session_attributes['runlog']=json.dumps(runlog_entry.__dict__)
            
        resolution_list = getResolution(runlog_id)
        
        if not resolution_id: 
                attachments=[]
                for resolution in resolution_list:                    
                    buttons = [ {"text":"Select "+resolution['id'], "value":resolution['id']} ]
                    response_card = { 'title': (resolution['source']), 'subTitle' :resolution['resolution'][:75]+"...", 'options': buttons }
                    attachments.insert(0, response_card)
                
                response_cards=build_multiple_response_cards(attachments)
                return elicit_slot_with_response_card(output_session_attributes,
                               intent,
                               slots,
                               'ResolutionId',
                               'Please select from below list',
                               response_cards)        
        
        resolution = [item for item in resolution_list if resolution_id == item['id']][0] #TODO
                                   
        if not confirm_resolution:
            buttons = [{"text":"yes","value":"yes"},{"text":"no","value":"no"}]
            response_card = build_response_card('Details','Resolution available',buttons)
            return elicit_slot_with_response_card(output_session_attributes,
                               intent,
                               slots,
                               'ConfirmResolution',
                               resolution['resolution']+'\n Did this resolve the issue?',response_card)
                               
        if confirm_resolution=="yes" and resolution['source'] == "stackoverflow":
            runlog_entry = Runlog.resolve(runlog_id, last_task_entry.id, last_task_entry.name, 'TASK', current_user, last_task_entry.originator, 'Resolution found for issue :\n'+summary, 
                                              None,json.dumps(Issue(issue_type, severity, environment, summary, description)),last_task_entry.resolutionCount)
            save(runlog_entry)
            print('respond save runlog={}'.format(str(runlog_entry)))
            output_session_attributes['runlog']=json.dumps(runlog_entry.__dict__)
            
        if confirm_resolution=="yes" and resolution['source'] == "runlog":
            runlog_entry = Runlog.resolve(runlog_id, last_task_entry.id, last_task_entry.name, 'TASK', current_user, last_task_entry.originator, summary, 
                                              None,json.dumps(Issue(issue_type, severity, environment, summary, description)),last_task_entry.resolutionCount+1)
            save(runlog_entry)
            print('respond save runlog={}'.format(str(runlog_entry)))
            output_session_attributes['runlog']=json.dumps(runlog_entry.__dict__)
            
        if confirm_resolution=="no" and not confirm_assign:
            buttons = [{"text":"yes","value":"yes"},{"text":"no","value":"no"}]
            response_card = build_response_card('Delegate issue to user','Choose one',buttons)
            return elicit_slot_with_response_card(output_session_attributes,
                               intent,
                               slots,
                               'ConfirmAssign',
                               'Do you want to delegate this issue to someone?',response_card)
                               
        if assignee is not None and confirm_assign=="yes":
            runlog_entry = Runlog.assign( runlog_id, last_task_entry.id, last_task_entry.name,  last_task_entry.originator, assignee)
            save(runlog_entry)
            print('respond save runlog={}'.format(str(runlog_entry)))
            output_session_attributes['runlog']=json.dumps(runlog_entry.__dict__)
        
        # TODO add functionality when user doesn't want to assign issue
        if confirm_assign =="no":                        
            return delegate(output_session_attributes, get_slots(intent_request))
        
    print('respond close session={}'.format(str(output_session_attributes)))
    return close(output_session_attributes, 'Fulfilled', {'contentType': 'PlainText', 'content': 'Noted your issue'})
    
""" --- Intents --- """
def dispatch(intent_request):
    print('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))
    return respond(intent_request)


""" --- Main handler --- """
def lambda_handler(event, context):
    print('event.bot.name={}'.format(event['bot']['name']))
    return dispatch(event)
    