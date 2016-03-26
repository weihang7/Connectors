import json, time
from urllib import urlencode
import urllib2
from bd_connect.connect_bd import get_json
from config.setting import Setting

"""
About:
This module is a connector that connects any Netatmo Weather station to the
Building DepotV3.1 with the help of the bd connect program.

Configuration:
To be able to have the program accessing your netatmo data, you have
to register your program as a Netatmo app in your Netatmo account at
https://auth.netatmo.com/en-US/access/signup. All you have
to do is to give it a name and you will be returned a client_id and
secret that your app has to supply to access netatmo servers.Enter the
information of your Netatmo Device in the json file in config folder.
"""


class ClientAuth:
    """
   Class definition of Netatmo to request authentication and keep access
   token available through token method.Renew it automatically if necessary
    """

    def __init__(self):
        """
        Initialises the Client Id and Client key and obtains the Access
        token of the netatmo device

        Args as Data:
                clientid: #netatmo id of the user
                clientsecret: #netatmo secret key of the user
                username: #username used in netatmo login
                password: #password used in netatmo login
        """
        netatmo_cred = Setting("netatmo")
        self.clientId = netatmo_cred.setting['client_auth']['_CLIENT_ID']
        self.clientSecret = netatmo_cred.setting['client_auth']['_CLIENT_SECRET']
        self.username = netatmo_cred.setting['client_auth']['_USERNAME']
        self.password = netatmo_cred.setting['client_auth']['_PASSWORD']
        postparams = {
            "grant_type": "password",
            "client_id": self.clientId,
            "client_secret": self.clientSecret,
            "username": self.username,
            "password": self.password,
            "scope": "read_station"
        }
        self._AUTH_REQ = netatmo_cred.get("url")["_AUTH_REQ"]
        response = get_request(self._AUTH_REQ, postparams)
        self._clientId = self.clientId
        self._clientSecret = self.clientSecret
        self._accessToken = response['access_token']
        self.refreshToken = response['refresh_token']
        self._scope = response['scope']
        self.expiration = int(response['expire_in'] + time.time())

    @property
    def access_token(self):
        """
        Renew the access token if the token is expired

        Returns:
                New Access token
        """
        if self.expiration < time.time():  # Token should be renewed

            postparams = {
                "grant_type": "refresh_token",
                "refresh_token": self.refreshToken,
                "client_id": self._clientId,
                "client_secret": self._clientSecret
            }
            response = get_request(self._AUTH_REQ, postparams)

            self._accessToken = response['access_token']
            self.refreshToken = response['refresh_token']
            self.expiration = int(response['expire_in'] + time.time())

        return self._accessToken


class DeviceList:
    """
   Class definition of Netatmo to obtain the Natatmo station data and
   update the data in the Building depot.

    """

    def __init__(self, authdata):
        """
            Initilize the auth token and obtain the device modules data
            of Netatmo
            Args as data:
                            "authdata": class object of ClientAuth provides
                                        access token.
                                        
        """
        self.getAuthToken = authdata.access_token
        postparams = {
            "access_token": self.getAuthToken,
            "app_type": "app_station"
        }
        url_cred = Setting("netatmo")
        _DEVICELIST_REQ = url_cred.get("url")["_DEVICELIST_REQ"]
        response = get_request(_DEVICELIST_REQ, postparams)
        # print "\nDeviceList: ",resp
        self.rawData = response['body']
        self.stations = {d['_id']: d for d in self.rawData['devices']}
        # print  "\nStations: ",self.stations
        self.modules = {m['_id']: m for m in self.rawData['modules']}
        # print  "\nModules: ",self.modules
        self.default_station = list(self.stations.values())[0]['station_name']
        # print "\nSelf Station: ",self.default_station

    def station_by_name(self, station=None):
        """
            Find the Netatmo station data by name if none given finds all the
            data of the netatmo stations
            Args as data:
                            "station": #Station name
        """
        if not station:
            station = self.default_station
        for i, s in self.stations.items():
            if s['station_name'] == station:
                return self.stations[i]
        return None

    def get_module_data(self, module_id):
        """
            Obtain the Netatmo outdoor module data 
            Args as data:
                            "module_id": #module_id of the outdoor module
            Returns:
                            {
                             u'min_temp_NAModule1': #minimum temperature of
                                                     outdoor module,
                             u'Humidity_NAModule1': #Humidity of outdoor module,
                             u'Temperature_NAModule1': #current temp of outdoor
                                                        module,
                             u'max_temp_NAModule1': #maximum temperature of
                                                     outdoor module
                            }
        """
        module_data = self.modules[module_id]['dashboard_data']
        for k in ('date_max_temp', 'date_min_temp', 'time_utc'):
            module_data.pop(k, None)
        for i in module_data.keys():
            module_data[i + "_" + self.modules[module_id]['type']] = module_data.pop(i)
        return module_data

    def get_stations_data(self, station=None):
        """
            Obtain the Netatmo indoor module data and form common dict of
            all the module data
            
            Args as data:
                            "station": #station name of the Base station
            Returns:
                            {
                                u'Noise_indoor': #noise in decibels
                                                  of indoor module,
                                u'max_temp_indoor': #maximum temperature of
                                                     indoor module, 
                                u'Temperature_indoor': #current temp of indoor
                                                        module,
                                u'Pressure_indoor': #pressure in pascal of
                                                     indoor module,
                                u'Humidity_indoor': #humidity of the indoor
                                                     module,
                                u'CO2_indoor': #Co2 levels of indoor
                                                module,
                                u'min_temp_indoor': #minimum temperature of
                                                     indoor module,
                                u'AbsolutePressure_indoor': #absolute pressure
                                                            of indoor module
                            }
        """
        if not station:
            station = self.default_station
        s = self.station_by_name(station)
        global mac_id
        # obtain the Netatmo indoor main module data
        netatmo_data = s['dashboard_data']
        mac_id = s['_id']
        for k in ('date_max_temp', 'date_min_temp', 'time_utc'):
            netatmo_data.pop(k, None)
        for i in netatmo_data.keys():
            netatmo_data[i + "_indoor"] = netatmo_data.pop(i)

        # obtain the Netatmo other outdoor module data
        module_data = {}
        for n in s['modules']:
            module_data.update(self.get_module_data(n))

        netatmo_data.update(module_data)
        return netatmo_data

    def post_to_bd(self, stationdata):
        """
        Post json object information to BD_Connect in this format
        data={"sensor_data":{<all sensor data>}}

        Args as data:
                        {<netatmo station data>}
        Returns:
                        {
                            "success": "True" 
                            "HTTP Error 400": "Bad Request"
                        }
        """
        data = {'sensor_data': {}}
        data['sensor_data'].update(stationdata)
        data['sensor_data'].update({"mac_id": mac_id})
        response = get_json(json.dumps(data))
        return response


def get_request(url, params):
    """
    Get the Netatmo station data
    Args as data:
               url   : Url of Netatmo station data
    Returns:
                Netatmo device and module list
            
    """

    params = urlencode(params)
    headers = {"Content-Type": "application/x-www-form-urlencoded;charset=utf-8"}
    req = urllib2.Request(url=url, data=params, headers=headers)
    response = urllib2.urlopen(req).read()
    return json.loads(response)


if __name__ == "__main__":
    """
    Reads the netatmo station data and writes it to the building depot.

    Returns:
            Reads the data from Netatmo station
            {
                "success": "True"
                "HTTP Error 400": "Bad Request"
            }
            else
            {   "Error in Device Connection"
            }
    """
    from sys import exit, stderr

    try:
        auth = ClientAuth()  # Get authentication key
        if not auth.clientId or not auth.clientSecret or not auth.username \
                or not auth.password:
            stderr.write("Please Enter the Netatmo Clientid and ClientSecret")
            exit(1)

        devList = DeviceList(auth)  # Obtain the DEVICELIST
        netatmo_data = devList.get_stations_data()  # Get the Stations data
        try:
            resp = devList.post_to_bd(netatmo_data)  # Send Data to the BuildingDepot
            print "Response from connect_bd.py:\n", resp
        except Exception as e:
            print "Error in Sending data to connect_bd.py", e

    except Exception as e:
        print "Error in Device Connection", e
