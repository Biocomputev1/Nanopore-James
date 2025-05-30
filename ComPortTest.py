"""
@author - Naveen M
Biocompute - Electronics Department
Bicompute, Bengaluru, IN.
electronics@biocomputeinc.com
"""
import time
import serial
#Arduino Relay Output
try:
    ser_out = serial.Serial('COM4', 115200, timeout=0.1)
    ser_out.write(b'0')
    time.sleep(0.1)
    print(ser_out.readline().decode('ascii').strip())  # Read response from the arduino if successfully connected there will be a response from the arduino begin function
    print("Aruino Connected Successfully :)")
except serial.SerialException as e:
    print("Serial error:", e)
#Current Ranger input 
try:
    ser = serial.Serial('COM5', 115200, timeout=1)
    print("Current RangerConnected successfully :)")
    ser.close()
except serial.SerialException as e:
    print("Serial error:", e)



