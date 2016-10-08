import re
import urllib2
import json
import time
import sys
class WemoActuator:
    """Class definition of WemoActuator to send SOAP calls to
        the Wemo Switch to perform various operations"""
    OFF_STATE = '0'
    ON_STATES = ['1', '8']
    ip = None
    ports = [49153, 49152, 49154, 49151, 49155]

    def __init__(self,identity):
        """Initialises the IP of the Wemo Switch"""
        #wemo_cred = Setting("wemo")
        #self.ip = wemo_cred.setting["ip"]
	self.ip = identity
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

def Actuate_wemo(identity,new_state):
    switch = WemoActuator(identity)
    try:
            # Uncomment any of these to actuate Wemo Switch
	    if(new_state=="0"):  
            	switch.output(switch.off())
	    elif(new_state=="1"):            
		switch.output(switch.on())
    except Exception as e:
            print "Device Not Found"
            print str(e)

def print_this():
    print "Hello I am In Wemo"

if __name__=="__main__":
    print "I have been called"
    print_this()
