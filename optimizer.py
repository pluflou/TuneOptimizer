import numpy as np
from setup import SaveIm, SetCorr, GetCorr, SetQuads, GetQuads, GetBeamPos, Dist


###import current state
#Get initial corrector values
h13_init, v13_init, h31_init, v31_init= GetCorr()
#Get initial quad values
q1_init, q2_init, q3_init, q4_init= GetQuads()


###Tuning Q1 and Q2

##take pictures
#take picture with all at init values
SetQuads(q1_init, q2_init, 0, 0)
all_nom_im= SaveIm('allNom')

#take picture with all at zero
SetQuads(0, 0, 0, 0)
all_zero_im= SaveIm('allZero')

#take picture with Q1 at half
SetQuads(q1_init/2, q2_init, 0, 0)
q1_half_im= SaveIm('q1half')

#take picture with Q2 at half
SetQuads(q1_init, q2_init/2, 0, 0)
q2_half_im= SaveIm('q2half')
 
#return quads to original values
SetQuads(q1_init, q2_init, q3_init, q4_init)

##get centroids from pictures
pos_1= GetBeamPos(all_nom_im)
pos_2= GetBeamPos(all_zero_im)
pos_3= GetBeamPos(q1_half_im)
pos_4= GetBeamPos(q2_half_im)

##get quadratic distance from centroids
distance= Dist(pos_1, pos_2, pos_3, pos_4)

###Run GP thing here??#####


#save corrector values and distance to file
f= open("optimizer_output", "a+")
c1, c2, c3, c4= GetCorr()
f.write(f"{c1} {c2} {c3} {c4} {distance}\n")
f.close()
