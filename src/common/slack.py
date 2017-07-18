# -*- coding: utf-8 -*-
"""
Created on Sun Jul 09 20:38:43 2017

@author: 160229
"""
import requests

with open('.context', 'r') as f:
    env = json.loads(f.read())

token = env['slack_token']
#token='xoxp-188678725313-190051123590-213129018897-8e3bf46ee5cb72ab040c9a88a10c2b13'
#token='xoxp-211753204212-211803581285-214269624194-9cf329ca2b79658def2cf8711d90b0d2'

def getIdForSlackUser(user):
    response = requests.get('https://slack.com/api/users.list?token='+token)

    if response and response.json()['ok']:
        for member in response.json()['members']:
            if user[1:]==member['name']:
                return member['id']
    return None
	
def getSlackUserById(slackId):
    if slackId and len(slackId.split(':'))>0:
        slackId=slackId.split(':')[-1] # apparently the last token is the slackid
    
    payload = {'token': token, 'user': slackId}
    response = requests.post('https://slack.com/api/users.info', data=payload)

    if response and response.json()['ok']:
        return '@'+response.json()['user']['name']
    return None
    
    
if __name__=="__main__":
    print(getSlackUserById('U5L1H3MHC'))
    print(getIdForSlackUser('@praveen.koduganty'))