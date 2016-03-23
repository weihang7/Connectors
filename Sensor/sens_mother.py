#!/usr/bin/python
# -*- coding: utf-8 -*-
import pip
import json, time
from urllib import urlencode
import urllib2
import requests
import datetime
from BD_connect.connect_bd import get_json
from config.setting import Setting
'''
About:
This module is a connector that connects any Sen.se Mother Device to the
Building DepotV3.1 with the help of the bd connect program.

Configuration:
To be able to have the program accessing your Sen.se Mother data, you have
to register yourself in the Sen.se's Developer website with an email and
a password.To obtain an access to the Sen.se APIs you have to register at
https://sen.se/developers/ and fill up the form. Once you get a mail from
sen.se regarding your access to their Api(which may take a week) regarding
providing access to their servers you can start implementing the codes below.
Enter the information of your Netatmo Device in the json file in config folder.
'''


#BuildingDepot Specific Definitions
global mac_id
mac_id='00:04:A3:FF:BA:C0'

class ClientAuth:
    '''Class defintion of Sen.se Mother to request authentication and
       keep access token available through token method.'''
    def __init__(self):
        mother_cred=Setting("mother")
        self.username=mother_cred.setting['client_auth']['_USERNAME']
        self.password=mother_cred.setting['client_auth']['_PASSWORD']
        params= {'username': str(self.username),'password': str(self.password)}
        params={'username': 'sud335', 'password': '469321#'}
        self._AUTH_REQ=mother_cred.get("url")["_AUTH_REQ"]
        self._NODE_REQ=mother_cred.get("url")["_NODE_REQ"]
        resp= requests.post(self._AUTH_REQ,params).json()
        if 'token' in resp:
            self.api_token=resp["token"]
        else:
            print self.api_token,"Error"
            exit(1)

#Class for Client authentication and access token        
class DeviceList:
    '''
        Class defintion of Sen.se mother to request for the Device List ,
        obtain the cookie data  and send itto the Building Depot so as to
        update the metadata
    '''
    def __init__(self,authData):
        '''
            Initilize the auth token and obtain the cookie data of Sen.se Mother
            Args as data:
                            "authData": class object of ClientAuth provides
                                        access token.
        '''
        self.getAuthToken = authData.api_token
        params = {'resource__type': 'device', 'resource__slug': 'cookie'}
        resp = self.getRequest(authData._NODE_REQ,params)
        self.rawData = resp["objects"]
        self.cookie_feeds={}
        for cookie in self.rawData:
            cok_id=cookie["label"]+"#"+cookie["uid"]
            self.cookie_feeds[cok_id]=cookie["publishes"]
        self.cookie_event_urls={}
        #obtains the cookie feeds of the Sen.se mother
        for key,value in self.cookie_feeds.items():
            self.cookie_event_urls[key]=[]
            for app in value:
                self.cookie_event_urls[key].append(app["url"]+"events/")
            #If none of the apps for the respective cookies are not activated
            if not self.cookie_event_urls[key]:
                self.cookie_event_urls.pop(key,None)
                
    def getCookieAppData(self,eventdata,device):
        ''' Obtain each Sen.se mother cookie's app data and return them
            Args as data:
                            "eventdata": #The event information of each app
                                          installed in the Sen.se mother
                                          cookie
                            "device": #Device name of the Sen.se mother cookie
            Returns:
                            Data readings of the cookie for the specific app
                            
        '''
        print "DATA :",eventdata["type"]
        for key,value in eventdata["data"].items():
            reading=device+"_"+eventdata["type"]+"_"+key
            eventdata["data"][reading]=eventdata["data"].pop(key)
        print eventdata["data"]
        return eventdata["data"]
    
    def getMotherData(self):
        '''Obtain the all app data of all cookie connected to the mother and get
            each app's data installed on the cookie
            Returns:
                        A json which consists all the Sen.se mothers cookie
                        recent data 
        '''
        app_data={}
        for key,value in self.cookie_event_urls.items():
            device_name=key.split("#")[0]
            print "Fetching:",key.split("#")[0],"'s data"
            for url in value:
                #Get the data of the apps installed on the cookie
                latest_reading=self.getRequest(url)["objects"][0]
                app_data.update(self.getCookieAppData(latest_reading,device_name))
        return app_data
            
    def getRequest(self,url,params=None):
        '''
            Get Device List for Sen.se Mother and its cookies
            Args as data:
                           url   : Url of Sen.se mothers cookies data
                           params : cookie specific parameters
            Returns:
                          Sen.se mothers cookie and app data
            
        '''
        header = {'Authorization': \
                  u' Token '+self.getAuthToken}
        resp = requests.get(url,headers=header,params=params).json()
        return resp
    
    #Post Values to Building Depot.
    def post_BD(self,mother_data):
        '''
        Format of the JSON Object to be sent to bd_connect.py.
        sensor_data contains all information from sensor to be Read
        and sensor_points to be created in accordance with that.
        client_data contains all information about client_id,client_key etc
        for authentication
        data={"sensor_data":{}}

            Args as data:
                            {<Sen.se mothers data>}
            Returns:
                            {
                                "success": "True" 
                                "HTTP Error 400": "Bad Request"
                            }
        '''
        data={'sensor_data':{}}
        data['sensor_data'].update(mother_data)
        data['sensor_data'].update({"mac_id":mac_id})
        resp=get_json(json.dumps(data))
        return resp
        

if __name__=='__main__':

    '''
        Reads the Sen.se mothers cookie data and writes it to the building depot.

        Returns:
                Reads the data from Sen.se mother cookies
                {
                    "success": "True" 
                    "HTTP Error 400": "Bad Request"
                }
                else
                {"Error in Device Connection"}
        
        
    '''
    from sys import exit, stdout, stderr
    try:
        auth=ClientAuth()
        if not auth.username or not auth.password:
            stderr.write("Please Enter the Sen.se Mothers username and password")
            exit(1)
        devList = DeviceList(auth)         #Obtain the Device List
        mother_data = devList.getMotherData()       #Get the Mother Sensor data

        try:
            resp=devList.post_BD(mother_data)   #Send Data to the BuildingDepot
            print resp
        except Exception as e:
            print "Error in Sending data to connect_bd.py",e
            
    except Exception as e:
        
        print "Error in Device Connection",e
