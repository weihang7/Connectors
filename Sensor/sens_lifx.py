#!/usr/bin/python
# -*- coding: utf-8 -*-
import re
import urllib2
import requests
from urllib import urlencode
import warnings
import json
import time
import sys
from BD_connect.connect_bd import get_json
from config.setting import Setting
warnings.filterwarnings("ignore")
'''
About:
This module is a connector that connects any Lifx Bulb to the
Building DepotV3.1 with the help of the bd connect program.

Configuration:
To be able to have the program accessing and reading your Lifx bulb data,
you have to register yourself at https://community.lifx.com/. After registering,
All you have to do is go to https://cloud.lifx.com/settings and click on
generate new token to give it a name and you will be provided a token through
you will be able to access lifx servers.Enter the information of your
Lifx Device in the json file in config folder.
'''
class DeviceList:
    '''Class definition of lifx to send API calls to
        the Lifx Bulb to perform various operations'''
    
    def __init__(self):
        '''Initialises the Client token and obtains the raw_data
            of the devices'''
        lifx_cred=Setting("lifx")
        self.getclienttoken=lifx_cred.setting["client_auth"]["_CLIENT_TOKEN"]
        self.rawData=self.getRequest(lifx_cred.get("url")["_DEVICELIST_REQ"])

    def stationData(self):
        '''
        Obtains the Lifx bulb data and writes them to the Building depot
        Returns:
                {
                    "success": "True" 
                    "HTTP Error 400": "Bad Request"
                }
        '''
        global mac_id
        for device in self.rawData:
            lifx_data={}
            mac_id=device["id"]
            name=device["label"].replace(" ","_")
            for k in device["color"].keys():
                lifx_data[k+"_"+name]=device["color"][k]
            lifx_data["brightness_"+name]=device["brightness"]
            lifx_data["status_"+name]=device["power"]
            return self.post_BD(lifx_data)
        
    def post_BD(self,stationdata):
        '''
            Format of the JSON Object to be sent to bd_connect.py.
            sensor_data contains all information from sensor to be
            Read and sensor_points to be created in accordance with that.
            client_data contains all information about client_id,client_keyetc
            for authentication
            data={"sensor_data":{}}
            Args as data:
                            {<Lifx bulb data>,<brightness>, <hue> etc.}
            Returns:
                            {
                                "success": "True" 
                                "HTTP Error 400": "Bad Request"
                            }
        '''
        global mac_id
        print stationdata
        data={'sensor_data':{}}
        data['sensor_data'].update(stationdata)
        data['sensor_data'].update({"mac_id":mac_id})
        try:
            resp=get_json(json.dumps(data))
        except Exception as e:
            print e
        return resp
    
    def getRequest(self,url):
        '''
            Get Status of the Bulb and the device list of Lifx bulbs
            Args as data:
                       url   : Url of lifx bulb
            Returns:
                    Lifx bulb device list and status
                
        '''
        headers = {
                    "Authorization": "Bearer %s" % self.getclienttoken
                    }
        resp= requests.get(url,headers=headers).json()
        return resp

def main(args):
    ''' Accepts the command to either read or actuate the Lifx Bulb.

                Args as Data:
                                '': Empty to Write data to the Building depot
                Returns:
                                If the No args read status and write data
                                to building depot 
                                {
                                    "success": "True" 
                                    "HTTP Error 400": "Bad Request"
                                } else

                                {"Device Not Found/Error in fetching data"}
    '''
    from sys import exit, stdout, stderr
    devList=DeviceList()

    if not devList.getclienttoken:
           stderr.write("Please Enter the Client token from Lifx in\
                        the config file")
           exit(1)
           
    try:
        resp=devList.stationData()  #Get the Lifx Bulbs data and updates the BD
        print resp
                
    except Exception as e:
        print "Device Not Found/Error in fetching data"
        exit(0)
        
    
if __name__ == "__main__":
    main(sys.argv)
