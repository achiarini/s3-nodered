#leggo dal db i parametri

#while(count=1000)
  #foreach device
    #latitude = lat
from random import randint
from requests import post
from requests.auth import HTTPBasicAuth
from multiprocessing import Pool

import datetime, os, time

def main():
    devices = [{'deviceId':1,'latitude':44.45,'longitude':11.34,'ImageSamplingPeriod':5},
    {'deviceId':9,'latitude':38.12,'longitude':13.36,'ImageSamplingPeriod':5}
    ]
    MAX_CYCLES = int(os.environ['MAX_CYCLES'])


    for cycle in range(1, MAX_CYCLES):
        p = Pool(processes=len(devices))
        result = p.map(uploadImage, devices)


def uploadImage(device):
    url = os.environ['BACKEND_URL']
    basic = HTTPBasicAuth("apiuser", "AW3nTja4Pj")
    #latitude = device.latitude + randint(0,100)/10000
    latitude = device['latitude'] + randint(0,100)/10000
    longitude = device['longitude'] + randint(0,100)/10000
    deviceId = device['deviceId']
    timeStamp = datetime.datetime.now()
    payload = {
                    'timeStamp':timeStamp,
                    'deviceId':deviceId,
                    'latitude':latitude,
                    'longitude':longitude
                }
    files = {'file': ('sample.jpeg', open('sample.jpeg', 'rb'),'image/jpg')}
    res = post(url, data=payload, files=files, auth = basic)
    print(res)
    time.sleep(device['ImageSamplingPeriod'])
 
if __name__ == '__main__':
    main()