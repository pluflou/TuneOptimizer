import numpy as np
from time import *
from setup import *

cont = 'y'
## if in troubleshoot mode you can change the eps at every step
tbl = 'n'
## if no in tbl mode this is set to the following eps
count = 0

##I did not yet implement the printing of the images when it's in tbl mode
print("Make sure to delete the past corrector text files.")

theta = input("Enter theta (kernel param): ")
eps_stable = input("Enter eps (prob. of improvement): ")



while (cont == 'y' and count<11):
	
	#import current state
	#Get initial corrector values
	h13_init, v13_init, h31_init, v31_init= GetCorr()
	#Get initial quad values
	q1_init, q2_init, q3_init, q4_init= GetQuads()

	#Tuning Q1 and Q2

	#take picture with all at init values
	SetQuads(q1_init, q2_init, 0, 0)
	sleep(10)
	all_nom_im= SaveIm('allNom')
	sleep(2)

	#take picture with all at zero
	SetQuads(0, 0, 0, 0)
	pos_1= GetBeamPos(all_nom_im)
	sleep(10) #might need to increase this if the jumps in current are big
	all_zero_im= SaveIm('allZero')
	sleep(2)

	#take picture with Q1 at half # CHANGED.... Q2 also half
	SetQuads(q1_init/2, q2_init/2, 0, 0)
	pos_2= GetBeamPos(all_zero_im)
	sleep(10)
	q1_half_im= SaveIm('q1half')
	sleep(2)
	
	#take picture with Q2 at half # CHANGED... Q1 = 0
	SetQuads(0, q2_init/2, 0, 0)
	pos_3= GetBeamPos(q1_half_im)
	sleep(10)
	q2_half_im= SaveIm('q2half')
	sleep(2)
	
	#return quads to original values
	SetQuads(q1_init, q2_init, q3_init, q4_init)
	pos_4= GetBeamPos(q2_half_im)

	pk_1 = pos_1[2:]
	pk_2 = pos_2[2:]
	pk_3 = pos_3[2:]
	pk_4 = pos_4[2:]
	pos_1 = pos_1[0:2]
	pos_2 = pos_2[0:2]
	pos_3 = pos_3[0:2]
	pos_4 = pos_4[0:2]
		

	#get quadratic distance from centroids
	print("Centroids: ", pos_1, pos_2, pos_3, pos_4)
	#print("Peaks: ", pk_1, pk_2, pk_3, pk_4)
	distance= Dist(pos_1, pos_2, pos_3, pos_4)
	print("Dist= ", distance)

	#save corrector values and distance to file
	f= open("correctorValues_Distance.txt", "a+")
	c1, c2, c3, c4= GetCorr()
	f.write(f'{c1:.4f}\t{c2:.4f}\t{c3:.4f}\t{c4:.4f}\t{distance:.4f}\n')
	f.close()

	#run GP script
	if (tbl == 'y'):
		eps_input= input("Enter the desired acquisition function parameter:")	
	else:
		eps_input= eps_stable
		count = count + 1
	
	GaussProc(float(eps_input), float(theta))

	#continue or not
	if (tbl == 'y'): 
		cont= input("Continue? y/n ")
	elif (tbl == 'n' and count ==10):
		count = 0
		cont = input("Continue? y/n ")
