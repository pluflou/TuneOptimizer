import numpy as np
from time import sleep
from epics import caget, caput
from setup import GetBeamPos, SaveIm, Dist
from setup import set_probe, tlm_reading, GetMagnet, SetMagnet, CycleMagnet, nmrRange
import datetime

#start by setting the dipoles to a high current to be a the right edge of the viewer
##########################################
quad_pair = ['q6', 'q7'] ##### !!!! EDITED FOR B1-B2 downstream tuning !!!!!!
viewer = 'D1638'
small_step = 0.01
big_step = 0.1
total_steps = 20 #total steps of the big step
##########################################

timestring = (datetime.datetime.now()).strftime("%m-%d_%H-%M")


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

def scanDipoles(b_small, b_big):

    #set number of steps (from previous experience scanning although might need adjustments)
    bs_stepsize = small_step
    bb_stepsize = big_step

    #initial nominal quad values
    q0_init, q1_init = GetMagnet(quad_pair[0]), GetMagnet(quad_pair[1])
    
    for i in range(total_steps):

        print(f"Step {i+1} out of {total_steps} large steps.")
        #get initial current of dipoles 
        bs_init = GetMagnet(b_small) 
        bb_init = GetMagnet(b_big)

	    #set NMR teslameter to read B1 probe to save time later
        caput(set_probe, b1_probe)

        for j in range(0, int(bb_stepsize/bs_stepsize)+4): ## ADDED TWO MORE STEPS FOR THE FIELDS TO OVERLAP  

            #changing quads and taking pictures at 4 tunes
            #take picture with all at init values
            all_nom_im= SaveIm('allNom', viewer)

            #take picture with q8 nom, q9 half
            SetMagnet(quad_pair[0], q0_init)
            SetMagnet(quad_pair[1], q1_init/2)
            pos_1= GetBeamPos(all_nom_im, viewer)
            sleep(5) #might need to increase this if the jumps in current are big
            all_zero_im= SaveIm('Q7half', viewer)

            #take picture with q8/2 and q9/2
            SetMagnet(quad_pair[0], q0_init/2)
            SetMagnet(quad_pair[1], q1_init/2)
            pos_2= GetBeamPos(all_zero_im, viewer)
            sleep(5)
            q0_half_im= SaveIm('bothHalf', viewer)

            #take picture with 4/3 q8 and 5/4 q9
            SetMagnet(quad_pair[0], 4/3*q1_init)
            SetMagnet(quad_pair[1], 5/4*q1_init)
            pos_3= GetBeamPos(q0_half_im, viewer)
            sleep(5)
            q01_half_im= SaveIm('fracQ6Q7', viewer)

            #return quads to original values
            SetMagnet(quad_pair[0], q0_init)
            SetMagnet(quad_pair[1], q1_init)

            pos_4= GetBeamPos(q01_half_im, viewer)

            #centroid positions
            pos_1 = pos_1[0:2]
            pos_2 = pos_2[0:2]
            pos_3 = pos_3[0:2]
            pos_4 = pos_4[0:2]

		
            #get quadratic distance from centroids
            print(f"Centroids:\n({pos_1[0]:.2f}, {pos_1[1]:.2f})\n({pos_2[0]:.2f}, {pos_2[1]:.2f})\n({pos_3[0]:.2f}, {pos_3[1]:.2f})\n({pos_4[0]:.2f}, {pos_4[1]:.2f})")            

            distance= Dist(pos_1, pos_2, pos_3, pos_4)
            print(f"Dist= {distance:.5f}")


            #get NMR fields 
            if (b_small=='b1'):
                #saving the new actual nmr value of B1
                bs_nmr = caget(tlm_reading)
                #change b2 and compare
                #saving the new actual nmr value
                caput(set_probe, b2_probe)
                sleep(10)
                bb_nmr = caget(tlm_reading)
            elif (b_small=='b2'):
                #saving the new actual nmr value of B1
                bb_nmr = caget(tlm_reading)
                #change b2 and compare
                #saving the new actual nmr value
                caput(set_probe, b2_probe)
                sleep(10)
                bs_nmr = caget(tlm_reading)			

            bs_i = GetMagnet(b_small)
            bb_i = GetMagnet(b_big)

            #save i, hall values and distance to file
            f= open(f"{b_small}_{b_big}_Distance_{timestring}.txt", "a+")
            f.write(f'{bs_i:.3f}\t{bb_i:.3f}\t{bs_nmr:.7f}\t{bb_nmr:.7f}\t{distance:.4f}\t{pos_1[0]:.4f}\t{all_nom_im}\n')
            f.close()

            #ramps down this magnet in small steps multiple of the large step
            SetMagnet( b_small,   bs_init - bs_stepsize*(j+1))

            
        #this magnet goes down a big step
        SetMagnet( b_big, bb_init - bb_stepsize)

        #####################

        matchNMR()   

    
##############################################################
##############################################################

#two dipoles: dipole_pair[0] and dipole_pair[1]
dipole_pair = ['b1', 'b2']

print(f"\nTuning {dipole_pair[0].capitalize()} and {dipole_pair[1].capitalize()}, using {quad_pair[0].capitalize()} and {quad_pair[1].capitalize()} on viewer {viewer}.\n")

#check which probe range to use
b1_probe, b2_probe = nmrRange()

#cycle
time1 = CycleMagnet(dipole_pair[0])
time2 = CycleMagnet(dipole_pair[1])
sleep(np.max([time1, time2]))
print("Done cycling.")

cont= input("Once NMRs have settled, enter 'y' to continue...")

if (cont != 'y'):
    print("Exiting...")
    exit()

#match NMR probe readings
matchNMR()

#get initial values to return to for second scan
b0_init = GetMagnet(dipole_pair[0])
b1_init = GetMagnet(dipole_pair[1])
#'''
scanDipoles(dipole_pair[0], dipole_pair[1])
print(f"Done with {dipole_pair[0]} scan.")

#reset dipoles to original currents and cycle
SetMagnet(dipole_pair[0], b0_init)
SetMagnet(dipole_pair[1], b1_init)

#cycle
time1 = CycleMagnet(dipole_pair[0])
time2 = CycleMagnet(dipole_pair[1])
sleep(np.max([time1, time2]))
print("Done cycling.")

cont= input("Once magnets have settled, enter 'y' to continue...")

if (cont != 'y'):
    print("Exiting...")
    exit()
#'''
#match NMR probe readings
matchNMR()

scanDipoles(dipole_pair[1], dipole_pair[0])
print(f"Done with {dipole_pair[1]} scan.")