import time
import shutil
import os
import winsound
import serial
import threading
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style

# === Initialization ===
print("\nBIOCOMPUTE NANOPORE FAB - Constant Voltage Model\n")
stamp = time.strftime("%d-%m-%y")

try:
    os.mkdir(stamp)
    print(stamp, 'Directory Created')
except FileExistsError:
    print(stamp, 'Directory already exist!')

# === Globals ===
x_vals, y_vals = [], []
lock = threading.Lock()
outfile = ""
tCurrent = 0
ser_in = None
ser_out = None

# === Plot Setup ===
style.use('ggplot')
fig, ax = plt.subplots()
line, = ax.plot([], [], 'r', lw=1)


def init_plot():
    ax.set_title("Real-time Current Plot")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Current (nA)")
    ax.grid(True)
    return line,


def update(frame):
    with lock:
        line.set_data(x_vals, y_vals)
        if x_vals:
            ax.set_xlim(0, max(x_vals))
            ax.set_ylim(min(y_vals)-1, max(y_vals)+1)
    return line,


def _save_file(dt, data):
    with open(outfile, 'a') as f:
        f.write(f"{dt},{data}\n")


def serial_read_thread(tresh):
    global tCurrent, ser_in, x_vals, y_vals
    while True:
        try:
            raw_line = ser_in.readline().decode('utf-8').strip()
            if not raw_line:
                continue
            val = float(raw_line)
            dt = round(time.perf_counter() - tCurrent, 5)
            print(f"{dt} , {val}")

            with lock:
                x_vals.append(dt)
                y_vals.append(val * 1e9)  # convert to nA

            _save_file(dt, val)

            if abs(val) >= tresh or dt >= 600:
                print("\nThreshold or timeout reached, shutting down...")
                _shutdown()
                os._exit(0)
        except ValueError:
            print(f"Skipping invalid data: '{raw_line}'")
            continue
        except Exception as e:
            print("Error in serial reading thread:", e)
            break


def _final_plot():
    if not x_vals or not y_vals:
        print("No data to plot at shutdown.")
        return
    plt.figure()
    plt.plot(x_vals, y_vals, 'r', lw=1)
    plt.title(outfile)
    plt.xlabel("Time (s)")
    plt.ylabel("Current (nA)")
    plt.grid(True)
    figure_out = f'{outfile[:-4]}.png'
    plt.savefig(figure_out)
    plt.show()
    shutil.copy(figure_out, stamp)


def _shutdown():
    global ser_in, ser_out
    print("\nShutting down...")
    try:
        if ser_out and ser_out.is_open:
            ser_out.write(b'0')
        if ser_in and ser_in.is_open:
            ser_in.reset_input_buffer()
            ser_in.reset_output_buffer()
            ser_in.close()
        if ser_out and ser_out.is_open:
            ser_out.close()
    except Exception as e:
        print("Error closing serial ports:", e)

    _final_plot()

    if os.path.exists(outfile):
        try:
            shutil.move(outfile, stamp)
            print(f"Data file moved to {stamp}/")
        except Exception as e:
            print(f"Error moving file: {e}")
    else:
        print(f"No data file {outfile} found to move.")

    winsound.Beep(500, 2000)
    print("Experiment ended.")


# === COM Port Initialization ===
print("\nInitializing COM ports.......")

try:
    ser_out = serial.Serial('COM4', 230400, timeout=0.1)
    print(ser_out.readline().decode('ascii').strip())
    print("Arduino Connected Successfully :)")
except serial.SerialException as e:
    print("Serial error on COM4:", e)

try:
    ser_in = serial.Serial('COM5', 230400, timeout=1)
    print("Current Ranger Connected successfully :)")
except serial.SerialException as e:
    print("Serial error on COM5:", e)

if ser_out:
    ser_out.write(b'0')  # Close circuit initially

# === Input Section ===
print("\nCheck cables. Connect Arduino to PC. Relay is closed at startup.")
print("Acquisition rate of 200 Hz")
wafer = input('wafer name: ')
chip = int(input('chip n\u00b0: '))
tresh = float(input('Current threshold (A): '))

outfile = f'wafer_{wafer}_chip{chip}_{stamp}.dat'
print('File name: ', outfile)
input('Press ENTER key to begin in 5 sec. Relay will open the circuit.')

if ser_out:
    ser_out.write(b'1')  # Open circuit to start

# === Start ===
tCurrent = time.perf_counter()
threading.Thread(target=serial_read_thread, args=(tresh,), daemon=True).start()

ani = animation.FuncAnimation(fig, update, init_func=init_plot, interval=200)
plt.show()
