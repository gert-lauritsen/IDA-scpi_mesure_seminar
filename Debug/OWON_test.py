# -*- coding: utf-8 -*-
"""
Created on Sat Sep 20 15:40:42 2025

@author: gert
"""

import time
import pyvisa

rm = pyvisa.ResourceManager()
addr = rm.list_resources()[4] 
OWON=rm.open_resource(addr)
OWON.baud_rate=115200 # this is how to make it run with visa !!!!
print(addr,'-', OWON.query("*IDN?"))  
OWON.write ("CONF:VOLT:DC AUTO")
time.sleep(1)
for _ in range(10):
    print(OWON.query("MEAS:VOLT?").replace('V', ''))


OWON.close()