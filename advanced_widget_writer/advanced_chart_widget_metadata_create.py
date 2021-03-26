import os
import requests

# load the API token
API_TOKEN = os.getenv('RW_API_KEY')

# input dataset API ID of which you want to create/edit widget 
dataset_id = ''

# the headers for all requests in this script 
headers = {'Authorization': 'Bearer ' + API_TOKEN, 'Content-Type': 'application/json'}

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