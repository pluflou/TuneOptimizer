#!/usr/bin/env python

import sys, math
import os, shutil, signal
#import commands
import subprocess as commands
import re
import random
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm
import time
import multiprocessing
import itertools
import timeit

# Functions to display and save results 
# from Figures import *

# Hyper-parameter
num_points = 100000 # Number of points to sample
sigma2 = 0.0**2 # sigma # 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0

# Returns kernel
def kernel( x1, x2, theta ) :
    x1 = np.asarray(x1).reshape(-1)
    x2 = np.asarray(x2).reshape(-1)
    return np.exp( -1/(2*np.power(theta,2))*np.dot(x1-x2,x1-x2) ) 

# Returns vector (column) k at position x (vector has information at position x due to observations) 
def k(x, x_observed, theta) :
    num_observations = np.shape(x_observed)[1]
    k = np.zeros(shape=(num_observations,1)) #column
    for i in range(0, num_observations):
        #print(i, x, x_observed[:,i])
        k[i][0] = kernel(x, x_observed[:,i], theta)
    return np.asmatrix(k)

# Returns covariance matrix with information from observations
def K(x_observed, theta):
    num_observations = np.shape(x_observed)[1]
    # Constructing Kernel observations
    K = np.zeros(shape=(num_observations,num_observations))
    for i in range(0, num_observations):
        for j in range(0, num_observations):
            K[i][j] = kernel( x_observed[:,i], x_observed[:,j], theta )
    return np.asmatrix(K) + sigma2*np.identity(num_observations)

# returns distance between the latest observations
def distPoints(x_observed_last, x):
    x1 = np.asarray( x_observed_last ).reshape(-1)
    x2 = np.asarray( x ).reshape(-1)
    dist = np.sqrt(np.dot(x1-x2,x1-x2))     
    return dist 

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

# Return expectation of improvement
def EI(mean, fxmax, eps, sigma):
    zz = (mean-fxmax-eps)/sigma
    return (mean-fxmax-eps)*norm.cdf(zz)+sigma*norm.pdf(zz)
	
# Sample the PI/EI over phase space
def samplePS(num_points, fxmax) :
    PImax = 0
    for j in range(0, num_points):
        x = np.asmatrix( [ [random.uniform(-10, 10)],[random.uniform(-10, 10)], [random.uniform(-10, 10)], [random.uniform(-10, 10)]  ] )  # column
        #if j%50 == 0:
        #    print(x[:,0], x_observed)
        kk = k(x[:,0], x_observed, theta) 
        #if j%50 == 0:
        #    print("past kk")
        mean = mu( kk, KInv, f_observed )[0,0]
        sigma = sig( kk, KInv )[0,0]
        #PIx = PI(mean, fxmax, eps, sigma)
        PIx = EI(mean, fxmax, eps, sigma)
        if PIx > PImax:
            PImax = PIx
            xPImax = x
    f = open('temp-sampling.txt','a') 	# Writing to sampling file best case
    f.write( '{0: .6f} {1:.6f} {2:.6f} {3:.6f} {4:.6f} \n' .format(xPImax[0,0], xPImax[1,0], xPImax[2,0], xPImax[3,0], PImax) )
    return 0

def maxObservation(theta) :
    fxmax = 0
    num_observations = np.shape(x_observed)[1]
    for i in range(0, num_observations):
        kk = k( x_observed[:,i], x_observed, theta) 
        mean = mu( kk, KInv, f_observed )[0,0]
        if mean > fxmax:
            fxmax = mean
            xmax = x_observed[:,i]
    return fxmax, xmax


# Start of main ------------------------------------------------------------------------------------------------------------

cmd = 'rm -f results.txt'
failure, output = commands.getstatusoutput(cmd)

readMatrix =  np.asmatrix(np.loadtxt('correctorValues_DistanceRun369_success.txt')) 
x_observed = np.transpose(np.asmatrix(readMatrix[:, 0:4]))
f_observed =  np.transpose(np.asmatrix(readMatrix[:,4]))

f_observed = np.transpose(f_observed)  # transform to column
#fxmax = np.max(f_observed)

if __name__ == "__main__":
    for theta in [0.01, 0.02, 0.03, 0.05, 0.07, 0.1, 0.2, 0.5, 0.7, 1, 2]:
         for eps in [0.01, 0.02, 0.03, 0.05, 0.1, 0.2]:
            print("theta = {0}, eps = {1}".format(theta, eps))	
            KK = K(x_observed, theta)  # Covariance matrix
            KInv = np.linalg.inv(KK)   # Inverse of covariance matrix
            fxmax, xmax =  maxObservation(theta)

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
                pool.apply_async( samplePS, [250,fxmax] )
            pool.close()
            pool.join()
            reader = np.asmatrix(np.loadtxt('temp-sampling.txt'))
            x = np.transpose(np.asmatrix( reader[ np.argmax([ x[:,4] for x in reader] ), [0,1,2,3]] ))
            x_observed_last = x_observed[:, -1]
            newdistPoints = distPoints(x_observed_last, x) # calculating distance between points

            print("{0:.2f} {1:.2f} {2:.2f}".format(theta, eps, newdistPoints))
            f = open('results.txt','a') 	# Writing to sampling file best case
            f.write("{0:.2f} {1:.2f} {2:.2f}\n".format(theta, eps, newdistPoints))



