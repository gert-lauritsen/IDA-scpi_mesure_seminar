# -*- coding: utf-8 -*-
"""
Created on Sat Sep 20 14:46:48 2025

@author: gert
"""

import pyvisa  

rm = pyvisa.ResourceManager()
for res in rm.list_resources():
    print(res)

print('----------------------')
addr = rm.list_resources()[0] 
inst = rm.open_resource(addr)
print(addr,'-', inst.query("*IDN?"))
inst.close()
addr = rm.list_resources()[2] 
inst = rm.open_resource(addr)
print(addr,'-',inst.query("*IDN?"))
inst.close() 

addr = rm.list_resources()[4] 
OWON=rm.open_resource(addr)
OWON.baud_rate=115200 # this is how to make it run with visa !!!!
print(addr,'-', OWON.query("*IDN?"))  
print(addr,'-', OWON.query("SYST:ERR?"))  

"""        
addr = rm.list_resources()[3] 
print(addr)

addr = rm.list_resources()[3] 
inst = rm.open_resource(addr)
print(inst.query("*IDN?"))
inst.close() 

#inst = rm.open_resource(addr)
#inst.baudrate=115200
#print(inst.query("*IDN?"))
#inst.close() 
"""