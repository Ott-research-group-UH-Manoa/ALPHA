import pyvisa
import os
import csv
import re
import subprocess


TIME_SCALE = 50e-6      # seconds per division
TIME_DELAY = 0e-6       # horizontal offset
# Number of points to acquire
# (I believe is the same as the length parameter on the scope)
RECORD_LEN = 50000      # number of points to capture

# Address of Agilent MSOX2024A 
VISA_ADDRESS = "USB0::0x0957::0x1796::MY53280216::INSTR"

# Make valid directory to store data
SAVE_PATH = "Three-Chip-Eval-Board/Data"
if not os.path.exists(SAVE_PATH):
    os.makedirs(SAVE_PATH)
    print(f"Created directory: {SAVE_PATH}")
else:
    print(f"Directory already exists: {SAVE_PATH}")

rm = pyvisa.ResourceManager()
rm.list_resources()
scope = rm.open_resource(VISA_ADDRESS)
scope.timeout = 5000  # in milliseconds

# Optional: identify instrument
print("Connected to:", scope.query("*IDN?"))

scope.write(":WAVeform:SOURCE POD1")
scope.write(":WAVeform:FORMat ASCii")

# Apply timebase and record length BEFORE triggering
scope.write(f":TIMebase:SCALe {TIME_SCALE}")
scope.write(f":TIMebase:POSition {TIME_DELAY}")
scope.write(f":WAVeform:POINts {RECORD_LEN}")

print(f"Time scale set to {TIME_SCALE}")
print(f"Time delay set to {TIME_DELAY}")
print(f"Record length set to {RECORD_LEN}")

print("Actual time scale:", scope.query(":TIMebase:SCALe?"))
print("Actual time delay:", scope.query(":TIMebase:POSition?"))
print("Actual record length:", scope.query(":WAVeform:POINts?"))

# 🚀 **ARM SINGLE TRIGGER NOW**
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
out_filename = f"{SAVE_PATH}/scope_D0-D7.csv"
with open(out_filename, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["x-axis", "D0-D7"])
    writer.writerow(["second", ""])  # same header style as your reference
    for t, val in zip(times, samples):
        writer.writerow([f"{t:.6e}", val])

print(f"✅ Saved {out_filename} with {len(samples)} samples.")

plot_script = "Three-Chip-Eval-Board/src/plot_alpha_data.py"

try:
    subprocess.run(["python3", plot_script, out_filename], check=True)
    print(f"✅ Successfully ran {plot_script} with {out_filename}")
except subprocess.CalledProcessError as e:
    print(f"❌ Failed to run {plot_script}: {e}")