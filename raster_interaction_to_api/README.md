**Pushing raster interactions to the API**

All of the interactions for raster layers on Resource Watch are generated from metadata stored in an internally shared Google sheet ("Raster Interaction Metadata"). Each time we add a new raster layer on Resource Watch, we need to fill out the Raster Interaction Metadata sheet. This folder contains a Python script that converts this metadata into the proper format for a raster interaction and then pushes this interaction to the indicated layer to the API.

Each time you add a new raster layer that needs interaction or want to make changes to an existing raster interaction, you must fill out the Raster Interaction Metadata sheet and run this script. This will make the interaction appear on Resource Watch. 

To run this script on your computer: 
  1. This script is run in a Docker container. Before you can run this script, make sure you have downloaded [Docker](https://www.docker.com/).
    <br><br>
  2. Navigate to the root folder for this script (raster_interaction_to_api) in the command line, and create a symbolic link to the master copy of your .env file using the following command:
    <br>`ln -s /home/path/to/.env .`
    <br> Note: You only have to create this symbolic link once. You do *not* need to run the command above each time you want to run this script.
    <br><br>
  3. Run this script to update the raster interactions by running the following command:
    <br>`./start.sh`
