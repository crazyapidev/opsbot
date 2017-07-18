import dateutil.parser
import time
import os
import logging

from urlparse import parse_qs
from helper import *

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

""" --- Functions that control the bot's behavior --- """

def help(intent_request):

        help_topics = get_slots(intent_request)["HelpTopics"]
        runbook_actions = get_slots(intent_request)["Runbook_Actions"]
        execute_actions = get_slots(intent_request)['Execute_Actions']
        
        source = intent_request['invocationSource']    
        intent = intent_request['currentIntent']['name']
        output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
        
        if source == 'DialogCodeHook':
                slots = get_slots(intent_request)
                
                if not help_topics:
                        buttons = [ {"text":"Find Runbook","value": "search-runbook"}, {"text":"My Runbooks","value": "my-runbooks"}]
                        response_card = build_response_card('Bot Tour','Step 1: Search / List Runbooks', buttons)
                        print('respond elicit-slot response_card={}, invalid slot={}'.format(str(response_card),str(validation_result['violatedSlot'])))
                        return elicit_slot_with_response_card(output_session_attributes,
                                                               intent,
                                                               slots,
                                                               'HelpTopics',
                                                               '''Start the help tour either by searching for a runbook (Find Runbook) or
                                                                by listing runbooks that have been assigned to you (My Runbooks).
                                                                # Find Runbook
                                                                You can use runbook bot to search for information and tutorials with detailed steps regarding AWS products and services.
                                                                Just click on/specify valid AWS product name on being prompted and you get a list of runbook options to choose from.
                                                                # My Runbooks
                                                                You can use runbook bot to list all the runbooks assigned to you. It does this by fetching runbook results from the 
                                                                runlogs which have your name as recipient.
                                                                Please select one for further details
                                                                ''',
                                                               response_card)

                if help_topics=='search-runbook' and not runbook_actions:
                        buttons = [ {"text":"View","value": "view"}, {"text":"Assign","value": "assign"} , {"text":"Execute","value":"execute"}]
                        response_card = build_response_card('Bot Tour','Search/List > Step 2 : Select Runbook action', buttons)
                        print('respond elicit-slot response_card={}, invalid slot={}'.format(str(response_card),str(validation_result['violatedSlot'])))
                        return elicit_slot_with_response_card(output_session_attributes,
                               intent,
                               slots,
                               'Runbook_Actions',
                               '''
                                After selecting a runbook in Step 1, you get further options as to what next course of action you would like to take for the selected runbook. 
                                # View
                                The view action response shows the step by step tasks entailed in the selected runbook for a  particular product type
                                # Assign
                                The assign action response assigns the selected runbook to a slackuser team member you specify as @<username> after being prompted. A runlog is then 
                                automatically generated with fields such as originator,recipient, runbook id, name ,date and time, status'
                                # Execute
                                The execute action starts execution of a selected runbook. Each step in the runbook would be shown with its description alongwith options to 
                                mark the step as complete, to pause execution or raise an issue encountered during the step execution. A new runlog would be generated and the selected 
                                option would also be automatically updated in the status field of runlogs.
                                Please select one for more details''',
                               response_card)
                                                           
                if runbook_actions=='view':
                        return close(output_session_attributes, 'Fulfilled',
                                     {'contentType': 'PlainText',
                                      'content': '''*The following is an example of how selected runbook information is displayed*
                                                    # Step 1: <tasks in step 1>
                                                    # Step 2: <tasks in step 2>
                                                    and so on'''})
                                  
                if runbook_actions=='assign':
                        return close(output_session_attributes, 'Fulfilled',
                                     {'contentType': 'PlainText',
                                      'content': ''' The assignee name has to be specified as "@username" for the selected runbook. An example of generated runlog is shown below:'''})

                if runbook_actions=='execute' and not execute_actions:
                        buttons = [ {"text":"complete","value": "complete"}, {"text":"raise error","value":"raise-error"}]
                        response_card = build_response_card('Bot Tour','Search/List > Step 3 : Select Execution action', buttons)
                        print('respond elicit-slot response_card={}, invalid slot={}'.format(str(response_card),str(validation_result['violatedSlot'])))
                        return elicit_slot_with_response_card(output_session_attributes,intent,slots,'Execute_Actions',
                               ''' 
                               This is an example of how steps are shown during execution:
                               *Step 1*
                               _step description_
                               This is followed by the below response cards.
                               # Complete
                               On selecting complete, the particular step would be marked as complete and reflected so in the runlog
                               # Raise error
                               On selecting raise error when you are unable to execute a particular step, it would be reflected so in the runlog and hence used to troubleshoot the error
                               Please select any option for more details''',
                               response_card)
                                                           
                
                if help_topics=='my-runbooks' and not runbook_actions:
                        buttons = [ {"text":"view","value": "view"}, {"text":"assign to","value": "assign to"} , {"text":"execute","value":"execute"}]
                        response_card = build_response_card('List of Runbooks','Runbooks Assigned to you', buttons)
                        print('respond elicit-slot response_card={}, invalid slot={}'.format(str(response_card),str(validation_result['violatedSlot'])))
                        return elicit_slot_with_response_card(output_session_attributes,
                               intent,
                               slots,
                               'Runbook_Actions',
                               '''
                               The list of runbooks assigned to you are displayed in rows in descending order of time of assignment. On selecting one, you get further options as to 
                               what next course of action you would like to take for the selected runbook. 
                               # View
                               The view action response shows the step by step tasks entailed in the selected runbook for a  particular product type
                               # Assign
                               The assign action response assigns the selected runbook to a slackuser team member you specify as @<username> after being prompted. A runlog is then 
                               automatically generated with fields such as originator,recipient, runbook id, name ,date and time, status'
                               # Execute
                               The execute action starts execution of a selected runbook. Each step in the runbook would be shown with its description alongwith options to 
                               mark the step as complete, to pause execution or raise an issue encountered during the step execution. A new runlog would be generated and the selected 
                               option would also be automatically updated in the status field of runlogs.
                               Please select one for more details''',
                               response_card)
							   
				if runbook_actions=='view':
                        return close(output_session_attributes, 'Fulfilled',
                                     {'contentType': 'PlainText',
                                      'content': '''*The following is an example of how selected runbook information is displayed*
                                                    # Step 1: <tasks in step 1>
                                                    # Step 2: <tasks in step 2>
                                                    and so on'''})
                                  
                if runbook_actions=='assign':
                        return close(output_session_attributes, 'Fulfilled',
                                     {'contentType': 'PlainText',
                                      'content': ''' The assignee name has to be specified as "@username" for the selected runbook. An example of generated runlog is shown below:'''})

                if runbook_actions=='execute' and not execute_actions:
                        buttons = [ {"text":"complete","value": "complete"}, {"text":"raise error","value":"raise-error"}]
                        response_card = build_response_card('Bot Tour','Search/List > Step 3 : Select Execution action', buttons)
                        print('respond elicit-slot response_card={}, invalid slot={}'.format(str(response_card),str(validation_result['violatedSlot'])))
                        return elicit_slot_with_response_card(output_session_attributes,intent,slots,'Execute_Actions',
                               ''' 
                               This is an example of how steps are shown during execution:
                               *Step 1*
                               _step description_
                               This is followed by the below response cards.
                               # Complete
                               On selecting complete, the particular step would be marked as complete and reflected so in the runlog
                               # Raise error
                               On selecting raise error when you are unable to execute a particular step, it would be reflected so in the runlog and hence used to troubleshoot the error
                               Please select any option for more details''',
                               response_card)
                        

""" --- Intents --- """


def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """
    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))
    return help(intent_request)


""" --- Main handler --- """


def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    logger.debug('lambda_handler event.bot.name={}'.format(event['bot']['name']))
        
    return dispatch(event)
