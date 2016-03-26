#!/usr/bin/python
# -*- coding: utf-8 -*-
import requests
import warnings
import json
import sys
from bd_connect.connect_bd import get_json
from config.setting import Setting

warnings.filterwarnings("ignore")
"""
About:
This module is a connector that connects any Lifx Bulb to the
Building DepotV3.1 with the help of the bd connect program.

Configuration:
To be able to have the program accessing,reading and actuating your Lifx bulb data,
you have to register yourself at https://community.lifx.com/. After registering,
All you have to do is go to https://cloud.lifx.com/settings and click on
generate new token to give it a name and you will be provided a token through
you will be able to access lifx servers.Enter the information of your
Lifx Device in the json file in config folder.
"""


class LifxActuator:
    """Class definition of lifx to send API calls to
        the Lifx Bulb to perform various operations"""

    def __init__(self):
        """Initialises the Client token and obtains the raw_data
            of the devices"""
        lifx_cred = Setting("lifx")
        self.getclienttoken = lifx_cred.setting["client_auth"]["_CLIENT_TOKEN"]
        self._DEVICE_REQ = lifx_cred.get("url")["_DEVICE_REQ"]

    def switch(self, cmd):
        """Switch on/off the bulb
            Args :
                            'on' : switch on the bulb
                            'off': switch off the bulb
        """
        payload = {"power": cmd}
        print self.post_request(self._DEVICE_REQ, payload)

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
        print self.post_request(self._DEVICE_REQ, payload)

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


class LifxSensor:
    """Class definition of lifx to send API calls to
        the Lifx Bulb to perform various operations
    """

    def __init__(self):
        """Initialises the Client token and obtains the raw_data
            of the devices
        """
        lifx_cred = Setting("lifx")
        self.getclienttoken = lifx_cred.setting["client_auth"]["_CLIENT_TOKEN"]
        self.rawData = self.get_request(lifx_cred.get("url")["_DEVICELIST_REQ"])

    def station_data(self):
        """
        Obtains the Lifx bulb data and writes them to the Building depot
        Returns:
                {
                    "success": "True" 
                    "HTTP Error 400": "Bad Request"
                }
        """
        global mac_id
        for device in self.rawData:
            lifx_data = {}
            mac_id = device["id"]
            name = device["label"].replace(" ", "_")
            for k in device["color"].keys():
                lifx_data[k + "_" + name] = device["color"][k]
            lifx_data["brightness_" + name] = device["brightness"]
            lifx_data["status_" + name] = device["power"]
            return self.post_to_bd(lifx_data)

    def post_to_bd(self, station_data):
        """
            Format of the JSON Object to be sent to bd_connect.py.
            sensor_data contains all information from sensor to be
            Read and sensor_points to be created in accordance with that.
            client_data contains all information about client_id,client_keyetc
            for authentication
            data={"sensor_data":{}}
            Args :
                            {<Lifx bulb data>,<brightness>, <hue> etc.}
            Returns:
                            {
                                "success": "True" 
                                "HTTP Error 400": "Bad Request"
                            }
        """
        global mac_id
        print station_data
        data = {'sensor_data': {}}
        data['sensor_data'].update(station_data)
        data['sensor_data'].update({"mac_id": mac_id})
        try:
            resp = get_json(json.dumps(data))
        except Exception as e:
            print e
        return resp

    def get_request(self, url):
        """
            Get Status of the Bulb and the device list of Lifx bulbs
            Args :
                       url   : Url of lifx bulb
            Returns:
                    Lifx bulb device list and status
                
        """
        headers = {
            "Authorization": "Bearer %s" % self.getclienttoken
        }
        resp = requests.get(url, headers=headers).json()
        return resp


def main(args):
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
                         OR
                         '': Empty to Write data to the Building depot
        Returns:
                        If the No args read status and write data
                        to building depot
                        {
                            "success": "True"
                            "HTTP Error 400": "Bad Request"
                        }

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
    """
    from sys import exit, stderr
    if len(args) == 1:
        devlist = LifxSensor()
        if not devlist.getclienttoken:
            stderr.write("Please Enter the Client token from Lifx in\
                            the config file")
            exit(1)
        try:
            resp = devlist.station_data()  # Get the Lifx Bulbs data and updates the BD
            print resp

        except Exception as e:
            print "Device Not Found/Error in fetching data"
            exit(0)
    else:
        try:
            devlist = LifxActuator()
            if len(args) == 2:
                devlist.switch(args[1])
            elif len(args) > 2:
                print args, len(args)
                state = {"power": args[1], "color": args[2] + " " + args[3],
                         "brightness": args[4], "duration": args[5]}
                devlist.switch_state(state)
        except Exception as e:
            print "Device Not Found/Error in fetching data"
            exit(0)


if __name__ == "__main__":
    main(sys.argv)