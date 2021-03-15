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
	from setup import GetBeamPos, GetQuads, SetQuads, SaveIm, Dist, corr_set_pvs, GetMagnet, SetMagnet
	from setup import h13_cset, h13_ird, h31_cset, h31_ird
	from setup import v13_cset, v13_ird, v31_cset, v31_ird

#magnet_list = ['h13', 'v13', 'h31', 'v31']
magnet_list = ['v13', 'v31']
#magnet_list = ['h13', 'h31']

quad_pair = ['q4', 'q9'] 

num_points = 1000000  # Number of points considered in phase space sampling
count = 0 # Starting counter for number of iterations
cont = 'y' # Flag to stop it when troubleshooting

timestamp = (datetime.datetime.now()).strftime("%m-%d_%H-%M")
#timestamp = "06-09_20-24"
#~ viewer = 'D1542' #when optimizing through JENSA we always use this viewer
viewer = 'D1783' #for optimizing on downstream viewer

# Creating GP stuff
# Domain is phase space for each corrector magnet in Amps!
#~ spaceArray = [ {'name': m, 'type': 'continuous', 'domain': (-10, 10)} for m in magnet_list ]
spaceArray = [ {'name': 'v13', 'type': 'continuous', 'domain': (-49, -45)},  {'name': 'v31', 'type': 'continuous', 'domain': (26, 30)} ]
space = Design_space(spaceArray)
np.set_printoptions(precision=2)

count_iter = 0
#list for corrector magnet values
magnet_values = [0 for i in range(len(magnet_list))]

#initial nominal quad values
q0_init, q1_init = GetMagnet(quad_pair[0]), GetMagnet(quad_pair[1])

while (cont == 'y'):
	if sandbox != 'y':

		#import current state
		#Get initial quad values
		#~ q1_init, q2_init, q3_init, q4_init= GetQuads()

		#Tuning Q1 and Q2
		#take picture with all at init values
		#~ SetQuads(q1_init, q2_init,  q3_init, q4_init)
		#~ sleep(10)
		all_nom_im= SaveIm('allNom', viewer)
		sleep(2)

        #take picture with q1 *1/2, q2 nom
		SetMagnet(quad_pair[0], q0_init/2)
		SetMagnet(quad_pair[1], q1_init)
		pos_1= GetBeamPos(all_nom_im, viewer)
		pk_1 = pos_1[2]  # CHANGED FROM 6 BY F. MONTES


		if (count_iter == 0):
			init_peak = pk_1


		if (count_iter>0 and pk_1 < init_peak*0.05):
			print("Beam off viewer. Skipping iteration.")
			distance = 1000
		else:

			sleep(5) #might need to increase this if the jumps in current are big
			frac_im= SaveIm('Q4halfQ9nom', viewer)

			#take picture with q1 *1/2 and q2 *1/2
			SetMagnet(quad_pair[0], q0_init*2)
			SetMagnet(quad_pair[1], q1_init)
			pos_2= GetBeamPos(frac_im, viewer)
			sleep(5)
			q14_frac_im= SaveIm('Q4doubleQ9nom', viewer)

			#take picture with q1 nom, and q2 5/4
			SetMagnet(quad_pair[0], q0_init)
			SetMagnet(quad_pair[1], q1_init/2)
			pos_3= GetBeamPos(q14_frac_im, viewer)
			sleep(5)
			q15_frac_im= SaveIm('Q4nomQ9half', viewer)

			#return quads to original values
			SetMagnet(quad_pair[0], q0_init)
			SetMagnet(quad_pair[1], q1_init)

			pos_4= GetBeamPos(q15_frac_im, viewer)

			pos_1 = pos_1[0:2]
			pos_2 = pos_2[0:2]
			pos_3 = pos_3[0:2]
			pos_4 = pos_4[0:2]


			#get quadratic distance from centroids
			print(f"Centroids:\n({pos_1[0]:.2f}, {pos_1[1]:.2f})\n({pos_2[0]:.2f}, {pos_2[1]:.2f})\n({pos_3[0]:.2f}, {pos_3[1]:.2f})\n({pos_4[0]:.2f}, {pos_4[1]:.2f})")
			#print("Peaks: ", pk_1, pk_2, pk_3, pk_4)
			distance = Dist(pos_1, pos_2, pos_3, pos_4, separateXY=True)[1]

		for i,m in enumerate(magnet_list):
			magnet_values[i] = caget(corr_set_pvs[m])
		print("Correctors read.")

	else :
		if count == 0:
			magnet_values = [random.uniform(-10,10) for m in magnet_list]
                        #magnet_values = [random.uniform(-15,15) for m in magnet_list]
			#magnet_values = [7.73 for m in magnet_list]
		distance = gp.returnObservations(magnet_values)

	print(f"Dist= {distance:.5f}")
	#save corrector values and distance to file
	f= open(f"GP_results/correctorValues_Distance_{timestamp}.txt", "a+")
	f.write('%s' % ' '.join(map('{:.4f}'.format, magnet_values)) + ' {0:.4f}\n'.format(distance))
	f.close()

	#increase counter
	count = count + 1
	count_iter = count_iter + 1

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
	#~ m.kern.lengthscale.set_prior(GPy.priors.Gaussian(10,2))
	m.kern.lengthscale.set_prior(GPy.priors.Gaussian(1,1))

	m.Gaussian_noise.variance.unconstrain_positive()
	m.Gaussian_noise.variance.set_prior(GPy.priors.Gaussian(10,5))


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
	'''
	if (len(magnet_list)==1):
		gp.plot1D(f'GP_results/correctorValues_Distance_{timestamp}.txt')
	elif (len(magnet_list)==2):
		gp.plot2D(f'GP_results/correctorValues_Distance_{timestamp}.txt', timestamp = timestamp)
	'''
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
	if (tbl == 'y' or count%10 == 0):
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
