#!/usr/bin/python
# -*- coding: utf-8 -*-
import re
import urllib2
import json
import time
import sys
from BD_connect.connect_bd import get_json
from config.setting import Setting
'''
About:
This module is a connector that connects any wemo switch to the
Building DepotV3.1 with the help of the bd connect program

Configuration:
Enter the local IP address of your WeMo Switch in the json file in config
folder.You may have to check your router to see what local IP is
assigned to the WeMo.It is recommended that you assign a static local IP to
the WeMo to ensure the WeMo is always at that address.To run the code type
"python sens_wemo.py". 
'''
class wemo_sense:
        '''Class defintion of wemo_sense to send SOAP calls to
        the Wemo Switch to perform various operations'''
        ports = [49153, 49152, 49154, 49151, 49155]

        def __init__(self):
                """Initialises the IP of the Wemo Switch"""
                wemo_cred=Setting("wemo")
                self.ip = wemo_cred.setting["ip"]
        
        def energy_info(self):
                '''Obtains the energy info from the wemo which is in the format
                   1|1457|2487|9042|34794|21824|29|293|424|137.0|8000
                        1. State (0 = off, 1 = on)
                        2. Average power (W)
                        3. Instantaneous power (mW)
                        4. Energy used today in mW-minutes
                        5. Energy used over past two weeks in mW-minutes. '''
                
                res=self._send('Get','energy').split('|')
                edata={'status':res[0],'avg_power':res[7],
                       'instantaneous_power':res[8],'avg_energy_today':res[9],
                       'avg_energy_2weeks':res[10]}
                return edata
        
        def _send(self, method, obj, value=None):
                '''
                        Send request over various wemo ports and since we cannot
                        guarantee that wemo accepts request over a single port.
                        Args as data:
                                        method: Set/Get the state of Wemo
                                        obj   : object of the wemo state
                                        value : 0/1 to set the state 
                        Returns:
                                {
                                        "success": "True"
                                        "HTTP Error 400": "Bad Request"
                                }
                                           
                '''
                
                if obj=='energy':
                        '''Headers and body of xml to obtain device
                           energy information'''
                        body_xml='''<?xml version="1.0" encoding="utf-8"?>
                        <s:Envelope \
                        xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"\
                        s:encodingStyle="http://schemas.xmlsoap.org/soap/\
                        encoding/">
                        <s:Body>
                        <u:GetInsightParams \
                        xmlns:u="urn:Belkin:service:insight:1">
                        <InsightParams></InsightParams>
                        </u:GetInsightParams></s:Body>
                        </s:Envelope>'''
                        header_xml={
                        "Accept":"",
                        "Content-Type": "text/xml; charset=\"utf-8\"",
                        "SOAPACTION": "\"urn:Belkin:service:insight:1\
                        #GetInsightParams\""
                        }
                
                for port in self.ports:
                        result = self._try_send(self.ip, port,\
                                                body_xml, header_xml, obj)
                        if result is not None:
                                self.ports = [port]
                        return result
                raise Exception("TimeoutOnAllPorts")
        
        
        def _try_send(self, ip, port, body, header, data):
                '''
                        Send the Request to the Wemo Switch
                        Args as data:
                                        ip : ip address of the wemo
                                        port: port on which wemo accepts request
                                        header: header of the Soap request
                                        body: body of the Soap request
                                        data: 0/1 to switch on/off

                       Returns:
                                {
                                        Energy information or Status of wemo
                                        based on the request made
                                        or
                                        "HTTP Error 400": "Bad Request"

                                } 
                '''
                try:
                        url='http://%s:%s/upnp/control/insight1'\
                             % (ip, port)
                        request = urllib2.Request(url,body,header)
                        print "request: ",request
                        data= urllib2.urlopen(request,None,5).read()
                        regex=r'\<InsightParams\>(.*)\</InsightParams\>'
                        params = re.search(regex,data).group(1)
                        return params
                
                except Exception as e:
                        print str(e)
                        return None
                        
        def _extract(self, response, name):
                '''Extract information from the response'''
                exp = '<%s>(.*?)<\/%s>' % (name, name)
                g = re.search(exp, response)
                if g:
                        return g.group(1)
                return response

def get_devicedata():
        '''Get the device data information uncomment any of these to make
           work if device is connected retrieve device information in the
           format"status=switch.energyinfo()"
        '''
        wemo_cred=Setting("wemo")
        mac_id = wemo_cred.setting["mac_id"]
        switch = wemo_sense()
        edata=switch.energy_info()
        data={'sensor_data':{}}
        data['sensor_data'].update(edata)
        data['sensor_data'].update({"mac_id":mac_id})

def main(arguments):
        '''
        Accept the command to either read or actuate the Wemo Switch.

                Returns:
                                If the args is to read energy data from Wemo
                                {
                                    "success": "True" 
                                    "HTTP Error 400": "Bad Request"
                                }
                                If the args is to Actuate the Wemo Switch, then
                                {on/off : success} else
                                {"Device Not Found/Error in fetching data"}       
        '''
        global status,data
        cmd=arguments[1]
        switch = wemo_sense()
        try:
                get_devicedata()
        except Exception as e:
                print "Device Not Found/Error in fetching data"
                exit(0)
                
        '''Posts json object information to BD_Connect in this format
           data={"sensor_data":{<all sensor data>},
           "client_data":{<all client data>}}'''
        try:
                print get_json(json.dumps(data))
                print "Response from bd_connnect.py"
        except Exception as e:
                print e
    
if __name__ == "__main__":
        main(sys.argv)
