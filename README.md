
# data-team-tools
Data team tools

**Uploading metadata to the API**
All of our metadata is hosted on a google sheet, and we run the docker command 'metadata-to-api' to update it.  To set this up on your computer: 
  1) Download Docker
  2) Git clone the [data-team-tools] repo to a folder on your computer (https://github.com/resource-watch/data-team-tools) 
  3) Open the metadata-to-api file and add an .env file.
	  Commands:
		- touch .env
		- open .env (paste info from another DT member and save)
4) Run script file using ./start.sh
	  
