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
import matplotlib.pyplot as plt
import time
import threading
import csv
from typing import List
from os.path import split,join,exists

class keithley_lscan:
    def __init__(self,keith_com,baudrate=38400,timeout=1e-1):
        self._keith_com=keith_com
        self._baudrate=baudrate
        self._timeout=timeout
        if not self._is_on:
            raise Exception('No respond from Keithley. Check if it is on '\
                            'or restart it.')
    
    @property
    def _is_on(self):
        with serial.Serial(self._keith_com, baudrate=38400, timeout=self._timeout
                           ) as ser_keithley:
            ser_keithley.write(b'*rst\r')
            ser_keithley.write(b':STAT:MEAS?\r')
            if not ser_keithley.readline():
                return False
            else:
                return True
    
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

def make_soak_summary_header(names,scan_n,hys=False):
    for name in names:
        if exists(name):
            path,filename=split(name)
            root=tk.Tk()
            filename=tk.filedialog.asksaveasfilename(title=f'rename save file name for {filename}',
                                       initialdir=path,filetypes=[('csv','.csv')],
                                       defaultextension='.csv',initialfile=filename)
            if filename=='':
                raise Exception('saving process cancelled due to overwriting.')
            name=join(path,str(filename))
            root.destroy()
        with open(name,mode='w',newline='') as f:
            writer=csv.writer(f)
            if hys:
                writer.writerows([['pixel','soak_time','V\\-(OC)','J\\-(SC)',
                                   'FF','PCE','hysteresis index']*scan_n,
                                  [None,'s','V','mA/cm\\+(2)','%','%','%']*scan_n,
                                  [None,'soak_time','V\\-(OC)','J\\-(SC)','FF',
                                   'PCE','hysteresis index']*scan_n])
            else:
                writer.writerows([['pixel','soak_time','V\\-(OC)','J\\-(SC)',
                                   'FF','PCE']*scan_n,
                                  [None,'s','V','mA/cm\\+(2)','%','%']*scan_n,
                                  [None,'soak_time','V\\-(OC)','J\\-(SC)','FF',
                                   'PCE']*scan_n])
                
def save_soak_summary(names:List[str],devices:List[jvm.light_PVdevice],hys:bool=False):
    chars=('name','time','Voc','Jsc','FF','PCE')
    for name,device in zip(names,devices):
        with open(name,mode='a',newline='') as f:
            writer=csv.writer(f)
            s_name,time,Voc,Jsc,FF,PCE=[device.character(char).flatten() 
                                        for char in chars]
            if not hys:
                row=[[j for i in zip(s_name,time,Voc,Jsc,FF,PCE) for j in i]]
            else:
                hys_ind=device.hys.repeat(2)
                row=[[j for i in zip(s_name,time,Voc,Jsc,FF,PCE,hys_ind) for j in i]]
            writer.writerows(row)

def soaking_plot(data:List[List[jvm.light_PVdevice]], dev_char:str='PCE', 
                 norm:bool=False)->None:
    '''
    '''
    names=list(map(lambda i: i.name,data[0]))
    t_scans=[[device.find_best_scan(dev_char) for device in devices] 
             for devices in data]
    t=np.array([[scan.time for scan in scans] 
                for scans in t_scans])/3600
    char=np.array([[scan.__dict__[dev_char] for scan in scans] 
                        for scans in t_scans])
    if not norm:
        plt.figure(f'soaking_{dev_char} vs. time')
        plt.ylabel(f'{dev_char}')
    else:
        char=char/char.max(0)
        plt.figure(f'normalized_soaking_{dev_char} vs. time')
        plt.ylabel(f'normalized {dev_char}')
    plt.plot(t,char)
    plt.legend(names)
    plt.xlabel('Time (hr)')
    

# class MDPVT:
#     def __init__(self,keith,swbox,labels=''):
#         swbox.reset()
#         self.keith=keith
#         self.swbox=swbox
#         self.labels=labels
    
#     def multi_scan(devices_n,tot_pixel_n,start_v,stop_v,v_step,nplc,p_area,
#                    light=True,power_in=100,hys=False,plot=True,**kwargs):
#         pass
    
def multi_scan(keith,swbox,devices_n,tot_pixel_n,start_v,stop_v,v_step,nplc,p_area,
            light=True,power_in=100,hys=False,labels='',plot=True,**kwargs):       
    swbox.reset()
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
        scans=[]
        for pixel in range(1,1+tot_pixel_n):
            swbox.switch(device_n,pixel,on=1)
            t=time.perf_counter()
            v_list,c_list=keith.scan(start_v,stop_v,v_step,nplc,hys)
            swbox.switch(device_n,pixel,on=0)
            j_list=[i/p_area for i in c_list]
            try:
                t_soak=t-kwargs['start_t']
            except:
                t_soak=None
            for v,j in zip(v_list,j_list):
                p_dir='forward' if v[0]-v[1]<0 else 'reverse'
                if light:
                    scans.append(jvm.light_PV(v,j,f'{label}_p{pixel}_{p_dir}'
                                               ,p_area,power_in,time=t_soak))
                else:
                    scans.append(jvm.dark_PV(v,j,f'{label}_p{pixel}_{p_dir}'
                                              ,p_area))
        if light:
            device=jvm.light_PVdevice(scans,label,direction,p_area,power_in)
        else:
            device=jvm.dark_PVdevice(scans,label,direction,p_area)
        devices.append(device)
        device.save_all(location)
    if plot:
        for i,device in enumerate(devices):
            plt.figure(i)
            device.plot()
    return devices

class soak_thread(threading.Thread):
    func=multi_scan
    def __init__(self,stopEvent,keith,swbox,devices_n,tot_pixel_n,start_v,
                 stop_v,v_step,nplc,p_area,start_t,light=True,power_in=100,
                 hys=True,labels='',soak_delay=0):
        super().__init__()
        self.stopEvent=stopEvent
        self.kwargs={'keith':keith,'swbox':swbox,'devices_n':devices_n,
                   'tot_pixel_n':tot_pixel_n,'start_v':start_v,
                   'stop_v':stop_v,'v_step':v_step,'nplc':nplc,
                   'p_area':p_area,'start_t':start_t,'light':light,
                   'power_in':power_in,'hys':hys,'labels':labels,'plot':False}
        self.labels=labels if labels!=[''] else devices_n
        self.soak_delay=soak_delay
        
    def run(self):
        counter=0
        names=[location+f'/{i}_soaking_summary.csv' for i in self.labels]
        scan_n=tot_pixel_n*2 if self.kwargs['hys'] else tot_pixel_n
        make_soak_summary_header(names, scan_n, self.kwargs['hys'])
        self.data=[]
        while not stopEvent.is_set():
            print(f'Number {counter} run.')
            self.data.append(soak_thread.func(**self.kwargs))
            save_soak_summary(names, self.data[-1], self.kwargs['hys'])
            for device,device_0 in zip(self.data[-1],self.data[0]):
                pix=device.find_best_scan()
                pix_0=device_0.find_best_scan()
                try:
                    d_PCE=(pix.PCE-pix_0.PCE)/pix_0.PCE*100
                except:
                    d_PCE=0
                print(f'{pix.name}\tPCE: {pix.PCE:.2f}\t\u0394PCE: {d_PCE:.2f}%')
            print('-------------------')
            counter+=1
            self.kwargs['labels']=[str(label)+f'_re{counter}'for label in self.labels]
            time.sleep(self.soak_delay)

#%%% run as main
if __name__=='__main__':
    
    light=True
    hys=False
    start_v = 0.5
    stop_v = -0.4
    v_step = -0.2
    nplc = 0.1
    p_area = 0.045
    tot_pixel_n=4
    power_in=100
    stopEvent=threading.Event()
    labels= '0,1'#',207,208,209,210' # define labels
    labels=[i.strip() for i in labels.split(",")]
    devices_n=[1,2]
    soak_delay=10 #delay time in second between each run of soaking measurements
    
    # swbox=swb.switchbox(swb.switchbox_map.sixXfour,
    #                       ['COM10','COM9','COM8','COM4'])
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
    start_t=time.perf_counter()
    # soaking_thread=soak_thread(stopEvent,keith,swbox,devices_n,tot_pixel_n,start_v,stop_v,v_step,nplc,p_area,
    #         start_t,light,power_in,hys,labels,soak_delay=soak_delay)
    # soaking_thread.start()
    devices=multi_scan(keith,swbox,devices_n,tot_pixel_n,start_v,stop_v,v_step,nplc,p_area,
            light=light,power_in=power_in,hys=hys,labels=labels,plot=True)
