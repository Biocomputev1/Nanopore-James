"""
Started on Wed N 21, 2025
@author: Naveen M, 
Electronics Department, BioCompute.
Version 0.0.1
"""

import time
import shutil
import os
import winsound
import serial
import matplotlib.pyplot as plt

print()
print("BIOCOMPUTE NANOPORE FAB - Constant Voltage Model")
print()
stamp = time.strftime("%d-%m-%y")

try:
    os.mkdir(stamp)
    print(stamp,'Directory Created')
except FileExistsError:
    print(stamp,'Directory already exist!')

#Function to make and save plots at the end

def _plot():
    plt.rcParams['figure.figsize'] = [13,7]
    x,y = [],[]
    for line in open(outfile,'r'):
        values = [float(s) for s in line.split(',')]
        x.append(values[0])
        y.append(values[1]*1E9)

    plt.plot(x,y,'r',lw=1)
    plt.title(outfile)
    plt.grid(which='both', axis='both')
    plt.xlim(0, )
    plt.xlabel('time (s)')
    plt.ylabel('Currrent (nA)')
    figure_out='wafer_'+ wafer + '_'+ 'chip'+ str(chip) + '_' + voltage +'V_'+ stamp+'.png'
    plt.savefig(figure_out)
    plt.show()
    shutil.copy(figure_out, stamp)