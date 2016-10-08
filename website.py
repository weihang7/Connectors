from flask import Flask
from flask import request
from pymongo import MongoClient
from influxdb import InfluxDBClient
import json
import time
import Scripts.manager as manager
import requests
import time
app = Flask(__name__)

global url
url="http://bd-exp.andrew.cmu.edu:82"
def jsonString(obj,pretty=False):
    if pretty == True:
        return json.dumps(obj, sort_keys=True, indent=4, separators=(',', ': ')) + '\n'
    else:
        return json.dumps(obj)

def getOauthToken():
    url="http://bd-exp.andrew.cmu.edu:81/oauth/access_token/client_id=x5ZtdbIytLybGSeSJMqMr8tVKkZfciuAb1fRtqV4/client_secret=209F0QwIR7yPQUjabA68sqW9Ei80QONOdf8UdtFO2BOaWnoRL5"
    response = requests.get(url).json()
    access_token = response["access_token"]
    return access_token

def get_sensor_data(sensor):
    headers = {'content-type':'application/json',
			'charset' : 'utf-8',
			'Authorization' : 'Bearer '+ getOauthToken()}
    end_time = time.time()
    start_time =end_time-150
    sensor="c751b710-834b-4744-b9ce-0e9d06abc29b"
    get_url = url + "/api/sensor/"+sensor+"/timeseries?start_time="+`start_time` + "&end_time="+`end_time`
    try:
        response=requests.get(get_url, headers = headers).json()
	return response
    except Exception as e:
            print sensor+" didn't find data for the past 150 seconds.Please check the sensor"
            return str(e)

@app.route("/")
def hello():
    return "<h1 style='color:blue'>Hello There!This is the actuation engine!</h1>"
    
@app.route('/time', methods=['GET'])
def get_time():
    timestamp = time.time()
    dic = {
        'url':request.remote_addr,
        'method':request.method,
        'result':'ok',
        'ret':timestamp
    }
    return jsonString(dic)

@app.route('/api', methods=['POST'])
def run_script():
    data=request.data
    js=json.loads(data)
    type=js['type']
    identity=js['identity']
    new_state=js['new_state']
    manager.actuate(type,identity,new_state)
    return data

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=69,debug=True)
