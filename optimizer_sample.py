import os, shutil, signal, re
import sys, math
import datetime
import random
import numpy as np
from time import sleep

# GPy: Gaussian processes library
import GPy

# GPyOpt: Gaussian process optimization using GPy
import GPyOpt
from GPyOpt.acquisitions import AcquisitionEI, AcquisitionLCB, AcquisitionMPI
from GPyOpt import Design_space  ## GPyOpt design space
from GPyOpt.models import GPModel

# Module I wrote that contains a few functions to caculate the objective fn 
# and plot 1D and 2D results
import gaussianprocess as gp

# Import control system tools
from epics import caput, caget
# Import from setup module the control system communication functions
from setup import GetBeamPos, GetQuads, SetQuads, SaveIm, Dist, corr_set_pvs
from setup import h13_cset, h13_ird, h31_cset, h31_ird
from setup import v13_cset, v13_ird, v31_cset, v31_ird

num_points = 1000000  # Number of points considered in phase space sampling
count = 0 # Starting counter for number of iterations
cont = 'y' # Flag to stop it when troubleshooting
timestamp = (datetime.datetime.now()).strftime("%m-%d_%H-%M")

# Define the magnets being optimized (inputs of the algo)
magnet_list = ['h13', 'v13', 'h31', 'v31']

# Settings list for corrector magnet values
magnet_values = [0 for i in range(len(magnet_list))]

# ID of the camera viewer where the observations are being made.
# The observations are a series of CCD images at different system settings
# that get processed and the average distance of the beam spots among 
# the images is the 'objective' to minimize 
viewer = 'D1783'

# Detection intensity limit (threshold for detection)
int_limit = 1500

# Creating GP stuff
# Domain is phase space for each corrector magnet in Amps
spaceArray = [ {'name': 'h13', 'type': 'continuous', 'domain': (-10, 10)},\
               {'name': 'v13', 'type': 'continuous', 'domain': (-5, 5)},  \
               {'name': 'h31', 'type': 'continuous', 'domain': (-10, 10)},\
               {'name': 'v31', 'type': 'continuous', 'domain': (-1, 5)}]
space = Design_space(spaceArray)

# Main optimizing loop
while (cont == 'y'):
	peak_found = True

	# Import current state by
	#  Gets current settings from control system
	q1_init, q2_init, q3_init, q4_init= GetQuads()

	# Take picture with all magnets at initial values
    # Take image of beam (this is image #1)
	all_nom_im= SaveIm('allNom', viewer)

	sleep(2) # wait for image to process

	# Take picture with all quadrupoles at zero
	SetQuads(0, 0, 0, 0)

    # Analyze image #1 and get positions and peak intensity
	pos_1= GetBeamPos(all_nom_im, viewer) # x and y positions
	pk_1 = pos_1[2:4]  # peak intensitites

	if pk_1[0] <int_limit:
        # No beam found at these settings
		peak_found = False
        # Set magnets to desired values
		SetQuads(q1_init, q2_init, q3_init, q4_init) 
        # Assign high objective value to teach optimizer to avoid this region 
		distance = 1000
			
	if peak_found:
		sleep(10) # Allow time for quadrupoles to settle at new values
		all_zero_im= SaveIm('q1half', viewer) # Take image #2
		sleep(2)

		# Set quadrupole to new values to watch system behavior
		SetQuads(q1_init, 40, q3_init, q4_init)

        # Analyze image #2 and get positions and peak intensity
		pos_2= GetBeamPos(all_zero_im, viewer)
		pk_2 = pos_2[2:4]

		if pk_2[0] <int_limit:
            # No beam found at these settings
			peak_found = False
            #  Gets current settings from control system
			SetQuads(q1_init, q2_init, q3_init, q4_init)
            # Assign high objective value to teach optimizer to avoid this region 
			distance = 1000

	if peak_found:
		sleep(10) # Allow time for quadrupoles to settle at new values
		q1_half_im= SaveIm('q2half', viewer) # Take image #3
		sleep(2)

		#t Set new settings for image #4
		SetQuads(q1_init/2, 40, q3_init, q4_init)

        # Analyze image #3 and get positions and peak intensity
		pos_3= GetBeamPos(q1_half_im, viewer)
		pk_3 = pos_3[2:4]

		if pk_3[0] <int_limit:
            # No beam found at these settings
			peak_found = False
            #  Gets current settings from control system
			SetQuads(q1_init, q2_init, q3_init, q4_init)
            # Assign high objective value to teach optimizer to avoid this region 
			distance = 1000

	if peak_found:
		sleep(10) # Allow time for quadrupoles to settle at new values
		q2_half_im= SaveIm('bothhalf', viewer) # Take image #4
		sleep(2)

		# Return quads to original values
		SetQuads(q1_init, q2_init, q3_init, q4_init)
		pos_4= GetBeamPos(q2_half_im, viewer)

		pk_4 = pos_4[2:4]
		if pk_4[0] <int_limit:
			peak_found = False
			SetQuads(q1_init, q2_init, q3_init, q4_init)
			distance = 1000

	if peak_found:
		pos_1 = pos_1[0:2]
		pos_2 = pos_2[0:2]
		pos_3 = pos_3[0:2]
		pos_4 = pos_4[0:2]

		# Get quadratic distance from centroids
        # Function has the option to calculate x and y axis contributions separately
		distance = Dist(pos_1, pos_2, pos_3, pos_4, separateXY=False)

		for i,m in enumerate(magnet_list):
            # Get input magnet settings
			magnet_values[i] = caget(corr_set_pvs[m])
		print("Correctors set.")

	print(f"Dist= {distance:.5f}")

	#save corrector values and distance to file
	f= open(f"GP_results/correctorValues_Distance_{timestamp}.txt", "a+")
	f.write('%s' % ' '.join(map('{:.4f}'.format, magnet_values)) + ' {0:.4f}\n'.format(distance))
	f.close()

	#increase counter
	count = count + 1

	########################
	#### GaussProcess ######
	########################

	# Reading file with corrector values and measured distance between peaks
	reader = np.asmatrix(np.loadtxt(f'GP_results/correctorValues_Distance_{timestamp}.txt'))

    # Input parameters
	x_observed = np.asarray(reader[:,0:len(magnet_list)])
    # Observations
	f_observed = np.asarray(reader[:,-1])

	# Use GP regression to fit the data
	X_grid = gp.x_grid_func(num_points, space)
    # Choice of kernel for GP (RBF)
	k = GPy.kern.RBF(input_dim=len(magnet_list))  
	m = GPy.models.GPRegression(x_observed, f_observed, k)

	m.kern.lengthscale.unconstrain_positive()
    # Experimentally determined priors on RBF lengthscale
	m.kern.lengthscale.set_prior(GPy.priors.Gaussian(5,2))

    # Experimentally determined priors on noise
	m.Gaussian_noise.variance.unconstrain_positive()
	m.Gaussian_noise.variance.set_prior(GPy.priors.Gaussian(1,0.5))


	m.optimize('bfgs', max_iters=100)  # Hyper-parameters are optimized here (lengthscale and noise)

    # Save optimizer output with hyperparameters for later analysis
	f = open(f"GP_results/opt_params_{timestamp}.txt", "a+")
	ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
	text = ansi_escape.sub('', str(m))
	f.write(text + '\n')
	f.close()

	# Find next point
	model = GPModel(optimize_restarts=1, verbose=True)
	model.model = m
    # Acquisition function uses posterior to select next observation point
	acq = AcquisitionLCB(model, space, exploration_weight = 0.5) # Hardcoded trade-off parameter
	alpha_full = acq.acquisition_function(X_grid)
    # Next point is minimum of acquisition function
	magnet_values = X_grid[np.argmin(alpha_full),:]

	print("Min LCB: ", np.argmin(alpha_full), min(alpha_full), X_grid[np.argmin(alpha_full),:])
	print("Max LCB: ", np.argmax(alpha_full), max(alpha_full), X_grid[np.argmax(alpha_full),:])

	# Plot results if 1D 
    if (len(magnet_list)==1):
		gp.plot1D(f'GP_results/correctorValues_Distance_{timestamp}.txt')

	# Save new corrector values to file
	f = open(f"GP_results/newCorrectorValues_{timestamp}.txt", "a+")
	f.write('%s' % ' '.join(map('{:.4f}'.format, list(magnet_values))) + '\n')
	f.close()

	# Set next sampling settings in system 
	for i,m in enumerate(magnet_list):
	    caput(corr_set_pvs[m], magnet_values[i], wait= True)