from time import sleep
import datetime
from epics import caget, caput, cainfo


if( not (caget('SCR_BTS35:DD_D1638:POS_RSTS_VD') == 1)):
    print("Viewer is not in.")

while 1:
    try:

#if upstream FC is in, take screenshot of viewer
        if(caget('REA_BTS34:FC_D1448:LMOUT_RSTS') == 1):
        #if 1: #SWITCH TO ABOVE IF STATEMENT WHEN RUNNING OVERNIGHT
            print('Moving cup out')
            caput('SCR_BTS35:FC_D1485:IN_CMD', 0, wait=True, timeout=60)   #takes out cup
	    
            sleep(30)

            timestring = (datetime.datetime.now()).strftime("%m-%d_%H-%M")
            
            caput('SCR_BTS35:VD_D1638:TIFF1:FileName', f'D1638_stability_{timestring}', wait=True)
            caput('SCR_BTS35:VD_D1638:TIFF1:WriteFile', 1, wait=True, timeout=10)   #takes screenshot
            print('Screenshot obtained')
            sleep(2)

            print('Moving cup in')
            caput('SCR_BTS35:FC_D1485:IN_CMD', 1, wait=True, timeout=60)     #puts in cup

        else:
            print('Beam is blocked.')
    
        delay = 5

        sleep( delay * 60 )    #takes screenshot every [delay] minute(s)

    except:
        print('Error - waiting 30 s and trying again')
        sleep(30)
