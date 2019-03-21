#Centering w/ no multipoles routine
from time import *
from cothread.catools import caget, caput
import setup.py


if(caget(vd1542_atloc) == 1):
    

while 1:
    try:

#if upstream FC is in, take screenshot of viewer
        if(caget('REA_BTS34:FC_D1448:LMOUT_RSTS') == 1):
        #if 1: #SWITCH TO ABOVE IF STATEMENT WHEN RUNNING OVERNIGHT
            print('Moving cup out')
            caput('SCR_BTS35:FC_D1485:IN_CMD', 0, wait=True, timeout=60)   #takes out cup
	    
            sleep(30)
            caput('SCR_BTS35:VD_D1542:TIFF1:WriteFile', 1, wait=True, timeout=10)   #takes screenshot
 	    print('Screenshot obtained')
            sleep(2)

            print('Moving cup in')
            caput('SCR_BTS35:FC_D1485:IN_CMD', 1, wait=True, timeout=60)     #puts in cup

        else:
            print('Beam is blocked.')
    
        sleep(60)    #takes screenshot every 1 minute

    except:
        print('Error - waiting 30 s and trying again')
        sleep(30)

