# -*- coding: utf-8 -*-
"""
Created on Tue Mar 29 14:22:37 2022

@author: yc6017
"""
#%% packages and libraries
import matplotlib.pyplot as plt, tkinter as tk, tkinter.filedialog
from os.path import normpath,split
from os import getenv
import numpy as np
import JVmodule as jvm
from Keithley_lscan import soaking_plot, make_soak_summary_header, save_soak_summary
import pandas as pd
onedrive=getenv('OneDrive')
JVdir=normpath(onedrive+'\\Data\\PV stability')

#%% clean filenames
filenames=[]

#%% choose files
root=tk.Tk()
root.withdraw()
root.iconify()
filenames+=tkinter.filedialog.askopenfilenames(parent=root,initialdir=JVdir, title='Please select JV files',filetypes=[('csv','*.csv')])
root.destroy()

#%% load files into devices
plt.close('all')
device_n=6
# devices=jvm.dark_PVdevice.import_from_files(filenames,direction='reverse',header_length=1,trunc=-25)
# devices=jvm.light_PVdevice.import_from_files(filenames,direction='both',header_length=1,trunc=-25,power_in=100)
devices=jvm.light_PVdevice.import_from_files(filenames,direction='both',header_length=3,trunc=-4,p_area=0.045,power_in=100)
devices=np.array(devices)
devices_map=devices.reshape((len(devices)//6,6))

#%% rename the devices due to computer shutdown
previous_n=184
for i,devices in enumerate(devices_map):
    for device in devices:
        device.name=f'{device.name[:3]}_re{i+1+previous_n}'
    
#%% load time for each pixels
sum_files=[]
root=tk.Tk()
root.withdraw()
root.iconify()
sum_files+=tkinter.filedialog.askopenfilenames(parent=root,initialdir=JVdir, title='Please select summary files',filetypes=[('csv','*.csv')])
root.destroy()
pix_n=4
spp=2 #how many scans per pixel
soak_t_map=[pd.read_csv(file,skiprows=2,header=0).iloc[:,np.arange(1,pix_n*spp*6,6)]
                                                      for file in sum_files]
for device_over_t,device_times in zip(devices_map.T,soak_t_map):
    for i,device in enumerate(device_over_t):
        t=device_times.iloc[i,:]
        # print(device)
        for scan,time in zip(device.scans,t):
            scan.time=time+44463+119396.6389134
            # scan.time=time
            
#%% plot soaking graph
soaking_plot(devices_map,'PCE',norm=False)

#%% saving JV and device summary
location=split(filenames[0])[0]
location=location+'\\..\\batch 205-216'
for devices in devices_map:
    for device in devices:
        device.save_all(location)

#%% Save soaking summary
names=[f'{location}\\{device.name}_soaking_summary.csv' for device in devices_map[0]]
make_soak_summary_header(names, pix_n*spp,hys=True)
for devices in devices_map:
    save_soak_summary(names, devices,hys=True)
