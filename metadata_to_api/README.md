# data-team-tools

**Uploading metadata to the API**

All of our metadata is hosted on a Google sheet. Each time we add or update metadata in the Google sheet, we have to push this metadata to the API before it is updated on Resource Watch. We push this metadata to the API using a Python script that is run in a Docker container.

run the docker command 'metadata-to-api' to update it.  

To set this up on your computer: 
  1) Download [Docker](https://www.docker.com/)
  2) Create a folder on your computer where you want to store this tool.
  3) [Clone the data-team-tools repository](https://help.github.com/en/github/creating-cloning-and-archiving-repositories/cloning-a-repository) to the folder you just created.
  4) Navigate to the metadata-to-api file in the command line, and add an .env file using the following commands:
		- touch .env (to create a new environmental variables file)
		- open .env (to open this file, then paste info from another DT member and save)
  5) Run this script to update the metadata by running the following command:
        - ./start.sh
        
	  
