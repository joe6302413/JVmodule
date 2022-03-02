# -*- coding: utf-8 -*-
"""
Created on Tue Feb  8 11:02:17 2022

@author: yc6017
"""
import serial
import numpy as np
import JVmodule as jvm
import tkinter as tk, tkinter.filedialog
import switchbox as swb
import os.path
import matplotlib.pyplot as plt
import time
import threading

class keithley_lscan:
    def __init__(self,keith_com,baudrate=38400,):
        self._keith_com=keith_com
        self._baudrate=baudrate
    
    def scan(self,start_v,stop_v,v_step,nplc,hys=False):
        if (stop_v-start_v)*v_step<0:
            v_step=-v_step
            print('swap v_step sign.')
        trigger_count = int(1 + (stop_v-start_v)/v_step)
        num_of_read=28*trigger_count
        
        with serial.Serial(self._keith_com,self._baudrate) as ser_keithley:
            #Initialisation of Keithley
            ser_keithley.write(b'*RST\r')                    #Reset Keithley
            ser_keithley.write(b':SOUR:FUNC VOLT\r')         #Set Voltage as SOURCE
            ser_keithley.write(b':SENS:FUNC "CURRENT"\r')    #Set Current as SENSOR
            ser_keithley.write(b':FORM:ELEM VOLT, CURR\r')   #Retrieve Voltage and Current 
            ser_keithley.write(b':SENS:VOLT:PROT 5\r')       #Cmpl voltage in Volt
            ser_keithley.write(b':SENS:CURR:PROT 0.5\r')     #Cmpl current in Ampere
            ser_keithley.write(b':SENS:CURR:NPLC %f\r' %nplc)     #AC noise integration time. Longer time will suppress noise level
            ser_keithley.write(b':SOUR:VOLT:START %f\r' %start_v)
            ser_keithley.write(b':SOUR:VOLT:STOP %f\r' %stop_v)
            ser_keithley.write(b':SOUR:VOLT:STEP %f\r' %v_step)
            # ser_keithley.write(b':SOUR:DEL %f\r' %delay_time)
            ser_keithley.write(b':SOUR:VOLT:MODE SWE\r')
            ser_keithley.write(b':TRIG:COUN %f\r' %trigger_count)
            ser_keithley.write(b':OUTP ON\r')
            ser_keithley.write(b':READ?\r')
            raw_data=ser_keithley.read(num_of_read)
            #Convert read values to float number and separate to voltage and current
            value_lists = [[float(i) for i in 
                            raw_data.decode('ascii').strip().split(',')]]
            if hys:
                ser_keithley.write(b':SOUR:SWE:DIR DOWN\r')
                ser_keithley.write(b':READ?\r')
                raw_data=ser_keithley.read(num_of_read)
                value_lists+=[[float(i) for i in 
                               raw_data.decode('ascii').strip().split(',')]]
            ser_keithley.write(b':OUTP OFF\r')
            # ser_keithley.write(b'*RST\r')
        v_list,c_list=[],[]
        for value in value_lists:
            v_list.append(np.array(value[::2]))
            c_list.append(np.array(value[1::2])*1e3)
        return v_list,c_list

def multi_scan(keith,swbox,devices_n,tot_pixel_n,start_v,stop_v,v_step,nplc,p_area,
            light=True,power_in=100,hys=False,labels='',plot=True):       
    if labels==['']:
        labels=devices_n
    if hys:
        direction='both'
    elif start_v<stop_v:
        direction='forward'
    else:
        direction='reverse'
        
    devices=[]
    for device_n,label in zip(devices_n,labels):
        pixels=[]
        for pixel in range(1,1+tot_pixel_n):
            swbox.switch(device_n,pixel,on=1)
            # t=time.perf_counter()
            v_list,c_list=keith.scan(start_v,stop_v,v_step,nplc,hys)
            swbox.switch(device_n,pixel,on=0)
            j_list=[i/p_area for i in c_list]
            # t_soak=t-start_t
            for v,j in zip(v_list,j_list):
                p_dir='forward' if v[0]-v[1]<0 else 'reverse'
                if light:
                    pixels.append(jvm.light_PV(v,j,f'{label}_p{pixel}_{p_dir}'
                                               ,p_area,power_in))
                else:
                    pixels.append(jvm.dark_PV(v,j,f'{label}_p{pixel}_{p_dir}'
                                              ,p_area))
        if light:
            device=jvm.light_PVdevice(pixels,label,direction,p_area,power_in)
        else:
            device=jvm.dark_PVdevice(pixels,label,direction,p_area)
        devices.append(device)
        device.save_all(location)
    if plot:
        for i,device in enumerate(devices):
            plt.figure(i)
            device.plot()
    return devices

class soak_thread(threading.Thread):
    def __init__(self,stopEvent,keith,swbox,devices_n,tot_pixel_n,start_v,
                 stop_v,v_step,nplc,p_area,start_t,light=True,power_in=100,
                 hys=True,labels='',plot=True):
        super().__init__()
        self.func=multi_scan
        self.stopEvent=stopEvent
        self.kwargs={'keith':keith,'swbox':swbox,'devices_n':devices_n,
                   'tot_pixel_n':tot_pixel_n,'start_v':start_v,
                   'stop_v':stop_v,'v_step':v_step,'nplc':nplc,
                   'p_area':p_area,'start_t':start_t,'light':light,
                   'power_in':power_in,'hys':hys,'labels':labels,'plot':plot}
        self.labels=labels if labels!=[''] else devices_n
    def run(self):
        counter=0
        self.data=[]
        while not stopEvent.is_set():
            print(f'Number {counter} run.')
            self.data.append(self.func(**self.kwargs))
            counter+=1
            self.kwargs['labels']=[str(label)+f'_re{counter}'for label in self.labels]

#%%% run as main
if __name__=='__main__':
    start_t=time.perf_counter()
    light=True
    hys=False
    start_v = -2.0
    stop_v = 1.2
    v_step = 0.02
    nplc=0.1
    p_area=0.06
    power_in=100
    tot_pixel_n=6
    stopEvent=threading.Event()
    labels='' # define labels
    labels=[i.strip() for i in labels.split(",")]
    devices_n=[1,2]
    
    # swbox=swb.switchbox(swb.switchbox_map.sixXfour,
    #                      ['COM10','COM9','COM8','COM4'])
    swbox=swb.switchbox(swb.switchbox_map.twoXsix,
                          ['COM5','COM6'])
    swbox.reset()
    keith=keithley_lscan('COM7', baudrate=38400)
    
    assert len(devices_n)==len(labels) or labels==[''],\
        'Label doesn\'t match with number of devices or is not empty.'
    
    #%% choose save location and name
    root=tk.Tk()
    location=tkinter.filedialog.askdirectory()
    # dlg = tkinter.filedialog.asksaveasfilename(confirmoverwrite=False,filetypes=[('csv','.csv')])
    root.destroy()	#closing the UI interface
    
    #%% measure
    
    # soaking_thread=soak_thread(stopEvent,keith,swbox,devices_n,tot_pixel_n,start_v,stop_v,v_step,nplc,p_area,
    #         start_t,light,power_in,hys,labels,plot=False)
    # soaking_thread.start()
    devices=multi_scan(keith,swbox,devices_n,tot_pixel_n,start_v,stop_v,v_step,nplc,p_area,
            light=light,power_in=power_in,hys=hys,labels=labels,plot=True)
