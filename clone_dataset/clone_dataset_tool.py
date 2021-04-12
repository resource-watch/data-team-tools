'''
After cloning each dataset, you will need to update certain fields for this dataset in the back office.
You will have to fix these fields manually:
        Edit Dataset: Layer Sorting
        Layers: default layer
        Widgets: default editable widget

NOTES:
-If a dataset cloning fails:
    Find the partially cloned dataset it the back office, delete it and run this whole script again.
'''

import LMIPy
import os
import json
import requests
import time


# INPUTS
# enter dataset id of dataset to duplicate here
dataset_id = '' # ex: '79e06dd8-a2ae-45eb-8e99-e73bc87ec946'

# what do you want to name the new dataset in the back office?
# this should be different than the original dataset name
# remember that this name is what makes the url slug for the dataset!
new_dataset_name = '' # ex: cli.051a Projected Minimum Temperature Ensemble (RCP 8.5)

# do you want to replace the connector url with a new one?
# Should be one of the format:
#   1)https://{carto_account}.carto.com/tables/{table_name}/public
#   2)full asset/collection name on GEE (ex: users/resourcewatch_wri/cit_035_tropomi_atmospheric_chemistry_model_30day_avg/O3)
# If it is left blank, the new dataset will use the same connectorUrl as the original dataset
new_dataset_connectorUrl = ''

# do you want to clone only the first layer or all of the layers?
clone_first_layer_only = False

# do you want to clone only the default editable widget or all the widgets?
clone_default_widget_only = True



API_TOKEN = os.getenv('RW_API_KEY')

def create_headers():
    return {
        'content-type': "application/json",
        'authorization': "{}".format(os.getenv('apiToken')),
    }

def clone_ds(self, token=None, enviro='preproduction', clone_server=None, dataset_params=None, clone_children=True, clone_first_layer_only=True, clone_default_widget_only=True, published = False):
    """
    Create a clone of a target Dataset as a new staging or prod Dataset.
    A set of attributes can be specified for the clone Dataset. 
    The argument `clone_server` specifies the server to clone to. Default server = https://api.resourcewatch.org
    Set clone_children=True to clone all child layers, and widgets.
    Set published=True to publish the layer.
    """
    if not clone_server: clone_server = self.server
    if not token:
        raise ValueError(f'[token] Resource Watch API token required to clone.')
    else:
        name = dataset_params.get('name', self.attributes['name'] + 'CLONE')
        clone_dataset_attr = {**self.attributes, 'name': name}
        for k, v in clone_dataset_attr.items():
            if k in dataset_params:
                clone_dataset_attr[k] = dataset_params.get(k, '')
        payload = {
            'dataset': {
                'application': ['rw'],
                'connectorType': clone_dataset_attr['connectorType'],
                'connectorUrl': clone_dataset_attr['connectorUrl'],
                'tableName': clone_dataset_attr['tableName'],
                'provider': clone_dataset_attr['provider'],
                'published': published,
                'env': enviro,
                'name': clone_dataset_attr['name'],
                'widgetRelevantProps': clone_dataset_attr['widgetRelevantProps'],
                'geoInfo': clone_dataset_attr['geoInfo'],
                'layerRelevantProps': clone_dataset_attr['layerRelevantProps'],
                'type': clone_dataset_attr['type']
            }
        }
        if 'applicationConfig' in clone_dataset_attr:
            payload['dataset'].update({'applicationConfig': clone_dataset_attr['applicationConfig']})
        if 'subscribable' in clone_dataset_attr:
            payload['dataset'].update({'subscribable': clone_dataset_attr['subscribable']})
        if new_dataset_connectorUrl:
            if 'carto' in new_dataset_connectorUrl:
                payload['dataset'].update({'connectorUrl': new_dataset_connectorUrl})
                payload['dataset'].update({'tableName': new_dataset_connectorUrl.split('/')[-2]})
            else:
                payload['dataset'].update({'tableName': new_dataset_connectorUrl})
        print(f'Creating clone dataset')
        url = f'{clone_server}/dataset'
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json', 'Cache-Control': 'no-cache'}
        r = requests.post(url, data=json.dumps(payload), headers=headers)
        if r.status_code == 200:
            clone_dataset_id = r.json()['data']['id']
            clone_dataset = LMIPy.Dataset(id_hash=clone_dataset_id, server=clone_server)
        else:
            print(r.status_code)
        print(f'{clone_server}/v1/dataset/{clone_dataset_id}')
        if clone_children:
            layers = self.layers
            if len(layers) > 0:
                if clone_first_layer_only:
                    l = layers[0]
                    if l.attributes['application'] == ['rw']:
                        try:
                            layer_name = l.attributes['name']
                            print('Cloning layer: {}'.format(layer_name))
                            l.clone(token=token, env='production', layer_params={'name': layer_name},
                                    target_dataset_id=clone_dataset_id)
                            time.sleep(2)
                        except:
                            raise ValueError(f'Layer cloning failed for {l.id}')
                else:
                    for l in layers:
                        if l.attributes['application']==['rw']:
                            try:
                                layer_name = l.attributes['name']
                                print('Cloning layer: {}'.format(layer_name))
                                l.clone(token=token, env='production', layer_params={'name': layer_name}, target_dataset_id=clone_dataset_id)
                                time.sleep(2)
                            except:
                                raise ValueError(f'Layer cloning failed for {l.id}')
            else:
                print("No child layers to clone!")
            #clone widgets
            try:
                url = f'{self.server}/v1/dataset/{self.id}?includes=vocabulary,metadata,layer,widget'
                r = requests.get(url)
                widgets = r.json()['data']['attributes']['widget']
            except:
                print("Could not retrieve widgets.")
            if len(widgets) > 0:
                if clone_default_widget_only:
                    for w in widgets:
                        widget = w['attributes']
                        if widget['defaultEditableWidget']:
                            try:
                                name = widget['name'],
                                widget_config = widget['widgetConfig'],
                                app = widget['application']
                                ds_id = clone_dataset_id
                                if app == ['rw']:
                                    if name and widget_config and app:
                                        widget_payload = {
                                            "name": widget['name'],
                                            "description": widget.get('description', None),
                                            "env": widget['env'],
                                            "widgetConfig": widget['widgetConfig'],
                                            "application": ['rw']
                                        }
                                        try:
                                            url = f'{self.server}/v1/dataset/{ds_id}/widget'
                                            print(url)
                                            headers = {'Authorization': 'Bearer ' + token,
                                                       'Content-Type': 'application/json'}
                                            r = requests.post(url, data=json.dumps(widget_payload), headers=headers)
                                            print(r.json())
                                        except:
                                            raise ValueError(f'Widget creation failed.')
                                        if r.status_code == 200:
                                            print(f'Widget created.')
                                            # self.attributes = self.get_dataset()
                                        else:
                                            print(f'Failed with error code {r.status_code}')
                                    else:
                                        raise ValueError(
                                            f'Widget creation requires name string, application list and a widgetConfig object.')

                                    # clone_dataset.add_widget(token=token, widget_params=widget_payload)
                                else:
                                    print("Non-rw app. Not cloning.")
                            except:
                                raise ValueError(f'Widget cloning failed for {widget.id}')
                else:
                    for w in widgets:
                        widget = w['attributes']
                        try:
                            name = widget['name'],
                            widget_config = widget['widgetConfig'],
                            app = widget['application']
                            ds_id = clone_dataset_id
                            if app==['rw']:
                                if name and widget_config and app:
                                    widget_payload = {
                                        "name": widget['name'],
                                        "description": widget.get('description', None),
                                        "env": widget['env'],
                                        "widgetConfig": widget['widgetConfig'],
                                        "application": ['rw']
                                    }
                                    try:
                                        url = f'{self.server}/v1/dataset/{ds_id}/widget'
                                        print(url)
                                        headers = {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'}
                                        r = requests.post(url, data=json.dumps(widget_payload), headers=headers)
                                        print(r.json())
                                    except:
                                        raise ValueError(f'Widget creation failed.')
                                    if r.status_code == 200:
                                        print(f'Widget created.')
                                        #self.attributes = self.get_dataset()
                                    else:
                                        print(f'Failed with error code {r.status_code}')
                                else:
                                    raise ValueError(
                                        f'Widget creation requires name string, application list and a widgetConfig object.')

                                #clone_dataset.add_widget(token=token, widget_params=widget_payload)
                            else:
                                print("Non-rw app. Not cloning.")
                        except:
                            raise ValueError(f'Widget cloning failed for {widget.id}')
            else:
                print("No child widgets to clone!")
            vocabs = self.vocabulary
            if len(vocabs) > 0:
                for v in vocabs:
                    vocab = v.attributes
                    if vocab['application']=='rw':
                        vocab_payload = {
                            'application': vocab['application'],
                            'name': vocab['name'],
                            'tags': vocab['tags']
                        }
                        try:
                            clone_dataset.add_vocabulary(vocab_params=vocab_payload, token=token)
                        except:
                            raise ValueError('Failed to clone Vocabulary.')
            metas = self.metadata
            if len(metas) > 0:
                for m in metas:
                    meta = m.attributes
                    if meta['application']=='rw':
                        meta_payload = {
                            "dataset": meta['dataset'],
                            'application': meta['application'],
                            'language': meta['language'],
                            "name": meta['name'],
                            'description': meta['description'],
                            "source": meta['source'],
                            'info': meta['info'],
                        }
                        if 'columns' in meta:
                            meta_payload.update({'columns': meta['columns']})
                        try:
                            rw_api_url = 'https://api.resourcewatch.org/v1/dataset/{}/metadata'.format(clone_dataset.id)
                            res = requests.request("POST", rw_api_url, data=json.dumps(meta_payload),
                                                   headers=create_headers())
                            print('Metadata created.')
                        except:
                            raise ValueError('Failed to clone Metadata.')
        # self.attributes = Dataset(clone_dataset_id, server=clone_server).attributes
        return clone_dataset_id

# Make a copy
dataset_to_copy = LMIPy.Dataset(dataset_id)
clone_attributes = {
    'name': new_dataset_name
}
# Clone dataset
new_dataset_id = clone_ds(dataset_to_copy, token=API_TOKEN, enviro='production', dataset_params=clone_attributes, clone_children=True, clone_first_layer_only=clone_first_layer_only, clone_default_widget_only=clone_default_widget_only)
print('new dataset API ID:' + new_dataset_id)