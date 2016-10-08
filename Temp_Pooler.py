import requests, json, time

global url,uuids,sensor_names,sensor_values,actuator_identity,actuator_type,actuator_values
url="http://bd-exp.andrew.cmu.edu"

sensor_names=[]
sensor_values=[]
actuator_type=[]
actuator_identity=[]
actuator_values=[]


def getOauthToken():
    url="http://bd-exp.andrew.cmu.edu:81/oauth/access_token/client_id=wNl7LZ5F4xMmtEzPbXk19aGOz0iWouk4O7A7I3hd/client_secret=Obd7ynwLdq6A7TBuXn7PRdrc2BAIJRc3RcvFMxDvxKX4jbrOrO"
    #print url
    response = requests.get(url).json()
    #print response
    access_token = response["access_token"]
    #print response
    return access_token

def get_sensor_data(sensor):
  headers = {'content-type':'application/json',
	'charset' : 'utf-8',
	'Authorization' : 'Bearer '+ getOauthToken()}
  end_time = time.time()
  start_time =end_time-30
  get_url = url + ":82/api/sensor/"+sensor+"/timeseries?start_time="+`start_time` + "&end_time="+`end_time`
  try:
    response=requests.get(get_url, headers = headers).json()
    #print response
    return response
  except Exception as e:
    print sensor+" didn't find data for the past 150 seconds . Please check the sensor"
    return str(e)

def sensorlist():
  access_token=getOauthToken()
  #print access_token
  header = {"Authorization": "Bearer " + access_token, 'content-type':'application/json'}
  url_sensor_list = url+":81/api/search"
  data={"data":{"Tags":["room:2502"]}}
  #print url_sensor_list,data,type(data)
  response = requests.post(url_sensor_list,data=json.dumps(data),headers = header).json()
  #print response
  for x in response['result']:
    sensor_values.append(return_latest_values(x['name']))
    sensor_names.append(x['source_name'])

    try:
      for tag in x['tags']:
       if(x['source_name']=='status' or tag['name']=='status'):
        if(tag['name']=='identity'):
          actuator_identity.append(tag['value'])        
        
	if(tag['name']=='type'):
          actuator_type.append(tag['value'])
          actuator_values.append(return_latest_values(x['name']))

      #print "in"
    except:
      print "No actuator present in the region!"


def return_latest_values(uuid):
  temp=get_sensor_data(uuid)
  print uuid
  print temp
  for t in temp['data']['series']:
    for sens in t['values']:
      if(sens==t['values'][-1]):
        return (sens[2])
        #print i

def actuate_devices():
  for d in range(0,len(actuator_identity)):
    url_post=url+':69/api'
    #print url_post
    data={"type":actuator_type[d],"identity":actuator_identity[d],"new_state":actuator_values[d]}
    print data
    response=requests.post(url_post,data=json.dumps(data))
    return response
  
while 1:
  sensorlist()
  actuate_devices()
  print sensor_values
  print sensor_names
  print actuator_type
  print actuator_identity
  print actuator_values

  sensor_names=[]
  sensor_values=[]
  actuator_type=[]
  actuator_identity=[]
  actuator_values=[]
  time.sleep(5)

print sensor_values
print sensor_names
print actuator_type
print actuator_identity
print actuator_values


