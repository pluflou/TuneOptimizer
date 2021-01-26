
from time import sleep
from epics import caget, caput


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
#get current dipole nmr fields
#check if I need high range or low range probes by looking at the current set
irangeswitch= 43.4 

b1_current = caget(b1_ird)

print("Checking probe ranges...")
if (b1_current >= irangeswitch):
    b1_probe = 1
    b2_probe = 3
else:
    b1_probe = 2
    b2_probe = 4

#testing lowering matched dipoles
count=0
dI =   0.001 

while(count<15):
    b1_i = caget(b1_icset) 
    b2_i = caget(b2_icset)

    caput(set_probe, b1_probe)
    caput(b1_icset, b1_i - dI)
        #saving the new actual nmr value
    sleep(4)
    b1_nmr_h = caget(tlm_reading)

    caput(set_probe, b2_probe)
    # change b2 and compare
    caput(b2_icset, b2_i - dI)
    #saving the new actual nmr value
    sleep(4)
    b2_nmr_h = caget(tlm_reading)
    
    print(f"Fields: {b1_nmr_h:.6f}, {b2_nmr_h:.6f}, dNMR: {((b1_nmr_h - b2_nmr_h)/b1_nmr_h*100):.5f}%")
    count = count + 1
