import os, shutil, signal
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
sandbox = 'n' # if 'y' uses madeup function
num_points = 1000000  # Number of points considered in phase space sampling
count = 0
cont = 'y'

quad_list  = input("Enter which quads to optimize (i.e. q2, q3, q4): ").lower()
viewer     = input("Enter viewer location (i.e. D1542): ").capitalize()

#getting list of quads to loop through
magnet_list = [x.lstrip().rstrip() for x in quad_list.split(",")]

#magnet_list = ['q1', 'q2', 'q3', 'q4']

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
			q_ps = {q : [ 0.85*q_init[q] , 1.15*q_init[q] ] for q in magnet_list}

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
			wid_gp = wid_init 	

		else:
			magnet_values = [random.uniform(-10,10) for q in magnet_list]
			spaceArray = [ {'name': q, 'type': 'continuous', 'domain': (-10, 10)} for q in magnet_list ]

			space = Design_space(spaceArray)
			wid_gp = gp.returnObservations(magnet_values)

	else:
		if sandbox != 'y':
			#starting with this state
			magnet_values = [GetMagnet(q) for q in magnet_list]
			gp_im= SaveIm('gp', viewer)
			sleep(2)

			pos_gp = GetBeamPos(gp_im, viewer)
		
      	  #widths (+/- 34.13%)
			
			wid_gp = pos_gp[5] - pos_gp[4]
			
				
		else: 
			wid_gp = gp.returnObservations(magnet_values)
	
	print(f"Width: {wid_gp:.2f}")

	#save currents and width values to file
	f= open(f"GP_results/{'_'.join(magnet_list)}Values_Widths_{timestamp}.txt", "a+")
	f.write('%s' % ' '.join(map('{:.4f}'.format, magnet_values)) + ' {0:.4f}\n'.format(wid_gp))
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
	k = GPy.kern.RBF(input_dim=len(magnet_list))   # Choice of Kernel!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
	m = GPy.models.GPRegression(x_observed, f_observed, k)
	m.optimize('bfgs', max_iters=100)  # Hyper-parameters are optimized here
	#print(m)

	# Find next point
	model = GPModel(optimize_restarts=1, verbose=True)
	model.model = m
    #acq = AcquisitionEI(model, space, jitter = 1)
	acq = AcquisitionLCB(model, space, exploration_weight = 2)
	alpha_full = acq.acquisition_function(X_grid)
	magnet_values = X_grid[np.argmin(alpha_full),:]


	print("New quad current values:\n")
	for i,q in enumerate(magnet_list):
		print(f"{q}: {magnet_values[i]:.2f}A\n")
		if sandbox != 'y':
			#set new quad currents
			SetMagnet(q, magnet_values[i])

    ####################
	"""#############"""
	####################

	#continue or not
	if (tbl == 'y' or count%10 == 0):
		cont= input("Continue? y/n ")
		if (cont == 'n' and sandbox =='y'):
			exit() 

##########################
##########################

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
