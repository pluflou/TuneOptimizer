import numpy as np
from time import sleep
from epics import caget, caput
from setup import GetBeamPos, SaveIm, Dist
from setup import set_probe, tlm_reading, GetMagnet, SetMagnet, CycleMagnet, nmrRange
from setup import GetHall
import datetime
import random

dHall = 0.0001 #max diff in hall readings when matching
timestring = (datetime.datetime.now()).strftime("%m-%d_%H-%M")
dNMR = 0.00001

##############################################################
##############################################################
def matchNMR():
    ''' Matches the NMR fields by lowering the highest current between B1 and B2 slowly until criteria is met '''
    print("Getting the starting NMR probe values...")
    #saving the new actual nmr value
    #b1
    caput(set_probe, b1_probe)
    sleep(13)
    b1_nmr_h = caget(tlm_reading)
    #b2
    caput(set_probe, b2_probe)
    sleep(13)
    b2_nmr_h = caget(tlm_reading)

    #using the nmr readback and the i_cset, slowly ramp down as you check that the nmrs are close

    print("Beginning matching...")
    while ( abs(b1_nmr_h - b2_nmr_h) > dNMR):
        diff = abs(b1_nmr_h - b2_nmr_h)
        dI = 0.001 

        #this takes too long if they're really far so I'm gona add this for now
        if (diff >= 0.001):
            dI = 0.1

        elif (diff > 0.00005):
            dI = 0.02  # Changed from 0.01 since this is sometimes the difference between set and RD

        b1_i = GetMagnet('b1') 
        b2_i = GetMagnet('b2')

        if (b1_nmr_h > b2_nmr_h):
            caput(set_probe, b1_probe)

            #decrease b1_nmr_h in small steps until it is dNMR off from b2

            # change b1 and compare
            SetMagnet('b1', b1_i - dI)
            #saving the new actual nmr value
            sleep(3)
            b1_nmr_h = caget(tlm_reading)

        elif (b1_nmr_h < b2_nmr_h):
            #go in opposite direction
            caput(set_probe, b2_probe)

            # change b2 and compare
            SetMagnet('b2', b2_i - dI)
            #saving the new actual nmr value
            sleep(3)
            b2_nmr_h = caget(tlm_reading)
    
        print(f"Fields: {b1_nmr_h:.6f}, {b2_nmr_h:.6f}, dNMR: {((b1_nmr_h - b2_nmr_h)/b1_nmr_h*100):.5f}%")

    print("Done matching NMR values.")
"""####################################################"""
def setInitNMR(init_hall=0):

    #b1
    caput(set_probe, b1_probe)
    sleep(13)
    b1_nmr_h = caget(tlm_reading)
    #b2
    caput(set_probe, b2_probe)
    sleep(13)
    b2_nmr_h = caget(tlm_reading)
    b0_hall = b1_nmr_h
    b1_hall = b2_nmr_h
    overshoot_margin = 0.001
    print("Beginning initializing dipoles...")
    while ( (b0_hall - init_hall) < overshoot_margin or (b1_hall - init_hall) < overshoot_margin ):

        diff = max(abs(b0_hall - init_hall),abs(b1_hall - init_hall))
        b0_i = GetMagnet(dipole_pair[0]) 

        dI = 0.02 
        if (diff >= 0.001):
            dI = 0.1

        elif (diff > 0.00005):
            dI = 0.01
        # change b0 and compare
        SetMagnet(dipole_pair[0], b0_i + dI)
        #saving the new actual hall value
        sleep(3)
        caput(set_probe, b1_probe)
        b0_hall = caget(tlm_reading)
        caput(set_probe, b2_probe)
        SetMagnet(dipole_pair[1], b0_i + dI)
        b1_hall = caget(tlm_reading)
    
        print(f"Fields: {b0_hall:.6f}, {b1_hall:.6f}")

    time1 = CycleMagnet(dipole_pair[0])
    time2 = CycleMagnet(dipole_pair[1])
    sleep(np.max([time1, time2])+30)
    cont= input("Once magnets have settled, enter 'y' to continue...")
    
    if (cont != 'y'):
        print("Exiting...")
        exit()

    print("Magnets cycled above initial Hall values.")

    while ( abs(b0_hall - init_hall) > dHall):
        diff = abs(b0_hall - init_hall)

        dI = 0.02 
        #this takes too long if they're really far so I'm gona add this for now
        if (diff >= 0.001):
            dI = 0.1

        elif (diff > 0.00005):
            dI = 0.01

        b0_i = GetMagnet(dipole_pair[0]) 

        if (b0_hall > init_hall):
            # change b0 and compare
            SetMagnet(dipole_pair[0], b0_i - dI)
            #saving the new actual hall value
            sleep(3)
            caput(set_probe, b1_probe)
            b0_hall = caget(tlm_reading)
    print("B0 set to initial value.")
    matchNMR()


def matchHall():

    b0_hall = GetHall(dipole_pair[0])
    b1_hall = GetHall(dipole_pair[1])

    print("Beginning matching...")
    while ( abs(b0_hall - b1_hall) > dHall):
        diff = abs(b0_hall - b1_hall)

        dI = 0.02 

        #this takes too long if they're really far so I'm gona add this for now
        if (diff >= 0.001):
            dI = 0.1

        elif (diff > 0.00005):
            dI = 0.01

        b0_i = GetMagnet(dipole_pair[0]) 
        b1_i = GetMagnet(dipole_pair[1])

        if (b0_hall > b1_hall):
            # change b0 and compare
            SetMagnet(dipole_pair[0], b0_i - dI)
            #saving the new actual hall value
            sleep(3)
            b0_hall = GetHall(dipole_pair[0])

        elif (b0_hall < b1_hall):
            # change b1 and compare
            SetMagnet(dipole_pair[1], b1_i - dI)
            #saving the new actual hall value
            sleep(3)
            b1_hall = GetHall(dipole_pair[1])
    
        print(f"Fields: {b0_hall:.6f}, {b1_hall:.6f}, dHall: {((b0_hall - b1_hall)/b0_hall*100):.5f}%")

    print("Done matching Hall values.")

# considering adding a way to initialize the fields to a specific value

def setInitHall(init_hall=0):

    b0_hall = GetHall(dipole_pair[0])
    b1_hall = GetHall(dipole_pair[1])
    overshoot_margin = 0.001
    print("Beginning initializing dipoles...")
    while ( (b0_hall - init_hall) < overshoot_margin or (b1_hall - init_hall) < overshoot_margin ):

        diff = max(abs(b0_hall - init_hall),abs(b1_hall - init_hall))
        b0_i = GetMagnet(dipole_pair[0]) 

        dI = 0.02 
        if (diff >= 0.001):
            dI = 0.1

        elif (diff > 0.00005):
            dI = 0.01
        # change b0 and compare
        SetMagnet(dipole_pair[0], b0_i + dI)
        #saving the new actual hall value
        sleep(3)
        b0_hall = GetHall(dipole_pair[0])
        SetMagnet(dipole_pair[1], b0_i + dI)
        b1_hall = GetHall(dipole_pair[1])
    
        print(f"Fields: {b0_hall:.6f}, {b1_hall:.6f}")

    time1 = CycleMagnet(dipole_pair[0])
    time2 = CycleMagnet(dipole_pair[1])
    sleep(np.max([time1, time2])+30)
    cont= input("Once magnets have settled, enter 'y' to continue...")
    
    if (cont != 'y'):
        print("Exiting...")
        exit()

    print("Magnets cycled above initial Hall values.")

    while ( abs(b0_hall - init_hall) > dHall):
        diff = abs(b0_hall - init_hall)

        dI = 0.02 
        #this takes too long if they're really far so I'm gona add this for now
        if (diff >= 0.001):
            dI = 0.1

        elif (diff > 0.00005):
            dI = 0.01

        b0_i = GetMagnet(dipole_pair[0]) 

        if (b0_hall > init_hall):
            # change b0 and compare
            SetMagnet(dipole_pair[0], b0_i - dI)
            #saving the new actual hall value
            sleep(3)
            b0_hall = GetHall(dipole_pair[0])
    print("B0 set to initial value.")
    matchHall()

    
##############################################################
##############################################################

#while (True):

    

#warning to set the correct range
#print("Make sure Hall probe ranges are set correctly.")

#cycle

#time1 = CycleMagnet(dipole_pair[0])
#time2 = CycleMagnet(dipole_pair[1])
#sleep(np.max([time1, time2]))
#print("Done cycling.")

#cont= input("Once magnets have settled, enter 'y' to continue...")
#
#if (cont != 'y'):
#    print("Exiting...")
#    exit()

#match Hall probe readings
#matchHall()
which_dipoles= input("""Which dipoles are being set?:
A) B1 & B2
B) B3 & B4
C) B5 & B6
D) B7 & B8
A/B/C/D""")


dipoles = { "A" : ['b1','b2'], "B" : ['b3','b4'], "C" : ['b5','b6'], "D": ['b7','b8'] } 

dipole_pair = dipoles[which_dipoles] 
print(f"\nSetting {dipole_pair[0].capitalize()} and {dipole_pair[1].capitalize()}\n")

init_hall= float(input("What should the initial Hall value be?"))


if which_dipoles == "A":
    b1_probe, b2_probe = nmrRange()
    setInitNMR(init_hall)
else:
    setInitHall(init_hall)
print(f"Done with {dipole_pair[1]} scan.")
#

