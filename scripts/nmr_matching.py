import numpy as np
import pandas as pd
from time import *
from epics import caget, caput
from setup import *
import datetime
import matplotlib.pyplot as plt

#start by setting the dipoles to a high current to be a the right edge of the viewer

#check which probe range to use
b1_probe, b2_probe = nmrRange()

#cycle
cycleB1B2()
#need to make sure NMRs have settled otherwise we cannot match the NMR readings
cont= input("Once NMRs have settled, enter 'y' to continue...")

if (cont != 'y'):
    print("Exiting...")
    exit()

'''############################################'''
def matchNMR():
    ''' Matches the NMR fields by lowering the highest current between B1 and B2 slowly until criteria is met '''
    print("Getting the starting NMR probe values...")
    #saving the new actual nmr value
    #b1
    caput(set_probe, b1_probe)
    sleep(10)
    b1_nmr_h = caget(tlm_reading)
    #b2
    caput(set_probe, b2_probe)
    sleep(10)
    b2_nmr_h = caget(tlm_reading)

    #using the nmr readback and the i_cset, slowly ramp down as you check that the nmrs are close
    dNMR = 0.00001

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

    print("Done matching NMR values.")

matchNMR()
