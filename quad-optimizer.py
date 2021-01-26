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

q_init = {}
q_ps = {}

#take picture at init values
init_im = SaveIm('init', viewer)
sleep(2)

#get initial beam spot width
pos_init = GetBeamPos(init_im, viewer)


#widths (+/- 34.13%)
try:
	wid_init = (pos_init[5] - pos_init[4])
	inverse_wid_init = 1/wid_init	
except RuntimeWarning:
	if (wid_init == 0):
		inverse_wid_init = 0.0
		print("Init width is zero.")

#start optimizing quads
for q in quad_list:

	cont = 'y'

	print(f"Starting {q} optimization.")
	#get init values for each quad
	q_init[q] = GetMagnet(q)

	#initialize phase space as +/- 15% of init value
	q_ps[q] = [ 0.85*q_init[q] , 1.15*q_init[q] ]

	
	#start with a random point
	rand_current = random.uniform(q_ps[q][0], q_ps[q][1]) 	
	SetMagnet(q, rand_current)

	#write inital value to file
	f= open(f"GP_results/{q}Values_Widths.txt", "a+")
	f.write(f'{q_init[q]:3.4f}\t{inverse_wid_init:3.4f}\n')
	f.close()

	while (cont == 'y' and count< iter_max+1):
		#starting with this state
		q_current = GetMagnet(q)
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
				print("New width is zero.")

		print(f"Inverse init width: {inverse_wid_init:.2f}")
		print(f"Inverse new width: {inverse_wid_gp:.2f}")
		
		#save currents and width values to file
		f= open(f"GP_results/{q}Values_Widths.txt", "a+")
		f.write(f'{q_current:3.4f}\t{inverse_wid_gp:3.4f}\n')
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
		reader = np.array(np.loadtxt(f'GP_results/{q}Values_Widths.txt'))

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
		f = open(f'GP_results/{q}results.txt','a') 	# Writing to sampling file best case
		f.write("{0:.2f} {1:.2f} {2:.2f}\n".format(theta, eps, newdistPoints))
		f.close()
    
        	#save new quad value to file
		f= open(f"GP_results/new{q}Value.txt", "a+")
		new_c = float(x)
		f.write(f'{new_c}\n')
		f.close()

        	####################
		"""#############"""
		####################

		#continue or not
		if (tbl == 'y'): 
            		cont= input("Continue with same quad? y/n ")

		elif (tbl == 'n' and count == iter_max):
	    		count = 0
	    		cont = input("Continue with same quad? y/n ")

		if (cont=='n'):
			SetMagnet(q, q_init[q])
			print(f"{q} set back to original value.")
		else:
			#set quad to new value
			SetMagnet(q, new_c)
			print(f"{q} set to new value.")


##########################
##########################
print("Adjusting quads...")
#select max 1/width from results 
q_diff = {}
count_q = 0 

for q in quad_list:

	q_best = 0
	#loading results
	results = np.loadtxt(f"GP_results/{q}Values_Widths.txt")
	#getting current corresponding to max 1/width
	q_best = results[results[:,1].argmax(), 0]

	q_diff[q] = q_best - q_init[q]
	wid_diff_percent = (1/np.max(results[:,1])-wid_init)/wid_init*100

	if (np.abs(q_diff[q]/q_init[q]) >= 0.0001 ):
		#if the difference in I is greater than 0.01%, optimize this quad
		count_q = count_q + 1
		print(f"{q} optimization changed the width by {wid_diff_percent:.2f}% from a difference in current of {(q_diff[q]/q_init[q]*100):.2f}%.")
	else:
		q_diff[q] = 0
		print(f"{q} does not need adjusting. Diff in I < 0.01%. Diff in widths {wid_diff_percent:.2f}%.")

#once we have checked what quads need to be changed, now we set them to the final value
if (count_q == 0):
	print("No quads needs optimizing. Exiting program")
	exit()

for q in quad_list:
	print(f"{q} will be adjusted by {q_diff[q]:.2f}/{count_q} A.")
	new_c = q_init[q] + q_diff[q]/count_q
	SetMagnet(q, new_c)

print(f"All {len(quad_list)} quads optimized.")
sleep(5)

#get final width 
final_im= SaveIm('final_gp', viewer)
sleep(2)
pos_final = GetBeamPos(final_im, viewer)
wid_final = pos_final[5] - pos_final[4]

print(f"Init width: {wid_init:.2f}.")
print(f"Final width: {wid_final:.2f}.")
print(f"Total change: {((wid_final-wid_init)/wid_init*100):.2f}%.")




