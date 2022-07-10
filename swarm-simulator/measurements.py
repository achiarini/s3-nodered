from google.cloud import pubsub_v1
from random import randint
from multiprocessing import Pool
import json,  datetime, os, time


project_id = os.environ [ 'GOOGLE_CLOUD_PROJECT'] 
topic_id = "measurements"
publisher = pubsub_v1.PublisherClient()
# The `topic_path` method creates a fully qualified identifier
# in the form `projects/{project_id}/topics/{topic_id}`
topic_path = publisher.topic_path(project_id, topic_id)
MAX_CYCLES = int(os.environ['MAX_CYCLES'])


def main():

    devices = [{'deviceId':1,'latitude':44.45,'longitude':11.34,'ImageSamplingPeriod':1},
    {'deviceId':9,'latitude':38.12,'longitude':13.36,'ImageSamplingPeriod':1}
    ]
    for cycle in range(1, MAX_CYCLES):
        p = Pool(processes=len(devices))
        result = p.map(sendMeasure, devices)


def sendMeasure(device):

    latitude = device['latitude'] + randint(0,100)/10000
    longitude = device['longitude'] + randint(0,100)/10000
    deviceId = device['deviceId']
    # datetime in zulu format
    timeStamp = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
    temperature = 25. + 15. * (randint(0,100)/100)
    humidity = 85. + 15 *  (randint(0,100)/100)
    payload = {
                'timeStamp':timeStamp,
                'deviceId':1,
                'latitude':latitude,
                'longitude':longitude,
                'temperature': temperature,
                'humidity': humidity
            }

    future = publisher.publish(topic_path, json.dumps(payload).encode('utf-8'))
    time.sleep(device['ImageSamplingPeriod'])

    print(future.result())
    print(json.dumps(payload))
    print(f"Published messages to {topic_path}.")


 
if __name__ == '__main__':
    main()