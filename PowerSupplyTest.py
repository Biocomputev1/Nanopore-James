import pyvisa
import time

def initialize_power_supply(resource_name):
    rm = pyvisa.ResourceManager()
    print("VISA Resources found:", rm.list_resources())

    ps = rm.open_resource(resource_name)
    ps.timeout = 1000
    ps.write_termination = '\n'
    ps.read_termination = '\n'

    # Clear previous errors
    ps.write("*CLS")
    print("Connected to:", ps.query("*IDN?").strip())
    print("Min Voltage:", ps.query("SOUR:VOLT? MIN").strip())
    print("Min Current:", ps.query("SOUR:CURR? MIN").strip())
    print("Initial error state:", ps.query("SYST:ERR?").strip())
    return ps

def configure_output(ps, current_limit=1.0, ovp=6.0, ocp=2.0):
    ps.write("*CLS")  # Clear any errors
    ps.write("OUTP OFF")  # Reset output state
    ps.write("SOUR:VOLT 0")  # Pull voltage to 0 to prevent command rejection
    ps.write(f"SOUR:CURR {current_limit}")
    ps.write(f"OVP {ovp}")
    ps.write(f"OCP {ocp}")
    ps.write("OUTP ON")
    print("✅ Output configured and enabled.")

def ramp_voltage(ps, start=0.0, end=5.0, step=1.0, delay=5):
    voltage = start
    print("\n🔁 Starting voltage ramp...")
    while voltage <= end:
        try:
            ps.write(f"SOUR:VOLT {voltage:.3f}")
            time.sleep(0.2)
            err = ps.query("SYST:ERR?").strip()
            if not err.startswith("0"):
                print(f"⚠️  Voltage {voltage:.3f} V set with warning: {err}")
            else:
                print(f"✅ Voltage set to {voltage:.3f} V")
        except Exception as e:
            print(f"❌ Error setting {voltage:.3f} V: {e}")
        time.sleep(delay)
        voltage += step
    print("✅ Voltage ramp complete.\n")

def shutdown(ps):
    print("🛑 Shutting down power supply...")
    ps.write("SOUR:VOLT 0")
    ps.write("OUTP OFF")
    ps.close()
    print("✅ Power supply output turned off and connection closed.")

def main():
    resource = 'USB0::0x2EC7::0x9200::800889011797710062::INSTR'
    ps = initialize_power_supply(resource)
    configure_output(ps)
    ramp_voltage(ps, start=0.0, end=5.0, step=1.0, delay=5)
    shutdown(ps)

if __name__ == "__main__":
    main()
