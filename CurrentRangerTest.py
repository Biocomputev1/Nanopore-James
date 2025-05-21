import serial

try:
    ser = serial.Serial('COM5', 115200, timeout=1)
    print("Connected successfully.")
    ser.close()
except serial.SerialException as e:
    print("Serial error:", e)
