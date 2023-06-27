import os
import requests
import json

API_TOKEN = os.getenv('RW_API_KEY')

def create_headers():
    return {
        'content-type': "application/json",
        'authorization': "{}".format(os.getenv('apiToken')),
    }

# Start with a dataset you cloned to make sure everything works
cloned_dataset = ['']
cloned_layer = ['']

# Add your real datasets here. Don't uncomment until you have tested.
datasets = ['', '']

# Choose the field you want to find and replace in, the value to fine, and what to replace it with
dataset_field = 'connectorUrl'
layer_field = 'layerConfig'
find = ''
replace = ''

# Don't actually to anything yet
dry_run = True

# Use test dataset
test_run = True

if test_run:
    datasets = cloned_dataset

# Print out what we are doing
print(f'Replacing "{find}" with "{replace}" in `{dataset_field}`.')


# Loop through datasets to find and replace values
for dataset_id in datasets:
    current_url = f'https://api.resourcewatch.org/v1/dataset/{dataset_id}/?includes=layer'
    print(f'DATASET URL: {current_url}')
    with requests.get(current_url) as r:
        if r.ok:
            ds = json.loads(r.content)
        else:
            raise ValueError(f'API request failed: {current_url}')
    assert 'data' in ds

    name = ds['data']['attributes']['name']
    print(f'DATASET NAME: {name}')

    old_value = ds['data']['attributes'][dataset_field]
    new_value = old_value.replace(find, replace)

    find_count = old_value.count(find)
    replace_count = new_value.count(replace)

    print(f'\nOLD VALUE: {old_value}')
    print(f'\nNEW VALUE: {new_value}')

    print(f'\nStarted with {find_count} instances of "{find}" and ended up with {replace_count} instances of "{replace}".')

    update = json.dumps({dataset_field: new_value})

    if dry_run == False: 
        with requests.patch(current_url, headers=create_headers(), data=update) as r:
            if r.ok:
                print('\nDONE')
            else:
                raise ValueError(f'API request failed: {current_url}')
        assert 'data' in ds
    else:
        print('\nDRY RUN')
    



    # Layers
    layers = [item["id"] for item in ds['data']['attributes']['layer']]
    if test_run:
        layers = cloned_layer

    for layer_id in layers:
        current_url = f'https://api.resourcewatch.org/v1/dataset/{dataset_id}/layer/{layer_id}'
        print(f'LAYER URL: {current_url}')
        with requests.get(current_url) as r:
            if r.ok:
                ly = json.loads(r.content)
            else:
                raise ValueError(f'API request failed: {current_url}')
        assert 'data' in ly

        name = ly['data']['attributes']['name']
        print(f'LAYER NAME: {name}')

        old_value = ly['data']['attributes']['layerConfig']

        #Convert to string and replace
        old_str = json.dumps(old_value)
        find_count = old_str.count(find)

        new_str = old_str.replace(find, replace)
        replace_count = new_str.count(replace)

        #Get obj back with replacement
        new_value = json.loads(new_str)

        print(f'\nOLD VALUE: {old_value}')
        print(f'\nNEW VALUE: {new_value}')

        print(f'\nStarted with {find_count} instances of "{find}" and ended up with {replace_count} instances of "{replace}".')

        update = json.dumps({layer_field: new_value})

        if dry_run == False: 
            with requests.patch(current_url, headers=create_headers(), data=update) as r:
                if r.ok:
                    print('\nDONE')
                else:
                    raise ValueError(f'API request failed: {current_url}')
            assert 'data' in ds
        else:
            print('\nDRY RUN')
