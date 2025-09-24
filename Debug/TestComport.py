# -*- coding: utf-8 -*-
"""
Created on Sat Sep 20 16:32:35 2025

@author: gert
"""

import serial
import time

# Common baud rates to try
baudrates = [9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]

port = "COM6"

for baud in baudrates:
    try:
        print(f"\nTrying {baud} baud...")
        with serial.Serial(port, baudrate=baud, timeout=1) as ser:
            # Clear input buffer
            ser.reset_input_buffer()
            
            # Send SCPI query
            ser.write(b"*IDN?\n")
            
            # Small wait for response
            time.sleep(0.2)
            
            # Read any available response
            response = ser.read(ser.in_waiting or 64)
            
            if response:
                print(f"Response at {baud} baud: {response.decode(errors='replace').strip()}")
            else:
                print("No response.")
                
    except Exception as e:
        print(f"Error at {baud} baud: {e}")
