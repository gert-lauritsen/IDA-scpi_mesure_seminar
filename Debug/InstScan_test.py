# -*- coding: utf-8 -*-
"""
Created on Sat Sep 20 14:46:48 2025

@author: gert
"""

import pyvisa  

TargetAddr = [0,3]

#rm = pyvisa.ResourceManager('@py')  # use the pure Python backend
#print(rm.list_resources())

rm = pyvisa.ResourceManager()
for res in rm.list_resources():
    print(res)

print('----------------------')
for inst in TargetAddr:
    print(inst)
    addr = rm.list_resources()[inst] 
    print(addr)
    inst = rm.open_resource(addr)
    if inst == 4:
        inst.baud_rate=115200
    print(addr,'-', inst.query("*IDN?"))
    inst.close()

inst = rm.open_resource("ASRL6::INSTR")
inst.baud_rate=115200
print("ASRL6::INSTR",'-', inst.query("*IDN?"))
inst.close()

#OWON.baud_rate=115200 # this is how to make it run with visa !!!!
