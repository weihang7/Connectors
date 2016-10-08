import wemo as wemo
import Philips_hue as Hue 
import lifx as lifx_lamp
def actuate(type,identity,new_state):
    if type=="wemo" :
        wemo.Actuate_wemo(identity,(new_state))
    elif type=="Philips_Hue" :
        Hue.print_this()
    elif type=="lifx" :
	lifx_lamp.actuate_lifx(identity,new_state)

