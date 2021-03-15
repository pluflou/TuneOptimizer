import os, shutil, signal, re
import sys, math
import datetime
import random
import numpy as np
from time import sleep
from epics import caput, caget
from setup import GetBeamPos, GetQuads, SetQuads, SaveIm

count = 0 # Starting counter for number of iterations
cont = 'y' # Flag to stop it when troubleshooting
timestamp = (datetime.datetime.now()).strftime("%m-%d_%H-%M")
#timestamp = "06-09_20-24"
viewer = 'D1542' #when optimizing through JENSA we always use this viewer

np.set_printoptions(precision=2)

while (count<21):

	#import current state
	#Get initial quad values
	q1_init, q2_init, q3_init, q4_init= GetQuads()

	#Tuning Q1 and Q2
	#take picture with all at init values
	SetQuads(q1_init, q2_init, q3_init, q4_init)
	sleep(10)
	all_nom_im= SaveIm('allNom', viewer)
	sleep(2)

	#take picture with all at zero
	SetQuads(q1_init/2, q2_init, q3_init, q4_init)
	pos_1= GetBeamPos(all_nom_im, viewer)
	sleep(10) #might need to increase this if the jumps in current are big
	q1_half_im= SaveIm('q1half', viewer)
	sleep(2)

	#take picture with Q1 at half # CHANGED.... Q2 also half
	SetQuads(q1_init, q2_init, q3_init/2, q4_init)
	pos_2= GetBeamPos(q1_half_im, viewer)
	sleep(10)
	q3_half_im= SaveIm('q3half', viewer)
	sleep(2)

	#take picture with Q2 at half # CHANGED... Q1 = 0
	SetQuads(q1_init, q2_init/2, q3_init, q4_init)
	pos_3= GetBeamPos(q3_half_im, viewer)
	sleep(10)
	q2_half_im= SaveIm('q2half', viewer)
	sleep(2)

	#return quads to original values
	SetQuads(q1_init, q2_init, q3_init, q4_init)
	pos_4= GetBeamPos(q2_half_im, viewer)

	pos_1 = pos_1[0:2]
	pos_2 = pos_2[0:2]
	pos_3 = pos_3[0:2]
	pos_4 = pos_4[0:2]

	#get quadratic distance from centroids
	print(f"Centroids: ({pos_1[0]:.2f}, {pos_1[1]:.2f}), ({pos_2[0]:.2f}, {pos_2[1]:.2f}), ({pos_3[0]:.2f}, {pos_3[1]:.2f}), ({pos_4[0]:.2f}, {pos_4[1]:.2f})")

	f= open(f"stability_quads_{timestamp}.txt", "a+")
	f.write('{0:.2f}\t{1:.2f}\t{2:.2f}\t{3:.2f}\t{4:.2f}\t{5:.2f}\t{6:.2f}\t{7:.2f}\n'.format(pos_1[0] ,pos_1[1], pos_2[0], pos_2[1], pos_3[0], pos_3[1], pos_4[0], pos_4[1]))
	f.close()

	#increase counter
	count = count + 1

	
	sleep(3*60)


