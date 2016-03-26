#!/usr/bin/python
import json
import requests
from config.setting import Setting

"""
About:
This module is a connector that connects various sensors to the Building DepotV3.1
Configuration:
Enter the Url of the Building Depot(BD) where its being hosted.
This Program requires the sensor connector program to send its sensor data in the
JSON format
data={
"sensor_data":
{
  <all sensor data>
 }
}
Working:
Writes sensor data of the sensor to the Building Depot
Accept Actuation information for the sensor from Building Depot
"""

"""Class object has access to all function to create new sensors and
update the sensor values."""


class BdConnect:
    def __init__(self, data):
        """Initialises the sensor data and client data of the sensors"""
        bdcredentials = Setting("bd_setting")
        self.data = bdcredentials.setting
        self.sensor_data = json.loads(data)['sensor_data']
        self.data["mac_id"] = self.sensor_data["mac_id"]
        self.sensor_data.pop("mac_id")
        self.url = bdcredentials.setting["url"]
        self.metadata = []
        self.common_data = []

    def get_oauth_token(self):
        """Obtains the oauth token of the user from Building Depot

            Returns:
                    Oauth token of the user
        """
        url = self.url + "/oauth/access_token/client_id=" + self.data['client_id'] + \
              "/client_secret=" + self.data['client_key']
        response = requests.get(url).json()
        self.oauth_token = response['access_token']
        self.header = {"Authorization": "bearer " + self.oauth_token}
        return self.oauth_token

    def get_sensor_list(self, call_type):
        """Gets the sensor list from Building depot

            Args :
                    call_type: "all_sensors":- Fetches all the list of sensors
                                "None":- Fetches sensor list based on the metadata
            Returns:
                    sensor List
        """
        if call_type == 'all_sensors':
            url = self.url + "/api/list"
            response = json.loads(requests.get(url, headers=self.header).text)
        else:
            url = self.url + "/api/mac_id=" + call_type + "/metadata"
            response = json.loads(requests.get(url, headers=self.header).text)
        return response

    def check_sensor(self):
        """Verification of the device with valid mac_id
            Returns:
                    True : if valid mac_id
                    False: if invalid mac_id
        """
        sensor_list = str(self.get_sensor_list('all_sensors'))
        if self.data['mac_id'] in sensor_list:
            return True
        else:
            return False

    def create_metadata(self):
        """Create common metadata for the sensor points."""
        temp = {}
        for key, val in self.sensor_data.iteritems():
            temp['name'] = key
            temp['value'] = val
            self.metadata.append(temp)
            temp = {}

        for key, val in self.data.iteritems():
            check = ['client_id', 'client_key', 'device_id', 'name', \
                     'identifier', 'building']
            if key not in check:
                temp['name'] = key
                temp['value'] = val
                self.common_data.append(temp)
                temp = {}

        self.metadata += self.common_data

    def _add_meta_data(self, call_type, uuid):
        """Updates the meta data of the sensor wrt to the uuid
        and sensor points
        Args :
                        call_type: "rest_post" updates the meta data
                                   "None" updates the meta data of the
                                    specific sensor points
                        uuid     :  uuid of the sensor point to updated

        Returns:
                        {
                                "success": "True" 
                                "HTTP Error 400": "Bad Request"
                        }
        """
        if call_type == "rest_post":
            payload = {'data': self.metadata}
        else:
            dic = {"name": call_type, "value": self.sensor_data[call_type]}
            payload = {"data": self.common_data + [dic]}
        headers = self.header
        headers['content-type'] = 'application/json'
        url = self.url + '/api/sensor/' + uuid + '/metadata'
        return requests.post(url, data=json.dumps(payload), \
                             headers=headers).json()

    def create_sensor_points(self):
        """ Create sensor points of a particular sensor and calls
            _add_meta_data() to add the metadata values
            Returns:
            {
                "success": "True" 
                "HTTP Error 400": "Bad Request"
            }
        """
        identifier = self.data['identifier']
        building = self.data['building']
        name = self.data['name']
        response = ''
        for key, val in self.sensor_data.iteritems():
            url = self.url + '/api/sensor_create/name=%s/identifier=%s/building=%s' \
                             % (key + '_' + name, identifier, building)
            iresponse = requests.post(url, headers=self.header).json()
            temp = json.dumps(self._add_meta_data(key, iresponse['uuid']))
            response = response + temp
            response = response + "\n" + key + ' :' + json.dumps(iresponse)
        return response

    def rest_post(self):
        """Get the data of the sensor and calls _add_meta_data()
            to add the metadata values
            Returns:
            {
                "success": "True" 
                "HTTP Error 400": "Bad Request"
            }
        """
        response = ''
        sensor_list = self.get_sensor_list(self.data['mac_id'])['data']
        # obtain the uuid of the sensor_points of the sensor and update
        for key1, val1 in sensor_list.iteritems():
            for key, val in self.sensor_data.iteritems():
                if key + '_' + self.data['name'] == sensor_list[key1]["source_name"]:
                    uuid = sensor_list[key1]["name"]
                    response = self._add_meta_data(key, uuid)
        return "Metadata updated\n", response


def get_json(data):
    """
    Function obtains a json object from sensor connector in the format
    Args :
        {
            "sensor_data":{
                            <all sensor data>
                            }
        }

    Returns:
        {
            "success": "True" 
            "HTTP Error 400": "Bad Request"
        }
    """
    info = BdConnect(data)
    # Check Valid Client id and Client key
    if 'Invalid credentials' not in info.get_oauth_token():
        # Client_id and details are correct and token Generate access token
        print'Client id Verified'
        """Function to create the meta data to be updated/created
            on Building Depot"""
        info.create_metadata()
        check = ('name', 'identifier', 'building')
        if set(check).issubset(info.data):
            """Check if UUID is given, if so update metadata else
                create a new sensor and add metadata"""
            if not info.check_sensor():
                return info.create_sensor_points()
            else:
                return info.rest_post()
        else:
            return """Provide valid source_name,source_identifier,
                    email and building values"""

    else:
        return 'Please Enter correct client_id/client_key Details'