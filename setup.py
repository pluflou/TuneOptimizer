#Setup of PVs and defined functions for optimizer
import datetime
from time import *
from cothread.catools import caget, caput
##Set currents##
q1_cset
q2_cset
dch1413_cset
dcv1413_cset
dch1431_cset
dcv1431_cset
##RB currents##
fc1448_ird
fc1485_ird
fc1542_ird
ap1460_ird
ap1456_ird
ap1468_ird
ap1470_ird
##I/O##
attn10_in
attn100_in
attn10_out
attn100_out
vd1542_in
vd1542_out
fc1485_in
fc1485_out
fc1448_in
fc1542_in
fc1448_out
##STATUS##
vd1542_atloc
q1_on
q2_on
fc1448_atloc= caget('....') #check if we want 0 or 1 and set functions below accordingly
fc1485_atloc
attn10_atloc
attn100_atloc
##ACTIONS#
save_image

q1_optics, q2_optics= -60, 120 #Change this based on tune
dch1413_current, dcv1413_current, dch1431_current, dcv1431_current= 0, 0, 0, 0

def QuadsSet(value):
	if (q1_on==True and q2_on==True):
		if (value=='optics'):
			caput(q1_cset, q1_optics, wait=False, timeout=60)
			caput(q2_cset, q2_optics, wait=True, timeout=60)
		elif (value == 'half'):
			caput(q1_cset, q1_optics/2, wait=False, timeout=60)
			caput(q2_cset, q2_optics/2, wait=True, timeout=60)
		elif (value == 'zero'):
			caput(q1_cset, 0, wait=False, timeout=60)
			caput(q2_cset, 0, wait=True, timeout=60)			
	else:
		print("Quads are not on.")

def AttIn():
	caput(attn10_in, 0, wait=True, timeout=60)
	caput(attn100_in, 0, wait=True, timeout=60)
	#add some line that double checks that they're in successfully

def AttOut():
	caput(attn10_out, 0, wait=True, timeout=60)
	caput(attn100_out, 0, wait=True, timeout=60)

def SaveIm():
	caput(vd1542_in, 0, wait=True, timeout=5)
	AttIn()
	caput(fc1448_out, 1, wait=True, timeout=5)
	caput(fc1485_out, 1, wait=True, timeout=5)
        sleep(40)
        timestring = (datetime.datetime.now()).strftime("%m-%d_%H:%M.%f")
        filename='D1542'+'_opt_'+timestring
        caput('SCR_BTS35:VD_D1542:TIFF1:FileName', filename, wait=True, timeout=5)   #takes screenshot
        caput('SCR_BTS35:VD_D1542:TIFF1:WriteFile', 1, wait=True, timeout=10)   #takes screenshot
 	print('Screenshot obtained')
        sleep(2)
	return filename

#def GetBeamPos():
	#run viewer code
	#import text with results
	#read x and y in mm
	#return (x, y)

def VarySteerers(loc, direction):
	if (loc=='upstream'):
		if (direction== 'increase'):

		elif(direction== 'decrease'):
	if (loc=='downstream'):
		if (direction== 'increase'):
		elif(direction== 'decrease'):























 

