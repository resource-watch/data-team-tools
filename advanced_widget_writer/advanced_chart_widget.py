import os
import json
import requests

'''
There are four things you can do using this tool:
    1. Create an advanced widget for a dataset
    2. Edit an advanced widget for a dataset
    3. Add metadata to an existing advanced widget 
    4. Edit existing metadata of an advanced widget
'''
# load the API token
API_TOKEN = os.getenv('RW_API_KEY')

# input dataset API ID of which you want to create/edit widget 
dataset_id = ''

# the headers for all requests in this script 
headers = {'Authorization': 'Bearer ' + API_TOKEN, 'Content-Type': 'application/json'}

# OPTION 1: CREATE AN ADVANCED WIDGET FOR A DATASET 

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
        **vega,
        "interaction_config":[{
            "name": "tooltip",
            "config": {
                "fields": [
                    {
                        "column": "y",
                        "property": "Total tCO₂e per Million Kilocalories Consumed",
                        "type": "number",
                        "format": ".2s"
                        },
                    {
                        "column": "x",
                        "property": "Food Type",
                        "type": "string",
                        "format": ".2f"
                        }
                    ]
                }
            }],
        "we_meta": {
            "core": "2.5.5",
            "editor": "2.5.5",
            "renderer": "2.5.5",
            "adapter": "rw-adapter",
            "advanced": True
            }
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

# OPTION 2: EDIT AN EXISTING ADVANCED WIDGET 

# input the API id of the widget you want to edit 
widget_id = ''

# include in the widget payload the fields you would like to edit 
'''
for example: 
    widget_payload = {"description": 'this is for a test'}
'''
widget_payload = {}

# send the request to create widget to the API 
try:
    url = f'https://api.resourcewatch.org/v1/dataset/{dataset_id}/widget/{widget_id}'
    r = requests.patch(url, data=json.dumps(widget_payload), headers=headers)
    print(r.json())
except:
    print('Failed to edit a widget')
    print('Response from API request: {}'.format(r.content))


# OPTION 3: ADD METADATA to AN EXISTING ADVANCED WIDGET

# input the id of the widget you would like to add metadata to
widget_id = ''

# input the caption you want to include in the metadata 
caption = ''

# input the widget links you want to include in the metadata 
widget_links = [{
    "link": "",
    "name": ""
    }]

# create the payload for a request to the API 
metadata_payload = {
    "application": "rw",
    "env": 'production',
    "language": "en",
    "info": {
        "caption": caption,
        "widgetLinks": widget_links
        }
    }

# construct the url for the request 
url = f'http://api.resourcewatch.org/v1/dataset/{dataset_id}/widget/{widget_id}/metadata'
# send it to the API 
r = requests.post(url = url, json = metadata_payload, headers = headers)
print(r.content)

# OPTION 4: EDIT EXISTING METADATA OF AN ADVANCED WIDGET

# input the id of the widget you would like to edit metadata of
widget_id = ''

# include in the payload fields you would like to update
# note: application and language must be included no matter which fields you want to edit
'''
for example: 
    metadata_payload = {
    "application": "rw",
    "language": "en",
    "info": {
        "caption": 'oh no',
        "widgetLinks": [
            {
                "link": "https://coralreefwatch.noaa.gov/climate/projections/piccc_oa_and_bleaching/index.php",
                "name": "Projections of Coral Bleaching and Ocean Acidification for Coral Reef Areas on Coral Reef Watch"
                },
            {
                "link": "https://onlinelibrary.wiley.com/doi/abs/10.1111/gcb.12394",
                "name": "\"Opposite latitudinal gradients in projected ocean acidification and bleaching impacts on coral reefs\" in Global Change Biology"
                }
            ]
        }
    }
'''
metadata_payload = {
    "application": "rw",
    "language": "en"
    }

# construct the url for the request 
url = f'http://api.resourcewatch.org/v1/dataset/{dataset_id}/widget/{widget_id}/metadata'
# send it to the API 
r = requests.patch(url = url, json = metadata_payload, headers = headers)
print(r.content)