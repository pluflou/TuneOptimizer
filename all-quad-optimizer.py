import os, shutil, signal
import sys, math
import warnings

import subprocess as commands
import re
import random
import multiprocessing
import itertools
import numpy as np

import gaussianprocess as gp
from time import sleep
from setup import GetBeamPos, GetMagnet, SetMagnet, SaveIm

warnings.filterwarnings("error")
warnings.simplefilter("ignore", category=PendingDeprecationWarning)

## if in troubleshoot mode you can change the eps at every step
tbl = 'n'
## if not in tbl mode this is set to the following eps
count = 0
iter_max = 10 # number of iterations for each quad 

##I did not yet implement the printing of the images when it's in tbl mode
print("Make sure to delete the past quad GP text files.")

quad_list  = input("Enter which quads to optimize (i.e. q2, q3, q4): ").lower()
viewer     = input("Enter viewer location (i.e. D1542): ").capitalize()
theta      = input("Enter theta (kernel param): ")
eps_stable = input("Enter eps (prob. of improvement): ")
sigma_noise_input = input("Enter sigma for noise: ")

#getting list of quads to loop through
quad_list = [x.lstrip().rstrip() for x in quad_list.split(",")]

q_num = len(quad_list)
q_init = {}
q_ps = {}

cont = 'y'

############################
############################

#take picture at init values
init_im = SaveIm('init', viewer)
sleep(2)

#get initial beam spot width
pos_init = GetBeamPos(init_im, viewer)


#widths (+/- 34.13%)
wid_init = (pos_init[5] - pos_init[4])
inverse_wid_init =  1/wid_init

#write value to file
f= open(f"GP_results/{'_'.join(quad_list)}Values_Widths.txt", "a+")
for q in quad_list:
	f.write(f'{q_init[q]:3.4f}\t')
f.write(f'{inverse_wid_init:3.4f}\n')
f.close()


#save intial state and set first random sample point
for q in quad_list:
	#get init values for each quad
	q_init[q] = GetMagnet(q)

	#initialize phase space as +/- 15% of init value
	q_ps[q] = [ 0.85*q_init[q] , 1.15*q_init[q] ]

	#sample one random point
	rand = random.uniform(q_ps[q][0], q_ps[q][1])
	SetMagnet(q, rand)
sleep(5)

while (cont == 'y' and count< iter_max+1):
	
	q_current = {}
	#starting with this state
	for q in quad_list:
		q_current[q] = GetMagnet(q)

	gp_im= SaveIm('gp', viewer)
	sleep(2)
	pos_gp = GetBeamPos(gp_im, viewer)

		
        #widths (+/- 34.13%)
	try:
		wid_gp = pos_gp[5] - pos_gp[4]
		inverse_wid_gp = 1/wid_gp
	except RuntimeWarning:
		if (wid_gp == 0):
			inverse_wid_gp = 0.0
			print("Width is zero.")

	print(f"Inverse width: {inverse_wid_gp:.2f}")
		
	#write value to file
	f= open(f"GP_results/{'_'.join(quad_list)}Values_Widths.txt", "a+")
	for q in quad_list:
		f.write(f'{q_current[q]:3.4f}\t')
	f.write(f'{inverse_wid_gp:3.4f}\n')
	f.close()

	#run GP 
	if (tbl == 'y'):
	    	eps_input= input("Enter the desired acquisition function parameter:")	
	else:
	    	eps_input= eps_stable
	    	count = count + 1
	
	####################
	"""##GaussProc##"""
	####################

        # Hyper-parameters
	theta = float(theta) # Kernel parameter
	eps = float(eps_input) # Acquisition function (probability of improvement) parameter
	num_points = 100000 # Number of points to sample when using PI to find the next corrector values
	sigma2 = float(sigma_noise_input)**2 #squaring the noise term

	ps_list = [] #phase space list for gp
	for q in quad_list:
		ps_list.append(q_ps[q]) #phase space of quads 

	# Reading file with corrector values and measured distance between peaks
	reader = np.array(np.loadtxt(f"GP_results/{'_'.join(quad_list)}Values_Widths.txt"))

	#take first columns corresponding to quad values as x and the last column with the dist as f
	f_observed = np.reshape( reader[:, q_num],(-1,1) ) #to 2D column
	#NOTE: np.asmatrix is pending deprecation. I have no idea why I get no warning when used in beam-optimizer.py
	#NOTE I suppressed it here. The two lines below show the alternative I was using that only works for ONE quad (that's why quad-opt works)
	#NOTE This should get investigated to see why it fails for more than one quad and what I can use to replace np.asmatrix()
	#x_observed = reader[:, np.arange(0, q_num)] #to 2D row
	x_observed = np.transpose(np.asmatrix(reader[:, np.arange(0, q_num)])) #to 2D row

	# Doing GP stuff 
	KK = gp.K(x_observed, theta, sigma2)  # Covariance matrix
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
		pool.apply_async( gp.samplePS, [250, f_observed, x_observed, theta, eps, KInv, ps_list] )
	pool.close()
	pool.join()

	PIreader = np.array(np.loadtxt('temp-sampling.txt'))
	#find the row where the distance is the max and get the quad currents in that row
	x = PIreader[ np.argmax(PIreader[:,q_num]), np.arange(0, q_num)] 

	print("New quad values:\n",  np.array_str(x, precision=2))

	x_observed_last = x_observed[:, -1]
	newdistPoints = gp.distPoints(x_observed_last, x) # calculating distance between points
	print("Theta: {0:.3f}, eps: {1:.3f}, dist. bet. points: {2:.2f}".format(theta, eps, newdistPoints))
	f = open(f"GP_results/{'_'.join(quad_list)}_results.txt",'a') 	# Writing to sampling file best case
	f.write("{0:.2f} {1:.2f} {2:.2f}\n".format(theta, eps, newdistPoints))
	f.close()
    
        #save new quad value to file and set quads
	f= open(f"GP_results/new_{'_'.join(quad_list)}_Values.txt", "a+")
	for i,q in enumerate(quad_list):
		SetMagnet(q, float(x[i]))
		print(f"{q} set.")
		f.write(f'{float(x[i])}\t')
	f.write('\n')
	f.close()

        ####################
	"""#############"""
	####################

	#continue or not
	if (tbl == 'y'): 
		cont= input("Continue? y/n ")
	elif (tbl == 'n' and count == iter_max):
		count = 0
		cont = input("Continue? y/n ")

##########################
##########################

print("Adjusting quads...")
#select max 1/width from GP_results 
q_diff = {}
count_q = 0

	
#loading GP_results
GP_results = np.loadtxt(f"GP_results/{'_'.join(quad_list)}Values_Widths.txt")
#getting current corresponding to max 1/width
q_best = GP_results[GP_results[:, q_num].argmax(), np.arange(0, q_num)] 

for i,q in enumerate(quad_list):

	q_diff[q] = q_best[i] - q_init[q]

	if (np.abs(q_diff[q])/q_init[q] >= 0.0001 ):
		#if the difference in I is greater than 0.01%, optimize this quad
		count_q = count_q + 1
		print(f"{q} optimization changed the current by {(q_diff[q]/q_init[q]*100):.2f}%.")
	else:
		q_diff[q] = 0
		print(f"{q} does not need adjusting. Diff in I < 0.01%.")

#once we have checked what quads need to be changed, now we set them to the final value
if (count_q == 0):
	print("No quads need optimizing. Exiting program")
	exit()

for q in quad_list:
	print(f"{q} will be adjusted by {q_diff[q]:.2f}/{count_q} A.")
	new_c = q_init[q] + q_diff[q]/count_q
	SetMagnet(q, new_c)

#get the final width change between start and best state
width_change  =  np.abs(1/GP_results[0,q_num] - 1/np.max(GP_results[:,q_num]) )/ (1/GP_results[0,q_num]) *100

print(f"All {len(quad_list)} quads optimized.")
print(f"Final change in width is {width_change:.2f}%.")

	



