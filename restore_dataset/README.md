**Restore Resource Watch Dataset**

This folder contains a Python script to restore a deleted Resource Watch dataset from a json backup of its RW API data.

Folder contents:
1. **restore_dataset_from_json.py**: This Python script allows you to create a new version of a dataset and it's layers using the json back up it's API data.

You will find instuctions on how to run the code within the script. This script requires one json file for the 'minimal' dataset info (no layers), as well as a folder containing all of the layer jsons.