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

## if in troubleshoot mode you can change the eps at every step
tbl = 'n'
## if no in tbl mode this is set to the following eps
count = 0
iter_max = 1 # number of iterations for each quad 

##I did not yet implement the printing of the images when it's in tbl mode
print("Make sure to delete the past quad GP text files.")

quad_list  = input("Enter which quads to optimize (i.e. q2, q3, q4): ").lower()
viewer     = input("Enter viewer location (i.e. D1542): ").capitalize()
theta      = input("Enter theta (kernel param): ")
eps_stable = input("Enter eps (prob. of improvement): ")
sigma_noise_input = input("Enter sigma for noise: ")

#getting list of quads to loop through
quad_list = [x.lstrip().rstrip() for x in quad_list.split(",")]

q_init = {}
q_wid_init = {}
q_ps = {}

for q in quad_list:

	cont = 'y'

	print(f"Starting {q} optimization.")
	#get init values for each quad
	q_init[q] = GetMagnet(q)
	#initialize phase space as +/- 15% of init value
	q_ps[q] = [ 0.85*q_init[q] , 1.15*q_init[q] ]

	#take picture at init values
	#init_im = SaveIm('init', viewer)
	sleep(2)

	#get initial beam spot width
	#pos_init = GetBeamPos(init_im, viewer)

	#TESTING
	pos_init = [0,1,2,3, 4, 5] 
	q_ps[q] = [-10,10]

	#widths (+/- 34.13%)
	try:
		wid_init = (pos_init[5] - pos_init[4])
		inverse_wid_init = 1/wid_init
	
	except RuntimeWarning:
		if (wid_init == 0):
			inverse_wid_init = 0.0
		print("Init width is zero.")

	q_wid_init[q] = wid_init
	#write inital value to file
	f= open(f"{q}Values_Widths.txt", "a+")
	
	#TESTING
	q_init[q], inverse_wid_init = random.uniform(-10,10), random.uniform(0,1)

	f.write(f'{q_init[q]:.4f}\t{inverse_wid_init:.4f}\n')
	f.close()

	while (cont == 'y' and count< iter_max+1):
	
		#selecting a random new state
		rand = random.uniform(q_ps[q][0], q_ps[q][1])

		#set quad to new random current and get new width
		SetMagnet(q, rand) 
		sleep(10)
		#rand_im= SaveIm('rand', viewer)
		sleep(2)

		#pos_rand = GetBeamPos(rand_im, viewer)

		#TESTING
		pos_rand = [0,1,2,3,4,5] 
		
        	#widths (+/- 34.13%)
		try:
			wid_rand = pos_rand[5] - pos_rand[4]
			inverse_wid_rand = 1/wid_rand

		except RuntimeWarning:
			if (wid_rand == 0):
				inverse_wid_rand = 0.0
			print("New width is zero.")

		print(f"Inverse init width: {inverse_wid_init:.2f}")
		print(f"Inverse new width: {inverse_wid_rand:.2f}")
		

		#save currents and width values to file
		f= open(f"{q}Values_Widths.txt", "a+")

		#TESTING
		rand, wid_rand = random.uniform(-10,10), random.uniform(0,1)

		f.write(f'{rand:.4f}\t{wid_rand:.4f}\n')
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
		ps_list = [q_ps[q]] #phase space for quad

		# Reading file with corrector values and measured distance between peaks
		reader = np.array(np.loadtxt(f'{q}Values_Widths.txt'))
		x_observed = np.reshape( np.transpose(reader[:,0]), (1,-1) )#to 2D row
		f_observed = np.reshape( reader[:,1],               (-1,1) ) #to 2D column
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
		x = PIreader[ np.argmax(PIreader[:,1]), 0]

		print(f"New {q} current value: {x:.2f}")

		x_observed_last = x_observed[:, -1]
		newdistPoints = gp.distPoints(x_observed_last, x) # calculating distance between points
		print("Theta: {0:.2f}, eps: {1:.2f}, dist. bet. points: {2:.2f}".format(theta, eps, newdistPoints))
		f = open(f'{q}results.txt','a') 	# Writing to sampling file best case
		f.write("{0:.2f} {1:.2f} {2:.2f}\n".format(theta, eps, newdistPoints))
		f.close()
    
        	#save new quad value to file
		f= open(f"new{q}Value.txt", "a+")
		new_c = float(x)
		f.write(f'{new_c}\n')
		f.close()

		#set quad to new value
		SetMagnet(q, new_c)
		print(f"{q} set.")

        	####################
		"""#############"""
		####################

		#continue or not
		if (tbl == 'y'): 
            		cont= input("Continue with same quad? y/n ")
		elif (tbl == 'n' and count == iter_max):
	    		count = 0
	    		cont = input("Continue with same quad? y/n ")

print("Adjusting quads...")
#select max 1/width from results 
q_diff = {}
count_q = 0 

for q in quad_list:

	q_best = 0
	#loading results
	results = np.loadtxt(f"{q}Values_Widths.txt")
	#getting current corresponding to max 1/width
	q_best = results[results[:,1].argmax(), 0]
	q_diff[q] = q_best - q_init[q]
	wid_diff_percent = (np.max(results[:,1])-q_wid_init[q])/(q_wid_init[q])*100

	if ( np.abs(q_diff[q]) > 0.0001 ):
		#if the difference is greater than 0.01%, optimize this quad
		count_q = count_q + 1
		print(f"{q} optimization changed the width by {wid_diff_percent:.2f}%.")
		print(f"{q} will be adjusted by {q_diff[q]:.2f}/N A.")
	else:
		q_diff[q] = 0
		print(f"{q} does not need adjusting. Diff in I < 0.01%. Diff in widths {wid_diff_percent:.2f}%.")

#once we have checked what quads need to be changed, now we set them to the final value
for q in quad_list:
	new_c = q_init[q] + q_diff[q]/count_q
	SetMagnet(q, new_c)

print(f"All {len(quad_list)} quads optimized.")

	

