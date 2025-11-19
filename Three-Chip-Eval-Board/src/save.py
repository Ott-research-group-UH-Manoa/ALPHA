import pyvisa
import os
import csv
import re
import subprocess
import datetime


######################## Adjustable Settings ###############################

########## Scope settings #########
TIME_SCALE = 50e-6      # seconds per division
TIME_DELAY = 0e-6       # horizontal offset
# Number of points to acquire
# (I believe is the same as the length parameter on the scope)
RECORD_LEN = 50000      # number of points to capture
###################################

### Function Generator settings ###
AMPLITUDE_V  = 0.25      # Amplitude of the function generator signal
FREQUENCY_HZ = 1e6  # Frequency of the function generator signal
###################################

# Add sub folder as nesscary 
SAVE_PATH = "Three-Chip-Eval-Board/Data"
#############################################################################

############################# Constants ####################################
# Ask Jenni about max voltage for the eval board
MAX_VOLTAGE_V = 0.5    # Maximum voltage expected from the scope input

####### Instrument Addresses #######
SCOPE_ADDRESS = "USB0::0x0957::0x1796::MY53280216::INSTR"
FUNCTION_GENERATOR_ADDRESS = "USB0::0x0957::0x0407::MY44013842::INSTR"
#############################################################################

# ---- Helper to format times ----
def format_time(value):
    if value >= 1:
        return f"{value:.0f}s"
    elif value >= 1e-3:
        return f"{value * 1e3:.0f}ms"
    elif value >= 1e-6:
        return f"{value * 1e6:.0f}us"
    else:
        return f"{value * 1e9:.0f}ns"
def generate_readable_filename(time_scale, time_delay, record_len, amplitude, frequency):
    # ---- Date Tag (YYYY-MM-DD) ----
    date_str = datetime.date.today().strftime("%Y-%m-%d")

    # Format time scale and delay
    time_scale_str = format_time(time_scale)
    time_delay_str = format_time(time_delay)

    # ---- Record Length ----
    if record_len >= 1e6:
        len_str = f"{record_len/1e6:.0f}Msa"
    elif record_len >= 1e3:
        len_str = f"{record_len/1e3:.0f}Ksa"
    else:
        len_str = f"{record_len}sa"

    # ---- Frequency ----
    if frequency >= 1e6:
        freq_str = f"{frequency/1e6:.0f}MHz"
    elif frequency >= 1e3:
        freq_str = f"{frequency/1e3:.0f}kHz"
    else:
        freq_str = f"{frequency:.0f}Hz"

    # ---- Amplitude ----
    amp_str = f"{amplitude}V"

    # ---- Build final filename ----
    filename = (
        f"{date_str}_"
        f"TS_{time_scale_str}_"
        f"TD_{time_delay_str}_"
        f"RL_{len_str}_"
        f"A_{amp_str}_"
        f"F_{freq_str}.csv"
    )

    return filename


def main():
    if not os.path.exists(SAVE_PATH):
        os.makedirs(SAVE_PATH)
        print(f"Created directory: {SAVE_PATH}")
    else:
        print(f"Directory already exists: {SAVE_PATH}")


    # Connect to instruments
    rm = pyvisa.ResourceManager()
    rm.list_resources()
    scope = rm.open_resource(SCOPE_ADDRESS)
    scope.timeout = 5000  # in milliseconds

    function_generator = rm.open_resource(FUNCTION_GENERATOR_ADDRESS)
    function_generator.timeout = 5000  # in milliseconds

    # Optional: identify instrument
    # print("Connected to scope:", scope.query("*IDN?"))
    # print("Connected to function generator:", function_generator.query("*IDN?"))

    ################################## Configure function generator ##########################################
    # Make sure output is off before configuring 
    function_generator.write(":OUTPut off")

    function_generator.write("FUNCtion SIN")
    function_generator.write(":VOLTage:UNIT VPP")
    function_generator.write(f"FREQuency {FREQUENCY_HZ}")

    if AMPLITUDE_V <= MAX_VOLTAGE_V:
        function_generator.write(f"VOLTage {AMPLITUDE_V}")
    else:
        print(f"Warning: Desired amplitude {AMPLITUDE_V} V exceeds max voltage {MAX_VOLTAGE_V} V. ")
        raise ValueError("Amplitude exceeds maximum voltage.")

    amplitude = float(function_generator.query("VOLTage?"))
    frequency = float(function_generator.query("FREQuency?"))

    if amplitude != AMPLITUDE_V:
        print(f"Warning: Function generator amplitude set to {amplitude} V, expected {AMPLITUDE_V} V.")
        raise ValueError("Function generator amplitude mismatch.")

    if amplitude <= MAX_VOLTAGE_V:
        function_generator.write(":OUTPut on")
        print(f"Function generator output turned ON with amplitude {amplitude} V.")

    print(f"Function generator configured: Amplitude = {amplitude} V, Frequency = {frequency:.3e} Hz")
    #####################################################################################################

    scope.write(":WAVeform:SOURCE POD1")
    scope.write(":WAVeform:FORMat ASCii")

    # Apply timebase and record length BEFORE triggering
    scope.write(f":TIMebase:SCALe {TIME_SCALE}")
    scope.write(f":TIMebase:POSition {TIME_DELAY}")
    scope.write(f":WAVeform:POINts {RECORD_LEN}")

    print(f"Time scale set to {format_time(TIME_SCALE)}")
    print(f"Time delay set to {format_time(TIME_DELAY)}")
    print(f"Record length set to {RECORD_LEN}")

    print("Actual time scale:", scope.query(":TIMebase:SCALe?"))
    print("Actual time delay:", scope.query(":TIMebase:POSition?"))
    print("Actual record length:", scope.query(":WAVeform:POINts?"))

    # Trigger 
    print("Arming single trigger — waiting for event...")
    scope.write(":SINGle")

    # Wait for acquisition to complete
    while True:
        if int(scope.query(":OPERegister?")) & 8:
            break

    print("✅ Trigger captured!")

    '''Everything Below Here'''
    # Get preamble for timing
    preamble = scope.query(":WAVeform:PREamble?").split(',')
    xinc = float(preamble[4])
    xorig = float(preamble[5])
    print("Time increment:", xinc, "Start:", xorig)

    # Query waveform data
    raw = scope.query(":WAVeform:DATA?")
    # print(raw)
    # --- Clean block header ---
    # Remove header like "#800003999"
    data_str = re.sub(r"^#\d+\d+", "", raw).strip()

    # Split into individual samples (remove any stray spaces)
    samples = [int(s) for s in re.split(r"[, ]+", data_str) if s.strip().isdigit()]

    # Compute time array
    times = [xorig + i * xinc for i in range(len(samples))]

    # --- Write to CSV ---
    filename = generate_readable_filename(TIME_SCALE, TIME_DELAY, RECORD_LEN, AMPLITUDE_V, FREQUENCY_HZ)
    out_filename = f"{SAVE_PATH}/{filename}"
    with open(out_filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["x-axis", "D0-D7"])
        writer.writerow(["second", ""])  # same header style as your reference
        for t, val in zip(times, samples):
            writer.writerow([f"{t:.6e}", val])

    print(f"✅ Saved {out_filename} with {len(samples)} samples.")

    function_generator.write(":OUTPut off")
    print("Function Generator Output off")


    # --- Call plotting script ---
    plot_script = "Three-Chip-Eval-Board/src/plot_alpha_data.py"

    try:
        subprocess.run(["python3", plot_script, out_filename], check=True)
        print(f"✅ Successfully ran {plot_script} with {out_filename}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to run {plot_script}: {e}")

if __name__ == "__main__":
    main()