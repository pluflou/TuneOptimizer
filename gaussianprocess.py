#!/usr/bin/env python

import random
import numpy as np
import matplotlib.pyplot as plt
import math
import datetime
# GPy: Gaussian processes library
import GPy
import GPyOpt
from GPyOpt.acquisitions import AcquisitionEI, AcquisitionLCB, AcquisitionMPI
from GPyOpt import Design_space  ## GPyOpt design space
from GPyOpt.models import GPModel

def x_grid_func(num_points, space):
    ''' Creates a grid of points that sample the phase space '''
    ps = space.get_continuous_bounds()
    ps_rows = len(ps)

    X_grid = []
    for j in range(0, num_points):
        x_array = []
        # create column matrix from random vals from phase space
        for k in range(ps_rows): #each row belongs to a device we're tuning
            x_array.append(random.uniform(ps[k][0], ps[k][1]))
        X_grid.append(x_array)
    return( np.asarray(X_grid) )

def returnObservations(x):
    ''' Sandbox function '''
    f = 0
    for m in x:
        f = f + np.sin(2 * m) + .2*m
    return( f  )

# Functions needed for plotting --------------

def evolution(filename = 'GP_results/test.txt', magnet_list = ['h13', 'v13', 'h31', 'v31']):
    ''' Plots and saves distance and magnetic fields as a function of iteration '''

    reader = np.asmatrix(np.loadtxt(filename))
    x_observed = np.asmatrix(reader[:,list(range(len(magnet_list))) ]).reshape(len(magnet_list),-1).T
    f_observed = np.asmatrix(reader[:,len(magnet_list)]).reshape(1,-1).T
    f_min = np.asarray([ np.min(f_observed[0:(i+1)]) for i in range(len(f_observed)) ]).T
    i_min = np.argmin(f_observed)

    num_steps =np.shape(x_observed)[0]
    n_rows = math.ceil(len(magnet_list)/2)
    f, sub = plt.subplots(n_rows+1, 2, sharex=True)
    #f.tight_layout() # to adjust spacing between subplots

    x = range(0, num_steps) # iterations
    y = f_observed
    yy = f_min

    sub[0,0].plot(x, y, 'k-')
    sub[0,0].set(ylabel='Distance [px]')
    sub[0,0].set_xlim(0, num_steps)
    sub[0,0].plot(x, yy, 'b-')
    sub[0,1].plot(x, y, 'k-')
    sub[0,1].set(ylabel='Distance [px]')
    sub[0,1].set_xlim(0, num_steps)
    sub[0,1].plot(x, yy, 'b-')

    for i in range(n_rows):
        y = np.asarray(x_observed[:,2*i]).reshape(-1)
        sub[i+1,0].plot(x, y, 'k-')
        sub[i+1,0].set(ylabel=magnet_list[2*i])
        sub[i+1,0].plot(i_min,y[i_min],'bo')

        if len(magnet_list) > 2*i + 1:
            y = np.asarray(x_observed[:,2*i+1]).reshape(-1)
            sub[i+1,1].plot(x, y, 'k-')
            sub[i+1,1].set(ylabel=magnet_list[2*i+1])
            sub[i+1,1].plot(i_min,y[i_min],'bo')

    f.subplots_adjust( wspace = 0.6, top = None, bottom = None )
    plt.savefig('ResFields-iter.pdf')
    plt.show()
    plt.close()
    return(None)

def GP_analysis(X, Y, X_grid):
    # X and Y are data points observed
    # X_grid are data points not yet observed
    # Use GP regression to fit the data
    k = GPy.kern.RBF(input_dim=X.shape[1])   # Hardcoded!!!!!!!!!!!!!!!!!!
    m = GPy.models.GPRegression(X, Y, k)
    m.kern.lengthscale.unconstrain_positive()
    #m.kern.lengthscale.set_prior(GPy.priors.Gaussian(10,2))
    m.kern.lengthscale.set_prior(GPy.priors.Gaussian(2,1))

    m.Gaussian_noise.variance.unconstrain_positive()
    m.Gaussian_noise.variance.set_prior(GPy.priors.Gaussian(3,3))

    #m.Gaussian_noise.fix(0.5)
    m.optimize('bfgs', max_iters=100)  # Hyper-parameters are optimized here

    # Predict the mean and covariance of the GP fit over the grid
    mean, Cov = m.predict(X_grid, full_cov=True)
    variance = np.diag(Cov)
    return mean, Cov, variance, m

def plot1D(filename = 'GP_results/test1.txt', magnet_list = ['h13', 'v13', 'h31', 'v31'], timestamp = "06-15_something", phase_space = [-10,10]):
    ''' Plots at every iteration GP. Requires some manual hardcoded interaction '''

    reader = np.asmatrix(np.loadtxt(filename))
    x_observed = np.asarray(reader[:,0])      # Hardcoded!!!!!!!!!
    f_observed = np.asarray(reader[:,-1])     # Hardcoded!!!!!!!!!

    n_rows = math.ceil(len(f_observed)/5) + 1
    f_mean, sub_mean = plt.subplots(n_rows, 5, sharex=True, sharey=False)
    f_mean.tight_layout() # to adjust spacing between subplots
    f_acq, sub_acq = plt.subplots(n_rows, 5, sharex=True, sharey=True)
    f_acq.tight_layout() # to adjust spacing between subplots

    num_points = 1000
    X_grid = np.linspace(phase_space[0], phase_space[1], num_points)[:,None]
    for i in range(n_rows-1):
        j = 0
        while len(f_observed) > 5*i + j and j < 5:
            X = x_observed[0:(5*i+j+1)]
            Y = f_observed[0:(5*i+j+1)]
            mean, Cov, variance, m = GP_analysis(X, Y, X_grid)
            sub_mean[i,j].plot( X_grid, mean)
            sub_mean[i,j].fill_between( X_grid[:,0], (mean.T+variance.T).T[:,0] , (mean.T-variance.T).T[:,0] , facecolor="gray", alpha=0.15 )
            sub_mean[i,j].scatter ( X, Y )

            model = GPModel(optimize_restarts=1, verbose=True)
            model.model = m
            space = Design_space([{'name': 'var1', 'type': 'continuous', 'domain': (phase_space[0], phase_space[1])}])
            acq = AcquisitionLCB(model, space, exploration_weight = 0.5)       # Hardcoded!!!!!!!!!
            alpha_full = acq.acquisition_function(X_grid)
            sub_acq[i,j].plot( X_grid, alpha_full)
            j = j+1

    f_mean.subplots_adjust( wspace = 0.3, top = None, bottom = None )
    f_mean.savefig(f'GP_results/dis_mean_M1-{timestamp}.pdf')
    f_acq.subplots_adjust( wspace = 0.3, top = None, bottom = None )
    f_acq.savefig(f'GP_results/dis_acq_M1-{timestamp}.pdf')
    #plt.show()
    plt.close()
    return(None)

def plot2D(filename = 'GP_results/test2.txt', magnet_list_2d = ['h13', 'v13', 'h31', 'v31'], timestamp = "06-15_something", phase_space=[-10,10]):
    ''' Plots at every iteration GP. Requires some manual hardcoded interaction '''

    reader = np.asmatrix(np.loadtxt(filename))
    xy_observed = np.asarray(reader[:,0:2])      # Hardcoded!!!!!!!!!
    f_observed = np.asarray(reader[:,-1])        # Hardcoded!!!!!!!!!

    n_rows = math.ceil(len(f_observed)/5) + 1
    f_mean, sub_mean = plt.subplots(n_rows, 5, sharex=True)#, sharey=True)
    f_mean.tight_layout() # to adjust spacing between subplots
    f_sigma, sub_sigma = plt.subplots(n_rows, 5, sharex=True)#, sharey=True)
    f_sigma.tight_layout() # to adjust spacing between subplots
    f_acq, sub_acq = plt.subplots(n_rows, 5, sharex=True)#, sharey=True)
    f_acq.tight_layout() # to adjust spacing between subplots
    
    #timestamp = (datetime.datetime.now()).strftime("%m-%d_%H-%M-%S")
    num_points = 100
    XY_grid = np.mgrid[phase_space[magnet_list_2d[0]][0]:phase_space[magnet_list_2d[0]][1]:0.3, phase_space[magnet_list_2d[1]][0]:phase_space[magnet_list_2d[1]][1]:0.3].reshape(2,-1).T  # Hardcoded!!!!!!!!!
    for i in range(n_rows-1):
        j = 0
        while len(f_observed) > 5*i + j and j < 5:
            XY = xy_observed[0:(5*i+j+1)]
            Z = f_observed[0:(5*i+j+1)]
            mean, Cov, variance, m = GP_analysis(XY, Z, XY_grid)
            xx = np.asarray(XY_grid[:,0])
            yy = np.asarray(XY_grid[:,1])
            xo = np.asarray(XY[:,0]).reshape(-1)
            yo = np.asarray(XY[:,1]).reshape(-1)
            sub_mean[i,j].scatter( xx, yy, c=mean.T[0],
                    vmin = min(mean.T[0]), vmax = max(mean.T[0]), edgecolors='none', cmap = 'GnBu')
            #print(min(mean.T[0]), max(mean.T[0]))
            sub_mean[i,j].scatter(xo, yo, c='k', marker='s')

            sub_sigma[i,j].scatter( xx, yy, c=variance,
                    vmin = min(variance), vmax = max(variance), edgecolors='none')
            sub_sigma[i,j].scatter(xo, yo, c='white')

            model = GPModel(optimize_restarts=1, verbose=True)
            model.model = m
            #space = Design_space([{'name': 'var1', 'type': 'continuous', 'domain': (-10, 10)},
             #                     {'name': 'var2', 'type': 'continuous', 'domain': (-10, 10)}])
            
            space = Design_space([ {'name': m, 'type': 'continuous', 'domain': (phase_space[m][0], phase_space[m][1])} for m in magnet_list_2d ])

            acq = AcquisitionLCB(model, space, exploration_weight = 0.5)       # Hardcoded!!!!!!!!!
            alpha_full = acq.acquisition_function(XY_grid)
            sub_acq[i,j].scatter( xx, yy, c=alpha_full.T[0],
                vmin = min(alpha_full.T[0]), vmax = max(alpha_full.T[0]), edgecolors='none', cmap = 'GnBu' )
            sub_acq[i,j].scatter(xo, yo, c='k', marker='s' )
            minXY = XY_grid[np.argmin(alpha_full)]
            sub_acq[i,j].scatter(minXY[0],minXY[1], marker = 'P')#, markersize = 1)

            j = j+1

    f_mean.subplots_adjust( wspace = 0.3, top = None, bottom = None )
    f_mean.savefig(f'GP_results/dis_mean_M1_M2-{timestamp}.pdf')
    f_sigma.subplots_adjust( wspace = 0.3, top = None, bottom = None )
    f_sigma.savefig(f'GP_results/dis_sigma_M1_M2-{timestamp}.pdf')
    f_acq.subplots_adjust( wspace = 0.3, top = None, bottom = None )
    f_acq.savefig(f'GP_results/dis_acq_M1_M2-{timestamp}.pdf')
    #plt.show()
    plt.close()

#evolution('GP_results/correctorValues_Distance_06-15_13-37.txt', magnet_list = ['h13', 'h31'])
#plot1D()
#plot2D()
