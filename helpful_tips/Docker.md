# Error: script won’t run at all
When trying to run a script, you encounter the folowing error:
```
sudo: ./start.sh: command not found
```

## Solution
In each script, the contents and src folders will always be executable. 

The file that determines if the script can run is the start.sh file. If this file is executable, the script will run; if the file is not executable, the script will not run.

When you navigate into any NRT script’s root folder and type “ls -l”, you will see a list of files and their permissions.

If the file is executable, you should see “-rwxr-xr-x” to the left of its name (the x means it is executable). If the file is not executable, you should see “-rw-r-xr--” to the left of its name. If the file won't execute, type  “chmod +x ./start.sh”. This adds the executable permissions on that file, so when you type “ls -l” now, you should see “-rwxr-xr-x” to the left of the start.sh file.

If the script will run locally, but not on the server--log in to the server and change the file permissions directly on the server.

# Error: Failure running apt-get update when running Docker for the first time
```
Step 5/16 : RUN apt-get update
---> Running in 38abf39cec19
Err:1 http://security.debian.org/debian-security buster/updates InRelease
Temporary failure resolving 'security.debian.org'
Err:2 http://deb.debian.org/debian buster InRelease
Temporary failure resolving 'deb.debian.org'
Err:3 http://deb.debian.org/debian buster-updates InRelease
Temporary failure resolving 'deb.debian.org'
Reading package lists...
W: Failed to fetch http://deb.debian.org/debian/dists/buster/InRelease Temporary failure resolving 'deb.debian.org'
W: Failed to fetch http://security.debian.org/debian-security/dists/buster/updates/InRelease Temporary failure resolving 'security.debian.org'
W: Failed to fetch http://deb.debian.org/debian/dists/buster-updates/InRelease Temporary failure resolving 'deb.debian.org'
W: Some index files failed to download. They have been ignored, or old ones used instead.
```

## Solution:
This problem might happen from time to time. You might also see errors like “Could not establish a connection”. We are still not sure about the exact cause of these kinds of docker specific problems and how to solve them. Based on reading similar bug reports from the web, I found that it's a DNS server issue. Some people recommend to wait 24 hours and the problem might solve automatically. If it doesn't I will have to fix it manually by adding Google server DNS or installing another Ubuntu package. I found that most of the time this problem solves by itself within a few days. Also, this problem might get solved if you run your docker in a different network. So, if you encounter this sort of docker related errors, either wait for a few days and then try running again or try running your docker in a different environment (in the office or at your friend’s house)

# Error: Docker has shut down
```
Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?
ERRO[0000] failed to dial gRPC: cannot connect to the Docker daemon. Is 'docker daemon' running on this host?: dial unix /var/run/docker.sock: connect: no such file or directory
docker: Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?.
See 'docker run --help'.
```

## Solution:
Docker may have shut down. Start Docker again by typing the following in the command line:
```
sudo service docker start
```

# Error: Cron error while running a script in Docker:
Error:
Step 6/18 : RUN apt-get install -y cron
 ---> Running in 15ba9ea01e2e
Reading package lists...
Building dependency tree...
Reading state information...
E: Unable to locate package cron
The command '/bin/sh -c apt-get install -y cron' returned a non-zero code: 100
Unable to find image 'dis_015a:latest' locally
docker: Error response from daemon: pull access denied for dis_015a, repository does not exist or may require 'docker login': denied: requested access to the resource is denied.
See 'docker run --help'.
 
## Solution:			
There is a variable in Dockerfile (ARG NAME=cli_041) and in start.sh (NAME=cli_041) to specify build argument for Docker. If you try to set these name variable as something like cli_041_antarctica_ice, you might encounter this error. To solve the issue change the arg name in both dockerfile and start.sh (for example: cli_041_antarctica_ice to cli_041) and the problem may go away. Sometimes your name could be too long and you need to shorted it. We still don’t know why this happens and the correct approach to solve the issue. However, this problem doesn’t happen while the script is running on the server. So, you don’t have to worry about that. This fix is just necessary when you try to run the docker locally to check something or fix a bug.

