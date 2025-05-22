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
import pyvisa

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

def _save_file():
    with open(outfile, 'a') as f:
        line = [str(dt),data]
        f.write(','.join(line)+'\n')
        f.flush()

def _read_print():
    dt = round(time.perf_counter()-tCurrent,5)
    data = ser_in.readline().rstrip().decode('utf-8')
    ser_in.flush()
    print(dt, ',',data, flush = True)
    return dt,data

#intializing the COM ports

print()
print("Intializing COM ports.......")

try:
    ser_out = serial.Serial('COM4', 115200, timeout=0.1)
    print(ser_out.readline().decode('ascii').strip())  # Read response from the arduino if successfully connected there will be a response from the arduino begin function
    print("Aruino Connected Successfully :)")
except serial.SerialException as e:
    print("Serial error:", e)
#Current Ranger input 
try:
    ser_in = serial.Serial('COM5', 115200, timeout=1)
    print("Current RangerConnected successfully :)")
except serial.SerialException as e:
    print("Serial error:", e)

rm = pyvisa.ResourceManager()
print("VISA Resources found: ",rm.list_resources())

ps = rm.open_resource(resource_name = 'USB0::0x2EC7::0x9200::800889011797710062::INSTR')
ps.timeout = 1000
ps.write_termination = '\n'
ps.read_termination = '\n'

ps.write("*CLS")
print("Connnected to:", ps.query("*IDN").strip())
print("Initial error state:", ps.query("SYST:ERR?").strip())

current_limit = float(input("Please to Set the Current Limit: "))
overVoltageProtection = float(input("Please to Set the Voltage for Over Voltage Protection: "))
overCurrentProtection = float(input("Please to Set the Current for Over Current Protection: "))
voltage = float(input("Please to Set the Target Voltage (Constant V mode): "))

ps.write("OUTP OFF")
ps.write("SOUR: VOLT 0")
ps.write(f"SOUR:CURR {current_limit}")
ps.write(f"OVP {overVoltageProtection}")
ps.write(f"OCP {overCurrentProtection}")
ps.write("OUTP ON")
print("Output configured and enabled")

print("Setting the Target Voltage")
try:
    ps.write(f"SOUR:VOLT {voltage}")
    time.sleep(0.2)
    err = ps.query("SYST:ERR?").strip()
    if not err.startswith("0"):
        print(f"Voltage {voltage} V set with warning : {err}")
    else:
        print(f"Voltage set to {voltage} V")
except Exception as e:
    print(f"Error Setting {voltage}V : {e}")

print("Setting Up Voltage is done")


