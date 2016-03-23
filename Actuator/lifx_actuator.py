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
To be able to have the program accessing and actuating your Lifx bulb data,
you have to register yourself at https://community.lifx.com/. After registering,
All you have to do is go to https://cloud.lifx.com/settings and click on
generate new token to give it a name and you will be provided a token through
you will be able to access lifx servers.Enter the information of your Lifx Device in the
json file in config folder.
'''
class DeviceList:
    '''Class definition of lifx to send API calls to
        the Lifx Bulb to perform various operations'''
    
    def __init__(self):
        '''Initialises the Client token and obtains the raw_data
            of the devices'''
        lifx_cred=Setting("lifx")
        self.getclienttoken=lifx_cred.setting["client_auth"]["_CLIENT_TOKEN"]
        self._DEVICE_REQ=lifx_cred.get("url")["_DEVICE_REQ"]
    
    def switch(self,cmd):
        '''Switch on/off the bulb
            Args as data:
                            'on' : switch on the bulb
                            'off': switch off the bulb
        '''
        payload ={"power": cmd}
        print self.postRequest(self._DEVICE_REQ,payload)
        
    def switch_state(self,cmd):
        '''Switch various states of the bulb
            Args as data:
                          Eg: {
                            "power": # "On/Off"
                            "color": # "blue saturation:0.5", 
                            "brightness": #0.5,
                            "duration": #5
                            }
                    
        '''
        payload =cmd
        print self.postRequest(self._DEVICE_REQ,payload)

    def  postRequest(self,url,params):
        '''Posts the actuation requests to the lifx bulb
           Args as data:
                       url   : url of lifx data to be posted
                       params: Actuation parameters
           Returns:
                   {u'results':
                        [
                            {u'status': u'ok',
                             u'id': #Id of the lifx bulb
                             u'label': #Name of the Lifx bulb
                            }
                        ]
                    }
            
        '''
        headers = {
                    "Authorization": "Bearer %s" % self.getclienttoken
                    }
        resp= requests.put(url,data=params,headers=headers).json()
        return resp

def main(args):
    ''' Accepts the command to either read or actuate the Lifx Bulb.

            Args as Data:
                            'on/off': Switch on/off the bulb
                            OR
                            '{
                                on/off: Switch on/off the bulb
                                blue saturation:0.5 ::  Provide color and
                                                    Saturation percent
                                brightness: Provide brightness percent
                                duration: Duration to be on in mins
                             }'
            Returns:
                            If the args is to Actuate the Lifx bulb, then
                            {u'results':
                                    [
                                        {u'status': u'ok',
                                         u'id': #Id of the lifx bulb
                                         u'label': #Name of the Lifx bulb
                                        }
                                    ]
                            } else

                            {"Device Not Found/Error in fetching data"}
    '''
    from sys import exit, stdout, stderr
    devList=DeviceList()
    
    if not devList.getclienttoken:
        stderr.write("Please Enter the Client token from Lifx in the config\
                     file")
        exit(1)
           
    try:
        if len(args)==2:
            devList.switch(args[1])
        elif len(args)>2 :
            state={"power": args[1],"color": args[2]+" "+args[3],
                "brightness": args[4],"duration": args[5]}
            devList.switch_state(state)
                
    except Exception as e:
        print "Device Not Found/Error in fetching data"
        print e
        exit(0)
           
if __name__ == "__main__":
    main(sys.argv)
