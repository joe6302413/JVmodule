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
from JVmodule import deviceJV
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
devices=deviceJV.import_from_files(filenames,direction='both',header_length=3,power=100,trunc=-4)

#%% Saving APS and APS fit and HOMO with error
location=split(filenames[0])[0]
for i in devices:
    # i.save_device_csv(location)
    i.save_device_summary_csv(location)