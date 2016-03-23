import json
class Setting:
    def __init__(self, settingFileName):
        settingFilePath="../config/"+settingFileName+".json"
        self.setting = json.loads(open(settingFilePath,'r').read())
        
    def get(self,settingName):
        return self.setting[settingName]
test =Setting("netatmo")
print test.setting
