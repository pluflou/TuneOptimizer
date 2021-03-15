import numpy as np
from time import sleep
from epics import caget, caput
from setup import GetBeamPos, SaveIm, GetQuads, SetQuads, nmrRange, Dist, cycleB1B2
from setup import set_probe, tlm_reading, GetMagnet, SetMagnet
import datetime

viewer = 'D1638'
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
    sleep(13)
    b1_nmr_h = caget(tlm_reading)
    #b2
    caput(set_probe, b2_probe)
    sleep(13)
    b2_nmr_h = caget(tlm_reading)

    #using the nmr readback and the i_cset, slowly ramp down as you check that the nmrs are close
    dNMR = 0.0002

    print("Beginning matching...")
    while ( abs(b1_nmr_h - b2_nmr_h) > dNMR):
        diff = abs(b1_nmr_h - b2_nmr_h)
        dI = 0.001 

        #this takes too long if they're really far so I'm gona add this for now
        if (diff >= 0.001):
            dI = 0.1

        elif (diff > 0.00005):
            dI = 0.01  
        b1_i = GetMagnet('b1') 
        b2_i = GetMagnet('b2')

        if (b1_nmr_h > b2_nmr_h):
            caput(set_probe, b1_probe)

            #decrease b1_nmr_h in small steps until it is dNMR off from b2

            # change b1 and compare
            SetMagnet('b1', b1_i - dI)
            #saving the new actual nmr value
            sleep(6)
            b1_nmr_h = caget(tlm_reading)

        elif (b1_nmr_h < b2_nmr_h):
            #go in opposite direction
            caput(set_probe, b2_probe)

            # change b2 and compare
            SetMagnet('b2', b2_i - dI)
            #saving the new actual nmr value
            sleep(6)
            b2_nmr_h = caget(tlm_reading)
    
        print(f"Fields: {b1_nmr_h:.6f}, {b2_nmr_h:.6f}, dNMR: {((b1_nmr_h - b2_nmr_h)/b1_nmr_h*100):.5f}%")

    print("Done matching NMR values.")
"""####################################################"""

timestring = (datetime.datetime.now()).strftime("%m-%d_%H_%M")

"""####################################################"""
"""ramp down slowly and analyze steering from Q3 and Q4"""
#go down in small steps and record Dist AND currents (these are reproducible)
#dI = 0.03
dI = 0.01
Dmin = 0
atTune = False

while (atTune == False):
 
    #using the nmr readback and the i_cset, slowly ramp down as you check that the nmrs are close
    dNMR = 0.0002
   #get Is of dipoles (reproducible)
    b1_i = GetMagnet('b1') 
    b2_i = GetMagnet('b2')

    caput(set_probe, b1_probe)
    
    SetMagnet( 'b1', b1_i - dI)
    SetMagnet( 'b2', b2_i - dI)

    sleep(10)

    #saving the new actual nmr value
    b1_nmr = caget(tlm_reading)

    caput(set_probe, b2_probe)
    #change b2 and compare
    #saving the new actual nmr value
    sleep(10)
    b2_nmr = caget(tlm_reading)

    #~ if (abs(b1_nmr_h - b2_nmr_h) > dNMR):
    if (abs(b1_nmr - b2_nmr) > dNMR):			# changed b1_nmr_h to b1_nmr and similarly for b2_nmr_h
        matchNMR()     
    else:
        print(f"Fields: {b1_nmr:.6f}, {b2_nmr:.6f}, dNMR: {((b1_nmr - b2_nmr)/b1_nmr*100):.5f}%")
    
    
#compare current dist with previous, once I pass the min, stop, set back to Imin, cycle
    q1_init, q2_init, q3_init, q4_init= GetQuads()
    q5_init = GetMagnet('q5')

    #Tuning Q3 and Q4
    #take picture with all at init values
    SetQuads(q1_init, q2_init, q3_init, q4_init)
    sleep(1)
    all_nom_im= SaveIm('allNom', viewer)

    #take picture with all at zero
    SetQuads(q1_init, q2_init, 90, q4_init)
    pos_1= GetBeamPos(all_nom_im, viewer)
    sleep(5) #might need to increase this if the jumps in current are big
    q3_90_im= SaveIm('q3_90', viewer)

    #take picture with Q3 at half
    SetQuads(q1_init, q2_init, q3_init, -90)
    pos_2= GetBeamPos(q3_90_im, viewer)
    sleep(5)
    q4_90_im= SaveIm('q4_90', viewer)

    #take picture with Q2 at half
    SetQuads(q1_init, q2_init, q3_init, q4_init)
    SetMagnet('q5', 50)
    pos_3= GetBeamPos(q3_90_im, viewer)
    sleep(5)
    q5_50_im= SaveIm('q5_50', viewer)

    #return quads to original values
    SetQuads(q1_init, q2_init, q3_init, q4_init)
    SetMagnet('q5', q5_init)
    pos_4= GetBeamPos(q5_50_im, viewer)

    pk_1 = pos_1[2:]
    pk_2 = pos_2[2:]
    pk_3 = pos_3[2:]
    pk_4 = pos_4[2:]
    pos_1 = pos_1[0:2]
    pos_2 = pos_2[0:2]
    pos_3 = pos_3[0:2]
    pos_4 = pos_4[0:2]
		
    #get quadratic distance from centroids
    print("Centroids: ", pos_1, pos_2, pos_3, pos_4)
    #print("Peaks: ", pk_1, pk_2, pk_3, pk_4)
    distance= Dist(pos_1, pos_2, pos_3, pos_4)
    print(f"Dist= {distance:.5f}")

    #get Is of dipoles (reproducible)
    b1_i = GetMagnet('b1') 
    b2_i = GetMagnet('b2')

    #save i, nmr values and distance to file
    f= open(f"b1_b2_Distance_{timestring}.txt", "a+")
    f.write(f'{b1_i:.3f}\t{b2_i:.3f}\t{b1_nmr:.7f}\t{b2_nmr:.7f}\t{distance:.4f}\t{pos_1[0]:.4f}\t{all_nom_im}\n')
    f.close()

