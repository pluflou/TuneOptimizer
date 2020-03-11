#!/usr/bin/env python

import sys, math
import os, shutil, signal
#import commands
import subprocess as commands
import re
import random
import numpy as np
from scipy.stats import norm
import multiprocessing
import itertools
from epics import caput

# Functions to display and save results 
# from Figures import *

# Hyper-parameters
theta = float(sys.argv[2]) # Kernel parameter
eps = float(sys.argv[1]) # Acquisition function (probability of improvement) parameter
#eps = 0.05 # Acquisition function (probability of improvement) parameter
num_points = 100000 # Number of points to sample when using PI to find the next corrector values

# Phase-space range when PI sampling: 
c1 = [-10,10] # Range in Amps for 1413H 
c2 = [-10,10] # Range in Amps for 1413V 
c3 = [-10,10] # Range in Amps for 1431H 
c4 = [-10,10] # Range in Amps for 1431V 

#PV names for correctors
h13_cset= 'REA_BTS34:DCH_D1413:I_CSET'
v13_cset='REA_BTS34:DCV_D1413:I_CSET'
h31_cset= 'REA_BTS34:DCH_D1431:I_CSET'
v31_cset= 'REA_BTS34:DCV_D1431:I_CSET'

# Returns kernel
def kernel( x1, x2, theta) :
    x1 = np.asarray(x1).reshape(-1)
    x2 = np.asarray(x2).reshape(-1)
    return np.exp( -1/(2*np.power(theta,2))*np.dot(x1-x2,x1-x2) ) 

# Returns vector (column) k at position x (vector has information at position x due to observations) 
def k(x, x_observed, theta) :
    num_observations = np.shape(x_observed)[1]
    k = np.zeros(shape=(num_observations,1)) #column
    for i in range(0, num_observations):
        k[i][0] = kernel(x, x_observed[:,i], theta)
    return np.asmatrix(k)

# Returns covariance matrix K with information from observations
def K(x_observed, theta):
    num_observations = np.shape(x_observed)[1]
    # Constructing Kernel observations
    K = np.zeros(shape=(num_observations,num_observations))
    for i in range(0, num_observations):
        for j in range(0, num_observations):
            K[i][j] = kernel( x_observed[:,i], x_observed[:,j], theta )
    return np.asmatrix(K)

# Returns mean mu at position x
def mu( k, KInv, f_observed ):
    return np.transpose(k)*KInv*f_observed

# Returns sigma at position x
def sig( k, KInv ):
    tmp = 1- np.transpose(k)*KInv*k 
    if tmp[0,0] <= 0:
        return np.asmatrix([[0.0001]])
    else:
        return np.sqrt(tmp)

# Returns probability of improvement
def PI(mean, fxmax, eps, sigma):
    return norm.cdf((mean-fxmax-eps)/sigma)
	
# Samples the PI over phase space
def samplePI(num_points) :
    fxmax = np.max(f_observed[0,:]) # Maximum of the observations
    PImax = 0
    for j in range(0, num_points):
        x = np.asmatrix( [ [random.uniform(c1[0], c1[1])], [random.uniform(c2[0], c2[1])], [random.uniform(c3[0], c3[1])], [random.uniform(c4[0], c4[1])] ] )  # column
        kk = k(x[:,0], x_observed, theta) 
        mean = mu( kk, KInv, f_observed )[0,0]
        sigma = sig( kk, KInv )[0,0]
        PIx = PI(mean, fxmax, eps, sigma)
        #if j%50 == 0:
        #	print j
        if PIx > PImax:
            PImax = PIx
            xPImax = x
    f = open('temp-sampling.txt','a') 	# Writing to sampling file best case
    f.write( '{0: .6f}\t{1:.6f}\t{2:.6f}\t{3:.6f}\t{4:.6f} \n' .format(xPImax[0,0], xPImax[1,0], xPImax[2,0], xPImax[3,0], PImax) )
    return 0


# Start of main -------------------------------------------------------------------------------

# Reading file with corrector values and measured distance between peaks
reader = np.asmatrix(np.loadtxt('correctorValues_Distance.txt'))
x_observed = np.transpose(np.asmatrix(reader[:,[0,1,2,3]]))
f_observed = np.transpose(np.asmatrix(reader[:,4]))

# Doing GP stuff
f_observed = np.transpose(f_observed)  # transform to column 
KK = K(x_observed, theta)  # Covariance matrix
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
    pool.apply_async( samplePI, [250] )
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
