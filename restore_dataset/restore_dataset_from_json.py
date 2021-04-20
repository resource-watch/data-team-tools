import requests
import json
import LMIPy
import os

# user input needed
# enter the location of the json file containing your minimal dataset info json (no layers)
dataset_json_data_loc = '' # ex: /home/data/aqueduct_rw_api_2021-02-19/aq_floods_minimal_2021-02-19.json
# enter the location of the folder containing your layer json files
layer_json_data_loc = '' # ex: /home/data/aqueduct_rw_api_2021-02-19/layers

# read in the minimal dataset json
dataset_f = open(dataset_json_data_loc)
dataset_json = json.load(dataset_f)
# get list of json files for all the layers
layer_files = os.listdir(layer_json_data_loc)

# import your API token
API_TOKEN = os.getenv('RW_API_KEY')


def create_headers():
    return {
        'content-type': "application/json",
        'authorization': "{}".format(os.getenv('apiToken')),
    }

def clone_ds_ly_from_json(dataset_json, layer_files, token=None, dataset_pub = False, layer_pub = True):
    """
    Create a clone of a target Dataset as a new staging or prod Dataset.
    INPUT   dataset_json: minimal json of dataset info (dictionary)
            layer_files: list of layer json files (list of strings)
            token: RW API token (string)
            dataset_pub: should the dataset be published when it is created (boolean)
            layer_pub: should the layers be published when it is created (boolean)
    """
    clone_server = 'https://api.resourcewatch.org'
    if not token:
        raise ValueError(f'[token] Resource Watch API token required to clone.')
    else:
        ### update dataset
        dataset_json.pop("id", None)
        dataset_json['attributes']['published'] = dataset_pub
        dataset_fields_to_drop = ["createdAt", "updatedAt", "userId"]

        for field in dataset_fields_to_drop:
            dataset_json['attributes'].pop(field, None)

        ### clone dataset
        url = f'{clone_server}/dataset'
        headers = create_headers()
        payload = {
            'dataset': {**dataset_json['attributes']
            }}
        display(json.dumps(payload))
        r = requests.post(url, data=json.dumps(payload), headers=headers)
        if r.status_code == 200:
            clone_dataset_id = r.json()['data']['id']
            clone_dataset = LMIPy.Dataset(id_hash=clone_dataset_id, server=clone_server)
            print('Dataset created:')
            print(r.json()['data']['id'])
        else:
            print(r.status_code)
        
        ### clone layers
        layer_fields_to_drop = ["createdAt", "updatedAt", "userId", "dataset"]
        
        for i in range(len(layer_files)):
            layer_f = open(os.path.join(layer_json_data_loc, layer_files[i]))
            layer_json = json.load(layer_f)
            layer_json.pop("id", None)
            layer_json['attributes']['published'] = layer_pub
            for field in layer_fields_to_drop:
                layer_json['attributes'].pop(field, None)
            url = f'{clone_server}/dataset/{clone_dataset_id}/layer'
            print(url)
            payload = {
            'layer': {**layer_json['attributes']
            }}
            r = requests.post(url, data=json.dumps(payload), headers=headers)
            if r.status_code == 200:
                clone_layer_id = r.json()['data']['id']
                clone_layer = LMIPy.Layer(id_hash=clone_layer_id, server=clone_server)
                print('Layer created:')
                print(r.json()['data']['id'])
            else:
                print(r.status_code)

clone_ds_ly_from_json(dataset_json, layer_files, token=API_TOKEN, dataset_pub=True, layer_pub=True)



# if you accidentally make a dataset incorrectly, you can delete it by 
# entering the dataset id below and running the code that follows
dataset_id = ''
r = requests.delete(f'https://api.resourcewatch.org/dataset/{dataset_id}',
                headers=create_headers())
if r.status_code==200:
    print(f'Dataset {id} has been deleted.')