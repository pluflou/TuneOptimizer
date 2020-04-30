import os, shutil, signal
import sys, math

import subprocess as commands
import re
import random
import multiprocessing
import itertools
import numpy as np
from epics import caput

import gaussianprocess as gp
from time import sleep
from setup import GetBeamPos, GetQuad, SetQuad, SaveIm

## if in troubleshoot mode you can change the eps at every step
tbl = 'n'
## if no in tbl mode this is set to the following eps
count = 0

##I did not yet implement the printing of the images when it's in tbl mode
print("Make sure to delete the past corrector text files.")

quad_list  = input("Enter which quads to optimize (i.e. q2, q3, q4): ")
viewer     = input("Enter viewer location (i.e. D1542): ")
theta      = input("Enter theta (kernel param): ")
eps_stable = input("Enter eps (prob. of improvement): ")

#getting list of quads to loop through
quad_list = [x.lstrip().rstrip() for x in quad_list.split(",")]


q_init = {}
q_ps = {}

for q in quad_list:

    cont = 'y'
	print("Starting {q} optimization.")

	#get init values for each quad
	q_init[q] = GetQuad(q)
	#initialize phase space as +/- 15% of init value
	q_ps[q] = [ 0.85*q_init[q] , 1.15*q_init[q] ]

	#take picture at init values
	init_im = SaveIm('init')
	sleep(2)

	#get initial beam spot width
	pos_init = GetBeamPos(init_im, viewer)

	#widths (+/- 34.13%)
    wid_init = 1/(pos_init[5] - pos_init[4])

	#write inital value to file
	f= open(f"{q}Values_Widths.txt", "a+")
	f.write(f'{q_init[q]:.4f}\t{wid_init:.4f}\n')
	f.close()

    while (cont == 'y' and count<11):
	
	    #selecting a random new state
		rand = random.uniform(q_ps[q][0], q_ps[q][1])

	    #set quad to new random current and get new width
	    SetQuad(q, rand) 
	    sleep(10)
	    rand_im= SaveIm('rand') #dont I need init width first?? need to run this once... 
	    sleep(2)

	    pos_rand = GetBeamPos(rand_im, viewer)

        #widths (+/- 34.13%)
        wid_rand = 1/(pos_rand[5] - pos_rand[4])

	    print("Init Width: ", 1/wid_init)
		print("New Width: ", 1/wid_rand)

	    #save currents and width values to file
	    f= open(f"{q}Values_Widths.txt", "a+")
        f.write(f'{rand:.4f}\t{wid_rand:.4f}\n')
	    f.close()

	    #run GP 
	    if (tbl == 'y'):
		    eps_input= input("Enter the desired acquisition function parameter:")	
	    else:
		    eps_input= eps_stable
		    count = count + 1
	
	    ####################
	    """##GaussProc##""""
	    ####################

        # Hyper-parameters
	    theta = float(theta) # Kernel parameter
	    eps = float(eps_input) # Acquisition function (probability of improvement) parameter
	    num_points = 100000 # Number of points to sample when using PI to find the next corrector values

	    # Reading file with corrector values and measured distance between peaks
	    reader = np.asmatrix(np.loadtxt(f'{q}Values_Widths.txt'))
	    x_observed = np.transpose(np.asmatrix(reader[:,0]))
	    f_observed = np.transpose(np.asmatrix(reader[:,1]))

	    # Doing GP stuff
	    f_observed = np.transpose(f_observed)  # transform to column 
	    KK = gp.K(x_observed, theta)  # Covariance matrix
	    KInv = np.linalg.inv(KK)   # Inverse of covariance matrix
	
	    # Removing sampling file from previous step
	    cmd = 'rm -f temp-sampling.txt'
	    failure, output = commands.getstatusoutput(cmd)
	    try: 
    	    pool = multiprocessing.Pool()  # Take as many processes as possible			
	    except: 
    	    for c in multiprocessing.active_children():
        	    os.kill(c.pid, signal.SIGKILL)
        	    pool = multiprocessing.Pool(1)  # Number of processes to be used during PI sampling	
	    for j in range(0, int(num_points/250)):
    	    pool.apply_async( gp.samplePI, [250, f_observed, x_observed, theta, eps, KInv, ps] )
	    pool.close()
	    pool.join()
	    PIreader = np.asmatrix(np.loadtxt('temp-sampling.txt'))
	    x = np.transpose(np.asmatrix( PIreader[ np.argmax([ x[:,1] for x in PIreader] ), 0] ))

	    print(f"New {q} current value: ", x)
    
	    #save new quad value to file
	    f= open(f"new{q}Value.txt", "a+")
	    new_c = float(x)
	    f.write(f'{new_c}\n')
	    f.close()

	    #set quad to new value
	    SetQuad(q, new_c)
	    print(f"{q} set.")

        ####################
	    """#############""""
	    ####################

	    #continue or not
	    if (tbl == 'y'): 
		    cont= input("Continue with same quad? y/n ")
	    elif (tbl == 'n' and count ==10):
		    count = 0
		    cont = input("Continue with same quad? y/n ")

print(f"All {len(quad_list)} quads optimized.")


#select max 1/width from results 
#check if (init (first val) - best tune current)>0.01%, if yes, count quad and save diff
#for each quad that was different, divide diff by count and add to init, then set to that value
