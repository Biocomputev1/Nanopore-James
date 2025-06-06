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
    x, y = [], []
    try:
        with open(outfile, 'r') as f:
            for line in f:
                values = [float(s) for s in line.strip().split(',')]
                x.append(values[0])
                y.append(values[1] * 1E9)
    except Exception as e:
        print(f"Error reading {outfile}: {e}")
        return

    if not x:
        print("No data to plot.")
        return

    plt.plot(x, y, 'r', lw=1)
    plt.title(outfile)
    plt.grid(True)
    plt.xlabel('Time (s)')
    plt.ylabel('Current (nA)')
    figure_out = f'wafer_{wafer}_chip{chip}_{stamp}.png'
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
    print(f"Raw data: '{data}'")
    ser_in.flush()
    print(dt, ',',data, flush = True)
    return dt,data

def _shutdown(): #to do after end of experiment
    ser_out.write(b'0')# close circuit
    ser_in.reset_input_buffer()#Flush input buffer, discarding 
                                        #all it’s contents.
    ser_in.reset_output_buffer()#Clear output buffer, aborting the
    ser_in.close()                   #current output and discarding 
    ser_out.close()        
    _plot()
    
    shutil.move(outfile, stamp) #move file to date directory
    
    print(outfile)
    winsound.Beep(500, 5000)

#intializing the COM ports

print()
print("Intializing COM ports.......")
#Arduino connection
try:
    ser_out = serial.Serial('COM4', 230400, timeout=0.1)
    print(ser_out.readline().decode('ascii').strip())  # Read response from the arduino if successfully connected there will be a response from the arduino begin function
    print("Aruino Connected Successfully :)")
except serial.SerialException as e:
    print("Serial error:", e)
#Current Ranger input 
try:
    ser_in = serial.Serial('COM5', 230400, timeout=1)
    print("Current RangerConnected successfully :)")
except serial.SerialException as e:
    print("Serial error:", e)

ser_out.write(b'0') # close the circuit

#INPUTS

print()
print('Check cables. Connect Arduino to PC. This Relay is closed at startup.')
print('Acquisition rate of 200 Hz')
wafer = input('wafer name: ')
chip = int(input('chip n°: '))
tresh = float(input('Current threshold (A): '))

outfile = 'wafer_'+ wafer + '_'+ 'chip'+ str(chip) +'_'+  stamp +'.dat'

print('File name: ', outfile)
print()
print('....press CRTL+C to BREAK experiment.') 
begin = input('press ENTER key to begin in 5 sec. Relay will open the circuit.')

ser_out.write(b'1')# open circuit to start 
tCurrent = time.perf_counter()# timer - start reference time

while time.perf_counter() <= tCurrent + 5 :  #time with no treshold
    dt, data=_read_print()
    _save_file()
        
while True:
    try:
        dt, data=_read_print()
        _save_file()
    
        if(float(data) >= tresh) or (time.perf_counter() >= tCurrent+600):
            #shutdown if current theshold is reached or after 500 seconds
            _shutdown()
            print('The End')        
            break
    except ValueError:
        continue #skip error value
    except:
        _shutdown()
        print('Keyboard Interrupt!')
        break