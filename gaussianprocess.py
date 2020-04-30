#!/usr/bin/env python

import sys, math
import os, shutil, signal
import re
import random
import numpy as np
from scipy.stats import norm
import itertools

# Functions to display and save results 
# from Figures import *
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
def samplePI(num_points, f_obs, x_obs, theta, eps, KInv, ps_par) :
    fxmax = np.max(f_obs[0,:]) # Maximum of the observations
    PImax = 0
    ps = np.array(ps_par)
    ps_rows = ps.shape[0]
    x = []

    for j in range(0, num_points):
        # create column matrix from random vals from phase space 
        for k in range(ps_rows):
            x.append(random.uniform(ps[k][0], ps[k][1])) 
        x = np.transpose( np.asmatrix(x))
        
        kk = k(x[:,0], x_obs, theta) 
        mean = mu( kk, KInv, f_obs )[0,0]
        sigma = sig( kk, KInv )[0,0]
        PIx = PI(mean, fxmax, eps, sigma)
        #if j%50 == 0:
        #	print j
        if PIx > PImax:
            PImax = PIx
            xPImax = x

    xPImax_col = np.transpose(np.array(xPImax[:,0]))
    f = open('temp-sampling.txt','a') 	# Writing to sampling file best case
    for i in range(ps_rows):
        f.write( '{0:.6f}\t'.format(xPImax_col[0][i]) )
    f.write( '{0: .6f}\n' .format(PImax) )

    return 0
