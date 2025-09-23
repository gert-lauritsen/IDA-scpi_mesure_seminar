# BatteryCapacity - Battery Capacity Measurement Tool

## Overview
`BatteryCapacity.py` is a Python script that measures the capacity of a battery using an **SCPI-compatible electronic load**. The script sets a constant discharge current, monitors battery voltage over time, and stops when the voltage reaches a defined cutoff. The total discharge time is used to calculate battery capacity in **mAh (milliamp-hours)**.

## Features
- **Connects to an electronic load** via SCPI commands (VISA protocol).
- **Configurable discharge current** and **voltage cutoff**.
- **Logs and plots** battery voltage over time.
- **Automatically stops** the test when the voltage drops below the threshold.
- **Calculates battery capacity** in mAh.

## Requirements
- Python 3.x
- Required Python libraries:
  - `pyvisa` (for SCPI communication)
  - `matplotlib` (for plotting)

### Install Dependencies
```bash
pip install pyvisa matplotlib
```

## Usage

### 1️⃣ Configure the Electronic Load Address
Edit the following line in `BatteryCapacity.py` to match your electronic load’s **VISA address**:
```python
ELECTRONIC_LOAD_ADDRESS = "ASRL16::INSTR"  # Replace with actual VISA address
```
To list available VISA addresses, use:
```python
import pyvisa
print(pyvisa.ResourceManager().list_resources())
```

### 2️⃣ Set Test Parameters
Modify these values before running the test:
```python
LOAD_CURRENT = 2.0   # Discharge current in Amperes
VOLTAGE_CUTOFF = 10.5  # Cutoff voltage in Volts
POLL_INTERVAL = 5  # Time interval (seconds) between voltage checks
```

### 3️⃣ Run the Script
Execute the script from the terminal:
```bash
python BatteryCapacity.py
```

### 4️⃣ Interpreting the Results
The script will:
- Display real-time battery voltage readings.
- Stop when voltage drops below `VOLTAGE_CUTOFF`.
- Calculate battery capacity in **mAh**.
- Generate a **voltage vs. time graph**.

Example Output:
```
Connecting to electronic load...
Connected to: KEYSIGHT ELOAD
Configuring electronic load...
Starting capacity test...
Battery Voltage: 12.45 V
Battery Voltage: 12.40 V
...
Voltage cutoff reached. Stopping test...
Elapsed Time: 1.25 hours
Measured Battery Capacity: 2500.00 mAh
```

## Function Breakdown
### `main()`
- Initializes communication with the electronic load.
- Sets constant current mode and starts the test.
- Monitors battery voltage in a loop.
- Stops the test when the voltage cutoff is reached.
- Calculates and displays battery capacity.
- Calls `plot_voltage_curve()` to generate a graph.

### `plot_voltage_curve(timestamps, voltages)`
- Plots **battery voltage vs. time**.
- Draws a **red line** for the cutoff voltage.

## License
This project is licensed under the **MIT License**.

## Author
Created by **Gert** on January 27, 2025.

---
For more details, refer to your **electronic load’s SCPI command manual**.

