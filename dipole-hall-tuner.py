import numpy as np
from time import sleep
from setup import CycleMagnet, GetMagnet, SetMagnet, GetHall, Dist
from setup import SaveIm, GetBeamPos
import datetime
import random

#when done testing, uncomment all SetMagnet, CycleMagnet and 
#make sure current step sizes are multiples of each other
small_step = 0.02
big_step = 0.06
total_steps = 10 #total steps of 0.06A

dHall = 0.00001 #max diff in hall readings when matching
timestring = (datetime.datetime.now()).strftime("%m-%d_%H:%M")

##############################################################
##############################################################

def matchHall():

    b0_hall = GetHall(dipole_pair[0])
    b1_hall = GetHall(dipole_pair[1])

    print("Beginning matching...")
    while ( abs(b0_hall - b1_hall) > dHall):
        diff = abs(b0_hall - b1_hall)

        dI = 0.001 

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

        #one magnet goes down 0.06 A, the other 0.02 A x 3
        SetMagnet( b_big, bb_init - bb_stepsize)

        for j in range(0, int(bb_stepsize/bs_stepsize)): 
            #ramps down this magnet in small steps multiple of the large step
            SetMagnet( b_small,   bs_init - bs_stepsize*(j+1))

            sleep(5)        

            #changing quads and taking pictures at 4 tunes
            #take picture with all at init values
            all_nom_im= SaveIm('allNom', viewer)

            #take picture with all at zero
            SetMagnet(quad_pair[0], 0)
            SetMagnet(quad_pair[1], 0)
            pos_1= GetBeamPos(all_nom_im, viewer)
            sleep(5) #might need to increase this if the jumps in current are big
            all_zero_im= SaveIm('allZero', viewer)

            #take picture with first quad at half
            SetMagnet(quad_pair[0], q0_init/2)
            pos_2= GetBeamPos(all_zero_im, viewer)
            sleep(5)
            q0_half_im= SaveIm('q0half', viewer)

            #take picture with second quad at half
            SetMagnet(quad_pair[1], q1_init/2)
            pos_3= GetBeamPos(q0_half_im, viewer)
            sleep(5)
            q01_half_im= SaveIm('q01half', viewer)

            #return quads to original values
            SetMagnet(quad_pair[0], q0_init)
            SetMagnet(quad_pair[1], q1_init)

            pos_4= GetBeamPos(q01_half_im, viewer)

            #peak/intensity
            #pk_1 = pos_1[2:]
            #pk_2 = pos_2[2:]
            #pk_3 = pos_3[2:]
            #pk_4 = pos_4[2:]
            #centroid positions
            pos_1 = pos_1[0:2]
            pos_2 = pos_2[0:2]
            pos_3 = pos_3[0:2]
            pos_4 = pos_4[0:2]

		
            #get quadratic distance from centroids
            print(f"Centroids:\n({pos_1[0]:.2f}, {pos_1[1]:.2f})\n({pos_2[0]:.2f}, {pos_2[1]:.2f})\n({pos_3[0]:.2f}, {pos_3[1]:.2f})\n({pos_4[0]:.2f}, {pos_4[1]:.2f})")            

            distance= Dist(pos_1, pos_2, pos_3, pos_4)
            print(f"Dist= {distance:.5f}")

            bs_hall = GetHall(b_small)
            bb_hall = GetHall(b_big)

            bs_i = GetMagnet(b_small)
            bb_i = GetMagnet(b_big)

            #save i, hall values and distance to file
            f= open(f"dipole_{b_small}_Distance_{timestring}.txt", "a+")
            f.write(f'{bs_i:.3f}\t{bb_i:.3f}\t{bs_hall:.7f}\t{bb_hall:.7f}\t{distance:.4f}\t{pos_1[0]:.4f}\t{all_nom_im}\n')
            f.close()

        #####################

        if (abs(bs_hall - bb_hall) > dHall):
            #if they are different, match again			
            matchHall()   
        else:
            print(f"Fields: {bs_hall:.6f}, {bb_hall:.6f}, dHall: {((bs_hall - bb_hall)/bs_hall*100):.5f}%")
    
##############################################################
##############################################################

while (True):

    dipole_pair  = input("Enter which dipole pair to tune (i.e. b5, b6): ").lower()
    #getting list of dipoles
    dipole_pair = [x.lstrip().rstrip() for x in dipole_pair.split(",")]

    if (len(dipole_pair) == 2 and dipole_pair[0]!=dipole_pair[1] and 'b1' not in dipole_pair):
        break
    else:
        print("Invalid choice.")

#two dipoles: dipole_pair[0] and dipole_pair[1]
#setting correct devices to use
if  ('b3' in dipole_pair):
    quad_pair = ['q6', 'q7']
    viewer = 'D1638'
elif ('b5' in dipole_pair):
    quad_pair = ['q10', 'q11']
    viewer = 'D1783'
elif ('b7' in dipole_pair):
    quad_pair = ['q14', 'q15']
    viewer = 'D1879'
    
print(f"\nTuning {dipole_pair[0].capitalize()} and {dipole_pair[1].capitalize()}, using {quad_pair[0].capitalize()} and {quad_pair[1].capitalize()} on viewer {viewer}.\n")

#warning to set the correct range
print("Make sure Hall probe ranges are set correctly.")

#cycle
time1 = CycleMagnet(dipole_pair[0])
time2 = CycleMagnet(dipole_pair[1])
sleep(np.max([time1, time2]))
print("Done cycling.")

cont= input("Once magnets have settled, enter 'y' to continue...")

if (cont != 'y'):
    print("Exiting...")
    exit()

#match Hall probe readings
matchHall()

#get initial values to return two for second scan
b0_init = GetMagnet(dipole_pair[0])
b1_init = GetMagnet(dipole_pair[1])

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

scanDipoles(dipole_pair[1], dipole_pair[0])
print(f"Done with {dipole_pair[1]} scan.")
