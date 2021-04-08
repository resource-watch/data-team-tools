import os
import requests

# load the API token
API_TOKEN = os.getenv('RW_API_KEY')

# input dataset API ID of which you want to create/edit widget 
dataset_id = ''

# the headers for all requests in this script 
headers = {'Authorization': 'Bearer ' + API_TOKEN, 'Content-Type': 'application/json'}

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