# -*- coding: utf-8 -*-
"""
Created in 2020
@author: Pedro Miguel Sousa, 
Single molecule Processes Lab, ITQB-NOVA
pm.sousa@itqb.unl.pt
"""

import time  # Required to use delay functions
import shutil
import numpy as np
import pandas as pd
import os
import winsound
import serial  # Serial imported for Serial communication
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

from matplotlib.ticker import MultipleLocator

print()
print('DIELECTRIC BREAKDOWN SLOPE SCRIPT')
print()

# set working directory

stamp = time.strftime("%m-%d-%Y")

print(os.getcwd())

try:
    os.mkdir(stamp)
    print(stamp, 'Directory created')
except FileExistsError:
    print(stamp, 'Directory already exists')


# FUNCTIONS

def _sendV(app_voltage):
    voltage_com = 'VOLT'+str(app_voltage).zfill(3)+'\r'
   # power_s.write(voltage_com.encode('ascii'))


def _read_print():  # function to read and print data current
    try:
        if not ser_in.is_open:
            print("Error: Serial input port is not open.")
            return None, None

        raw_line = ser_in.readline()
        if not raw_line:
            print("Warning: No data read from serial.")
            return None, None

        data = raw_line.rstrip().decode('utf-8').strip()

        if data.lower() == 'shutdown':
            print("Shutdown signal received.")
            return None, 'shutdown'

        ser_in.flush()
        dt = round(time.perf_counter() - tCurrent, 4)
        print(dt, ' , ', app_voltage / 10, ' , ', data, flush=True)

        return dt, data

    except Exception as e:
        print(f"Exception in _read_print(): {e}")
        return None, None



def _save_file():  # append data to file
    with open(outfile, 'a') as f:
        line = [str(dt), str(app_voltage/10), data]
        f.write(','.join(line)+'\n')
        f.flush()


def _shutdown():  # to do after end of experiment
    print("Shutdown initiated...")

    try:
        if ser_out.is_open:
            ser_out.write(b'0')  # Close circuit
        else:
            print("Warning: Serial output port is not open.")
    except Exception as e:
        print(f"Error writing to ser_out: {e}")

    # acquire data for +1 second after relay is off
    stime = time.perf_counter()
    while time.perf_counter() <= stime + 1:
        try:
            if not ser_in.is_open:
                print("Serial input port not open. Skipping data read.")
                break

            data = ser_in.readline().rstrip().decode('utf-8').strip()
            ser_in.flush()

            dt = round(time.perf_counter() - tCurrent, 4)
            print(dt, ' , 0 , ', data, flush=True)

            with open(outfile, 'a') as f:
                line = [str(dt), '0', data]
                f.write(','.join(line) + '\n')
                f.flush()

        except Exception as e:
            print(f"Error during shutdown data collection: {e}")
            break

    # Safe closing of serial ports
    try:
        if ser_out.is_open:
            ser_out.close()
    except Exception as e:
        print(f"Error closing ser_out: {e}")

    try:
        if ser_in.is_open:
            ser_in.reset_input_buffer()
            ser_in.reset_output_buffer()
            ser_in.close()
    except Exception as e:
        print(f"Error closing ser_in: {e}")

    print("Shutdown complete. Generating plot...")

    try:
        _plot()  # send data to plot function
        shutil.copy(outfile, stamp)  # move file to date directory
        print(f"Output file saved: {outfile}")
    except Exception as e:
        print(f"Error during plot or file copy: {e}")

    winsound.Beep(500, 5000)


def _plot():  # function to make and save plots at the end
    plt.rcParams['figure.figsize'] = [13, 7]
    plt.rcParams.update({'font.size': 18})

    headers = ['time', 'voltage', 'current']
    df = pd.read_csv(outfile, names=headers)
    df.current = df.current.apply(pd.to_numeric, args=('coerce',))

    mx_current = df.current.max()
    mx_index_voltage = df.voltage.idxmax()
    mxvoltage = df.voltage[mx_index_voltage]

    figure_out = 'wafer_' + wafer + '_chip_' + str(chip) + '_' + stamp + '.png'

    fig, ax1 = plt.subplots()

    # Main plot
    ax1.plot(df.time.values, df.current.values * 1E9, color='red', lw=0.5, alpha=0.9)
    ax1.set_ylabel('Current (nA)', fontsize=22, labelpad=10)
    ax1.xaxis.set_minor_locator(MultipleLocator(5))
    ax1.set_xlabel('Time (s)', fontsize=22, labelpad=10)
    ax1.tick_params(which='both', axis='x', direction='in')
    ax1.tick_params(axis='y', direction='in')

    # Inset Plot
    axins = inset_axes(ax1, loc=2, width='40%', height='55%', borderpad=1)
    axins.plot(df.time.values, df.current.values * 1E9, 'r.-', lw=1)
    axins.tick_params(labelright=True, labelbottom=True, labelleft=False, labelsize=12)
    axins.tick_params(which='both', axis='both', direction='in')
    axins.xaxis.set_minor_locator(MultipleLocator(0.01))
    axins.xaxis.grid(True, which='both')
    axins.yaxis.grid(True, which='major')
    plt.axhline(y=(tresh * 1E9), color='blue', linestyle='dotted')

    try:
        axins.set_xlim(df.time.iloc[-1] - 1.2, df.time.iloc[-1] - 0.7)
    except Exception as e:
        print(f"Warning: Failed to set inset x-limits: {e}")

    # 2nd top x-axis (Voltage)
    ax2 = ax1.twiny()

    vmin = df.voltage.iloc[0]
    vmax = df.voltage.max()

    valid_x2 = True
    if len(df.current) == 0 or pd.isna(vmin) or pd.isna(vmax) or vmax == vmin:
        print("Warning: Invalid values for voltage range or current length.")
        valid_x2 = False
    else:
        steps = (vmax - vmin) / len(df.current)
        if steps <= 0 or np.isnan(steps) or np.isinf(steps):
            print("Warning: Invalid step size for voltage range.")
            valid_x2 = False

    if valid_x2:
        x2 = np.arange(vmin, vmax, steps)
        y2 = df.current.values * 1E9
        if len(x2) == len(y2):
            ax2.plot(x2, y2, lw=0)
        else:
            print("Warning: Skipping voltage axis plot due to length mismatch.")
    else:
        print("Skipping voltage axis plot due to bad input.")

    ax2.set_xlabel('Voltage (V)', fontsize=22, labelpad=10)
    ax2.tick_params(which='both', axis='x', direction='in')
    ax2.tick_params(axis='y', direction='in')
    ax2.ticklabel_format(style='plain')

    plt.text(0.5, 0.9, 'Max current (nA) =', horizontalalignment='left',
             verticalalignment='center', transform=ax1.transAxes)
    plt.text(0.76, 0.9, round(mx_current * 1E9, 1), horizontalalignment='left',
             verticalalignment='center', transform=ax1.transAxes)
    plt.text(0.5, 0.85, 'at', horizontalalignment='left',
             verticalalignment='center', transform=ax1.transAxes)
    plt.text(0.54, 0.85, f'{mxvoltage:.2f}', horizontalalignment='left',
             verticalalignment='center', transform=ax1.transAxes)
    plt.text(0.60, 0.85, 'V', horizontalalignment='left',
             verticalalignment='center', transform=ax1.transAxes)

    plt.title(outfile, fontsize=24, pad=35)
    plt.savefig(figure_out)
    plt.show()

    shutil.copy(figure_out, stamp)  # move file to date directory


# initialize COM PORTS
print()
print()
print('initializing COM ports....')
#1
# INPUT-CURRENT RANGER
#
#cr_com='COM'+str(int(cr_com_n))
#a_com='COM'+str(int(a_com_n))
#ps_com='COM'+str(int(ps_com_n))
#
#
ser_in = serial.Serial('COM5', 230400, timeout=0.1)
#
# OUTPUT TO ARDUINO RELAY
ser_out = serial.Serial('COM4', 230400, timeout=0.1)  # COM4
#
# POWER SUPPLY SOURCE
#
#power_s = serial.Serial('COM3', 9600, timeout=0.1)

#power_s.write('GMOD\r'.encode('ascii'))  # INFO
#print(power_s.readline().decode('ascii'))
#power_s.write('VOLT008\r'.encode('ascii'))  # voltage zero
#print(power_s.readline().decode('ascii'))
#power_s.write('CURR003\r'.encode('ascii'))  # Set MAX current
#print(power_s.readline().decode('ascii'))


# Initial INPUTS

print()
print('Check cables. Turn CurrentRanger ON. Turn Power supply ON. Connect Arduino to PC. Relay is closed at startup.')
print('Current Acquisition rate = 200 Hz')
print('Voltage slope = 0.01 V/s')

wafer = 'DUMMY' #input('wafer name: ')  SILSON2_JY_
print('Wafer: ', wafer
      )
chip = int(input('chip n°: '))
start_voltage = int(10) #input('DEB start Voltage (V): '))*10
print('Start voltage: ', start_voltage/10)

tresh = float(100e-9) #input('Current threshold (A): '))
print('I_th: ', tresh,' A')

#sec_per_step=float(input('seconds per 100mV:'))
end_voltage = 400  # Voltage limit
print('V_lim: ', end_voltage/10,' V')

sec_per_step = (15/1)  # Time seconds per step. 10/3 as default

outfile = 'wafer_' + wafer + '_' + 'chip_' + str(chip) + '_' + stamp + '.dat'

print('File name: ', outfile)
print()
print('....press CRTL+C to BREAK experiment.')
begin = input(
    'press ENTER key to begin in 5 sec. Relay will open the circuit. Auto PS and CurrentRanger.')

# time to stabilize data read from the CR

Twait = time.perf_counter()  # timer

while time.perf_counter() <= Twait + 5:  # time wait while calling
    # serial data
    ser_in.readline().rstrip().decode('utf-8')  # starts calling read data
    ser_in.flush()

# START EXPERIMENT

ser_out.write(b'1')  # open circuit to start
# ser_in.readline().rstrip().decode('utf-8') #starts calling read data
# ser_in.flush()


# PS ON to initial voltage value 0.1 V/sec
for app_voltage in np.arange(10, start_voltage+2, 2):
    _sendV(app_voltage)
    print(app_voltage/10, ser_in.readline().rstrip().decode('utf-8'))
   # power_s.readline().decode('ascii')


tCurrent = time.perf_counter()  # timer - start reference time
tic = 0

#while True:

while 1:
    try:            
        timer = time.perf_counter()  # timer
        dt, data = _read_print()
        _save_file()
        tic += time.perf_counter()-timer

        if tic >= sec_per_step:
            app_voltage += 1  # voltage steps
            _sendV(app_voltage)
            tic = 0

        if (float(data) >= tresh) or (app_voltage >= end_voltage):
            # shutdown if current theshold is reached or max voltage
            _shutdown()
            print('The End')
            break
    except ValueError:
        continue  # skip error value
    except:
        _shutdown()
        print('Keyboard Interrupt!')
        break
