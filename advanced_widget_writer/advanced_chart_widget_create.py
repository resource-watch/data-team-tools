import os
import json
import requests

# load the API token
API_TOKEN = os.getenv('RW_API_KEY')

# input dataset API ID of which you want to create/edit widget 
dataset_id = ''

# the headers for all requests in this script 
headers = {'Authorization': 'Bearer ' + API_TOKEN, 'Content-Type': 'application/json'}

# name of the widget
name = ''

# description of the widget 
description = ''

# replace the empty dictionary with the code from the vega editor
# replace true with True, false with False, and null with None
# note: you ONLY have to replace values that are NOT strings (inside quotation marks),
# e.g. you should replace null with None, but do not replace "null" - keep all strings as they are
vega = {}

# create payload to send to API
# you must edit the interaction_config
widget_payload = {
    "name": name,
    "description": description,
    "widgetConfig": {
        "schema": "https://vega.github.io/schema/vega/v5.json",
        **vega
      },
    "env": 'production',
    "application": ['rw']
    }

# send the request to create widget to the API 
try:
    url = f'https://api.resourcewatch.org/v1/dataset/{dataset_id}/widget'
    r = requests.post(url, data=json.dumps(widget_payload), headers=headers)
    widget_id = r.json()['data']['id']
except:
    print('Failed to create a widget')
    print('Response from API request: {}'.format(r.content))
else:
    print('API id for the advanced widget created is {}'.format(widget_id))
# check the backoffice before proceeding
# it may still 404 even if response from the API looks good