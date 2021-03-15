import numpy as np
from time import sleep
from setup import CycleMagnet, GetMagnet, SetMagnet, GetHall, Dist
from setup import SaveIm, GetBeamPos
import datetime
import random

#when done testing, uncomment all SetMagnet, CycleMagnet and 
#make sure current step sizes are multiples of each other
small_step = 0.01
big_step = 0.06
total_steps = 4 #total steps of big step
extra_small_step = 0 # number of extra small step

dHall = 0.0001 #max diff in hall readings when matching
timestring = (datetime.datetime.now()).strftime("%m-%d_%H-%M")

##############################################################
##############################################################

def matchHall():

    b0_hall = GetHall(dipole_pair[0])
    b1_hall = GetHall(dipole_pair[1])

    print("Beginning matching...")
    while ( abs(b0_hall - b1_hall) > dHall):
        diff = abs(b0_hall - b1_hall)

        dI = 0.02 
        '''

        #this takes too long if they're really far so I'm gona add this for now
        if (diff >= 0.001):
            dI = 0.1

        elif (diff > 0.00005):
            dI = 0.01
        '''

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
    sleep(np.max([time1, time2]))
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

def scanDipoles(b_small, b_big):

    #set number of steps (from previous experience scanning although might need adjustments)
    bs_stepsize = small_step
    bb_stepsize = big_step

    #initial nominal quad values
    q0_init, q1_init = GetMagnet(quad_pair[0]), GetMagnet(quad_pair[1])
    #q2_init = GetMagnet("q11")

    for i in range(total_steps):

        print(f"Step {i+1} out of {total_steps} large steps.")
        #get initial current of dipoles 
        bs_init = GetMagnet(b_small) 
        bb_init = GetMagnet(b_big)



        for j in range(0, int(bb_stepsize/bs_stepsize)+extra_small_step): ## ADDED TWO MORE STEPS FOR THE FIELDS TO OVERLAP 

            #changing quads and taking pictures at 4 tunes
            #take picture with all at init values
            all_nom_im= SaveIm('allNom', viewer)

            #take picture with q11 nom, q12 7/6
#            SetMagnet(quad_pair[0], q0_init)
            SetMagnet(quad_pair[0], 40)
            SetMagnet(quad_pair[1], q1_init)
            #SetMagnet("q11", q2_init)
            pos_1= GetBeamPos(all_nom_im, viewer)
            sleep(5) #might need to increase this if the jumps in current are big
            all_zero_im= SaveIm('Q11_40', viewer)

            #take picture with q11 8/10 and q12 nom
            SetMagnet(quad_pair[0], q0_init)
#            SetMagnet(quad_pair[1], q1_init-17)
            SetMagnet(quad_pair[1], 20)
            #SetMagnet("q11", q2_init)
            pos_2= GetBeamPos(all_zero_im, viewer)
            sleep(5)
            q0_half_im= SaveIm('Q13_20', viewer)

            #take picture with q11 *3/4, and q12 *11/12
            SetMagnet(quad_pair[0], 52)
            SetMagnet(quad_pair[1], 35)
            #SetMagnet("q11", 40)
            pos_3= GetBeamPos(q0_half_im, viewer)
            sleep(5)
            q01_half_im= SaveIm('Q11_52_Q13_35', viewer)

            #return quads to original values
            SetMagnet(quad_pair[0], q0_init)
            SetMagnet(quad_pair[1], q1_init)
            #SetMagnet("q11", q2_init)

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

            distance= Dist(pos_1, pos_2, pos_3, pos_4, True)[0]
            print(f"Dist= {distance:.5f}")

            bs_hall = GetHall(b_small)
            bb_hall = GetHall(b_big)

            bs_i = GetMagnet(b_small)
            bb_i = GetMagnet(b_big)

            #save i, hall values and distance to file
            f= open(f"{b_small}_{b_big}_Distance_{timestring}.txt", "a+")
            f.write(f'{bs_i:.3f}\t{bb_i:.3f}\t{bs_hall:.7f}\t{bb_hall:.7f}\t{distance:.4f}\t{pos_1[0]:.4f}\t{all_nom_im}\n')
            f.close()
            #ramps down this magnet in small steps multiple of the large step
            SetMagnet( b_small,   bs_init - bs_stepsize*(j+1))

            
        #one magnet goes down 0.06 A, the other 0.02 A x 3
        #SetMagnet( b_big, bb_init - bb_stepsize)

        #####################

        #if (abs(bs_hall - bb_hall) > dHall):
            #if they are different, match again			
        matchHall()   
        #else:
        bs_hall = GetHall(b_small)
        bb_hall = GetHall(b_big)
        print(f"Fields: {bs_hall:.6f}, {bb_hall:.6f}, dHall: {((bs_hall - bb_hall)/bs_hall*100):.5f}%")
    
##############################################################
##############################################################

#while (True):
dipole_pair = ['b5', 'b6']

#two dipoles: dipole_pair[0] and dipole_pair[1]
#setting correct devices to use
#~ quad_pair = ['q14', 'q15'] 
#quad_pair = ['q10', 'q11'] 
quad_pair = ['q11', 'q13'] 
#viewer = 'D1783'
viewer = 'D1836'
    
print(f"\nTuning {dipole_pair[0].capitalize()} and {dipole_pair[1].capitalize()}, using {quad_pair[0].capitalize()} and {quad_pair[1].capitalize()} on viewer {viewer}.\n")

#warning to set the correct range
print("Make sure Hall probe ranges are set correctly.")

#cycle
'''
time1 = CycleMagnet(dipole_pair[0])
time2 = CycleMagnet(dipole_pair[1])
sleep(np.max([time1, time2]))
print("Done cycling.")

cont= input("Once magnets have settled, enter 'y' to continue...")

if (cont != 'y'):
    print("Exiting...")
    exit()
'''
#match Hall probe readings
matchHall()
#init_hall= float(input("What should the initial Hall value be?"))

#setInitHall(init_hall)

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

cont= input("Once magnets have settled, enter 'y' to continue...")

if (cont != 'y'):
    print("Exiting...")
    exit()

#'''
#match Hall probe readings
matchHall()
scanDipoles(dipole_pair[1], dipole_pair[0])
print(f"Done with {dipole_pair[1]} scan.")
#
