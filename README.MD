# Selido client and server
Selido is an application for storing aribtrary resources in a key:value format (tags), with various features to search through those tags.
# About
Selido has three components: 
* One server that manages storing and searching through tags
* One client that can interact with the server
* One database that stores the physical data (mongodb)
It is not neccessary to run both, they are independent of eachother. The server accepts various HTTP requests (GET, POST, DELETE etc.), but the client is one way to interact with the server.

# Setup

## Mongo
You will need to run an instance of mongo yourself. I recommend Docker, but it should work if you just run mongo any way you like on port 27017.

### Docker
If you use docker, here is the official mongo image: https://hub.docker.com/_/mongo. 

One way to start the database:
docker run -d --name mongo -e MONGO_INITDB_ROOT_USERNAME=selido -e MONGO_INITDB_ROOT_PASSWORD=supersecretpassword -p 27017:27017 mongo:latest
Replace the password with anything you like, or remove the two "-e" options if you want an open database.


#### If you would like to run Docker, here are some guides to get it up and running:
* Ubuntu: https://docs.docker.com/engine/install/ubuntu/
* Windows: https://docs.docker.com/docker-for-windows/install/
 
### Other install guides for mongo
* Windows: https://www.mongodb.com/try/download/community
* Ubuntu: https://docs.mongodb.com/manual/tutorial/install-mongodb-on-ubuntu/

## Server
I recommend running the server on a linux machine, (Todo, add use the docker image here) but it should work on Windows aswell. You will **need** the "openssl" program installed on the machine where you run the server, as this is used for authentication. Most regular linux distributions come with openssl, but if not, you can install it through your preferred package manager. On Windows, I recommend chocolatey: https://chocolatey.org/install and the openssl package: https://chocolatey.org/packages/openssl

Once openssl is installed, you will need node as well. 
* Windows: https://nodejs.org/en/download/
* Linux: https://nodejs.org/en/download/package-manager/

Now you can open a terminal and change into the server directory, then run the server with "npm start -- \<options here>". If you are running your database on the same machine, you will atleast need the "-d localhost" option, which specifies where to connect to the database. You will be asked some questions relating to HTTPS certifcates, then your server will be running. If you answered no when asked if the same machine would be the first client, you will need to manually copy the specified files to the client machine, in the selido client directory (see [Client](Client) section)

##Client
Currently, the code changes way too often to build binaries, but the plan is to release the client as an executable. For now, you will need python3 (>3.5, I believe) installed. There are a bajillion guides online on downloading python, just google it. Change into the directory where the client is, and type "python3 src/main.py init" (on Windows, exclude the "3" in python). When prompted for a username, make sure you type the same as when you where asked for a username on the server side.

#Usage

Todo
