# -*- coding: utf-8 -*-
"""
Created on Tue Sep 29 2020

Note:

Last editing time: 
@author: Yi-Chun Chin    joe6302413@gmail.com
"""
#%% packages and libraries
import matplotlib.pyplot as plt, tkinter as tk, tkinter.filedialog
from os.path import normpath,split
from os import getenv
from JVmodule import dark_PVdevice, light_PVdevice
onedrive=getenv('OneDrive')
JVdir=normpath(onedrive+'\\Data\\JV')

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
# devices=dark_PVdevice.import_from_files(filenames,direction='reverse',header_length=1,trunc=-25)
# devices=light_PVdevice.import_from_files(filenames,direction='both',header_length=1,trunc=-25,power_in=100)
devices=light_PVdevice.import_from_files(filenames,direction='both',header_length=3,trunc=-4,p_area=0.045,power_in=100)

#%% calibrate current to current density
devices=light_PVdevice._calibrate_Gihan_devices(devices)

#%% Saving APS and APS fit and HOMO with error
location=split(filenames[0])[0]
for device in devices:
    device.save_all(location+'\\processed')