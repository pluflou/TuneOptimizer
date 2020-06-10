import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from epics import caget, caput
from time import *
import sys

filename = sys.argv[1]

#b1 is the "first" dipole and b2 is the "second" dipole of the pair

scan = pd.read_csv(filename, sep='\t', header=None)

scan.columns = ["b1_i", "b2_i", "b1_nmr", "b2_nmr", "dist", "xpos", "im_name"]

avg_nmr = (scan["b1_nmr"] + scan["b2_nmr"])/2

#polyfit for dist and nmr
z = np.polyfit(avg_nmr, scan["dist"], 3)
p = np.poly1d(z)

xp = np.linspace(avg_nmr.min(), avg_nmr.max(), 500)

nmr_min = xp[p(xp).argmin()]

#linear regression for currents and nmr
z1 = np.polyfit( scan["b1_nmr"], scan["b1_i"], 1)
z2 = np.polyfit( scan["b2_nmr"], scan["b2_i"], 1)

p1 = np.poly1d(z1)
p2 = np.poly1d(z2)

xp1 = np.linspace(scan["b1_nmr"].min(), scan["b1_nmr"].max(), 500)
xp2 = np.linspace(scan["b2_nmr"].min(), scan["b2_nmr"].max(), 500)

b1_i_tune = p1(nmr_min)
b2_i_tune = p2(nmr_min)

#plt.plot(xp1, p1(xp1), label = 'B1')
#plt.plot(xp2, p2(xp2), label = 'B2')
#plt.legend()


print(f"Best tune is at nmr_avg = {nmr_min}")
print(f"Corres. {filename[0:2]} current is = {b1_i_tune}")
print(f"Corres. {filename[3:5]} current is = {b2_i_tune}")

plt.plot(xp, p(xp), '--', color='green')
plt.plot(avg_nmr, scan["dist"])
plt.plot(nmr_min, p(xp).min(), marker = '.', color = 'red', markersize=12)
plt.savefig(f"{filename[0:2]}_{filename[3:5]}_dipole_scan_fit.png", dpi=300)


plt.show() 
