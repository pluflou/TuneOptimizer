import numpy as np
import gaussianprocess as gp
from time import *
from setup import *
from epics import caput
import sys, math
import os, shutil, signal
import subprocess as commands
import re
import multiprocessing
import itertools

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

#get init values for each quad
#set ps for each quad here         #take range of fine tuning as +/- 15% of init value

for q in quad_list:

    cont = 'y'

    while (cont == 'y' and count<11):
	
	    #import current state
	    #Get initial quad values
	    q_init = GetQuad() #am i guetting the rd or the cset?

	    #Tuning quad
	    #take picture at init values
	    SetQuad(rand from ps )
	    sleep(10)
	    rand_im= SaveIm('rand') #dont I need init width first?? need to run this once... 
	    sleep(2)

	    pos= GetBeamPos(rand_im, viewer)


        #peaks
	    pk_ = pos[2:4]
        #median centroid positions
	    med = pos[0:2]
        #widths (+/- 34.13%)
        wid = 1/(pos[5] - pos[4])

	    print("Centroid: ", med)
	    print("Width: ", 1/wid)

	    #save currents and width values to file
	    f= open(f"{q}Values_Widths.txt", "a+")
	    f.write(f'{q_init:.4f}\t{wid_1:.4f}\n') #?????????????
        f.write(f'{rand:.4f}\t{wid_2:.4f}\n')

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

	    print(f"New {q} value: ", x)
    

	    #save new quad value to file
	    f= open(f"new{q}Value.txt", "a+")
	    new_c = float(x)
	    f.write(f'{new_c}\n')
	    f.close()

	    #set quad to new value
	    caput(q_cset, new_c, wait= True)
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
#need a way to select best tune (max 1/width) from results 
#then for each check if (init (first val) - best tune)>0.01%, if yes, count quad and save diff
# for each quad that was different, divide diff by count and add to init, then set to that value
