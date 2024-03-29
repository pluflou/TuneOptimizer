import os, shutil, signal, re
import sys, math
import datetime
import random
import numpy as np
from time import sleep

# GPy: Gaussian processes library
import gaussianprocess as gp
import GPy
import GPyOpt
from GPyOpt.acquisitions import AcquisitionEI, AcquisitionLCB, AcquisitionMPI
from GPyOpt import Design_space  ## GPyOpt design space
from GPyOpt.models import GPModel

tbl = 'n' # troubleshooting flag
sandbox = 'n' # if 'y' uses madeup function

# Comment if not working with magnets and packages are not installed
if sandbox != 'y':
	from epics import caput, caget
	from setup import GetBeamPos, GetQuads, SetQuads, SaveIm, Dist, corr_set_pvs
	from setup import h13_cset, h13_ird, h31_cset, h31_ird
	from setup import v13_cset, v13_ird, v31_cset, v31_ird

magnet_list = ['h13', 'v13', 'h31', 'v31']
#magnet_list = ['v13', 'v31']
#magnet_list = ['h13', 'h31']

num_points = 1000000  # Number of points considered in phase space sampling
count = 0 # Starting counter for number of iterations
cont = 'y' # Flag to stop it when troubleshooting

timestamp = (datetime.datetime.now()).strftime("%m-%d_%H-%M")
#timestamp = "06-09_20-24"
viewer = 'D1783' #when optimizing through JENSA we always use this viewer

# Creating GP stuff
# Domain is phase space for each corrector magnet in Amps!
#spaceArray = [ {'name': m, 'type': 'continuous', 'domain': (-15, 15)} for m in magnet_list ]
#~ spaceArray = [ {'name': m, 'type': 'continuous', 'domain': (-10, 10)} for m in magnet_list ]
spaceArray = [ {'name': 'h13', 'type': 'continuous', 'domain': (-10, 10)}, {'name': 'v13', 'type': 'continuous', 'domain': (-5, 5)}, {'name': 'h31', 'type': 'continuous', 'domain': (-10, 10)}, {'name': 'v31', 'type': 'continuous', 'domain': (-1, 5)}]
#spaceArray = [ {'name': 'v13', 'type': 'continuous', 'domain': (-7.5, 0)}, {'name': 'v31', 'type': 'continuous', 'domain': (2.4, 12)}]
#~ spaceArray = [ {'name': 'h13', 'type': 'continuous', 'domain': (7, 9)}, {'name': 'v13', 'type': 'continuous', 'domain': (-3, -1)}, {'name': 'h31', 'type': 'continuous', 'domain': (-7, -5)}, {'name': 'v31', 'type': 'continuous', 'domain': (3, 5)}]
space = Design_space(spaceArray)
np.set_printoptions(precision=2)

#list for corrector magnet values
magnet_values = [0 for i in range(len(magnet_list))]
int_limit = 1500

while (cont == 'y'):
	if sandbox != 'y':
		peak_found = True

		#import current state
		#Get initial quad values
		q1_init, q2_init, q3_init, q4_init= GetQuads()

		#Tuning Q1 and Q2
		#take picture with all at init values
		#SetQuads(q1_init, q2_init, q3_init, q4_init)

		sleep(10)
		all_nom_im= SaveIm('allNom', viewer)
		sleep(2)

		#take picture with all at zero
		#SetQuads(q1_init, q2_init, q3_init*1.3, q4_init)
		SetQuads(q1_init/2, q2_init, q3_init, q4_init)
		pos_1= GetBeamPos(all_nom_im, viewer)
		pk_1 = pos_1[2:4]
		if pk_1[0] <int_limit:
			peak_found = False
			SetQuads(q1_init, q2_init, q3_init, q4_init)
			distance = 1000
			
		if peak_found:
			sleep(10) #might need to increase this if the jumps in current are big
			all_zero_im= SaveIm('q1half', viewer)
			sleep(2)

			#take picture with Q1 at half # CHANGED.... Q2 also half
			#SetQuads(q1_init, q2_init, q3_init/1.1, q4_init)
			#~ SetQuads(-30, q2_init, q3_init, q4_init)
			SetQuads(q1_init, 40, q3_init, q4_init)

			pos_2= GetBeamPos(all_zero_im, viewer)
			pk_2 = pos_2[2:4]
			if pk_2[0] <int_limit:
				peak_found = False
				SetQuads(q1_init, q2_init, q3_init, q4_init)
				distance = 1000
		if peak_found:
			sleep(10)
			q1_half_im= SaveIm('q2half', viewer)
			sleep(2)

			#take picture with Q2 at half # CHANGED... Q1 = 0
			#SetQuads(q1_init, q2_init, q3_init, q4_init/1.1)
			SetQuads(q1_init/2, 40, q3_init, q4_init)

			pos_3= GetBeamPos(q1_half_im, viewer)
			pk_3 = pos_3[2:4]
			if pk_3[0] <int_limit:
				peak_found = False
				SetQuads(q1_init, q2_init, q3_init, q4_init)
				distance = 1000

		if peak_found:
			sleep(10)
			q2_half_im= SaveIm('bothhalf', viewer)
			sleep(2)

			#return quads to original values
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

			#get quadratic distance from centroids
			print(f"Centroids:\n({pos_1[0]:.2f}, {pos_1[1]:.2f})\n({pos_2[0]:.2f}, {pos_2[1]:.2f})\n({pos_3[0]:.2f}, {pos_3[1]:.2f})\n({pos_4[0]:.2f}, {pos_4[1]:.2f})")
			#print("Peaks: ", pk_1, pk_2, pk_3, pk_4)
#		print("distances, x, y")
#		print(Dist(pos_1, pos_2, pos_3, pos_4, True))
#		print("distances, combined")
#		print(Dist(pos_1, pos_2, pos_3, pos_4))
			distance = Dist(pos_1, pos_2, pos_3, pos_4, separateXY=False)

		for i,m in enumerate(magnet_list):
			magnet_values[i] = caget(corr_set_pvs[m])
		print("Correctors set.")

	else :
		if count == 0:
			#magnet_values = [random.uniform(-10,10) for m in magnet_list]
                        magnet_values = [random.uniform(-15,15) for m in magnet_list]
			#magnet_values = [7.73 for m in magnet_list]
		distance = gp.returnObservations(magnet_values)

	print(f"Dist= {distance:.5f}")
	#save corrector values and distance to file
	f= open(f"GP_results/correctorValues_Distance_{timestamp}.txt", "a+")
	f.write('%s' % ' '.join(map('{:.4f}'.format, magnet_values)) + ' {0:.4f}\n'.format(distance))
	f.close()

	#increase counter
	count = count + 1

	####################
	####GaussProc######
	####################

	# Reading file with corrector values and measured distance between peaks
	reader = np.asmatrix(np.loadtxt(f'GP_results/correctorValues_Distance_{timestamp}.txt'))
	#print(reader)
	x_observed = np.asarray(reader[:,0:len(magnet_list)])
	f_observed = np.asarray(reader[:,-1])

	print(x_observed)
	print(f_observed)
	# Use GP regression to fit the data
	X_grid = gp.x_grid_func(num_points, space)
	k = GPy.kern.RBF(input_dim=len(magnet_list))   # Choice of Kernel!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
	m = GPy.models.GPRegression(x_observed, f_observed, k)

	m.kern.lengthscale.unconstrain_positive()
	#~ m.kern.lengthscale.set_prior(GPy.priors.Gaussian(2,0.5))
	m.kern.lengthscale.set_prior(GPy.priors.Gaussian(5,2))
	#m.kern.lengthscale.set_prior(GPy.priors.Gaussian(5,2))

	m.Gaussian_noise.variance.unconstrain_positive()
	m.Gaussian_noise.variance.set_prior(GPy.priors.Gaussian(1,0.5))


	m.optimize('bfgs', max_iters=100)  # Hyper-parameters are optimized here
	print(m)

	f = open(f"GP_results/opt_params_{timestamp}.txt", "a+")
	ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
	text = ansi_escape.sub('', str(m))
	f.write(text + '\n')
	f.close()

	# Find next point
	model = GPModel(optimize_restarts=1, verbose=True)
	model.model = m
    #acq = AcquisitionEI(model, space, jitter = 1)
	acq = AcquisitionLCB(model, space, exploration_weight = 0.5) # Hardcoded HYPER_PARAMETER!!!!!!!!
	alpha_full = acq.acquisition_function(X_grid)
	magnet_values = X_grid[np.argmin(alpha_full),:]

	print("Min LCB: ", np.argmin(alpha_full), min(alpha_full), X_grid[np.argmin(alpha_full),:])
	print("Max LCB: ", np.argmax(alpha_full), max(alpha_full), X_grid[np.argmax(alpha_full),:])

	if (len(magnet_list)==1):
		gp.plot1D(f'GP_results/correctorValues_Distance_{timestamp}.txt')
	#elif (len(magnet_list)==2):
	#	gp.plot2D(f'GP_results/correctorValues_Distance_{timestamp}.txt', magnet_list_2d = magnet_list, timestamp = timestamp)

	#save new corrector values to file
	f = open(f"GP_results/newCorrectorValues_{timestamp}.txt", "a+")
	f.write('%s' % ' '.join(map('{:.4f}'.format, list(magnet_values))) + '\n')
	f.close()

	if sandbox != 'y':
		#set new corrector values
		for i,m in enumerate(magnet_list):
			caput(corr_set_pvs[m], magnet_values[i], wait= True)
		print("Correctors set.")

    ####################
	####################

	#continue or not
	if (tbl == 'y' or count%20 == 0):
		cont = input("Continue? y/n ")
		while (cont not in ['y','n']):
			cont = input("Continue? y/n ")
		if (cont == 'y'):
			new_vals = input("Do you want to enter new corrector values? y/n ")
			if (new_vals=='y'):
				magnet_values = input("Enter new current values for magnets in order (i.e. 10, -10):")
				magnet_values = np.asarray([float(x.lstrip().rstrip()) for x in magnet_values.split(",")])

				#set new corrector values
				for i,m in enumerate(magnet_list):
					caput(corr_set_pvs[m], magnet_values[i], wait= True)
					print("Correctors set.")