import requests
import warnings
import json
import sys

global identity,url
url="https://api.lifx.com/v1/lights/"

class LifxActuator:
    """Class definition of lifx to send API calls to
        the Lifx Bulb to perform various operations"""

    def __init__(self,identity):
        """Initialises the Client token and obtains the raw_data
            of the devices"""
        self.getclienttoken ="c1a43d5aea60179a295f3c5d791c1c035730327a8c055c51cb1d669b24fb054b"
        self._DEVICE_REQ =("https://api.lifx.com/v1/lights/"+identity)
	#print self._DEVICE_REQ

    def switch(self, cmd):
        """Switch on/off the bulb
            Args :
                            'on' : switch on the bulb
                            'off': switch off the bulb
        """
        payload = {"power": cmd}
	#print payload
        print self.post_request((self._DEVICE_REQ+"/state"), payload)

    def switch_state(self, cmd):
        """Switch various states of the bulb
            Args :
                          Eg: {
                            "power": # "On/Off"
                            "color": # "blue saturation:0.5",
                            "brightness": #0.5,
                            "duration": #5
                            }

        """
        payload = cmd
        print self.post_request(self._DEVICE_REQ+'/state', payload)
    def post_request(self, url, params):
        """Posts the actuation requests to the lifx bulb
           Args :
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

        """
        headers = {
            "Authorization": "Bearer %s" % self.getclienttoken
        }
        resp = requests.put(url, data=params, headers=headers).json()
        return resp

    def post_breathe(self,params):
	headers = {
    "Authorization": "Bearer "+self.getclienttoken}
 
        data = {
    "period": 2,
    "cycles": 5,
    "color": "green",
}

        response = requests.post('https://api.lifx.com/v1/lights/all/effects/breathe', data=data, headers=headers)
	print response
def actuate_lifx(iden,new_state):
    """ Accepts the command to either read or actuate the Lifx Bulb.

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
"""
    identity=iden
    new_state=(new_state)
    #print new_state
    try:
       devlist = LifxActuator(identity)
       print identity,new_state
       if(len(new_state)<=3):
	 print "less than 3"
         devlist.switch(new_state)
       elif "period" in new_state:
	 print "here"
	 devlist.post_breathe(new_state)
       elif "color" in new_state:
	 print "more than three"
         devlist.switch_state(new_state)
    except Exception as e:
       print "Device Not Found/Error in fetching data"


if __name__ == "__main__":
   senda = { 'power' : 'on' , 'color':"red saturation:0.5" , 'brightness' : 0.6,'duration' : 1}
   send={'period':2,'cycles':100,'color':'green'}
   send=json.dumps(send)
   #print send
   actuate_lifx("all",send)
