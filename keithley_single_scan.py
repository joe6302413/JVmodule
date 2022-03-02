# -*- coding: utf-8 -*-
"""
Created on Mon Nov 15 16:31:55 2021

@author: solsimuser
"""


import serial
# import matplotlib.pyplot as plt
import numpy as np
import JVmodule as jvm
import tkinter as tk, tkinter.filedialog
import os.path
# import datetime

dark=False
start_voltage = -5
stop_voltage = 2
voltage_step = 0.02
nplc=1
p_area=0.04
power_in=100
# name='test'
direction='forward' if start_voltage<stop_voltage else 'reverse'

trigger_count = int(1 + (stop_voltage - start_voltage) / voltage_step)
num_of_read = 28 * trigger_count
delay_time = 0
#%% choose files
root=tk.Tk()
dlg = tkinter.filedialog.asksaveasfilename(confirmoverwrite=False,filetypes=[('csv','.csv')])
location=os.path.split(dlg)[0]
name=os.path.split(dlg)[1]
root.destroy()	#closing the UI interface 

# start = time.time()
with serial.Serial(port="COM7", baudrate=38400, parity=serial.PARITY_NONE, bytesize=8, stopbits=1) as ser_keithley:
    #Initialisation of Keithley
    ser_keithley.write(b'*RST\r')                    #Reset Keithley
    # ser_keithley.write(b'*CLS\r')                    #clear Keithley
    ser_keithley.write(b':SOUR:FUNC VOLT\r')         #Set Voltage as SOURCE
    ser_keithley.write(b':SENS:FUNC "CURRENT"\r')    #Set Current as SENSOR
    ser_keithley.write(b':FORM:ELEM VOLT, CURR\r')   #Retrieve Voltage and Current 
    ser_keithley.write(b':SENS:VOLT:PROT 5\r')       #Cmpl voltage in Volt
    ser_keithley.write(b':SENS:CURR:PROT 0.5\r')     #Cmpl current in Ampere
    ser_keithley.write(b':SENS:CURR:NPLC %d\r' %nplc)     #AC noise integration time. Longer time will suppress noise level
    
    ser_keithley.write(b':SOUR:VOLT:START %f\r' %start_voltage)
    ser_keithley.write(b':SOUR:VOLT:STOP %f\r' %stop_voltage)
    ser_keithley.write(b':SOUR:VOLT:STEP %f\r' %voltage_step)
    ser_keithley.write(b':SOUR:VOLT:MODE SWE\r')
    # ser_keithley.write(b':SOUR:DEL:AUTO ON\r')
    # ser_keithley.write(b':SOUR:SWE:RANG AUTO\r') #default is BEST
    # ser_keithley.write(b':SOUR:SWE:SPAC LIN\r') #default is LIN
    ser_keithley.write(b':TRIG:COUN %f\r' %trigger_count)
    # ser_keithley.write(b':SOUR:DEL %f\r' %delay_time)
    ser_keithley.write(b':SOUR:DEL MIN\r')
    # ser_keithley.write(b':SYST:AZER:STAT OFF\r')
    # ser_keithley.write(b':SYST:AZER:CACH:STAT OFF\r')
    ser_keithley.write(b':OUTP ON\r')
    ser_keithley.write(b':READ?\r')
    raw_data=ser_keithley.read(num_of_read)
    # ser_keithley.write(b':SOUR:SWE:DIR DOWN\r')
    # ser_keithley.write(b':READ?\r')
    # raw_data1=ser_keithley.read(num_of_read)
    
    ser_keithley.write(b':OUTP OFF\r')
    ser_keithley.write(b'*RST\r')
    
#Convert read values to float number and separate to voltage and current
value_list = [float(i) for i in raw_data.decode('ascii').strip().split(',')]
# value_list1 = [float(i) for i in raw_data1.decode('ascii').strip().split(',')]
    
j=np.array(value_list[1::2])*1e3/p_area
v=np.array(value_list[::2])

if not dark:
    pixel=[jvm.light_PV(v,j,name,p_area,power_in)]
    device=jvm.light_PVdevice(pixel,name,direction,p_area,power_in)
    device.save_all(location)
    device.plot()
else:
    pixel=[jvm.dark_PV(v,j,name,p_area,power_in)]
    device=jvm.dark_PVdevice(pixel,name,direction,p_area,power_in)
    device.save_all(location)
    device.plot()