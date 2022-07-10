## How-to boostrap a IOT platform in Node-Red

### Rationale

### Prerequisites

- Docker
- Google Cloud Platform account and a GCP active project
- GCP SDK & Command line utilities

### Setup Environment on Docker

#### Node-Red
From a commandline (let's assume the Terminal in MacOS or a shell in WSL): 

    docker pull nodered/node-red
    docker network create s3 
    docker run -it -p 1880:1880 -v node_red_data:/data --network s3 --env GOOGLE_CLOUD_PROJECT=s3-unibo-nodered --name mynodered nodered/node-red

Let's dissect the command:

    docker run                                      - run this container, initially building locally if necessary
    -it                                             - attach a terminal session so we can see what is going on
    -p 1880:1880                                    - connect local port 1880 to the exposed internal port 1880
    -v node_red_data:/data                          - mount a docker named volume called `node_red_data` to the container /data directory so any changes made to flows are persisted
    --name mynodered                                - give this machine a friendly local name
    nodered/node-red                                - the image to base it on - currently Node-RED v1.2.0
    --env  GOOGLE_CLOUD_PROJECT=s3-unibo-nodered    - set the env var GOOGLE_CLOUD_PROJECT to our current GCP 
    project
    --network s3                                    - attach the container to a user defined bridge network

Check the installation was ok by pointing the browser to localhost:1880:
    ![Nodered start page](/img/nodered-start.png)


#### Mysql
In another shell, from the commandline type: 

    docker pull mysql
    docker run --name  s3-mysql --network s3 -e MYSQL_ROOT_PASSWORD=<MYSQL_PWD> -d mysql


Let's dissect the command:

    docker run                                      - run this container, initially building locally if necessary
    --name s3-mysql                                 - give this machine a friendly local name
    mysql                                           - the image to base it on
    -e  MYSQL_ROOT_PASSWORD=<MYSQL_PWD>             - set the env var MYSQL_ROOT_PASSWORD with the root password
    --network s3                                    - attach the container to a our user defined bridge network

Check that the installation is ok with a sql client:

    docker run -it --network s3 --rm mysql mysql -hs3-mysql -uroot -p

Prompt the password and check that everything is ok

#### Set-up a Google Cloud Platform Project
- Storage Bucket
- IOT Core/MQTT Topic


### Start building things:
#### 1. Populating the DB

Run the container with mysql client:

    docker run -it --network s3 --rm mysql mysql -hs3-mysql -uroot -p

Prompt your password and check you can connect to your db. 

Then: 

        CREATE DATABASE s3;
        USE s3;
        CREATE TABLE devices(deviceID INT NOT NULL, location VARCHAR(50) NOT NULL, latitude FLOAT NOT NULL, longitude FLOAT NOT NULL, imagingSamplingPeriod INT NOT NULL,measureSamplingPeriod INT NOT NULL, PRIMARY KEY(deviceId));
        INSERT INTO devices VALUES(1,"Bologna",44.494887,11.3426163,5,1);
        INSERT INTO devices VALUES(2,"Brescia",45.5257,10.2283,5,1);
        INSERT INTO devices VALUES(3,"Trento",46.0793,11.1302,5,1);
        INSERT INTO devices VALUES(4,"Treviso",45.6723,12.2422,5,1);
        INSERT INTO devices VALUES(5,"Firenze",43.7695604,11.2558136,5,1);
        INSERT INTO devices VALUES(6,"Siena",43.318809,11.3307574,5,1);
        INSERT INTO devices VALUES(7,"Bari",41.1187,16.852,5,1);
        INSERT INTO devices VALUES(8,"Roma",41.9109,12.4818,5,1);
        INSERT INTO devices VALUES(9,"Palermo",38.1156879,13.361267,5,1);

#### 2. Creating the Device View

Install the Node-red dashboard through the "Manage Palette" section. Install the following packages:
- node-red-dashboard
- node-red-node-ui-table
- node-red-node-mysql

#### Connect to DB

Drop a mysql node and then configure it as follows: 
    ![Nodered start page](/img/mysqlnode-conf.png)

#### Create the view
Drop a ui-table node into the flow and then connect it to the query ouput. 
Point the browser to http://localhost:1880/ui to see the web page rendering. 

#### 3. Creating the first flow: images

First of all, we will install the GCP nodes from the Manage Palette section in the configuration section. 
You need to select the  node-red-contrib-google-cloud package. 
Then, we create the backend Google Cloud Storage bucket, to store our images. From the commandline where you installed the Google Cloud CLI type: 

    gsutil mb -l EU gs://unibo-s3-nodered-images


Now, you need to create a flow as follows (see flow-1.json). 
Let's discuss the major nodes:
- http
- change
- template
- gcswrite

Before testing, we need to make sure that our service is authorized by Google Cloud. 
Let's create a service account: 

    gcloud iam service-accounts create helper-sa

Then, we need to bind the service account to proper role (Cloud Storage & Pub/Sub Admin)

    gcloud projects add-iam-policy-binding PROJECT_ID --member="serviceAccount:SERVICE_ACCOUNT_NAME@PROJECT_ID.iam.gserviceaccount.com" --role=ROLE

where: 

    PROJECT_ID              - is your GCP Project Id, 
    SERVICE_ACCOUNT_NAME    - is the service account name just created
    ROLE                    - is the ROLE to bind to our service account, for the scope of this workshop we use roles/pubsub.admin and roles/storage.admin

so in our case: 

    gcloud projects add-iam-policy-binding s3-unibo-nodered --member="serviceAccount:helper-sa@s3-unibo-nodered.iam.gserviceaccount.com" --role=roles/pubsub.admin --role=roles/storage.admin

and we generate a json key: 

    gcloud iam service-accounts keys create service-account-key.json --iam-account=helper-sa@s3-unibo-nodered.iam.gserviceaccount.com

Next, we move the service key on the container stateful volume: 

    docker cp service-account-key.json mynodered:/data

And finally we need to make sure that the json credential are referenced by the env var GOOGLE_APPLICATION_CREDENTIAL, so we need to re-start the container:

    docker rm -f mynodered
    docker run -it -p 1880:1880 -v node_red_data:/data --network s3 --env GOOGLE_CLOUD_PROJECT=s3-unibo-nodered --env GOOGLE_APPLICATION_CREDENTIAL=/data/service-account-key.json --name mynodered nodered/node-red

And now here we are, we are ready to test:

    curl -X POST http://localhost:1880/upload -F "filename=@./img/mysqlnode-conf.png" -F 'deviceId=1' -F 'timeStamp=2022-07-05T09:43:36Z' -F 'latitude=44.5' -F 'longitude=11.35'

And it works! Ok, so now let's move to the other operating flow.

#### 4. Creating the second flow: images events

#### Pub/Sub topic creation

    gcloud services enable pubsub
    gcloud pubsub topics create images
    gcloud pubsub subscriptions create images-subscription --topic=images



#### newImage event

Let's add a pub/sub node into the imageUpload flow. You should configure the node as follow and connect to the json template node: 
    ![Nodered start page](/img/mysqlnode-conf.png)

#### insertIntoDB

Now catch the message and  insert the image event into the samples table: you will set up a new flow (newImageEvent.json). Create a table into the DB: 

    CREATE TABLE samples(sampleId INT AUTO_INCREMENT NOT NULL, deviceId INT NOT NULL, latitude FLOAT NOT NULL, longitude FLOAT NOT NULL, imageFileURI VARCHAR(512), timeStamp VARCHAR(32), PRIMARY KEY(sampleId));


Now let's connect the flow components, set the new query with this jsonata expression into the **msg.topic** element: 

    "INSERT INTO  samples (deviceId, timeStamp, latitude, longitude, imageFileURI)"&	" VALUES("&msg.payload.deviceId&","	&'"'&msg.payload.timeStamp&'"'&","	&msg.payload.latitude&","	&msg.payload.longitude&","	&'"'&msg.payload.imageFileURI&'"'	&");"

Then, test by sending a post to the /upload endpoint previously created. 
Let's see by querying the samples table if we get the result.

    mysql> select * from samples
    -> ;
    +----------+----------+----------+-----------+-------------------------------------------------------------+----------------------+
    | sampleId | deviceId | latitude | longitude | imageFileURI                                                | timeStamp            |
    +----------+----------+----------+-----------+-------------------------------------------------------------+----------------------+
    |        1 |        1 |     44.5 |     11.35 | gs://unibo-s3-nodered-images/1/2022-07-09T17:51:42.874Z.png | 2022-07-05T09:43:36Z |
    +----------+----------+----------+-----------+-------------------------------------------------------------+----------------------+
    1 row in set (0.00 sec)


Yep, it is here

#### 5. Creating the third flow: measurements

The third flow is pretty similar to the samples one. A subscription is listening to new messages that arrives from the devices. A new topic and subscriber are required: 

    gcloud pubsub topics create measurements
    gcloud pubsub subscriptions create measurements-subscription --topic=measurements


Then, we prepare a table for the measurements, on the mysql prompt:

    CREATE TABLE measurements(measureId INT AUTO_INCREMENT NOT NULL, deviceId INT NOT NULL, latitude FLOAT NOT NULL, longitude FLOAT NOT NULL, temperature INT NOT NULL, humidity INT NOT NULL, timeStamp VARCHAR(32), PRIMARY KEY(measureId));


We create a flow with the same components as the samples one. The query in jsonata synthax this time is: 

    "INSERT INTO  samples (deviceId, timeStamp, latitude, longitude, temperature, humidity)"&	" VALUES("&msg.payload.deviceId&","	&'"'&msg.payload.timeStamp&'"'&","	&msg.payload.latitude&","	&msg.payload.longitude&","&msg.payload.temperature&","&msg.payload.humidity	&");"

This time we test with a helper flow we set up just for testing purposes. 

#### 9. Simulating the IOT swarm behaviour

Create a dedicated container that executes the code that simulates the behaviour of the devices. 
Let's see how the Dockerfile looks like:

    FROM ubuntu

    WORKDIR /app

    ADD requirements.txt .
    ADD images.py .
    ADD measurements.py .
    ADD sample.jpeg .
    ADD s3-unibo-nodered-23522a5c8ecd.json .

    # REQUIRED FOR AUTH*
    ENV GOOGLE_CLOUD_PROJECT s3-unibo-nodered
    ENV GOOGLE_APPLICATION_CREDENTIALS /app/s3-unibo-nodered-23522a5c8ecd.json
    ENV MAX_CYCLES 300
    ENV BACKEND_URL http://mynodered:1880/upload
    # INSTALL PYTHON
    RUN apt update
    RUN apt install -y python3 python3-dev python3-venv

    RUN apt-get  -y install wget
    RUN wget  https://bootstrap.pypa.io/get-pip.py
    RUN python3 get-pip.py


    # INSTALL GOOGLE CLOUD SDK
    RUN pip install google-cloud-pubsub
    # INSTALL DEPENDENCIES
    #RUN pip install -r requirements.txt

    ENTRYPOINT [ "/bin/bash" , "-l", "-c"]

Next step is to build the docker image, and  test it locally. Let's see how to do it:

    docker build -t swarm-sim .
    docker run --network s3  -ti swarm-sim "python3 measurements.py"
    docker run --network s3  -ti swarm-sim "python3 images.py"

You can point the browser to the localhost:1880/ui dashboard to see that the database is being populated. 

#### 8. Deploying the environment on GCP

Everything is running locally, it is time to move the backend of your IOT devices on the cloud. 
Having a containerized environment, makes this quite easier. First of all we, need to create/modify the docker images. 

- node-red

During the workshop we modified the flow.json file which has been updated with the flows that we graphically created. In order to get the same flows,  we need to make sure it is in the docker image of the deployed image. 
The flows.json in the mynodered folder of this repo, contains the updated flows. Next, we need to install all the nodered packages that have been used in the workshop. 
Then, you need to add credentials and to set the ENV for Google Cloud authentication & authorization. 
We do not need any further change to the docker image. 
Time to point your shell to mynodered folder and type: 

    docker build -t mynodered .

And we will push our image into our private Container Registry

    gcloud artifacts repositories create s3-nodered-repo --repository-format=docker \
    --location=europe-west1 --description="Docker repository"
    # Configure authentication
    gcloud auth configure-docker europe-west1-docker.pkg.dev
    # tag the image for the upload
    docker tag mynodered \
    europe-west1-docker.pkg.dev/s3-unibo-nodered/s3-nodered-repo/mynodered:1.0
    docker push europe-west1-docker.pkg.dev/s3-unibo-nodered/s3-nodered-repo/mynodered:1.0

And now you are ready to deploy this image on a VM. Google Cloud provide the capability to spin a VM starting from an image container. Let's see how to do it: 

    gcloud compute instances create-with-container mynodered --project=s3-unibo-nodered --zone=europe-west1-b --machine-type=e2-medium --network-interface=network-tier=PREMIUM,subnet=default --maintenance-policy=MIGRATE --provisioning-model=STANDARD --service-account=793199356273-compute@developer.gserviceaccount.com --scopes=https://www.googleapis.com/auth/cloud-platform --tags=nodered --image=projects/cos-cloud/global/images/cos-stable-97-16919-103-4 --boot-disk-size=10GB --boot-disk-type=pd-balanced --boot-disk-device-name=mynodered --container-image=europe-west1-docker.pkg.dev/s3-unibo-nodered/s3-nodered-repo/mynodered:2.0 --container-restart-policy=always --container-stdin --container-tty --container-mount-host-path=host-path=/tmp,mode=rw,mount-path=/data --no-shielded-secure-boot --shielded-vtpm --shielded-integrity-monitoring --labels=container-vm=cos-stable-97-16919-103-4
    # Add a rule in cloud firewall
    gcloud compute firewall-rules create allow-http \
    --allow tcp:1880 --target-tags nodered

Make sure that flows.json is correctly stored on data. 

- mysql

The mysql image doesn't need to be altered. The container does not communicated with Google Cloud services. 

    gcloud compute instances create-with-container s3-mysql --project=s3-unibo-nodered --zone=europe-west1-b --machine-type=e2-medium --network-interface=network-tier=PREMIUM,subnet=default --maintenance-policy=MIGRATE --provisioning-model=STANDARD --service-account=793199356273-compute@developer.gserviceaccount.com --scopes=https://www.googleapis.com/auth/devstorage.read_only,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/trace.append --tags=s3-mysql --image=projects/cos-cloud/global/images/cos-stable-97-16919-103-4 --boot-disk-size=10GB --boot-disk-type=pd-balanced --boot-disk-device-name=s3-mysql --container-image=mysql --container-restart-policy=always --container-stdin --container-tty --container-env=MYSQL_ROOT_PASSWORD=s3-summer-school --container-mount-host-path=host-path=/tmp/,mode=rw,mount-path=/VAR/LIB/MYSQL --no-shielded-secure-boot --shielded-vtpm --shielded-integrity-monitoring --labels=container-vm=cos-stable-97-16919-103-4

Access to the remote VM

    gcloud compute ssh s3-mysql

Access to the container

    docker ps
    docker exec -ti <CONTAINER_ID> /bin/bash


Access to the mysql interface

    mysql -p

Re-Create db and tables, as in the above examples.

- swarm-sim

The swarm-sim is ready to be deployed on its cloud environment. 

    gcloud compute instances create-with-container swarm-sim --project=s3-unibo-nodered --zone=europe-west1-b --machine-type=e2-medium --network-interface=network-tier=PREMIUM,subnet=default --maintenance-policy=MIGRATE --provisioning-model=STANDARD --service-account=793199356273-compute@developer.gserviceaccount.com --scopes=https://www.googleapis.com/auth/cloud-platform --image=projects/cos-cloud/global/images/cos-stable-97-16919-103-4 --boot-disk-size=10GB --boot-disk-type=pd-balanced --boot-disk-device-name=swarm-sim --container-image=europe-west1-docker.pkg.dev/s3-unibo-nodered/s3-nodered-repo/swarm-sim:1.0 --container-restart-policy=always --container-stdin --container-tty --no-shielded-secure-boot --shielded-vtpm --shielded-integrity-monitoring --labels=container-vm=cos-stable-97-16919-103-4


We now connect to the VM to startup the simulation jobs

    gcloud compute ssh swarm-sim
    docker exec -ti 41f702c0039b /bin/bash 
    python3 measurements.py
    python3 images.py

### Clean-up cloud resources

    #delete instances
    gcloud compute instances delete swarm-sim
    gcloud compute instances delete s3-mysql
    gcloud compute instances delete mynodered
    #delete firewall rules
    gcloud  compute firewall-rules delete allow-http
    #delete service-account
    gcloud iam service-accounts delete helper-sa@s3-unibo-nodered.iam.gserviceaccount.com
    #delete repositories 
    gcloud artifacts repositories delete s3-nodered-repo  --location europe-west1
    #delete topic
    gcloud pubsub topics delete projects/s3-unibo-nodered/topics/images
    #delete subscription
    gcloud pubsub subscriptions delete projects/s3-unibo-nodered/subscriptions/images-subscription
    gcloud pubsub subscriptions delete projects/s3-unibo-nodered/subscriptions/measurements-subscription
    #delete bucket
    gsutil rm -r  gs://unibo-s3-nodered-images/

