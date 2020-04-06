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
#~ cycleB1B2()
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
"""####################################################"""

timestring = (datetime.datetime.now()).strftime("%m-%d_%H:%M")

"""####################################################"""
"""ramp down slowly and analyze steering from Q3 and Q4"""
#go down in small steps and record Dist AND currents (these are reproducible)
dI =   0.03
Dmin = 0
atTune = False

while (atTune == False):
 
     #using the nmr readback and the i_cset, slowly ramp down as you check that the nmrs are close
    dNMR = 0.00001
   #get Is of dipoles (reproducible)
    b1_i = caget(b1_icset) 
    b2_i = caget(b2_icset)

    caput(set_probe, b1_probe)
    
    caput(b1_icset, b1_i - dI)
    caput(b2_icset, b2_i - dI)
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

    #Tuning Q3 and Q4
    #take picture with all at init values
    SetQuads(q1_init, q2_init, q3_init, q4_init)
    sleep(1)
    all_nom_im= SaveIm('allNom')

    #take picture with all at zero
    SetQuads(q1_init, q2_init, 0, 0)
    pos_1= GetBeamPos(all_nom_im)
    sleep(5) #might need to increase this if the jumps in current are big
    all_zero_im= SaveIm('allZero')

    #take picture with Q3 at half
    SetQuads(q1_init, q2_init, q3_init/2, q4_init)
    pos_2= GetBeamPos(all_zero_im)
    sleep(5)
    q3_half_im= SaveIm('q3half')

    #take picture with Q2 at half
    SetQuads(q1_init, q2_init, q3_init, q4_init/2)
    pos_3= GetBeamPos(q3_half_im)
    sleep(5)
    q4_half_im= SaveIm('q4half')

    #return quads to original values
    SetQuads(q1_init, q2_init, q3_init, q4_init)
    pos_4= GetBeamPos(q4_half_im)

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
    b1_i = caget(b1_icset) 
    b2_i = caget(b2_icset)

    #save i, nmr values and distance to file
    f= open(f"dipoles_Distance_{timestring}.txt", "a+")
    f.write(f'{b1_i:.3f}\t{b2_i:.3f}\t{b1_nmr:.7f}\t{b2_nmr:.7f}\t{distance:.4f}\t{pos_1[0]:.4f}\t{all_nom_im}\n')
    f.close()


"""##################"""
""" fitting results """
'''
scan = pd.read_csv(f'dipoles_Distance_{timestring}.txt', sep='\t', header=None)
scan.columns = ["b1_i", "b2_i", "b1_nmr", "b2_nmr", "dist"]

avg_nmr = (scan["b1_nmr"] + scan["b2_nmr"])/2

#polyfit for dist and nmr
z = np.polyfit(avg_nmr, 1/scan["dist"], 3)
p = np.poly1d(z)

xp = np.linspace(avg_nmr.min(), avg_nmr.max(), 500)

nmr_min = xp[p(xp).argmin()]
print(f"NMR value at tune is: {nmr_min}")

#linear regression for currents and nmr
z1 = np.polyfit(scan["b1_i"], scan["b1_nmr"], 1)
z2 = np.polyfit(scan["b2_i"], scan["b2_nmr"], 1)

p1 = np.poly1d(z1)
p2 = np.poly1d(z2)

xp1 = np.linspace(scan["b1_i"].min(), scan["b1_i"].max(), 500)
xp2 = np.linspace(scan["b2_i"].min(), scan["b2_i"].max(), 500)

b1_i_tune = xp1[p1(nmr_min).argmin()]
b2_i_tune = xp2[p1(nmr_min).argmin()]

print(f"Best tune is at nmr_avg = {nmr_min}")
print(f"Corres. B1 current is = {b1_i_tune}")
print(f"Corres. B2 current is = {b2_i_tune}")

plt.plot(xp, p(xp), '--', color='green')
plt.plot(avg_nmr, 1/scan["dist"])
plt.plot(nmr_min, p(xp).min(), marker = '.', color = 'red', markersize=12)
plt.savefig(f"dipole_scan_fit_{timestring}.png", dpi=300)
plt.show() 

'''
'''
#to make sure NMRs are matched and values are reproducible:
#go up to a value I>Imin
caput(b1_icset, b1_i_min + 0.08)
caput(b2_icset, b2_i_min + 0.08)

#cycle
cycleB1B2()

#match NMRs
print("Getting the starting NMR probe values...")
#saving the new actual nmr value
#b1
caput(set_probe, b1_probe)
sleep(15)
b1_nmr_h = caget(tlm_reading)
#b2
caput(set_probe, b2_probe)
sleep(15)
b2_nmr_h = caget(tlm_reading)

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

print("Done matching NMR values.")

#Final step
#go DOWN to Imin
if (caget(b1_icset)<b1_i_min or caget(b2_icset)<b2_i_min):
    print("oops, NMR matching took too many iterations")
else:
    caput(b1_icset, b1_i_min)
    caput(b2_icset, b2_i_min)
    print("Tuning done. Check Q3 and Q4 steering.")
    print('B1= {b1_i_min:.3f}A\tB2= {b2_i_min:.3f}A\tNMR1= {b1_nmr_h:.7f}T\tNMR2={b2_nmr_h:.7f}T\n')
'''

