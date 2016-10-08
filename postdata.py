import requests
import json

global url
url='http://bd-exp.andrew.cmu.edu:69'
def post_type():
    url_post=url+'/api'
    data={"type":"lifx","identity":"all","new_state":"off"}
    response=requests.post(url_post,data=json.dumps(data))
    return response.json()

def get_time():
    url_time=url+'/time'
    response=requests.get(url_time)
    return response

print(post_type())
