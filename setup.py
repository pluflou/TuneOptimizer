#Setup of PVs and defined functions for optimizer
import datetime
from time import *
import os
import numpy as np
from epics import caget, caput, cainfo

cont = 'yes'

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

##dipoles##
#nmr probes
set_probe = 'SCR_BTS35:NMR1_D1489:PRB_CSET'
tlm_reading = 'SCR_BTS35:NMR_N0001:B_RD'
lock_status = caget('SCR_BTS35:NMR_N0001:LOCK_RSTS')

#power supplies
b1_icset = 'SCR_BTS35:PSD_D1489:I_CSET'
b2_icset = 'SCR_BTS35:PSD_D1504:I_CSET'
b1_ird = 'SCR_BTS35:PSD_D1489:I_RD'
b2_ird = 'SCR_BTS35:PSD_D1504:I_RD'

#hlc field settings
b1_bcset = 'SCR_BTS35:DH_D1489:B_CSET'
b2_bcset = 'SCR_BTS35:DH_D1504:B_CSET'
b1_brd = 'SCR_BTS35:DH_D1489:B_RD'
b2_brd = 'SCR_BTS35:DH_D1504:B_RD'

#cycling parameters
b1_cycle = 'SCR_BTS35:PSD_D1489:CYCL_CMD'
b1_iters = caget('SCR_BTS35:PSD_D1489:CYCL_ITERS')
b1_cpstm = caget('SCR_BTS35:PSD_D1489:CYCL_PSTM')
b2_cycle = 'SCR_BTS35:PSD_D1504:CYCL_CMD'
b2_iters = caget('SCR_BTS35:PSD_D1504:CYCL_ITERS')
b2_cpstm = caget('SCR_BTS35:PSD_D1504:CYCL_PSTM')


##Status##  #should probably complete this later

##Viewer Actions##
set_image_name= 'SCR_BTS35:VD_D1542:TIFF1:FileName'
write_image= 'SCR_BTS35:VD_D1542:TIFF1:WriteFile'

def GetQuads():

    '''Gets current quad values'''

    q1= caget(q1_ird)
    q2= caget(q2_ird)
    q3= caget(q3_ird)
    q4= caget(q4_ird)
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

    c1= caget(h13_ird)
    c2= caget(v13_ird)
    c3= caget(h31_ird)
    c4= caget(v31_ird)
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
    print(f"Screenshot {tunename} obtained")
    return filename

def GetBeamPos(imname):

    '''Run viewer image analysis code to get centroids'''

    #run viewer code
    os.system(f"python3 /user/e18514/Documents/viewer-image-analysis/src/im_analysis.py /mnt/daqtesting/secar_camera/new_captures/{imname}_000.tiff")
    #import text with results
    data= np.loadtxt(f"/user/e18514/Documents/viewer-image-analysis/output/optimizer/BeamLoc_{imname}_000.csv")
    #read x and y in mm
    x_centroid= data[0]
    y_centroid= data[1]

    x_peak= data[6]
    y_peak= data[7]
    #return (x, y)
    return x_centroid, y_centroid, x_peak, y_peak

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
    if dist == 0:
        return 0
    else: 
        return 1/np.sqrt(dist)
    
def GaussProc(eps_input, theta_input):

    '''Run Gaussian Process script and set correctors to new value'''
    
    os.system(f"python /user/e18514/Documents/tuneoptimizer/GaussianProcess.py {eps_input} {theta_input}")

def nmrRange():
    ''' Checks which range the NMR probes should be in and returns probe numbers for B1 and B2 '''
 
    irangeswitch= 43.4 

    b1_current = caget(b1_ird)

    print("Checking probe ranges...")
    if (b1_current >= irangeswitch):
        b1 = 1
        b2 = 3
    else:
        b1 = 2
        b2 = 4

    return b1, b2

def cycleB1B2():
    
    time = max(b1_cpstm, b2_cpstm)*max(b1_iters, b2_iters)*2 + 30
    print(f"Cycling...wait {time/60} minutes")
    caput(b1_cycle, 1)
    caput(b2_cycle, 1)
    #this wait time is long enough for the cycling to end and the NMRs to settle
    sleep(time)

    print("Done cycling.")






















 

