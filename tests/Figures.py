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
import numpy as np
import matplotlib.pyplot as plt

# Functions to display and save results 
# from Figures import *

# Hyper-parameters
theta = 0.1 # Kernel parameter
eps = float(sys.argv[1]) # Acquisition function (probability of improvement) parameter
#eps = 0.05 # Acquisition function (probability of improvement) parameter
num_points = 250 # Number of points to sample when using PI to find the next corrector values

# Phase-space range when PI sampling: 
c1 = [-20,20] # Range in Amps for 1413H 
c2 = [0,0] # Range in Amps for 1413V 
c3 = [0,0] # Range in Amps for 1431H 
c4 = [0,0] # Range in Amps for 1431V 

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
    f = open('plot-sampling.txt','w') 	# Plot temp file
    jitter = random.uniform(0, 0.001)   # to prevent numerical issues due to iterating x's already checked
    for j in range(0, num_points):
        x = np.asmatrix( [ [c1[0] + j*(c1[1]-c1[0])/num_points + jitter], [random.uniform(c2[0], c2[1])], [random.uniform(c3[0], c3[1])], [random.uniform(c4[0], c4[1])] ] )  # column
        kk = k(x[:,0], x_observed, theta) 
        mean = mu( kk, KInv, f_observed )[0,0]
        sigma = sig( kk, KInv )[0,0]
        PIx = PI(mean, fxmax, eps, sigma)
        #if j%50 == 0:
        #	print j
        f.write( '{0: .6f} {1:.6f} {2:.6f} {3:.6f}\n' .format(x[0,0], mean, sigma, PIx) )
        if PIx > PImax:
            PImax = PIx
            xPImax = x
    f = open('temp-sampling.txt','a') 	# Writing to sampling file best case
    f.write( '{0: .6f} {1:.6f} {2:.6f} {3:.6f} {4:.6f} \n' .format(xPImax[0,0], xPImax[1,0], xPImax[2,0], xPImax[3,0], PImax) )
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
samplePI(num_points)
PIreader = np.asmatrix(np.loadtxt('temp-sampling.txt'))
xPImax = np.transpose(np.asmatrix( PIreader[ np.argmax([ x[:,4] for x in PIreader] ), [0]] ))[0,0]
PImax = np.transpose(np.asmatrix( PIreader[ np.argmax([ x[:,4] for x in PIreader] ), [4]] ))[0,0]

print(xPImax, PImax)

reader = np.asmatrix(np.loadtxt('plot-sampling.txt'))
x = np.asarray(np.transpose(np.asmatrix(reader[:,[0]]))).reshape(-1)
mean = np.asarray(np.transpose(np.asmatrix(reader[:,1]))).reshape(-1)
sigma = np.asarray(np.transpose(np.asmatrix(reader[:,2]))).reshape(-1)
PIx = np.asarray(np.transpose(np.asmatrix(reader[:,3]))).reshape(-1)

plt.subplot(211)
plt.plot( x, mean )
plt.fill_between( x, mean+sigma, mean-sigma, facecolor="gray", alpha=0.15 )
#print ( np.array(x_observed[0,:]).reshape(-1), np.asarray(f_observed).reshape(-1) )
plt.scatter ( np.array(x_observed[0,:]).reshape(-1), np.asarray(f_observed).reshape(-1) )
plt.xlabel("c1")
plt.ylabel("distance")
axes = plt.gca()
axes.set_ylim([-1,1])
plt.subplot(212)
plt.scatter( x, PIx ) 
plt.plot( xPImax, PImax )
plt.xlabel("c1")
plt.ylabel("PI")
#plt.savefig('ResQ2-%03d.pdf'%i)
plt.show()
plt.close()
    


