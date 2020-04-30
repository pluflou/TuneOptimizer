import os, shutil, signal
import sys, math

import subprocess as commands
import re
import multiprocessing
import itertools
import numpy as np
from epics import caput

import gaussianprocess as gp
from time import sleep
from setup import GetBeamPos, GetCorr, GetQuads, SetQuads, SaveIm, Dist
from setup import h13_cset, h13_ird, h31_cset, h31_ird
from setup import v13_cset, v13_ird, v31_cset, v31_ird


cont = 'y'
## if in troubleshoot mode you can change the eps at every step
tbl = 'n'
## if no in tbl mode this is set to the following eps
count = 0

##I did not yet implement the printing of the images when it's in tbl mode
print("Make sure to delete the past corrector text files.")

theta = input("Enter theta (kernel param): ")
eps_stable = input("Enter eps (prob. of improvement): ")

viewer = 'D1542' #when optimizing through JENSA we always use this viewer

# Phase-space range when PI sampling: 
ps1 = [-10,10] # Range in Amps for 1413H 
ps2 = [-10,10] # Range in Amps for 1413V 
ps3 = [-10,10] # Range in Amps for 1431H 
ps4 = [-10,10] # Range in Amps for 1431V 

while (cont == 'y' and count<11):
	
	#import current state
	#Get initial corrector values
	h13_init, v13_init, h31_init, v31_init= GetCorr()
	#Get initial quad values
	q1_init, q2_init, q3_init, q4_init= GetQuads()

	#Tuning Q1 and Q2

	#take picture with all at init values
	SetQuads(q1_init, q2_init, 0, 0)
	sleep(10)
	all_nom_im= SaveIm('allNom')
	sleep(2)

	#take picture with all at zero
	SetQuads(0, 0, 0, 0)
	pos_1= GetBeamPos(all_nom_im, viewer)
	sleep(10) #might need to increase this if the jumps in current are big
	all_zero_im= SaveIm('allZero')
	sleep(2)

	#take picture with Q1 at half # CHANGED.... Q2 also half
	SetQuads(q1_init/2, q2_init/2, 0, 0)
	pos_2= GetBeamPos(all_zero_im, viewer)
	sleep(10)
	q1_half_im= SaveIm('q1half')
	sleep(2)
	
	#take picture with Q2 at half # CHANGED... Q1 = 0
	SetQuads(0, q2_init/2, 0, 0)
	pos_3= GetBeamPos(q1_half_im, viewer)
	sleep(10)
	q2_half_im= SaveIm('q2half')
	sleep(2)
	
	#return quads to original values
	SetQuads(q1_init, q2_init, q3_init, q4_init)
	pos_4= GetBeamPos(q2_half_im, viewer)

	pk_1 = pos_1[2:4]
	pk_2 = pos_2[2:4]
	pk_3 = pos_3[2:4]
	pk_4 = pos_4[2:4]
	pos_1 = pos_1[0:2]
	pos_2 = pos_2[0:2]
	pos_3 = pos_3[0:2]
	pos_4 = pos_4[0:2]

	#get quadratic distance from centroids
	print("Centroids: ", pos_1, pos_2, pos_3, pos_4)
	#print("Peaks: ", pk_1, pk_2, pk_3, pk_4)
	distance= Dist(pos_1, pos_2, pos_3, pos_4)
	print("Dist= ", distance)

	#save corrector values and distance to file
	f= open("correctorValues_Distance.txt", "a+")
	c1, c2, c3, c4= GetCorr()
	f.write(f'{c1:.4f}\t{c2:.4f}\t{c3:.4f}\t{c4:.4f}\t{distance:.4f}\n')
	f.close()

	#run GP 
	if (tbl == 'y'):
		eps_input= input("Enter the desired acquisition function parameter:")	
	else:
		eps_input= eps_stable
		count = count + 1
	
	####################
    ####GaussProc######
	####################

    # Hyper-parameters
	theta = float(theta) # Kernel parameter
	eps = float(eps_input) # Acquisition function (probability of improvement) parameter
	num_points = 100000 # Number of points to sample when using PI to find the next corrector values
	ps_list = [ps1,ps2,ps3,ps4]

	# Reading file with corrector values and measured distance between peaks
	reader = np.asmatrix(np.loadtxt('correctorValues_Distance.txt'))
	x_observed = np.transpose(np.asmatrix(reader[:,[0,1,2,3]]))
	f_observed = np.transpose(np.asmatrix(reader[:,4]))

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
		pool.apply_async( gp.samplePI, [250, f_observed, x_observed, theta, eps, KInv, ps_list] )
	pool.close()
	pool.join()
	PIreader = np.asmatrix(np.loadtxt('temp-sampling.txt'))
	x = np.transpose(np.asmatrix( PIreader[ np.argmax([ x[:,4] for x in PIreader] ), [0,1,2,3]] ))

	print("New corrector values: ", x)

	#save new corrector values to file
	f= open("newCorrectorValues.txt", "a+")
	c1, c2, c3, c4= float(x[0]), float(x[1]), float(x[2]), float(x[3])
	f.write(f'{c1} {c2} {c3} {c4}\n')
	f.close()

	#set new corrector values
	caput(h13_cset, c1, wait= True)
	caput(v13_cset, c2, wait= True)
	caput(h31_cset, c3, wait= True)
	caput(v31_cset, c4, wait= True)
	print("Correctors set.")

    ####################
	####################

	#continue or not
	if (tbl == 'y'): 
		cont= input("Continue? y/n ")
	elif (tbl == 'n' and count ==10):
		count = 0
		cont = input("Continue? y/n ")
