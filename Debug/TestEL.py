# -*- coding: utf-8 -*-
"""
Created on Sun Sep 21 10:04:29 2025

@author: gert
"""

import pyvisa, time, csv

# load_addr = "<DIN_LOAD_VISA>"
rm = pyvisa.ResourceManager()
for res in rm.list_resources():
    print(res)
load_addr = rm.list_resources()[3]     
el = rm.open_resource(load_addr)


rows = []
for i_ma in range(50, 1050, 50):  # 50 mA → 1000 mA
    i = i_ma/1000.0
    el.write(':CURR ' + str(i) + 'A')
    time.sleep(0.15)
    el.write(":INP 1")  # Enable the load input
    time.sleep(0.15)
    v = el.query(":MEAS:VOLT?")  # e.g., '0.10000V\n'
    voltage = float(v.strip().replace('V', ''))  # Clean and convert
    ia = float(el.query("MEAS:CURR?").replace('A', ''))
    print("Voltage:",voltage,"V Current:",ia,"A")
    rows.append((i, voltage, ia))
el.write("INP OFF"); el.close()

with open("usb_current_profile.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["i_set_a","v_meas_v","i_meas_a"]); w.writerows(rows)
print("OK – gemt usb_current_profile.csv")