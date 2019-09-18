#Setup of PVs and defined functions for optimizer
import datetime
from time import *
from os import system
import numpy as np
from epics import caget, caput, cainfo

##Set currents##
q1_cset= 'SCR_BTS35:PSQ_D1475:I_CSET'
q2_cset= 'SCR_BTS35:PSQ_D1479:I_CSET'
q3_cset= 'SCR_BTS35:PSQ_D1525:I_CSET'
q4_cset= 'SCR_BTS35:PSQ_D1532:I_CSET'
h13_cset= 'REA_BTS34:DCH_D1413:I_CSET'
v13_cset='REA_BTS34:DCV_D1413:I_CSET'
h31_cset= 'REA_BTS34:DCH_D1431:I_CSET'
v31_cset= 'REA_BTS34:DCV_D1431:I_CSET'

##Read currents##
q1_ird= 'SCR_BTS35:PSQ_D1475:I_RD'
q2_ird= 'SCR_BTS35:PSQ_D1479:I_RD'
q3_ird= 'SCR_BTS35:PSQ_D1525:I_RD'
q4_ird= 'SCR_BTS35:PSQ_D1532:I_RD'
h13_ird='REA_BTS34:DCH_D1413:I_RD'
v13_ird='REA_BTS34:DCV_D1413:I_RD'
h31_ird='REA_BTS34:DCH_D1431:I_RD'
v31_ird='REA_BTS34:DCV_D1431:I_RD'

##Status##  #should probably complete this later

##Viewer Actions##
set_image_name= 'SCR_BTS35:VD_D1542:TIFF1:FileName'
write_image= 'SCR_BTS35:VD_D1542:TIFF1:WriteFile'

def GetQuads():

	'''Gets current quad values'''
	q1= caget(q1_ird, wait= True)
	q2= caget(q2_ird, wait= True)
	q3= caget(q3_ird, wait= True)
	q4= caget(q4_ird, wait= True)
	return q1, q2, q3, q4


def SetQuads(v1, v2, v3, v4):

	'''Set quads to new value'''

	caput(q1_cset, v1, wait= True)
	caput(q2_cset, v2, wait= True)
	caput(q3_cset, v3, wait= True)
	caput(q4_cset, v4, wait= True)
	print("Quads set.")


def GetCorr():

	'''Gets the current corrector values'''

	c1= caget(h13_ird, wait= True)
	c2= caget(v13_ird, wait= True)
	c3= caget(h31_ird, wait= True)
	c4= caget(v31_ird, wait= True)
	return c1, c2, c3, c4


def SetCorr(v1, v2, v3, v4):

	'''Sets the correctors to new values'''

	caput(h13_cset, v1, wait= True)
	caput(v13_cset, v2, wait= True)
	caput(h31_cset, v3, wait= True)
	caput(v31_cset, v4, wait= True)
	print("Correctors set.")


def SaveIm(tunename):

	'''Save viewer image at FP1'''

    timestring = (datetime.datetime.now()).strftime("%m-%d_%H:%M.%f")
    filename='D1542'+'_'+tunename+'_'+timestring
    caput(set_image_name, filename, wait=True)   #sets image name
    caput(write_image, 1, wait=True)   #saves image
 	print(f'Screenshot {tunename} obtained')
	return filename

def GetBeamPos(imname):

	'''Run viewer image analysis code to get centroids'''

	#run viewer code
	os.system(f"python3 ~/Document/Viewer-Image-Analysis/src/im_analysis {imname}.tiff")
	#import text with results
	data= np.loadtxt=(f"~/Document/Viewer-Image-Analysis/output/optimizer/BeamLoc_{imname}.csv")
	#read x and y in mm
	x_centroid= data[4]
	y_centroid= data[5]
	#return (x, y)
	return x_centroid, y_centroid 

def Dist(p1, p2, p3, p4):

	'''Get quadratic distance between the 4 centroids (mm)'''
    meas_num= 12
	x1, y1, x2, y2, x3, y3, x4, y4= p1[0], p1[1], p2[0], p2[1], p3[0], p3[1], p4[0], p4[1]
    dist= 1/meas_num * (np.power((x1-x2),2)
                      + np.power((y1-y2),2)
                      + np.power((x1-x3),2) 
                      + np.power((y1-y3),2) 
                      + np.power((x1-x4),2) 
                      + np.power((y1-y4),2)
					  + np.power((x2-x4),2) 
                      + np.power((y2-y4),2)
					  + np.power((x3-x4),2) 
                      + np.power((y3-y4),2)
					  + np.power((x2-x3),2) 
                      + np.power((y2-y3),2)
                       ) 
    return np.sqrt(dist)























 

