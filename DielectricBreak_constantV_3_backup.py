# -*- coding: utf-8 -*-
"""
Created on Wed N 27, 2019
@author: Pedro Miguel Sousa, 
Single molecule Processes Lab, ITQB-NOVA
pm.sousa@itqb.unl.pt
"""

import time #Required to use delay functions
import shutil
import os
import winsound
import serial #Serial imported for Serial communication
import matplotlib.pyplot as plt

print()
print('DIELECTRIC BREAKDOWN - Constant voltage SCRIPT')
print()
stamp = time.strftime("%d-%m-%Y")

try:
#    os.mkdir(stamp)
   print (stamp, 'Directory created')
except FileExistsError:
   print (stamp, 'Directory already exists')
     

def _plot(): #function to make and save plots at the end    
    plt.rcParams['figure.figsize'] = [13, 7]    
    x, y = [], []
    for line in open(outfile, 'r'):
        values = [float(s) for s in line.split(',')]
        x.append(values[0])
        y.append(values[1]*1E9)
    #########
    plt.plot(x, y, 'r', lw=1)
    plt.title(outfile)
    plt.grid(which='both', axis='both')
    plt.xlim(0, )
    plt.xlabel('time (s)')
    plt.ylabel('Currrent (nA)')
    figure_out='wafer_'+ wafer + '_'+ 'chip'+ str(chip) + '_' + voltage +'V_'+ stamp+'.png'
    plt.savefig(figure_out)
    plt.show()
    ########
    # plt.semilogy(y, 'ro-', lw=1)
    # plt.grid(which='both', axis='both')
    # plt.xlim(0, )
    # plt.ylabel('Currrent (nA)')
    # plt.savefig('wafer_' + wafer + '_'+ 'chip'+ str(chip)  + '_' + voltage +'V_'+ stamp + '_log.png')
    # plt.show()
    shutil.copy(figure_out, stamp)  # move file to date directory

    
def _save_file(): #function to write data to file
        with open(outfile, 'a') as f:
            line= [str(dt),data]
            f.write (','.join(line)+'\n')
            f.flush()

def _read_print(): #function to read data current 
        dt = round(time.perf_counter()-tCurrent, 5)# current time variable
        data = ser_in.readline().rstrip().decode('utf-8')    
        ser_in.flush()
        print(dt, ' , ', data, flush=True)
        return dt, data #send data to main program
    
def _shutdown(): #to do after end of experiment
    ser_out.write(b'0')# close circuit
    ser_in.reset_input_buffer()#Flush input buffer, discarding 
                                        #all it’s contents.
    ser_in.reset_output_buffer()#Clear output buffer, aborting the
    ser_in.close()                   #current output and discarding 
    ser_out.close()                    #all that is in the buffer.
    
    power_s.write('VOLT008\r'.encode('ascii'))# 
    power_s.readline().decode('ascii')
    power_s.close()
    
    _plot()
    
    shutil.move(outfile, stamp) #move file to date directory
    
    print(outfile)
    winsound.Beep(500, 5000)

##############################################

# initialize COM PORTS
print()
print()
print('initializing COM ports....')
#
# INPUT-CURRENT RANGER
#
#cr_com='COM'+str(int(cr_com_n))
#a_com='COM'+str(int(a_com_n))
#ps_com='COM'+str(int(ps_com_n))
#
#
ser_in = serial.Serial('COM6', 230400, timeout=0.1)
#
# OUTPUT TO ARDUINO RELAY
ser_out = serial.Serial('COM4', 230400, timeout=0.1)  # COM4
#
# POWER SUPPLY SOURCE
#
power_s = serial.Serial('COM3', 9600, timeout=0.1)

power_s.write('GMOD\r'.encode('ascii'))  # INFO
print(power_s.readline().decode('ascii'))
power_s.write('VOLT008\r'.encode('ascii'))  # voltage zero
print(power_s.readline().decode('ascii'))
power_s.write('CURR003\r'.encode('ascii'))  # Set MAX current
print(power_s.readline().decode('ascii'))

ser_out.write(b'0')  # close circuit


######################### Initial INPUTS

print('Check cables. Connect Arduino to PC. This Relay is closed at startup.')
print('Acquisition rate of 200 Hz')
wafer = input('wafer name: ')
chip = int(input('chip n°: '))
voltage = input('Applied Voltage (V): ')
c_voltage = float(voltage)*10
tresh = float(input('Current threshold (A): '))
no_tresh = float(input('Initial time with NO current limit (s): '))

outfile = 'wafer_'+ wafer + '_'+ 'chip'+ str(chip) +'_'+ voltage +'V_'+ stamp +'.dat'


voltage_com='VOLT'+str(int(c_voltage)).zfill(3)+'\r'

print('File name: ', outfile)
print()
print('....press CRTL+C to BREAK experiment.') 
begin = input('press ENTER key to begin in 5 sec. Relay will open the circuit.')

power_s.write(voltage_com.encode('ascii')) #Set conditioning voltage
print(power_s.readline().decode('ascii')) #wait for reply

Twait = time.perf_counter()# timer

while time.perf_counter() <= Twait + 5:  #time wait while calling 
                                            #serial data
    ser_in.readline().rstrip().decode('utf-8') #starts calling read data
    ser_in.flush()

##################################START READING DATA

ser_out.write(b'1')# open circuit to start 
tCurrent = time.perf_counter()# timer - start reference time

while time.perf_counter() <= tCurrent + no_tresh:  #time with no treshold
    dt, data=_read_print()
    _save_file()
        
while True:
    try:
        dt, data=_read_print()
        _save_file()
    
        if (float(data) >= tresh) or (time.perf_counter() >= tCurrent+600):
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