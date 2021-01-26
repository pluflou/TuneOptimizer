from time import sleep
from epics import caget, caput
from setup import *

#before running this, set cycling parameters to the ones you want to use
#then center the dipoles on the middle dot of the viewer

#caput(b1_bcset, 0.561)
#caput(b2_bcset, 0.560)

#check which probe range to use
b1_probe, b2_probe = nmrRange()

print("Setting offset...")
#set both to a slightly higher value 
#note that the actual nmr value and the HL optics values on CSS are off by quite a bit
#so they're treated separately here
offset =  0.0 #0.03
#setting: the magnets through the HLC
b1_i = caget(b1_icset) 
b2_i = caget(b2_icset)
#caput(b1_icset, b1_i + offset)
#caput(b2_icset, b2_i + offset)

#cycleB1B2()
def match():
    print("Getting the starting NMR probe values...")
#saving the new actual nmr value
#b1
    caput(set_probe, b1_probe)
    sleep(3)
    b1_nmr_h = caget(tlm_reading)
#b2
    caput(set_probe, b2_probe)
    sleep(3)
    b2_nmr_h = caget(tlm_reading)



######start matching#####
#using the nmr readback and the i_cset, slowly ramp down as you check that the nmrs are close
    dNMR = 0.000001
    print("Beginning matching...")

    while ( abs(b1_nmr_h - b2_nmr_h) > dNMR):
        diff = abs(b1_nmr_h - b2_nmr_h)
        dI = 0.001 

        #this takes too long if they're really far so I'm gona add this for now
        if (diff >= 0.001):
            dI = 0.1

        elif (diff > 0.00005):
            dI = 0.01

        b1_i = caget(b1_icset) 
        b2_i = caget(b2_icset)

        if (b1_nmr_h > b2_nmr_h):
            caput(set_probe, b1_probe)

        #decrease b1_nmr_h in small steps until it is dNMR off from b2

        # change b1 and compare
            caput(b1_icset, b1_i - dI, wait = True)
        #saving the new actual nmr value
            sleep(3)
            b1_nmr_h = caget(tlm_reading)

        elif (b1_nmr_h < b2_nmr_h):
        #go in opposite direction
            caput(set_probe, b2_probe)

        # change b2 and compare
            caput(b2_icset, b2_i - dI, wait = True)
        #saving the new actual nmr value
            sleep(3)
            b2_nmr_h = caget(tlm_reading)
    
        print(f"Fields: {b1_nmr_h:.6f}, {b2_nmr_h:.6f}, dNMR: {((b1_nmr_h - b2_nmr_h)/b1_nmr_h*100):.5f}%")
 
match() 

print("Done matching NMR values.")



