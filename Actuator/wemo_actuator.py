#!/usr/bin/python
# -*- coding: utf-8 -*-
import re
import urllib2
import json
import time
import sys
from BD_connect.connect_bd import get_json
from config.setting import Setting
"""
About:
This module is a connector that connects any wemo switch to the
Building DepotV3.1 with the help of the bd connect program

Configuration:
Enter the local IP address of your WeMo Switch in the json file in config
folder.You may have to check your router to see what local IP is
assigned to the WeMo.It is recommended that you assign a static local IP to
the WeMo to ensure the WeMo is always at that address.To run the code type
"python sens_wemo.py " To Actuate the Wemo Switch
"""

class wemo_actuator:
        """Class defintion of wemo_actuator to send SOAP calls to
        the Wemo Switch to perform various operations"""
        OFF_STATE = '0'
        ON_STATES = ['1', '8']
        ip = None
        ports = [49153, 49152, 49154, 49151, 49155]

        def __init__(self):
                """Initialises the IP of the Wemo Switch"""
                wemo_cred=Setting("wemo")
                self.ip = wemo_cred.setting["ip"]
                
        def toggle(self):
                """Toggle the switch
                   Switch status is on then switch off else
                   if the switch staus is off switch on"""
                status = self.status()
                if status in self.ON_STATES:
                        result = self.off()
                        #result = 'WeMo is now off.'
                elif status == self.OFF_STATE:
                        result = self.on()
                        #result = 'WeMo is now on.'
                else:
                        raise Exception("UnexpectedStatusResponse")
                return result    

        def on(self):
                """Switch on the wemo switch"""
                return self._send('Set', 'BinaryState', 1)
          
        def off(self):
                """Switch off the wemo switch"""
                return self._send('Set', 'BinaryState', 0)
        
        def status(self):
                """Get the status of switch"""
                return self._send('Get', 'BinaryState')
        
        def name(self):
                """Get the name of the switch"""
                return self._send('Get', 'FriendlyName')

        def signal(self):
                """Get the Signal Strength of the wemo switch"""
                return self._send('Get', 'SignalStrength')
        
        def _get_header_xml(self, method, obj):
                """Defines Header of SOAP request
                   Args as data:
                                   method: Set/Get the state of Wemo
                                   obj   : object of the wemo state
                   Returns:
                                   Header of the Soap Request
                """
                method = method + obj
                return '"urn:Belkin:service:basicevent:1#%s"' % method
   
        def _get_body_xml(self, method, obj, value=0):
                """Defines Body of the SOAP request
                   Args as data:
                                   method: Set/Get the state of Wemo
                                   obj   : object of the wemo state
                   Returns:
                                   Body of the Soap Request
                """
                method = method + obj
                return '<u:%s xmlns:u="urn:Belkin:service:basicevent:1">'\
                       '<%s>%s</%s></u:%s>'%(method, obj, value, obj, method)
        
        def _send(self, method, obj, value=None):
                """
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
                                           
                """
                body_xml = self._get_body_xml(method, obj, value)
                #print "body: ", body_xml
                header_xml = self._get_header_xml(method, obj)
                #print "Header",header_xml
                
                for port in self.ports:
                        result = self._try_send(self.ip, port,\
                                                body_xml, header_xml, obj)
                        if result is not None:
                                self.ports = [port]
                        return result
                raise Exception("TimeoutOnAllPorts")
        
        
        def _try_send(self, ip, port, body, header, data):
                """
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
                """
                try:

                        url='http://%s:%s/upnp/control/basicevent1'\
                             %(ip, port)
                        request = urllib2.Request(url)
                        print "request: ",request
                        request.add_header('Content-type',\
                                           'text/xml; charset="utf-8"')
                        request.add_header('SOAPACTION', header)
                        request_body='<?xml version="1.0" encoding="utf-8"?>'
                        request_body+='<s:Envelope xmlns:s='\
                                '"http://schemas.xmlsoap.org'\
                                '/soap/envelope/"s:encodingStyle'\
                                '="http://schemas.xmlsoap.org/soap'\
                                '/encoding/">'
                        request_body+='<s:Body>%s</s:Body>'%body
                        request_body+='</s:Envelope>'
                        request.add_data(request_body)                                
                        result = urllib2.urlopen(request, timeout=3)
                        return self._extract(result.read(), data)
                except Exception as e:
                        print str(e)
                        return None
                        
        def _extract(self, response, name):
                """Extract information from the response"""
                exp = '<%s>(.*?)<\/%s>' % (name, name)
                g = re.search(exp, response)
                if g:
                        return g.group(1)
                return response

def output(message):
        print message

def main(arguments):
        """
        Accept the command to actuate the Wemo Switch.
                Returns:
                                If the args is to read energy data from Wemo
                                {
                                    "success": "True" 
                                    "HTTP Error 400": "Bad Request"
                                }
                                If the args is to Actuate the Wemo Switch, then
                                {on/off : success} else
                                {"Device Not Found/Error in fetching data"}       
        """
        global status,data
        cmd=arguments[1]
        switch = wemo_actuator()
        try:
                #Uncomment any of these to actuate Wemo Switch
                #output(switch.on())
                #output(switch.off())
                output(switch.toggle())
                #output(switch.status())
        except Exception as e:
                print str(e)
    
if __name__ == "__main__":
        main(sys.argv)
