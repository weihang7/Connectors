#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

This file is part of **python-openzwave** project https://github.com/OpenZWave/python-openzwave.
    :platform: Unix, Windows, MacOS X
    :sinopsis: openzwave wrapper

.. moduleauthor:: bibi21000 aka Sébastien GALLET <bibi21000@gmail.com>

License : GPL(v3)

**python-openzwave** is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

**python-openzwave** is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with python-openzwave. If not, see http://www.gnu.org/licenses.

"""

import sys, os
import resource
import openzwave
from openzwave.node import ZWaveNode
from openzwave.value import ZWaveValue
from openzwave.scene import ZWaveScene
from openzwave.controller import ZWaveController
from openzwave.network import ZWaveNetwork
from openzwave.option import ZWaveOption
import time
import requests
import json

device="/dev/ttyACM0"
local_url = 'http://127.0.0.1'
client_id = "Qxmb54cg2JcqGr7OFvdwsWPekX2nTmUljc7WJiXz"
client_secret = "ZoIzG4QRJnrGlYnaAjRcsObHx5AlPFesJMBOI89ufPapJanUoP"
building = "Gates-Hillman Complex"

class ZWaveSensor:
    def __init__(self):
        self.cs_url = local_url + ":81"
        self.ds_url = local_url + ":82"
        self.session = requests.Session()
        self.session.headers.update({'Authorization': 'Bearer ' + self.get_oauth_token()})
        self.session.verify = False

    def get_oauth_token(self):
        url = self.cs_url + '/oauth/access_token/client_id=' + client_id + '/client_secret=' + client_secret
        resp = requests.get(url).json()
        if resp['success']:
            print resp['access_token']
            return resp['access_token']

    def create_sensor(self, name, identifier, building):
        url = self.cs_url + '/api/sensor'
        data = {
                'data':{
                    'name': name,
                    'identifier': identifier,
                    'building': building
                }
        }
        resp = self.session.post(url, json=data).json()
        if resp['success'] == 'True':
            return resp['uuid']
        else:
            return False

    def sensor_lookup(self, source_id):
        url = self.cs_url + '/api/search'
        payload = {
                'data': {
                    'Building': building,
                    'Source_Identifier': source_id
                }
        }
        print json.dumps(payload)
        resp = self.session.post(url, json=payload).json()
        print resp
        if resp['success'] == 'True':
            return resp['result'][0]
        else:
            return False

    def update_metadata(self, uuid, metadata):
        url = self.cs_url + '/api/sensor/' + uuid + '/metadata'
        print metadata.items()
        resp = self.session.post(url, json={
            'data': [{
                'name': k,
                'value': v
            } for (k, v) in metadata.iteritems()]
        }).json()
        if resp['success'] == 'True':
            return True
        else:
            return False

    def _timeseries_write(self, sensor_data):
        url = self.ds_url + '/api/sensor/timeseries'
        payload = []
        for sensor in sensor_data:
            payload.append({
                'sensor_id': sensor['uuid'],
                'samples': [{
                    'time': time.time(),
                    'value': sensor['value']
                }]
            })
        resp = self.session.post(url, json=payload).json()
        if resp['success'] == 'True':
            return True
        else:
            return False

    def timeseries_write(self, sensor_data):
        for sensor in sensor_data:
            resp = self.sensor_lookup(sensor['sensor_id'])
            if not resp:
                sensor['uuid'] = self.create_sensor(sensor['sensor_name'], sensor['sensor_id'], building)
            else:
                sensor['uuid'] = resp['name']
            self.update_metadata(sensor['uuid'], sensor['metadata'])
        self._timeseries_write(sensor_data)

if __name__ == '__main__':
    conn = ZWaveSensor()
    mock_sensor_data = [{
            'sensor_id': 'Alexa:Roomba',
            'sensor_name': 'Alex Wei',
            'metadata':{
                'floor': '8',
                'type': 'hvac'
            },
            'value': 7
    }]
    conn.timeseries_write(mock_sensor_data)
    exit()
    #Define some manager options
    options = ZWaveOption(device, \
      config_path="./config", \
      user_path=".", cmd_line="")
    options.set_log_file("OZW_Log.log")
    options.set_append_log_file(False)
    options.set_console_output(False)
    options.set_save_log_level('Info')
    options.set_logging(False)
    options.lock()

    #Create a network object
    network = ZWaveNetwork(options, log=None)

    # Waiting for network awaked
    for i in range(0,300):
        if network.state>=network.STATE_AWAKED:
            break
        else:
            time.sleep(1.0)
    if network.state<network.STATE_AWAKED:
        exit()
    print("Network home id : {}".format(network.home_id_str))
    print("Controller node id : {}".format(network.controller.node.node_id))
    print("Controller node version : {}".format(network.controller.node.version))
    print("Nodes in network : {}".format(network.nodes_count))
    # Waiting for network ready
    for i in range(0,300):
        if network.state>=network.STATE_READY:
            break
        else:
            time.sleep(1.0)

    if not network.is_ready:
        exit()

    print("Nodes in network : {}".format(network.nodes_count))
    values = {}
    for node in network.nodes:
        # Uniquely identify device by controller + node id
        node_metadata = {
                'Name': network.nodes[node].name,
                'Manufacturer name / id': (network.nodes[node].manufacturer_name, network.nodes[node].manufacturer_id),
                'Product name / id / type': (network.nodes[node].product_name, network.nodes[node].product_id, network.nodes[node].product_type),
                "Version": network.nodes[node].version,
                "Command classes": network.nodes[node].command_classes_as_string,
                "Capabilities": network.nodes[node].capabilities,
                "Neighbors": network.nodes[node].neighbors,
                "Can sleep": network.nodes[node].can_wake_up()
        }
        sensor_data = {}
        for val in network.nodes[node].values :
            sensor_data[network.nodes[node].values[val].object_id] = {'metadata': {
                    'index': network.nodes[node].values[val].index,
                    'instance': network.nodes[node].values[val].instance,
                    'label':network.nodes[node].values[val].label,
                    'help':network.nodes[node].values[val].help,
                    'command_class':network.nodes[node].values[val].command_class,
                    'max':network.nodes[node].values[val].max,
                    'min':network.nodes[node].values[val].min,
                    'units':network.nodes[node].values[val].units,
                    'data':network.nodes[node].values[val].data_as_string,
                    'ispolled':network.nodes[node].values[val].is_polled,
                    'id_on_network': network.nodes[node].values[val].id_on_network
                },
                'name': network.nodes[node].product_name + '.' + network.nodes[node].values[val].label,
                'identifier': network.nodes[node].product_id + '.' + network.nodes[node].values[val].object_id
            }
            sensor_data[network.nodes[node].values[val].object_id]['metadata'].update(node_metadata)
        # Retrieve switches on the node
        switches = network.nodes[node].get_switches()
        for val in switches :
            # Add 'type': 'switch' to metadata?
            sensor_data[network.nodes[node].values[val].object_id]['value'] = network.nodes[node].get_switch_state(val)

        # Retrieve dimmers on the node
        dimmers = network.nodes[node].get_dimmers()
        for val in dimmers:
            sensor_data[network.nodes[node].values[val].object_id]['value'] = network.nodes[node].get_dimmer_level(val)

        # Retrieve RGB Bulbs on the node
        rgbbulbs = network.nodes[node].get_rgbbulbs()
        for val in rgbbulbs:
            sensor_data[network.nodes[node].values[val].object_id]['value'] = network.nodes[node].get_dimmer_level(val)

        # Retrieve sensors on the node
        sensors = network.nodes[node].get_sensors()
        for val in sensors:
            sensor_data[network.nodes[node].values[val].object_id]['metadata']['units'] = network.nodes.values[val].units
            sensor_data[network.nodes[node].values[val].object_id]['value'] = network.nodes[node].get_sensor_value(val)

        # Retrieve thermostats on the network
        thermostats = network.nodes[node].get_thermostats()
        for val in thermostats:
            sensor_data[network.nodes[node].values[val].object_id]['metadata']['units'] = network.nodes.values[val].units
            sensor_data[network.nodes[node].values[val].object_id]['value'] = network.nodes[node].get_thermostat_value(val)

        # Retrieve switches all compatibles devices on the network
        switches_all = network.nodes[node].get_switches_all()
        for val in switches_all:
            print("  value / items:  / {}".format(network.nodes[node].get_switch_all_item(val), network.nodes[node].get_switch_all_items(val)))
            print("  state: {}".format(network.nodes[node].get_switch_all_state(val)))

        # Removed protections, what are they?

        # Retrieve battery compatibles devices on the network
        battery_levels = network.nodes[node].get_battery_levels()
        for val in battery_levels:
            sensor_data[network.nodes[node].values[val].object_id]['value'] = network.nodes[node].get_battery_level(val)

        # Retrieve power level compatibles devices on the network
        power_levels = network.nodes[node].get_power_levels()
        for val in power_levels :
            sensor_data[network.nodes[node].values[val].object_id]['value'] = network.nodes[node].get_power_level(val)

        conn.timeseries_write(sensor_data)

    # Stop network
    network.stop()
