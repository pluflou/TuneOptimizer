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
    #plt.savefig('ResFields-iter.pdf')
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
    m.kern.lengthscale.set_prior(GPy.priors.Gaussian(10,2))   
    #m.kern.lengthscale.set_prior(GPy.priors.Gaussian(5,2))   

    m.Gaussian_noise.variance.unconstrain_positive()
    m.Gaussian_noise.variance.set_prior(GPy.priors.Gaussian(1,0.5))

    m.Gaussian_noise.fix(0.5)
    m.optimize('bfgs', max_iters=100)  # Hyper-parameters are optimized here

    # Predict the mean and covariance of the GP fit over the grid
    mean, Cov = m.predict(X_grid, full_cov=True)
    variance = np.diag(Cov)
    return mean, Cov, variance, m

def plot1D(filename = 'GP_results/test1.txt', magnet_list = ['h13', 'v13', 'h31', 'v31']):
    ''' Plots at every iteration GP. Requires some manual hardcoded interaction '''

    reader = np.asmatrix(np.loadtxt(filename))
    x_observed = np.asarray(reader[:,0])      # Hardcoded!!!!!!!!!
    f_observed = np.asarray(reader[:,-1])     # Hardcoded!!!!!!!!!

    #for i in range(3, len(f_observed)):
    for i in range(len(f_observed)-1, len(f_observed)):
        plt.subplot(211)
        num_points = 1000
        X_grid = np.linspace(-10, 10, num_points)[:,None]
        #X_grid = np.linspace(-15, 15, num_points)[:,None]
        X = x_observed[0:(i+1)]
        Y = f_observed[0:(i+1)]

        mean, Cov, variance, m = GP_analysis(X, Y, X_grid)
        plt.plot( X_grid, mean)
        plt.fill_between( X_grid[:,0], (mean.T+variance.T).T[:,0] , (mean.T-variance.T).T[:,0] , facecolor="gray", alpha=0.15 )
        plt.scatter ( X, Y )
        plt.ylabel("Distance [px]")

        axes = plt.gca()
        axes.set_ylim([-5,40])
        plt.subplot(212)
        model = GPModel(optimize_restarts=1, verbose=True)
        model.model = m
        space = Design_space([{'name': 'var1', 'type': 'continuous', 'domain': (-10, 10)}])
        #space = Design_space([{'name': 'var1', 'type': 'continuous', 'domain': (-15, 15)}])
        acq = AcquisitionLCB(model, space, exploration_weight = 3)       # Hardcoded!!!!!!!!!
        alpha_full = acq.acquisition_function(X_grid)
        plt.plot( X_grid, alpha_full )
        plt.xlabel("Magnet current")
        plt.ylabel("LCB")
        timestamp = (datetime.datetime.now()).strftime("%m-%d_%H-%M-%S")
        plt.savefig(f'GP_results/dis_M1-{timestamp}.pdf')
        plt.show()
        plt.close()
    return(None)

def plot2D(filename = 'GP_results/test2.txt', magnet_list = ['h13', 'v13', 'h31', 'v31']):
    ''' Plots at every iteration GP. Requires some manual hardcoded interaction '''

    reader = np.asmatrix(np.loadtxt(filename))
    xy_observed = np.asarray(reader[:,0:2])      # Hardcoded!!!!!!!!!
    f_observed = np.asarray(reader[:,-1])        # Hardcoded!!!!!!!!!
    #for i in range(3, len(f_observed)):
    for i in range(len(f_observed)-1, len(f_observed)):
        num_points = 100
        XY_grid = np.mgrid[-10:10:0.3, -10:10:0.3].reshape(2,-1).T  # Hardcoded!!!!!!!!!
        #XY_grid = np.mgrid[-15:15:0.3, -15:15:0.3].reshape(2,-1).T  # Hardcoded!!!!!!!!!
        XY = xy_observed[0:(i+1)]
        Z = f_observed[0:(i+1)]
        mean, Cov, variance, m = GP_analysis(XY, Z, XY_grid)

        f, (meanFig, sigmaFig, LCBFig) = plt.subplots(3, 1, sharex=True)
        xx = np.asarray(XY_grid[:,0])
        yy = np.asarray(XY_grid[:,1])
        xo = np.asarray(XY[:,0]).reshape(-1)
        yo = np.asarray(XY[:,1]).reshape(-1)

        mf1 = meanFig.scatter( xx, yy, c=mean.T[0],
                vmin = min(mean.T[0]), vmax = max(mean.T[0]), edgecolors='none', cmap = 'GnBu')
        cb1axes = f.add_axes([0.9, 0.653, 0.03, 0.227])
        cb1 = plt.colorbar(mf1, cax = cb1axes)
        cb1.ax.tick_params(labelsize = 9)
        meanFig.scatter(xo, yo, c='k', marker='s')
        meanFig.set(ylabel='Magnet 2 current')
        meanFig.title.set_text('Mean, sigma and LCB')

        sf1 = sigmaFig.scatter( xx, yy, c=variance,
                vmin = min(variance), vmax = max(variance), edgecolors='none')
        cb2axes = f.add_axes([0.9, 0.381, 0.03, 0.227])
        cb2 = plt.colorbar(sf1, cax = cb2axes)
        cb2.ax.tick_params(labelsize = 9)
        sigmaFig.scatter(xo, yo, c='white')
        sigmaFig.set(ylabel='Magnet 2 current')

        model = GPModel(optimize_restarts=1, verbose=True)
        model.model = m
        space = Design_space([{'name': 'var1', 'type': 'continuous', 'domain': (-10, 10)},
                              {'name': 'var2', 'type': 'continuous', 'domain': (-10, 10)}])
        #space = Design_space([{'name': 'var1', 'type': 'continuous', 'domain': (-15, 15)},
        #                      {'name': 'var2', 'type': 'continuous', 'domain': (-15, 15)}])
        acq = AcquisitionLCB(model, space, exploration_weight = 2)       # Hardcoded!!!!!!!!!
        alpha_full = acq.acquisition_function(XY_grid)
        pf1 = LCBFig.scatter( xx, yy, c=alpha_full.T[0],
            vmin = min(alpha_full.T[0]), vmax = max(alpha_full.T[0]), edgecolors='none', cmap = 'GnBu' )
        cb3axes = f.add_axes([0.9, 0.11, 0.03, 0.227])
        cb3 = plt.colorbar(pf1, cax = cb3axes)
        cb3.ax.tick_params(labelsize = 9)
        LCBFig.scatter(xo, yo, c='k', marker='s' )
        minXY = XY_grid[np.argmin(alpha_full)]
        LCBFig.scatter(minXY[0],minXY[1], marker = 'P')
        LCBFig.set(xlabel='Magnet 1 current')
        LCBFig.set(ylabel='Magnet 2 current')

        timestamp = (datetime.datetime.now()).strftime("%m-%d_%H-%M-%S")
        f.subplots_adjust()
        plt.savefig(f'GP_results/Dis_M1_M2_{timestamp}.pdf')
        plt.show()
        plt.close()

#evolution()
#plot1D()
#plot2D()

