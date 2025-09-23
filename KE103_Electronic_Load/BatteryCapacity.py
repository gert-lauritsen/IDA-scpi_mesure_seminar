# -*- coding: utf-8 -*-
"""
Created on Mon Jan 27 21:17:52 2025

@author: gert
"""

import pyvisa
import time
import matplotlib.pyplot as plt

# Configuration
ELECTRONIC_LOAD_ADDRESS = "ASRL4::INSTR"  # Replace with your device's VISA address
LOAD_CURRENT = 2.0  # Constant current in Amperes (adjust as needed)
VOLTAGE_CUTOFF = 14  # Voltage cutoff in Volts
POLL_INTERVAL = 5  # Interval to check the battery voltage (in seconds)

def main():
    # Initialize VISA resource manager
    rm = pyvisa.ResourceManager()
    print("Connecting to electronic load...")
    load = rm.open_resource(ELECTRONIC_LOAD_ADDRESS)
    print(f"Connected to: {load.query('*IDN?').strip()}")
    
    # Configure the electronic load for constant current mode
    print("Configuring electronic load...")
    load.write("MODE:CURR")  # Set mode to constant current
    load.write(':CURR ' + str(LOAD_CURRENT) + 'A')  # Set the load current
    load.write(":INP 1")  # Enable the load input

    # Start the test
    print("Starting capacity test...")
    voltages = []  # List to store voltage readings
    timestamps = []  # List to store timestamps
    start_time = time.time()  # Record the start time

    try:
        while True:
            # Query the current battery voltage
            raw_voltage = load.query(":MEAS:VOLT?")  # e.g., '0.10000V\n'
            voltage = float(raw_voltage.strip().replace('V', ''))  # Clean and convert
            print(f"Battery Voltage: {voltage:.2f} V")
            elapsed_time = time.time() - start_time
            voltages.append(voltage)
            timestamps.append(elapsed_time)
            # Stop the test if the voltage drops below the cutoff
            if voltage <= VOLTAGE_CUTOFF:
                print("Voltage cutoff reached. Stopping test...")
                break

            # Wait before polling again
            time.sleep(POLL_INTERVAL)
    finally:
        # Turn off the load and disconnect
        load.write(":INP 0")
        elapsed_time = time.time() - start_time  # Calculate total elapsed time (in seconds)
        print("Test complete.")
        print(f"Elapsed Time: {elapsed_time / 3600:.2f} hours")

    # Calculate and display capacity
    capacity_mAh = (LOAD_CURRENT * (elapsed_time / 3600)) * 1000  # Convert to mAh
    print(f"Measured Battery Capacity: {capacity_mAh:.2f} mAh")

    # Close the connection
    load.close()
    plot_voltage_curve(timestamps, voltages)

def plot_voltage_curve(timestamps, voltages):
    """Plots the voltage curve over time."""
    plt.figure(figsize=(10, 6))
    plt.plot(timestamps, voltages, label="Battery Voltage", color="blue", linewidth=2)
    plt.axhline(y=VOLTAGE_CUTOFF, color="red", linestyle="--", label="Cutoff Voltage")

    # Add labels, title, and legend
    plt.xlabel("Time (s)")
    plt.ylabel("Voltage (V)")
    plt.title("Battery Voltage vs Time")
    plt.legend()
    plt.grid()
    plt.show()

if __name__ == "__main__":
    main()