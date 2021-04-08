import os
import json
import requests

# load the API token
API_TOKEN = os.getenv('RW_API_KEY')

# input dataset API ID of which you want to edit widget 
dataset_id = ''

# the headers for all requests in this script 
headers = {'Authorization': 'Bearer ' + API_TOKEN, 'Content-Type': 'application/json'}

# input the API id of the widget you want to edit 
widget_id = ''

# include in the widget payload the fields you would like to edit 
'''
for example: 
    widget_payload = {"description": 'this is for a test'}
'''
widget_payload = {}

# send the request to edit the widget on the API 
try:
    url = f'https://api.resourcewatch.org/v1/dataset/{dataset_id}/widget/{widget_id}'
    r = requests.patch(url, data=json.dumps(widget_payload), headers=headers)
    print(r.json())
except:
    print('Failed to edit a widget')
    print('Response from API request: {}'.format(r.content))