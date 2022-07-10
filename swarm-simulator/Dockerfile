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
ENV MAX_CYCLES 100
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

ENTRYPOINT [ "/bin/bash" ]
