#!/usr/bin/python
# -*- coding: utf-8 -*-
import re
import time
import urllib2
import json
import time
import sys
from bd_connect.connect_bd import get_json
from config.setting import Setting

"""
About:
This module is a connector that connects any wemo switch to the
Building DepotV3.1 with the help of the bd_connect program

Configuration:
Enter the local IP address of your WeMo Switch in the json file in config
folder.You may have to check your router to see what local IP is
assigned to the WeMo.It is recommended that you assign a static local IP to
the WeMo to ensure the WeMo is always at that address.To run the code type
"python sens_wemo.py" on the terminal
"""
global status

class WemoSensor:
    """Class definition of WemoSensor to send SOAP calls to
        the Wemo Switch to perform various operations"""
    ports = [49153, 49152, 49154, 49151, 49155]

    def __init__(self):
        """Initialises the IP of the Wemo Switch"""
        wemo_cred = Setting("wemo")
        self.ip = wemo_cred.setting["ip"]

    def energy_info(self):
        """Obtains the energy info from the wemo which is in the format
                   1|1457|2487|9042|34794|21824|29|293|424|137.0|8000
                        1. State (0 = off, 1 = on)
                        2. Average power (W)
                        3. Instantaneous power (mW)
                        4. Energy used today in mW-minutes
                        5. Energy used over past two weeks in mW-minutes. """

        res = self._send('Get', 'energy').split('|')
        edata = {'status': res[0], 'avg_power': res[7],
                 'instantaneous_power': res[8], 'avg_energy_today': res[9],
                 'avg_energy_2weeks': res[10]}
        return edata

    def _send(self, obj, value=None):
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

        if value == 'energy':
            """Headers and body of xml to obtain device
                           energy information"""
            body_xml = """<?xml version="1.0" encoding="utf-8"?>
                        <s:Envelope \
                        xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"\
                        s:encodingStyle="http://schemas.xmlsoap.org/soap/\
                        encoding/">
                        <s:Body>
                        <u:GetInsightParams \
                        xmlns:u="urn:Belkin:service:insight:1">
                        <InsightParams></InsightParams>
                        </u:GetInsightParams></s:Body>
                        </s:Envelope>"""
            header_xml = {
                "Accept": "",
                "Content-Type": "text/xml; charset=\"utf-8\"",
                "SOAPACTION": "\"urn:Belkin:service:insight:1\
                        #GetInsightParams\""
            }

        for port in self.ports:
            result = self._try_send(self.ip, port, \
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
            url = 'http://%s:%s/upnp/control/insight1' \
                  % (ip, port)
            request = urllib2.Request(url, body, header)
            print "request: ", request
            wemo_data = urllib2.urlopen(request, None, 5).read()
            regex = r'\<InsightParams\>(.*)\</InsightParams\>'
            params = re.search(regex, wemo_data).group(1)
            return params

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

    def get_device_data(self):
        """Get the device data information uncomment any of these to make
                   work if device is connected retrieve device information in the
                   format"status=switch.energyinfo()"
                """
        wemo_cred = Setting("wemo")
        mac_id = wemo_cred.setting["mac_id"]
        edata = self.energy_info()
        global data
	data = {'sensor_data': {}}
        data['sensor_data'].update(edata)
        data['sensor_data'].update({"mac_id": mac_id})	


class WemoActuator:
    """Class definition of WemoActuator to send SOAP calls to
        the Wemo Switch to perform various operations"""
    OFF_STATE = '0'
    ON_STATES = ['1', '8']
    ip = None
    ports = [49153, 49152, 49154, 49151, 49155]

    def __init__(self):
        """Initialises the IP of the Wemo Switch"""
        wemo_cred = Setting("wemo")
        self.ip = wemo_cred.setting["ip"]
    def toggle(self):
        """Toggle the switch
                   Switch status is on then switch off else
                   if the switch status is off switch on"""
        wemo_status = self.status()
        if wemo_status in self.ON_STATES:
            result = self.off()
            result = 'WeMo is now off.'
        elif wemo_status == self.OFF_STATE:
            result = self.on()
            result = 'WeMo is now on.'
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
        return '<u:%s xmlns:u="urn:Belkin:service:basicevent:1">' \
               '<%s>%s</%s></u:%s>' % (method, obj, value, obj, method)

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
        # print "body: ", body_xml
        header_xml = self._get_header_xml(method, obj)
        # print "Header",header_xml

        for port in self.ports:
            result = self._try_send(self.ip, port, \
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

            url = 'http://%s:%s/upnp/control/basicevent1' \
                  % (ip, port)
            request = urllib2.Request(url)
            print "request: ", request
            request.add_header('Content-type', \
                               'text/xml; charset="utf-8"')
            request.add_header('SOAPACTION', header)
            request_body = '<?xml version="1.0" encoding="utf-8"?>'
            request_body += '<s:Envelope xmlns:s=' \
                            '"http://schemas.xmlsoap.org' \
                            '/soap/envelope/"s:encodingStyle' \
                            '="http://schemas.xmlsoap.org/soap' \
                            '/encoding/">'
            request_body += '<s:Body>%s</s:Body>' % body
            request_body += '</s:Envelope>'
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

    def output(self, message):
        print message


def main(arguments):
    """
        Accept the command to either read or actuate the Wemo Switch.
        Args as Data:
                        'r': Read the energy data from the Switch and
                        update the metadata on the Building Depot.
                        'w': Actuate the Wemo Switch to switch on
                             and off.
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
    cmd = 'r'
    if 'r' == cmd:
        switch = WemoSensor()
        try:
            switch = WemoSensor()
            switch.get_device_data()
        except Exception as e:
            print "Device Not Found/Error in fetching data"
            print e
            exit(0)
        """Posts json object information to BD_Connect in this format
                   data={"sensor_data":{<all sensor data>},
                   "client_data":{<all client data>}}"""
        try:
            print data
            get_json(json.dumps(data),'wemo')
            print "Response from bd_connnect.py"
        except Exception as e:
            print e,"Please provide file name"
    elif 'w' == cmd:
	switch = WemoActuator()
        try:
            # Uncomment any of these to actuate Wemo Switch
            # switch.output(switch.on())
            # output(switch.off())
              switch.output(switch.toggle())
            # output(switch.status())
        except Exception as e:
            print "Device Not Found"
            print str(e)


if __name__ == "__main__":
  while True:  
    time.sleep(2)
    main('r')
