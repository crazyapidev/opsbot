# -*- coding: utf-8 -*-
"""
Created on Fri Jul 07 10:10:39 2017

@author: 160229
"""
from __future__ import print_function

import re
import json
import logging
from elasticsearch import Elasticsearch 

from helper import get_slots, build_response_card, close, elicit_intent_with_response_card,elicit_slot_with_text_message
from runbook import getRunbookById
from runlog import getLastRunlogEntry, getLastRunlogEntryById, getRunbookIdForRunlog, save, Runlog
from slack import getSlackUserById

headers = {'content-type': 'application/json'}
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

with open('.context', 'r') as f:
    env = json.loads(f.read())

es_host = env['es_host']
es_port = env['es_port']

es = Elasticsearch(hosts=[{'host': es_host, 'port': int(es_port)}])

class ExecutionContext:
    def __init__(self, runlog_id, user):
        self.runlogId=runlog_id
        self.user=user
        runbook_id=getRunbookIdForRunlog(self.runlogId, self.user)
        print('ExecutionContext::getRunbook runbook_id={}'.format(str(runbook_id)))
        self.runbook=getRunbookById(runbook_id)
        print('ExecutionContext::getRunbook runbook_id={}, runbook={}'.format(str(runbook_id), str(self.runbook)))
      
    def getLastRunlogEntry(self):
        return getLastRunlogEntryById(self.runlogId) 
        
    def getRunbook(self):
        return self.runbook

    def getLastTaskLogEntry(self):
        return getLastRunlogEntry(self.runlogId, 'TASK', self.user)
                
    def getNextStepAndTask(self):
        current_task=self.getLastTaskLogEntry()
        print('ExecutionContext::getNextStepAndTask log_entry={}'.format(str(current_task)))

        if current_task is None: # first task
            print('ExecutionContext::getNextStepAndTask first task, step={}'.format(str(self.runbook['steps'][0])))
            return (0, 0, self.runbook['steps'][0])
        
        current_task_index=-1
        current_step_index=-1            
        for step_index in range(0, len(self.runbook['steps'])-1):
            step=self.runbook['steps'][step_index]
            for task_index in range(0,len(step['tasks'])-1):
                if current_task['name']==step['tasks'][task_index]:
                    current_task_index=task_index
                    current_step_index=step_index
                    print('ExecutionContext::getNextStepAndTask current step={}, step_index={}, current task={}, task_index={}'.format(str(self.runbook['steps'][current_step_index]), current_step_index,
                          str(self.runbook['steps'][current_step_index]['tasks'][current_task_index]), current_task_index))
                    break                    

        if current_task['status']=='START':
            if current_task_index < len(self.runbook['steps'][current_step_index])-1: # next task in step                
                print('ExecutionContext::getNextStepAndTask CURRENT_FINISH step={}, step_index={}, current task={}, task_index={}'.format(str(self.runbook['steps'][current_step_index]), current_step_index,
                      str(self.runbook['steps'][current_step_index]['tasks'][current_task_index]), current_task_index))                
                save(Runlog.finish(self.runlogId, current_task['id'], current_task['name'], current_task['level'], self.user, current_task['originator'], current_task['message']))

                print('ExecutionContext::getNextStepAndTask NEXT_TASK step={}, step_index={}, current task={}, task_index={}'.format(str(self.runbook['steps'][current_step_index]), current_step_index,
                      str(self.runbook['steps'][current_step_index]['tasks'][current_task_index+1]), current_task_index+1))                                
                return (current_step_index, current_task_index+1, self.runbook['steps'][current_step_index])

            elif current_step_index+1 <= len(self.runbook['steps'])-1: # next step in runbook
                print('ExecutionContext::getNextStepAndTask CURRENT_FINISH step={}, step_index={}, current task={}, task_index={}'.format(str(self.runbook['steps'][current_step_index]), current_step_index,
                      str(self.runbook['steps'][current_step_index].tasks[current_task_index]), current_task_index))                
                save(Runlog.finish(self.runlogId, current_task['id'], current_task['name'], current_task['level'], self.user, current_task['originator'], current_task['message']))

                print('ExecutionContext::getNextStepAndTask NEXT_STEP step={}, step_index={}, current task={}, task_index={}'.format(str(self.runbook['steps'][current_step_index+1]), current_step_index+1,
                      str(self.runbook['steps'][current_step_index]['tasks'][0]), 0))                                
                return (current_step_index+1, 0, self.runbook['steps'][current_step_index+1])

            else: # last task in runbook
                print('ExecutionContext::getNextStepAndTask CURRENT_FINISH step={}, step_index={}, current task={}, task_index={}'.format(str(self.runbook['steps'][current_step_index]), current_step_index,
                      str(self.runbook['steps'][current_step_index]['tasks'][current_task_index]), current_task_index))                
                save(Runlog.finish(self.runlogId, current_task['id'], current_task['name'], current_task['level'], self.user, current_task['originator'], current_task['message']))
                print('ExecutionContext::getNextStepAndTask LAST_STEP_TASK')                                
                return (-1, -1, None)
        else: # continue where you left off
            print('ExecutionContext::getNextStepAndTask CONTINUE_FROM_LAST step={}, step_index={}, current task={}, task_index={}'.format(str(self.runbook['steps'][current_step_index]), current_step_index,
                  str(self.runbook['steps'][current_step_index]['tasks'][current_task_index]), current_task_index))                
            return (current_step_index, current_task_index, self.runbook['steps'][current_step_index])
            


""" --- Functions that control the bot's behavior --- """
def respond(intent_request):
    """
    Performs dialog management for executing runlog
    """
    current_user = getSlackUserById(intent_request['userId'])
    source = intent_request['invocationSource']
    userInput = intent_request['inputTranscript']
    intent = intent_request['currentIntent']['name'] 
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
        
    isDone=re.match('(?i)DONE', userInput)
    intent_request['currentIntent']['slots']['IsDone']=isDone
    
    if source == 'DialogCodeHook':
        print('respond intentName={}, slots={}'.format(str(intent_request['currentIntent']['name']), str(get_slots(intent_request))))
        slots = get_slots(intent_request)
            
        if not runlog_id:
            print('respond elicit-slot session={}, invalid slot={}'.format(str(output_session_attributes),'RunlogId'))
            return elicit_slot_with_text_message(output_session_attributes, intent, slots, 'RunlogId', 'Invalid RunlogID, please provide a valid RunlogID')
            
        exec_context = ExecutionContext(runlog_id, current_user)
        runbook = exec_context.getRunbook()
        step_index, task_index, step = exec_context.getNextStepAndTask()

        if step is not None:
            #build response card to display step and task information
            buttons = [ {"text":"Done","value":"execute "+runlog_id },  {"text":"Raise Issue","value":"raise error "+runlog_id } ]
            response_card = build_response_card(runbook['name'] + ': Step '+str((step_index+1)) +' of '+str(len(runbook['steps'])), ' Task '+str(task_index+1), buttons)
            print('response elicit_intent_with_response_card = {}'.format(str(response_card)))
            
            runlog_entry = Runlog.start(runlog_id, runbook['steps'][step_index]['id'], runbook['steps'][step_index]['tasks'][task_index], 'TASK', current_user, current_user)
            save(runlog_entry)
            print('respond save runlog={}'.format(str(runlog_entry)))
            output_session_attributes['runlog']=json.dumps(runlog_entry.__dict__)
            print('respond output_session_attributes={}'.format(str(output_session_attributes)))
            
            task_text=runbook['steps'][step_index]['tasks'][task_index]
            return elicit_intent_with_response_card(output_session_attributes, task_text, response_card)
    
    return close(output_session_attributes, 'Fulfilled', {'contentType': 'PlainText', 'content': 'You have completed this task.'})
                  
""" --- Intents --- """
def dispatch(intent_request):
    print('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))
    return respond(intent_request)


""" --- Main handler --- """
def lambda_handler(event, context):
    print('event.bot.name={}, request={}'.format(event['bot']['name'], str(event)))
    return dispatch(event)
    