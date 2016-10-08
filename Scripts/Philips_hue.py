import requests


global url
url="128.237.174.169:1880/actuate"
def print_this():
    print "Hello I am in Philips_Hue"
def actuate():
    response=requests.get(url,data="on")
    print response
    return response

if __name__=="__main__":
    print_this()
