import LMIPy as lmi
import json
import requests
import dotenv

# input widget API ID for the empty advanced widget you have created and want to overwrite
dataset_id = ''
widget_to_overwrite = ''

# replace the empty dictionary with the code from the vega editor
# replace true with True and null with None
vega = {}

# create payload to send to API
# you must edit the interaction_config
payload = {
    "widgetConfig": {
        "schema": "https://vega.github.io/schema/vega/v5.json",
        **vega,
        "interaction_config": [
          {
            "config": {
                "fields": [
                    {
                        "format": ".2s",
                        "type": "number",
                        "property": "Global Reefs Experiencing Bleaching (%)",
                        "column": "bleaching_percentage"
                    },
                    {
                        "format": ".2f",
                        "type": "number",
                        "property": "Decade",
                        "column": "decade_start"
                    }
                ]
            },
            "name": "tooltip"
          }
        ],
      }
    }

# load in API credentials
API_TOKEN = os.getenv('RW_API_KEY')
headers = {
'Content-Type': 'application/json',
'Authorization': 'Bearer '+API_TOKEN, 
}

# load the widget we are going to overwrite
# option 1: LMIPY
#widget = lmi.Widget(widget_to_overwrite)
# option 2: requests
url = f'http://api.resourcewatch.org/v1/dataset/{dataset_id}/widget/{widget_to_overwrite}'

# Update the widget
# option 1: LMIPY
#widget = widget.update(update_params=payload, token=API_TOKEN)
# option 2: requests
r = requests.patch(url = url, json = payload, headers = headers)
print(r)