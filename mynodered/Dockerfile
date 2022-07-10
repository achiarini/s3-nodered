FROM nodered/node-red

COPY flows.json /tmp/
COPY s3-unibo-nodered-23522a5c8ecd.json /tmp/
RUN cp /tmp/flows.json /data/
RUN cp /tmp/s3-unibo-nodered-23522a5c8ecd.json /data/

# ui
RUN npm i node-red-dashboard
RUN npm i node-red-node-ui-table
# mysql 
# google cloud
RUN npm i node-red-contrib-google-cloud

RUN npm i node-red-node-mysql



ENV GOOGLE_APPLICATION_CREDENTIALS /data/s3-unibo-nodered-23522a5c8ecd.json
ENV GOOGLE_CLOUD_PROJECT s3-unibo-nodered
ENTRYPOINT ["npm", "--no-update-notifier", "--no-fund", "start", "--cache", "/data/.npm", "--", "--userDir", "/data"]

RUN cp /tmp/flows.json /data/
RUN cp /tmp/s3-unibo-nodered-23522a5c8ecd.json /data/
