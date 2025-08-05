#!/usr/bin/env python3

import pyvisa

print("Creating ResourceManager...")
rm = pyvisa.ResourceManager( '@py' )

print("Listing resources...")
print(rm.list_resources())  # Check if your instrument shows up here

print("Opening connection...")
inst = rm.open_resource('USB0::2391::1031::MY44013842::0::INSTR')

print("Querying *IDN?...")
print(inst.query("*IDN?"))  # Should return instrument ID string


inst.write( "FREQ 1000000" )

inst.write( "" )