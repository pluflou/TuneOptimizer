import os, shutil, signal, re
import sys, math
import warnings
import datetime
from time import sleep
import random
import numpy as np

# GPy: Gaussian processes library
import gaussianprocess as gp
import GPy
import GPyOpt
from GPyOpt.acquisitions import AcquisitionEI, AcquisitionLCB, AcquisitionMPI
from GPyOpt import Design_space  ## GPyOpt design space
from GPyOpt.models import GPModel

from setup import GetBeamPos, GetMagnet, SetMagnet, SaveIm

#warnings.filterwarnings("error")
#warnings.simplefilter("ignore", category=DeprecationWarning)

## if in troubleshoot mode you can change the eps at every step
tbl = 'n'
sandbox = 'y' # if 'y' uses madeup function
num_points = 1000000  # Number of points considered in phase space sampling
count = 0
cont = 'y'


#quad_list  = input("Enter which quads to optimize (i.e. q1, h2, o1, s1, t1,.. ): ").lower()
#viewer     = input("Enter viewer location (i.e. D1542, D1638): ").capitalize()
viewer= 'D1638'

#getting list of quads to loop through
#UNCOMMENT IF YOU ARE MANUALLY ENTERING MAGNET NAMES
#magnet_list = [x.lstrip().rstrip() for x in quad_list.split(",")]

magnet_list = ['q1', 'q2', 'q3', 'q4', 'q5', 'q6', 'q7', 's1']

timestamp = (datetime.datetime.now()).strftime("%m-%d_%H-%M")
np.set_printoptions(precision=2)

############################
###   optimizing quads   ###
############################
while (cont == 'y'):
	if count == 0 :
		if sandbox != 'y':
			#get inital tune for quads and assign the phase space for each
			q_init = {q : GetMagnet(q) for q in magnet_list} #need this for final scaling
			magnet_values = [q_init[q] for q in magnet_list]

			# !! PHASE SPACE FOR 1D/not using optimal values, uncomment following line
			#q_ps = {q : [ 0.50*q_init[q] , 2.0*q_init[q] ] if q_init[q]>0 else [ 2.0*q_init[q] , 0.5*q_init[q] ] for q in magnet_list  }
			# !! PHASE SPACE MANUALLY SET, after 1D test, from nominal to optimal 
			q_ps = { q: [q_init[q]-2.0,q_init[q]+2.0] for q in magnet_list }
#			q_ps = {'q1' : [-43.698, -34.5],
#				'q2' : [ 72.684, 75.55],
#				'q3' : [ 81.86,  82.564],
#				'q4' : [-83.13, -72.716],
#				'q5' : [ 47.54,  55.68],
#				'q6' : [ 75.72,  76.18],
#				'q7' : [-26.81, -24.18]
#				}
			
			#print the phase space
			print(q_ps)			

			# Creating GP stuff
			# Domain is phase space for each corrector magnet in Amps!
			spaceArray = [ {'name': q, 'type': 'continuous', 'domain': (q_ps[q][0], q_ps[q][1])} for q in magnet_list ]
			space = Design_space(spaceArray)

			#take picture at init values
			init_im = SaveIm('init', viewer)
			sleep(2)

			#get initial beam spot width
			pos_init = GetBeamPos(init_im, viewer)

			#widths (+/- 34.13%)
			wid_init = (pos_init[5] - pos_init[4])
			gp_im = init_im
			#x_init = pos_init[0]
			x_init = 409 
			# CHANGED from x_init to 400 to refer to pos at nominal, below and when saving the file 
			x_gp = pos_init[0]
			wid_y= pos_init[7] - pos_init[6]
			wid_gp = wid_init 	

		else:
			magnet_values = [random.uniform(-10,10) for q in magnet_list]
			spaceArray = [ {'name': q, 'type': 'continuous', 'domain': (-10, 10)} for q in magnet_list ]

			space = Design_space(spaceArray)
			f_gp = gp.returnObservations(magnet_values)
			x_init = random.randint(1,600)
			x_gp, wid_y, wid_gp = random.randint(10,600), random.randint(10,600), random.randint(10,600)

	else:
		if sandbox != 'y':
			#starting with this state
			magnet_values = [GetMagnet(q) for q in magnet_list]
			sleep(2)
			gp_im= SaveIm('gp', viewer)
			pos_gp = GetBeamPos(gp_im, viewer)
			x_gp = pos_gp[0]
			wid_gp = pos_gp[5] - pos_gp[4]
			wid_y = pos_gp[7] - pos_gp[6]
		else: 
			f_gp = gp.returnObservations(magnet_values)
			x_gp, wid_y, wid_gp = random.randint(10,600), random.randint(10,600), random.randint(10,600)

	
	if sandbox != 'y':
		print(f"Width: {wid_gp:.2f}")

		#adding the x-centroid as weight to optimize without moving the beam position
		#f_gp = wid_gp + ((x_gp-x_init)/30)**4 + (wid_y/50)**4
		if x_gp > x_init:
			f_gp = ((x_gp+wid_gp-x_init)/20)**4 + (wid_y/70)**4
		else:
			f_gp = ((x_gp-wid_gp-x_init)/20)**4 + (wid_y/70)**4
	#save currents and width values to file
	f= open(f"GP_results/{'_'.join(magnet_list)}Values_Widths_{timestamp}.txt", "a+")
	f.write('%s' % ' '.join(map('{:.4f}'.format, magnet_values)) + ' {0:.4f}'.format(wid_gp)+ ' {0:.1f}'.format(x_gp-x_init) + '  {0:.4f}'.format(wid_y) + '  {0:.4f} '.format(f_gp))
	if sandbox != 'y':
		f.write(f'{gp_im[20:]}\n')	
	#f.write('%s' % ' '.join(map('{:.4f}'.format, magnet_values)) + ' {0:.4f}\n'.format(wid_gp))
	f.close()

	#increase counter
	count = count + 1

	####################
	"""##GaussProc##"""
	####################

	# Reading file with corrector values and measured distance between peaks
	reader = np.asmatrix(np.loadtxt(f"GP_results/{'_'.join(magnet_list)}Values_Widths_{timestamp}.txt"))
	#print(reader)
	x_observed = np.asarray(reader[:,0:len(magnet_list)])
	f_observed = np.asarray(reader[:,-1])

	#print(x_observed)
	#print(f_observed)
	# Use GP regression to fit the data
	X_grid = gp.x_grid_func(num_points, space)
	k = GPy.kern.RBF(input_dim=len(magnet_list), ARD=True)   # Choice of Kernel!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
	m = GPy.models.GPRegression(x_observed, f_observed, k)
	
	m.kern.lengthscale.unconstrain_positive()
	#~ m.kern.lengthscale.set_prior(GPy.priors.Gaussian(10,2))
	m.kern.lengthscale.set_prior(GPy.priors.Gaussian(2,1))

	m.Gaussian_noise.variance.unconstrain_positive()
	m.Gaussian_noise.variance.set_prior(GPy.priors.Gaussian(3,3))

	m.optimize('bfgs', max_iters=100)  # Hyper-parameters are optimized here
	print(m.kern.lengthscale)

	f = open(f"GP_results/opt_params_{timestamp}.txt", "a+")
	ansi_escape = re.compile(r'\x1B\[[0-?]*[ -/]*[@-~]')
	text = ansi_escape.sub('', str(m))
	f.write(text + '\n')
	f.close()

	# Find next point
	model = GPModel(optimize_restarts=1, verbose=True)
	model.model = m
    #acq = AcquisitionEI(model, space, jitter = 1)
	acq = AcquisitionLCB(model, space, exploration_weight = 0.5)
	alpha_full = acq.acquisition_function(X_grid)
	magnet_values = X_grid[np.argmin(alpha_full),:]

	print("Min LCB: ", np.argmin(alpha_full), min(alpha_full), X_grid[np.argmin(alpha_full),:])
	print("Max LCB: ", np.argmax(alpha_full), max(alpha_full), X_grid[np.argmax(alpha_full),:])
	
	if (len(magnet_list)==1):
		gp.plot1D(f"GP_results/{'_'.join(magnet_list)}Values_Widths_{timestamp}.txt", timestamp = timestamp, phase_space = q_ps[magnet_list[0]])
	elif (len(magnet_list)==2):
		gp.plot2D(f"GP_results/{'_'.join(magnet_list)}Values_Widths_{timestamp}.txt", magnet_list_2d = magnet_list, timestamp = timestamp, phase_space = q_ps)

	print("New quad current values:\n")
	for i,q in enumerate(magnet_list):
		print(f"{q}: {magnet_values[i]:.2f}A")
		if sandbox != 'y':
			#set new quad currents
			SetMagnet(q, magnet_values[i])
	sleep(7)

    ####################
	"""#############"""
	####################

	#continue or not
	if (tbl == 'y' or count%30 == 0):
		cont= input("Continue? y/n ")
		if (cont == 'n' and sandbox =='y'):
			exit() 

##########################
##########################
'''
print("Adjusting quads...")

#select min width from results 
q_diff = {}
count_q = 0 

#loading results
results = np.loadtxt(f"GP_results/{'_'.join(magnet_list)}Values_Widths_{timestamp}.txt")
#getting list of currents corresponding to min width
q_best = results[results[:,len(magnet_list)].argmin(), list(range(len(magnet_list)))]

for i,q in enumerate(magnet_list):
	q_diff[q] = q_best[i] - q_init[q]

	if (np.abs(q_diff[q])/q_init[q] >= 0.0001 ):
		#if the difference in I is greater than 0.01%, optimize this quad
		count_q = count_q + 1
		print(f"{q} optimization changed the current by {(q_diff[q]/q_init[q]*100):.2f}%.")
	else:
		q_diff[q] = 0
		print(f"{q} does not need adjusting. Diff in I < 0.01%.")


#once we have checked what quads need to be changed, now we set them to the final value
if (count_q == 0):
	print("No quads needs optimizing. Exiting program")
	exit()

#check if we are optimizing more than one quad (GP method)
if len(magnet_list)>1: 
	for q in magnet_list:
		print(f"{q} will be adjusted by {q_diff[q]:.2f}/{count_q} A.\n")
		new_c = q_init[q] + q_diff[q]/count_q
		SetMagnet(q, new_c)

	print(f"All {len(magnet_list)} quads optimized.")
	sleep(5)

	#get final width 
	final_im= SaveIm('final_gp', viewer)
	sleep(2)
	pos_final = GetBeamPos(final_im, viewer)
	wid_final = pos_final[5] - pos_final[4]

#check if we are using the St George method (one by one holding other constant)
elif len(magnet_list)==1:
	final_width = np.min(results[:,1])
	width_change  =  (final_width - wid_init) / wid_init *100
	SetMagnet(magnet_list[0], q_init[0])
	print(f"Done with {magnet_list[0]}. Set back to inital value.")

#get the final width change between start and best state
print(f"Init width: {wid_init:.2f}.\n")
print(f"Final width: {wid_final:.2f}.\n")
print(f"Total change: {((wid_final-wid_init)/wid_init*100):.2f}%.\n")

#save init currents and init width/final currents and final widths values to file
f= open(f"GP_results/{'_'.join(magnet_list)}_gp_results_{timestamp}.txt", "a+")
f.write('%s' % ' '.join(map('{:.4f}'.format, [q_init[q] for q in magnet_list])) + ' {0:.4f}\n'.format(wid_init))
f.write('%s' % ' '.join(map('{:.4f}'.format, q_best)) + ' {0:.4f}\n'.format(wid_final))
f.close()


'''
