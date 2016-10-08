import json


class Setting:
    def __init__(self, filename=False):
	if(filename):
          settingfilepath = "/home/pi/Connectors/config/" + filename + ".json"
	  self.setting = json.loads(open(settingfilepath, 'r').read())
	else:
	  ValueError("Please specify the type of the device")

    def get(self, settingname):
        return self.setting[settingname]
