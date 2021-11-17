#--------------------------------------------------------------------------------
# This code is based on the previously developed one, stability_v2_1.
# Main improvement is the GUI part which used wxPython.
# Other improvement is the integration of multiple functions in a screen.
# Integrated functions are quick checking of Jsc of a device, J-V measurement for
# multiple devices and stability test. This code supports both 4-device chamber
# and 9-device chamber by selecting the check box.
# Due to the limitation of switch box 9-device chamber only can measure 2 pixels
# for each device but 2-device chamber can do 6 pixels for each.
# User can place devices any position in the chamber and type in the position in
# the 'Devices' section.
# 
# date: 16th October 2019
# update: 1st November 2019  (add saveas mode - possible to type in new filename)
# update: 7th July 2020 (replace pixel 5 to pixel 3)
# update: 4th February 2021 (replace the 4-device chamber to 2-device chamber)
# version: v1.3
#----------------------------------------------------------------------------------
__author__ = 'Gihan Ryu'


import wx
import matplotlib
matplotlib.use('Agg')             #Some computer use 'Agg' rather than 'WXAgg'
matplotlib.interactive(False)
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.figure import Figure
import serial
import time
import matplotlib.pyplot as plt
import datetime
import tkinter as tk , tkinter.filedialog
import csv
import os, sys
from itertools import zip_longest


#start_time = time.time()        #Reference time stamp

class MyFrame(wx.Frame):

    def __init__(self, *args, **kw):
        super(MyFrame, self).__init__(*args, **kw)

        self.SetTitle('Integrated Multiple Device Characterisation Tool')
        self.InitUI()
        
    def InitUI(self):
        self.start_time = time.time()
        #Define the main panel as pnl
        pnl = wx.Panel(self)
        #Devide the main panel horizontally to leftPanel and rightPanel
        leftPanel = wx.Panel(pnl)
        rightPanel = wx.Panel(pnl)
        
        font = wx.SystemSettings.GetFont(wx.SYS_SYSTEM_FONT)
#        font = wx.Font(12, wx.DECORATIVE, wx.ITALIC, wx.NORMAL)
#        font.SetPointSize(12)
#        font.SetUnderlined(True)
        
#----------------------------------------------------------------------------------
        parameter = wx.StaticText(rightPanel, label='Sweep Parameters')
        parameter.SetFont(font)
        parameter.SetForegroundColour((255, 255, 0))
        parameter.SetBackgroundColour((100, 100, 100))
        
        ParamBox = wx.GridBagSizer(8, 3)
        #Design two check boxes for Dark and Light conditioned J-V measurement
        self.check_Dark = wx.CheckBox(rightPanel, label='Dark')
        self.check_Light = wx.CheckBox(rightPanel, label='Light')
        self.check_Light.SetValue(True)
        ParamBox.Add(self.check_Dark, pos=(0,1), flag=wx.TOP, border=10)
        ParamBox.Add(self.check_Light, pos=(0,2), flag=wx.TOP, border=10)
        self.check_Dark.SetFont(font)
        self.check_Dark.SetForegroundColour(wx.RED)
        self.check_Light.SetFont(font)
        self.check_Light.SetForegroundColour(wx.RED)
        
#------------------------------------------------------------------------------------  
        #Define J-V measurement parameters
        st1 = wx.StaticText(rightPanel, label='Devices')
        self.tc1 = wx.TextCtrl(rightPanel, 1,value="1, 2", size=(120,20))
        ParamBox.Add(st1, pos=(1,0), flag=wx.LEFT, border=15)
        ParamBox.Add(self.tc1, pos=(1,1), span=(1,2), flag=wx.LEFT, border=2)
        
        st2 = wx.StaticText(rightPanel, label='Start')
        self.tc2 = wx.TextCtrl(rightPanel, -1, value='-1.2', size=(55,20))
        ParamBox.Add(st2, pos=(2,0), flag=wx.LEFT, border=15)
        ParamBox.Add(self.tc2, pos=(2,1), flag=wx.LEFT, border=2)
        ParamBox.Add(wx.StaticText(rightPanel, label='V'), pos=(2,2), flag=wx.LEFT, border=1)
        
        st3 = wx.StaticText(rightPanel, label='End')
        self.tc3 = wx.TextCtrl(rightPanel, -1, value='1.2', size=(55,20))      
        ParamBox.Add(st3, pos=(3,0), flag=wx.LEFT, border=15)
        ParamBox.Add(self.tc3, pos=(3,1), flag=wx.LEFT, border=2)
        ParamBox.Add(wx.StaticText(rightPanel, label='V'), pos=(3,2), flag=wx.LEFT, border=1)
        
        st4 = wx.StaticText(rightPanel, label='Step')
        self.tc4 = wx.TextCtrl(rightPanel, -1, value='0.01', size=(55,20))      
        ParamBox.Add(st4, pos=(4,0), flag=wx.LEFT, border=15)
        ParamBox.Add(self.tc4, pos=(4,1), flag=wx.LEFT, border=2)
        ParamBox.Add(wx.StaticText(rightPanel, label='V'), pos=(4,2), flag=wx.LEFT, border=1)
        
        st5 = wx.StaticText(rightPanel, label='Delay')
        self.tc5 = wx.TextCtrl(rightPanel, -1, value='5', size=(55,20))      
        ParamBox.Add(st5, pos=(5,0), flag=wx.LEFT, border=15)
        ParamBox.Add(self.tc5, pos=(5,1), flag=wx.LEFT, border=2)
        ParamBox.Add(wx.StaticText(rightPanel, label='ms'), pos=(5,2), flag=wx.LEFT, border=1)
        
        st6 = wx.StaticText(rightPanel, label='Area')
        self.tc6 = wx.TextCtrl(rightPanel, -1, value='0.045', size=(55,20))      
        ParamBox.Add(st6, pos=(6,0), flag=wx.LEFT, border=15)
        ParamBox.Add(self.tc6, pos=(6,1), flag=wx.LEFT, border=2)
        ParamBox.Add(wx.StaticText(rightPanel, label='cm2'), pos=(6,2), flag=wx.LEFT, border=1)
        
        st7 = wx.StaticText(rightPanel, label='Power')
        self.tc7 = wx.TextCtrl(rightPanel, -1, value='100', size=(55,20))
        ParamBox.Add(st7, pos=(7,0), flag=wx.LEFT, border=15)
        ParamBox.Add(self.tc7, pos=(7,1), flag=wx.LEFT, border=2)
        ParamBox.Add(wx.StaticText(rightPanel, label='mW/cm2'), pos=(7,2), flag=wx.LEFT, border=1)

#----------------------------------------------------------------------------------------------------
        #Define function binded Buttons 
        button_font = wx.Font(11, wx.ROMAN, wx.NORMAL, wx.BOLD)               
        single_measure_Btn = wx.Button(rightPanel, label='Jsc CHECK', size=(120, 70))
        single_measure_Btn.SetFont(button_font)
        single_measure_Btn.SetBackgroundColour(wx.YELLOW)  # set background color
        # single_measure_Btn.SetForegroundColour((176, 0, 255)) # set text color
        multi_measure_Btn = wx.Button(rightPanel, label='J-V MEASURE', size=(120, 70))
        multi_measure_Btn.SetFont(button_font)
        multi_measure_Btn.SetBackgroundColour((0, 100, 200))  # set background color
        stability_Btn = wx.Button(rightPanel, label='STABILITY', size=(120, 70))
        stability_Btn.SetFont(button_font)
        stability_Btn.SetBackgroundColour((176, 0, 200))  # set background color
        stop_Btn = wx.Button(rightPanel, label='FINISH', size=(80, 70))
        stop_Btn.SetFont(button_font)
        stop_Btn.SetBackgroundColour(wx.RED)  # set background color
        restart_Btn = wx.Button(rightPanel, label='RESTART', size=(80, 70))
        restart_Btn.SetFont(button_font)
        restart_Btn.SetBackgroundColour(wx.GREEN)  # set background color
        
        self.Bind(wx.EVT_BUTTON, self.OnSingleMeasurement, single_measure_Btn)
        self.Bind(wx.EVT_BUTTON, self.OnMultiMeasurement, multi_measure_Btn)
        self.Bind(wx.EVT_BUTTON, self.OnRestart, restart_Btn)
        self.Bind(wx.EVT_BUTTON, self.OnClose, stop_Btn)
        self.Bind(wx.EVT_BUTTON, self.OnStability, stability_Btn)          

#        stability_Btn.Disable()

#-------------------------------------------------------------------------------------------        
        #Define Stability test parameters
        stability_para = wx.StaticText(rightPanel, label='Stability Parameters')
        stability_para.SetFont(font)
        stability_para.SetForegroundColour((255, 255, 0))
        stability_para.SetBackgroundColour((100, 100, 100))
        
        StabilityParamBox = wx.GridBagSizer(2, 3)
                
        st11 = wx.StaticText(rightPanel, label='Period')
        self.tc11 = wx.TextCtrl(rightPanel, 1, value="200", size=(55,20))
        StabilityParamBox.Add(st11, pos=(0,0), flag=wx.LEFT|wx.BOTTOM, border=15)
        StabilityParamBox.Add(self.tc11, pos=(0,1), flag=wx.LEFT, border=2)
        StabilityParamBox.Add(wx.StaticText(rightPanel, label='hr'), pos=(0,2), flag=wx.LEFT, border=1)
        
        st12 = wx.StaticText(rightPanel, label='Interval')
        self.tc12 = wx.TextCtrl(rightPanel, 1, value="10", size=(55,20))
        StabilityParamBox.Add(st12, pos=(1,0), flag=wx.LEFT, border=15)
        StabilityParamBox.Add(self.tc12, pos=(1,1), flag=wx.LEFT, border=2)
        StabilityParamBox.Add(wx.StaticText(rightPanel, label='min'), pos=(1,2), flag=wx.LEFT, border=1)

#--------------------------------------------------------------------------------------
        #Checking current density of device1-pixel2
        hbox = wx.BoxSizer(wx.HORIZONTAL)        
        st8 = wx.StaticText(rightPanel, label='Jsc of Device 1 :')
        hbox.Add(st8, flag=wx.LEFT|wx.ALIGN_CENTER, border=5)
        self.c_density = wx.StaticText(rightPanel, label='')
        hbox.Add(self.c_density, flag=wx.LEFT|wx.ALIGN_LEFT, border=5)

#------------------------------------------------------------------------------------
        #Construct all components in the rightPanel screen        
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)        
        hbox1.Add(restart_Btn, flag=wx.LEFT, border=10)
        hbox1.Add(stop_Btn, flag=wx.LEFT, border=10)
        
        vbox1 = wx.BoxSizer(wx.VERTICAL)        
        vbox1.Add(parameter, 0, wx.LEFT|wx.TOP, border=10)
        vbox1.Add(ParamBox)
        vbox1.Add(wx.StaticLine(rightPanel), 0, wx.ALL|wx.EXPAND, 10)
        vbox1.Add(stability_para, 0, wx.LEFT|wx.BOTTOM, border=10)
        vbox1.Add(StabilityParamBox)
        vbox1.Add(wx.StaticLine(rightPanel), 0, wx.ALL|wx.EXPAND, 10)
        vbox1.Add(hbox, flag=wx.TOP|wx.LEFT, border=10)
        vbox1.Add(single_measure_Btn, flag=wx.LEFT|wx.BOTTOM, border=10)
        vbox1.Add(multi_measure_Btn, flag=wx.LEFT|wx.BOTTOM, border=10)
        vbox1.Add(stability_Btn, flag=wx.LEFT|wx.BOTTOM, border=10)
        vbox1.Add(hbox1, flag=wx.RIGHT, border=15)
        
        rightPanel.SetSizer(vbox1)
        
#---------------------------------------------------------------------------------
        #Define graph region
        vbox2 = wx.BoxSizer(wx.VERTICAL)
        graph = wx.StaticText(leftPanel, label='Graphs')
        graph.SetFont(wx.Font(16, wx.ROMAN, wx.NORMAL, wx.BOLD))
        #Define check boxes for chamber selection
        self.cb_4d = wx.CheckBox(leftPanel, label='2-Dev Chamber')
        self.cb_4d.SetValue(True)
        self.cb_9d = wx.CheckBox(leftPanel, label='9-Dev Chamber')
        # self.cb_9d.SetValue(True)
        #Define a Logbox for information display
        self.Logbox = wx.TextCtrl(leftPanel, size=(400, 60), style=wx.TE_BESTWRAP|wx.TE_MULTILINE)
        self.Logbox.SetFont(wx.Font(11, wx.SWISS, wx.NORMAL, wx.NORMAL))
        self.Logbox.SetForegroundColour(wx.BLUE)
        #Define time display box
        self.timebox = wx.TextCtrl(leftPanel)
        self.timebox.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL))
        self.timebox.SetForegroundColour(wx.BLUE)
        self.timebox.SetBackgroundColour((150, 150, 150))
        #Define Remaining time display box
        self.justbox = wx.TextCtrl(leftPanel)
        self.justbox.SetFont(wx.Font(10, wx.SWISS, wx.NORMAL, wx.NORMAL))
        self.justbox.SetForegroundColour(wx.RED)
        self.justbox.SetBackgroundColour((150, 255, 150))
        
        vbox3 = wx.BoxSizer(wx.VERTICAL)
        vbox3.Add(self.timebox)
        vbox3.Add(self.justbox)
        
        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox2.Add(self.cb_4d, flag=wx.LEFT, border=250)
        hbox2.Add(self.cb_9d, flag=wx.LEFT, border=20)
        hbox2.Add(self.Logbox, 0, flag=wx.LEFT, border=100)
        self.cb_4d.SetFont(font)
        self.cb_4d.SetForegroundColour(wx.RED)
        self.cb_9d.SetFont(font)
        self.cb_9d.SetForegroundColour(wx.RED)
        hbox2.Add(vbox3, 0, flag=wx.LEFT, border=20)
#        self.cb_9d.Disable()
        
        #Define Graph Plotting
        self.matplotlibhrapg = MatplotPanel(leftPanel)

        vbox2.Add(graph, 0, wx.LEFT|wx.TOP, border=10)
        vbox2.Add(hbox2)
        vbox2.Add(self.matplotlibhrapg, flag=wx.EXPAND, proportion=1)
        
        leftPanel.SetSizer(vbox2)
#---------------------------------------------------------------------------------
        #Construct all components in the leftPanel screen        
        hBox = wx.BoxSizer(wx.HORIZONTAL)
        hBox.Add(leftPanel, 1, wx.ALL|wx.EXPAND)
        hBox.Add(rightPanel, 0, wx.EXPAND)
                
        pnl.SetSizer(hBox)

        self.Centre()
        self.Maximize()
        
        #Timer setting for elapsed time display
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)

        self.timer.Start(1000)    # 1 second interval

#---------------------------------------------------------------------------------------        
    def OnRestart(self, event):
        
        self.timer.Stop()
        ex = MyFrame(None)
        ex.Show()
        self.Destroy()
        
#--------------------------------------------------------------------------------------       
    def OnClose(self, event):

        self.Destroy()

#--------------------------------------------------------------------------------------        
    def OnSingleMeasurement(self, event):   #Current measurement function for Jsc display
        
        area = float(self.tc6.GetValue())   #get area value from the area text control box
        
        if not self.cb_9d.IsChecked():
            self.pixel_on(1, 2)  #Switch on for Device1_Pixel2
        else:
            self.pixel_on_stability(1, 2)
        
        ser_keithley = serial.Serial(port="COM7", baudrate=19200, parity=serial.PARITY_NONE, bytesize=8, stopbits=1)

        #Initialisation of Keithley
        ser_keithley.write(b'*RST\r')                    #Reset Keithley
        ser_keithley.write(b':SOUR:FUNC VOLT\r')         #Set Voltage as SOURCE
        ser_keithley.write(b':SOUR:VOLT:MODE FIXED\r')   #Fixed Voltage
        ser_keithley.write(b':SOUR:VOLT:LEV 0.0\r')       #Set Voltage to 0V
        ser_keithley.write(b':SENS:FUNC "CURRENT"\r')    #Set Current as SENSOR
        ser_keithley.write(b':FORM:ELEM CURR\r')         #Retrieve Current only 
        ser_keithley.write(b':SENS:VOLT:PROT 5\r')       #Cmpl voltage in Volt
        ser_keithley.write(b':SENS:CURR:PROT 0.5\r')     #Cmpl current in Ampere
        ser_keithley.write(b':OUTP ON\r')
        ser_keithley.write(b':READ?\r')
        
        raw_data = ser_keithley.read(14)

        ser_keithley.write(b':OUTP OFF\r')
        
        current_density = float(raw_data.decode('ascii'))/area
        
        if not self.cb_9d.IsChecked():
            self.pixel_off(1, 2)  #Switch off for Device1_Pixel2
        else:
            self.pixel_off_stability(1, 2)
        
        self.c_density.SetLabel(str(round(current_density,10)))
        
        time_message = time.strftime("%H:%M:%S", time.gmtime(time.time() - self.start_time))
        self.Logbox.AppendText(time_message + '  Check Jsc of Device1-Pixel2\r' + str(current_density) + '    ')
        
        ser_keithley.close()

#-------------------------------------------------------------------------------------
    def OnTimer(self, event):
        now=time.time()
        etime = now - self.start_time

        m,s = divmod(etime,60)
        h,m = divmod(m,60)
        d,h = divmod(h,24)
        
        if d < 1:
            self.timebox.SetValue("%02d:%02d:%02d" % (h,m,s))
        elif d == 1:
            self.timebox.SetValue("%d Day  %02d:%02d:%02d" % (d,h,m,s))
        else:
            self.timebox.SetValue("%d Days  %02d:%02d:%02d" % (d,h,m,s))

#----------------------------------------------------------------------------------
    def OnMeasurement(self, event):             #Main I-V measurement function
        
        start_voltage = float(self.tc2.GetValue())
        stop_voltage = float(self.tc3.GetValue())
        voltage_step = float(self.tc4.GetValue())
        delay_time = float(self.tc5.GetValue())/1000
                
        trigger_count = int(1 + (stop_voltage - start_voltage) / voltage_step)
        num_of_read = 28 * trigger_count

        ser_keithley = serial.Serial(port="COM7", baudrate=57600, parity=serial.PARITY_NONE, bytesize=8, stopbits=1)

        #Initialisation of Keithley
        ser_keithley.write(b'*RST\r')                    #Reset Keithley
        ser_keithley.write(b':SOUR:FUNC VOLT\r')         #Set Voltage as SOURCE
        ser_keithley.write(b':SENS:FUNC "CURRENT"\r')    #Set Current as SENSOR
        ser_keithley.write(b':FORM:ELEM VOLT, CURR\r')   #Retrieve Voltage and Current 
        ser_keithley.write(b':SENS:VOLT:PROT 5\r')       #Cmpl voltage in Volt
        ser_keithley.write(b':SENS:CURR:PROT 0.5\r')     #Cmpl current in Ampere

        ser_keithley.write(b':SOUR:VOLT:START %f\r' %start_voltage)
        ser_keithley.write(b':SOUR:VOLT:STOP %f\r' %stop_voltage)
        ser_keithley.write(b':SOUR:VOLT:STEP %f\r' %voltage_step)
        ser_keithley.write(b':SOUR:VOLT:MODE SWE\r')
        ser_keithley.write(b':SOUR:SWE:RANG AUTO\r')
        ser_keithley.write(b':SOUR:SWE:SPAC LIN\r')
        ser_keithley.write(b':TRIG:COUN %f\r' %trigger_count)
        ser_keithley.write(b':SOUR:DEL %f\r' %delay_time)
        ser_keithley.write(b':OUTP ON\r')
        ser_keithley.write(b':READ?\r')
        
        raw_data = ser_keithley.read(num_of_read)
        
        ser_keithley.write(b':OUTP OFF\r')

        #Convert read values to float number and separate to voltage and current
        value_list = [float(i) for i in raw_data.decode('ascii').strip().split(',')]
        ser_keithley.close()

        return value_list

#-----------------------------------------------------------------------------------------
    def chamber_select(self, event):        #4- or 9-Device chamber selection function
        if not self.cb_4d.IsChecked() and not self.cb_9d.IsChecked():
            self.cb_4d.SetValue(True)
            self.cb_9d.SetValue(False)       #9-Device chamber is a default one
            pixel = [2,3]
            return pixel
        elif self.cb_4d.IsChecked() and self.cb_9d.IsChecked():
            self.cb_4d.SetValue(True)
            self.cb_9d.SetValue(False)
            pixel = [2,3]
            return pixel
        elif self.cb_4d.IsChecked():
            pixel = [1,2,3,4,5,6]
            return pixel
        else:
            pixel = [2,3]
            return pixel

#-----------------------------------------------------------------------------------------
    def mode_select(self, event):           #Dark or Light condition selection function
        if not self.check_Dark.IsChecked() and not self.check_Light.IsChecked():
            self.check_Dark.SetValue(False)
            self.check_Light.SetValue(True) #Light condition is a default setting
            suffix = "_Light"
            return suffix
        elif self.check_Dark.IsChecked() and self.check_Light.IsChecked():
            self.check_Dark.SetValue(False)
            self.check_Light.SetValue(True)
            suffix = "_Light"
            return suffix
        elif self.check_Light.IsChecked():
            suffix = "_Light"
            return suffix
        else:
            suffix = "_Dark"
            return suffix

#-----------------------------------------------------------------------------------------
    def OnMultiMeasurement(self, event):        #Activated by 'J-V Measure' Button
        
        self.Logbox.AppendText('Start to read Jsc of multiple devices')
        #select save directory
        self.saveData()
        
        devices = self.tc1.GetValue()       #get device numbers from the text control box as a text
        device_list = devices.split(",")    #convert the text format to list form
        area = float(self.tc6.GetValue())   #get area value from the area text control box
        P_in = float(self.tc7.GetValue())   #get light input power from the text control box

        pixel = self.chamber_select(event)  #number of pixel depends on device chamber
        suffix = self.mode_select(event)    #suffix for saved file name 
            
        for i in device_list:               #only measure the listed devices
            
            device_num = int(i)
            voltage_by_pixel = []
            current_by_pixel = []
            
            device_summary = self.fname + "_D" + str(device_num) + suffix + ".csv"   #Define file name for device's summary data
            
            with open(device_summary, 'a', newline='') as ff:
                wr = csv.writer(ff)
                wr.writerow(["Pixel Number", "Voc(V)", "Jsc(A/cm2)","Peak Power(W/cm2)", "FF", "PCE(%)"])
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M")
        
            for j in pixel:
                pixel_num = j
                # time.sleep(0.1)
                
                if not self.cb_9d.IsChecked():
                    self.pixel_on(device_num, pixel_num)  #switch on a pixel which is to be measured
                    flag = 4
                else:
                    self.pixel_on_stability(device_num, pixel_num)
                    flag = 9
                
                print('reading device #', str(device_num), '-pixel #', str(pixel_num))
                message = 'reading device'+ str(device_num) + '-pixel' + str(pixel_num)
                time_message = time.strftime("%H:%M:%S", time.gmtime(time.time() - self.start_time))
                self.Logbox.AppendText('\r' + time_message + '  ' + message)
                time.sleep(0.1)
                value_list = self.OnMeasurement(event)      #measure I-V data and get the data list
                wx.Yield()                                  #make the GUI keep refresh????
                                
                voltage = value_list[::2]                   #separate voltage data from the list
                current = value_list[1::2]                  #separate current data from the list
                
                #switch off of specific device-pixel
                if not self.cb_9d.IsChecked():
                    self.pixel_off(device_num, pixel_num)
                else:
                    self.pixel_off_stability(device_num, pixel_num)
                
                #Calculation of Jsc, Voc, Peak power, Fill factor
                curr_density = list(map(lambda x: x/area, current))
                power = list(map(lambda x, y: x*y, voltage, curr_density))

                for k in range(len(voltage) - 1):       #Find Jsc
                    if voltage[k] == 0:
                        Jsc = current[k]/area
                    elif voltage[k]*voltage[k+1] < 0:
                        ratio = (0 - voltage[k])/(voltage[k+1] - voltage[k])
                        Jsc = current[k] + ratio * (current[k+1] - current[k])
               
                # Default parameter setting as 'NA'
                Voc = 'NA'
                peak_power = 'NA'
                fill_factor = 'NA'
                pce = 'NA'

                for l in range(len(current) - 1):   #Find Voc
                    if current[l]*current[l+1] < 0:
                        ratio = (0 - current[l])/(current[l+1] - current[l])
                        Voc = voltage[l] + ratio * (voltage[l+1] - voltage[l])
           
                if Voc != 'NA':
                    peak_power = min(power)            #FInd Peak Power
                    fill_factor = peak_power/(Voc*Jsc)  #Find Fill Factor
                    pce = peak_power/P_in              #Find Power Conversion Efficiency
                    
                self.Logbox.AppendText('\r' + 'Device_' + str(device_num) + '-' + str(pixel_num) + ':' + 'Jsc: ' + str(Jsc) + 'Voc: ' + str(Voc))
                
                summary_data = [pixel_num, Voc, Jsc, peak_power, fill_factor, pce]
                with open(device_summary, 'a', newline='') as f:
                    wr = csv.writer(f)
                    wr.writerow(summary_data)

                #combine 6(2) pixels data in a device file
                voltage_by_pixel.append(voltage)    
                current_by_pixel.append(current)
                
                #call graph drawing class and draw a graph for the measured data
                self.matplotlibhrapg.drawData(value_list, device_num, pixel_num, flag)
                                
            #Generate raw data file by device number
            if not self.cb_9d.IsChecked():
                headings = ["Voltage(V)","Current(A)-P1","Voltage(V)","Current(A)-P2","Voltage(V)","Current(A)-P3","Voltage(V)","Current(A)-P4","Voltage(V)","Current(A)-P5","Voltage(V)","Current(A)-P6"]
                data = [voltage_by_pixel[0], current_by_pixel[0], voltage_by_pixel[1], current_by_pixel[1], voltage_by_pixel[2], current_by_pixel[2], voltage_by_pixel[3], current_by_pixel[3], voltage_by_pixel[4], current_by_pixel[4], voltage_by_pixel[5], current_by_pixel[5]]
            else:
                headings = ["Voltage(V)","Current(A)-P2","Voltage(V)","Current(A)-P3"]
                data = [voltage_by_pixel[0], current_by_pixel[0], voltage_by_pixel[1], current_by_pixel[1]]
            # headings=["Voltage(V)","Current(A)-P6","Voltage(V)","Current(A)-P6"]
            # data = [voltage_by_pixel[0], current_by_pixel[0]]
            filename = self.fname + "_D" + str(device_num) + suffix + "_RawData_" + str(timestamp) + ".csv"
            export_data = zip_longest(*data, fillvalue = '')
            
            with open(filename, 'a', newline='') as file:
                wr = csv.writer(file)
                wr.writerow(headings)
                wr.writerows(export_data)
            
        self.Logbox.AppendText('\rCompleted Jsc measurement!')
        self.Logbox.AppendText('\rIf you want to measure other samples continuously, Press RESTART BUTTON otherwise Press FINISH Button')
             
#--------------------------------------------------------------------------------------
    def OnStability(self, event):           #activated by 'Stability' Button
        
#        self.timer = wx.Timer(self)
#        self.Bind(wx.EVT_TIMER, self.OnTimer)
#        self.timer.Start(1000)    # 1 second interval
        
        self.Logbox.AppendText('Start Stability measurement of multiple devices\r')
        
#        self.start_time = time.time()
        
        self.saveData()
        
        devices = self.tc1.GetValue()
        device_list = devices.split(",")
        area = float(self.tc6.GetValue())
        P_in = float(self.tc7.GetValue())
        period = float(self.tc11.GetValue())
        interval = int(self.tc12.GetValue())

        elapsed_time = round((time.time() - self.start_time), 1)
        
        pixel = self.chamber_select(event)

        for i in device_list:
            device_num = int(i)
            
            for j in pixel:
                device_summary = self.fname + "_D" + str(device_num) + "_Pixel" + str(j) + ".csv"   #Define file name for device's summary data
                with open(device_summary, 'a', newline='') as ff:
                    wr = csv.writer(ff)
                    wr.writerow(["Elapsed_time(s)", "Voc(V)", "Jsc(A/cm2)","Peak Power(W/cm2)", "FF", "PCE(%)"])
        
        try:
            
            while elapsed_time < period * 3600:       #convert the period time from hour to seconds
                
                count = time.time()
                
                for i in device_list:
                        
                    device_num = int(i)
                    voltage_by_pixel = []
                    current_by_pixel = []
                    
                    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M")
        
                    for j in pixel:
                        
                        pixel_num = j
                        
                        if not self.cb_9d.IsChecked():
                            self.pixel_on(device_num, pixel_num)  #switch on a pixel which is to be measured
                            flag = 4
                        else:
                            self.pixel_on_stability(device_num, pixel_num)
                            flag = 9
                        
                        print('reading device #', str(device_num), '-pixel #', str(pixel_num))
                        message = 'reading device'+ str(device_num) + '-pixel' + str(pixel_num)
                        time_message = time.strftime("%H:%M:%S", time.gmtime(time.time() - self.start_time))
                        self.Logbox.AppendText('\r' + time_message + '  ' + message)
                        time.sleep(0.1)
                        
                        #readout Keithley data
                        value_list = self.OnMeasurement(event)
                        wx.Yield()
                                
                        voltage = value_list[::2]
                        current = value_list[1::2]
                        
                        if not self.cb_9d.IsChecked():
                            self.pixel_off(device_num, pixel_num)
                        else:
                            self.pixel_off_stability(device_num, pixel_num)
                
                        curr_density = list(map(lambda x: x/area, current))
                        power = list(map(lambda x, y: x*y, voltage, curr_density))

                        for k in range(len(voltage) - 1):       #Find Jsc
                            if voltage[k] == 0:
                                Jsc = current[k]/area
                            elif voltage[k]*voltage[k+1] < 0:
                                ratio = (0 - voltage[k])/(voltage[k+1] - voltage[k])
                                Jsc = current[k] + ratio * (current[k+1] - current[k])
                       
                        # Default parameter setting as 'NA'
                        Voc = 'NA'
                        peak_power = 'NA'
                        fill_factor = 'NA'
                        pce = 'NA'
        
                        for l in range(len(current) - 1):   #Find Voc
                            if current[l]*current[l+1] < 0:
                                ratio = (0 - current[l])/(current[l+1] - current[l])
                                Voc = voltage[l] + ratio * (voltage[l+1] - voltage[l])
                   
                        if Voc != 'NA':
                            peak_power = min(power)            #FInd Peak Power
                            fill_factor = peak_power/(Voc*Jsc)  #Find Fill Factor
                            pce = peak_power/P_in              #Find Power Conversion Efficiency
        
                        # device_summary = self.fname + str(i) + "_Pixel" + str(j) + ".csv"   #Define file name for device's summary data
                        device_summary = self.fname + "_D" + str(device_num) + "_Pixel" + str(pixel_num) + ".csv"
                        summary_data = [round(elapsed_time, 1), Voc, Jsc, peak_power, fill_factor, pce]
                        with open(device_summary, 'a', newline='') as f:
                            wr = csv.writer(f)
                            wr.writerow(summary_data)
            
                        voltage_by_pixel.append(voltage)
                        current_by_pixel.append(current)
                        
                        
                        #Display graphs
                        self.matplotlibhrapg.drawStability(peak_power, elapsed_time, device_num, pixel_num, flag)
                                
                    #Generate raw data file by device number
                    if not self.cb_9d.IsChecked():
                        headings = ["Voltage(V)","Current(A)-P1","Voltage(V)","Current(A)-P2","Voltage(V)","Current(A)-P3","Voltage(V)","Current(A)-P4","Voltage(V)","Current(A)-P5","Voltage(V)","Current(A)-P6"]
                        data = [voltage_by_pixel[0], current_by_pixel[0], voltage_by_pixel[1], current_by_pixel[1], voltage_by_pixel[2], current_by_pixel[2], voltage_by_pixel[3], current_by_pixel[3], voltage_by_pixel[4], current_by_pixel[4], voltage_by_pixel[5], current_by_pixel[5]]
                    else:
                        headings = ["Voltage(V)","Current(A)-P2","Voltage(V)","Current(A)-P3"]
                        data = [voltage_by_pixel[0], current_by_pixel[0], voltage_by_pixel[1], current_by_pixel[1]]

                    # #Generate raw data file by device number
                    # data = [voltage_by_pixel[0], current_by_pixel[0], voltage_by_pixel[1], current_by_pixel[1]]
                    raw_filename = self.fname + "_D" + str(device_num) + "_RawData_" + str(timestamp) + ".csv"
                    export_data = zip_longest(*data, fillvalue = '')
                    
                    with open(raw_filename, 'w', newline='') as file:
                        wr = csv.writer(file)
                        wr.writerow(headings)
                        # wr.writerow(["Voltage(V)","Current(A)-P2","Voltage(V)","Current(A)-P3"])
                        wr.writerows(export_data)
                    
                print(time.strftime("%H:%M:%S", time.gmtime(time.time() - self.start_time)) + '  elapsed since it is started.')
                print('.......Waiting for next round.......')
                time_message = time.strftime("%d %H:%M:%S", time.gmtime(time.time() - self.start_time))
                self.Logbox.AppendText('\rDay_' + time_message + ' elapsed.  .......Waiting for next round.......')
    
                consummed_time = time.time() - count
                break_time = interval*60 - consummed_time
                
#                time.sleep(break_time)
                while interval*60 > consummed_time:
                    consummed_time = time.time() - count
                    break_time = interval*60 - consummed_time
                    remain_time = time.strftime("%M:%S", time.gmtime(break_time))
#                    print(remain_time)
#                    self.timebox.SetValue(remain_time)
                    self.justbox.AppendText('In ' + remain_time + '   resume')
                    time.sleep(1)
                elapsed_time = time.time() - self.start_time
                self.justbox.AppendText('\t                       ')
                       
            print('Completed Measurement! Bye....')
            self.Logbox.AppendText('\rCompleted Measurement! Bye....')
            self.Logbox.AppendText('\rIf you want to measure other samples continuously, Press RESTART BUTTON otherwise Press FINISH Button')

        except KeyboardInterrupt:
            self.Destroy()
            sys.exit()

#---------------------------------------------------------------------------------------------
    def saveData(self):
        root = tk.Tk()	#get root location for the later GUI default start point
        saveloc = tkinter.filedialog.askdirectory(parent=root, initialdir='C:/Users/test/Desktop/User folders', title='Please select a directory to save your data')
        os.chdir(saveloc) 	#change to the location where works should be done
        dlg = tkinter.filedialog.asksaveasfilename(confirmoverwrite=False)
        self.fname = dlg
        root.withdraw()	#closing the UI interface remanent

                

######################################################################
#  Switch Configuration Table (2 Devices x 6 pixels operation)
#
#  S/W Board | TER1 | TER2 | TER3 | TER4 | TER5 | TER6 | TER7 | TER8
#  ------------------------------------------------------------------
#       1    | D1P1 | D1P2 | D1P3 | D1P4 | D1P5 | D1P6 |  x   | D1C
#  ------------------------------------------------------------------
#       2    | D2P1 | D2P2 | D2P3 | D2P4 | D2P5 | D2P6 |  x   | D2C
######################################################################
        
    def pixel_on(self, device_num, pixel_num):
        
        device_num = int(device_num)
        pixel_num = int(pixel_num)
        
        on_commands = [b'\x65', b'\x66', b'\x67', b'\x68', b'\x69', b'\x6a', b'\x6b', b'\x6c']

        #serial port selection for each switch board (COM5: TopBoard, COM6: BottomBoard)
        ser_switch = [serial.Serial("COM5", baudrate=9600, bytesize=8 ,stopbits=1), serial.Serial("COM6", baudrate=9600, bytesize=8 ,stopbits=1)]

        if device_num > 2:
            raise "Maximum Device Number is 2. Type number from 1 to 2"
        if pixel_num > 6:
            raise "Maximum Pixel Number is 6. Type number from 1 to 6"
        return ser_switch[device_num-1].write(on_commands[pixel_num - 1]), ser_switch[device_num-1].write(on_commands[7])


    def pixel_off(self, device_num, pixel_num):

        device_num = int(device_num)
        pixel_num = int(pixel_num)
        
        ser_switch = [serial.Serial("COM5", baudrate=9600, bytesize=8 ,stopbits=1), serial.Serial("COM6", baudrate=9600, bytesize=8 ,stopbits=1)]
        
        off_commands = [b'\x6f', b'\x70', b'\x71', b'\x72', b'\x73', b'\x74', b'\x75', b'\x76']

        if device_num > 2:
            raise "Maximum Device Number is 2. Type number from 1 to 2"
        if pixel_num > 6:
            raise "Maximum Pixel Number is 6. Type number from 1 to 6"
        return ser_switch[device_num-1].write(off_commands[pixel_num - 1]), ser_switch[device_num-1].write(off_commands[7])


#
#######################################################################
##  Switch Configuration Table (4 Devices x 6 pixels operation)
##
##  S/W Board | TER1 | TER2 | TER3 | TER4 | TER5 | TER6 | TER7 | TER8
##  ------------------------------------------------------------------
##       1    | D1P1 | D1P2 | D1P3 | D1P4 | D1P5 | D1P6 |  x   | D1C
##  ------------------------------------------------------------------
##       2    | D2P1 | D2P2 | D2P3 | D2P4 | D2P5 | D2P6 |  x   | D2C
##  ------------------------------------------------------------------
##       3    | D3P1 | D3P2 | D3P3 | D3P4 | D3P5 | D3P6 |  x   | D3C
##  ------------------------------------------------------------------
##       4    | D4P1 | D4P2 | D4P3 | D4P4 | D4P5 | D4P6 |  x   |D4C
#######################################################################
#        
#    def pixel_on(self, device_num, pixel_num):
#        
#        device_num = int(device_num)
#        pixel_num = int(pixel_num)
#        
#        on_commands = [b'\x65', b'\x66', b'\x67', b'\x68', b'\x69', b'\x6a', b'\x6b', b'\x6c']
#
#        #serial port selection for each switch board
#        ser_switch = [serial.Serial("COM8", baudrate=9600, bytesize=8 ,stopbits=1), serial.Serial("COM6", baudrate=9600, bytesize=8 ,stopbits=1), serial.Serial("COM9", baudrate=9600, bytesize=8 ,stopbits=1), serial.Serial("COM7", baudrate=9600, bytesize=8 ,stopbits=1)]
#
#        if device_num > 4:
#            raise "Maximum Device Number is 4. Type number from 1 to 4"
#        if pixel_num > 6:
#            raise "Maximum Pixel Number is 6. Type number from 1 to 6"
#        return ser_switch[device_num-1].write(on_commands[pixel_num - 1]), ser_switch[device_num-1].write(on_commands[7])
#
#
#    def pixel_off(self, device_num, pixel_num):
#
#        device_num = int(device_num)
#        pixel_num = int(pixel_num)
#        
#        ser_switch = [serial.Serial("COM8", baudrate=9600, bytesize=8 ,stopbits=1), serial.Serial("COM6", baudrate=9600, bytesize=8 ,stopbits=1), serial.Serial("COM9", baudrate=9600, bytesize=8 ,stopbits=1), serial.Serial("COM7", baudrate=9600, bytesize=8 ,stopbits=1)]
#        
#        off_commands = [b'\x6f', b'\x70', b'\x71', b'\x72', b'\x73', b'\x74', b'\x75', b'\x76']
#
#        if device_num > 4:
#            raise "Maximum Device Number is 4. Type number from 1 to 4"
#        if pixel_num > 6:
#            raise "Maximum Pixel Number is 6. Type number from 1 to 6"
#        return ser_switch[device_num-1].write(off_commands[pixel_num - 1]), ser_switch[device_num-1].write(off_commands[7])
#

#######################################################################
#  Switch Configuration Table (9 Devices x 2 pixels operation)
#
#  S/W Board | TER1 | TER2 | TER3 | TER4 | TER5 | TER6 | TER7 | TER8
#  -------------------------------------------------------------------
#       1    | D7P2 | D7P3 | D4P2 | D4P3 | D1P2 | D1P3 |   x  |   x
#  -------------------------------------------------------------------
#       2    | D8P2 | D8P3 | D5P2 | D5P3 | D2P2 | D2P3 |   x  |   x
#  -------------------------------------------------------------------
#       3    | D9P2 | D9P3 | D6P2 | D6P3 | D3P2 | D3P3 |   x  | D9C
#  -------------------------------------------------------------------
#       4    | D1C  | D2C  | D3C  | D4C  | D5C  | D6C  | D7C  | D8C
#######################################################################
        
    def pixel_on_stability(self, device_num, pixel_num):
        
        device_num = int(device_num)
        pixel_num = int(pixel_num)
        
        on_commands = [b'\x65', b'\x66', b'\x67', b'\x68', b'\x69', b'\x6a', b'\x6b', b'\x6c']

        #serial port selection for each switch board
        ser_switch = [serial.Serial("COM8", baudrate=9600, bytesize=8 ,stopbits=1), serial.Serial("COM6", baudrate=9600, bytesize=8 ,stopbits=1), serial.Serial("COM9", baudrate=9600, bytesize=8 ,stopbits=1), serial.Serial("COM7", baudrate=9600, bytesize=8 ,stopbits=1)]

        if (device_num == 1 and pixel_num == 2):
            return ser_switch[0].write(on_commands[4]), ser_switch[3].write(on_commands[device_num - 1])
        
        if (device_num == 1 and pixel_num == 3):
            return ser_switch[0].write(on_commands[5]), ser_switch[3].write(on_commands[device_num - 1])

        if (device_num == 4 and pixel_num == 2):
            return ser_switch[0].write(on_commands[2]), ser_switch[3].write(on_commands[device_num - 1])
        
        if (device_num == 4 and pixel_num == 3):
            return ser_switch[0].write(on_commands[3]), ser_switch[3].write(on_commands[device_num - 1])

        if (device_num == 7 and pixel_num == 2):
            return ser_switch[0].write(on_commands[0]), ser_switch[3].write(on_commands[device_num - 1])
        
        if (device_num == 7 and pixel_num == 3):
            return ser_switch[0].write(on_commands[1]), ser_switch[3].write(on_commands[device_num - 1])

        if (device_num == 2 and pixel_num == 2):
            return ser_switch[1].write(on_commands[4]), ser_switch[3].write(on_commands[device_num - 1])
        
        if (device_num == 2 and pixel_num == 3):
            return ser_switch[1].write(on_commands[5]), ser_switch[3].write(on_commands[device_num - 1])

        if (device_num == 5 and pixel_num == 2):
            return ser_switch[1].write(on_commands[2]), ser_switch[3].write(on_commands[device_num - 1])
        
        if (device_num == 5 and pixel_num == 3):
            return ser_switch[1].write(on_commands[3]), ser_switch[3].write(on_commands[device_num - 1])

        if (device_num == 8 and pixel_num == 2):
            return ser_switch[1].write(on_commands[0]), ser_switch[3].write(on_commands[device_num - 1])
        
        if (device_num == 8 and pixel_num == 3):
            return ser_switch[1].write(on_commands[1]), ser_switch[3].write(on_commands[device_num - 1])

        if (device_num == 3 and pixel_num == 2):
            return ser_switch[2].write(on_commands[4]), ser_switch[3].write(on_commands[device_num - 1])
        
        if (device_num == 3 and pixel_num == 3):
            return ser_switch[2].write(on_commands[5]), ser_switch[3].write(on_commands[device_num - 1])

        if (device_num == 6 and pixel_num == 2):
            return ser_switch[2].write(on_commands[2]), ser_switch[3].write(on_commands[device_num - 1])
        
        if (device_num == 6 and pixel_num == 3):
            return ser_switch[2].write(on_commands[3]), ser_switch[3].write(on_commands[device_num - 1])

        if (device_num == 9 and pixel_num == 2):
            return ser_switch[2].write(on_commands[0]), ser_switch[2].write(on_commands[7])
        
        if (device_num == 9 and pixel_num == 3):
            return ser_switch[2].write(on_commands[1]), ser_switch[2].write(on_commands[7])


    def pixel_off_stability(self, device_num, pixel_num):

        device_num = int(device_num)
        pixel_num = int(pixel_num)
        
        ser_switch = [serial.Serial("COM8", baudrate=9600, bytesize=8 ,stopbits=1), serial.Serial("COM6", baudrate=9600, bytesize=8 ,stopbits=1), serial.Serial("COM9", baudrate=9600, bytesize=8 ,stopbits=1), serial.Serial("COM7", baudrate=9600, bytesize=8 ,stopbits=1)]
        
        off_commands = [b'\x6f', b'\x70', b'\x71', b'\x72', b'\x73', b'\x74', b'\x75', b'\x76']

        if (device_num == 1 and pixel_num == 2):
            return ser_switch[0].write(off_commands[4]), ser_switch[3].write(off_commands[device_num - 1])
        
        if (device_num == 1 and pixel_num == 3):
            return ser_switch[0].write(off_commands[5]), ser_switch[3].write(off_commands[device_num - 1])

        if (device_num == 4 and pixel_num == 2):
            return ser_switch[0].write(off_commands[2]), ser_switch[3].write(off_commands[device_num - 1])
        
        if (device_num == 4 and pixel_num == 3):
            return ser_switch[0].write(off_commands[3]), ser_switch[3].write(off_commands[device_num - 1])

        if (device_num == 7 and pixel_num == 2):
            return ser_switch[0].write(off_commands[0]), ser_switch[3].write(off_commands[device_num - 1])
        
        if (device_num == 7 and pixel_num == 3):
            return ser_switch[0].write(off_commands[1]), ser_switch[3].write(off_commands[device_num - 1])

        if (device_num == 2 and pixel_num == 2):
            return ser_switch[1].write(off_commands[4]), ser_switch[3].write(off_commands[device_num - 1])
        
        if (device_num == 2 and pixel_num == 3):
            return ser_switch[1].write(off_commands[5]), ser_switch[3].write(off_commands[device_num - 1])

        if (device_num == 5 and pixel_num == 2):
            return ser_switch[1].write(off_commands[2]), ser_switch[3].write(off_commands[device_num - 1])
        
        if (device_num == 5 and pixel_num == 3):
            return ser_switch[1].write(off_commands[3]), ser_switch[3].write(off_commands[device_num - 1])

        if (device_num == 8 and pixel_num == 2):
            return ser_switch[1].write(off_commands[0]), ser_switch[3].write(off_commands[device_num - 1])
        
        if (device_num == 8 and pixel_num == 3):
            return ser_switch[1].write(off_commands[1]), ser_switch[3].write(off_commands[device_num - 1])

        if (device_num == 3 and pixel_num == 2):
            return ser_switch[2].write(off_commands[4]), ser_switch[3].write(off_commands[device_num - 1])
        
        if (device_num == 3 and pixel_num == 3):
            return ser_switch[2].write(off_commands[5]), ser_switch[3].write(off_commands[device_num - 1])

        if (device_num == 6 and pixel_num == 2):
            return ser_switch[2].write(off_commands[2]), ser_switch[3].write(off_commands[device_num - 1])
        
        if (device_num == 6 and pixel_num == 3):
            return ser_switch[2].write(off_commands[3]), ser_switch[3].write(off_commands[device_num - 1])

        if (device_num == 9 and pixel_num == 2):
            return ser_switch[2].write(off_commands[0]), ser_switch[2].write(off_commands[7])
        
        if (device_num == 9 and pixel_num == 3):
            return ser_switch[2].write(off_commands[1]), ser_switch[2].write(off_commands[7])

        
##-----------------------------------------------------------------------------------------------        
#def saveData():
#    root = tk.Tk()	#get root location for the later GUI default start point
#    saveloc = tkinter.filedialog.askdirectory(parent=root, initialdir='C:/Users/test/Desktop/User folders', title='Please select a directory to save your data')
#    os.chdir(saveloc) 	#change to the location where works should be done
#    root.withdraw()	#closing the UI interface remanent
#
##-------------------------------------------------------------------------------------------------


class MatplotPanel(wx.Window):
    
    def __init__(self, parent):
        wx.Window.__init__(self, parent)
        self.lines = []
        self.figure = Figure()
        self.canvas = FigureCanvasWxAgg(self, 1, self.figure)
#        self.drawData()
        self.Bind(wx.EVT_SIZE, self.sizeHandler)

    def sizeHandler(self, parent):
        self.canvas.SetSize(self.GetSize())
        
    def repaint(self):
        self.canvas.draw()

    def drawData(self, value_list, device_num, pixel_num, flag):
               
        if len(value_list) != 0:
            if flag == 4:
                self.subplot1 = self.figure.add_subplot(2,2,device_num)
            else:
                self.subplot1 = self.figure.add_subplot(3,3,device_num)
                
            voltage = value_list[::2]
            current = value_list[1::2]
            self.subplot1.plot(voltage, current, label='P'+str(pixel_num))
            self.subplot1.set_title('Device'+ str(device_num))
            
        self.subplot1.set_xlabel("Voltage (V)")
        self.subplot1.set_ylabel("Current (mA)")
#        self.subplot1.legend(loc='upper left', ncol=3, fontsize=8)
        self.subplot1.legend(loc='upper left', fontsize=8)
        self.subplot1.grid(True)
        self.figure.tight_layout()
        self.repaint()

#        plt.pause(0.1)
#        plt.tight_layout()

    def GetLineFormats(self):
        colors = ('r', 'g', 'b', 'c', 'm', 'y')
#        linestyles = ['-', '--', ':']
        lineFormats = []
        for col in colors:
            lineFormats.append(col)
        return lineFormats
    
    
    def drawStability(self, peak_power, elapsed_time, device_num, pixel_num, flag):
        
#        elapsed_time = time.time() - self.start_time
        if flag == 4:
            self.subplot2 = self.figure.add_subplot(2,2, device_num)
        else:
            self.subplot2 = self.figure.add_subplot(3,3, device_num)
        
        self.subplot2.plot(elapsed_time/60, round(peak_power*1000, 2), 'o', markersize=1)
        self.subplot2.set_title('Device #' + str(device_num))
        self.subplot2.set_xlabel('Elapsed Time (min)')
        self.subplot2.set_ylabel('Peak Power (mW/cm2)')
        self.figure.tight_layout()
        self.repaint()



def main():

    app = wx.App()
    ex = MyFrame(None)
    ex.Show()
    app.MainLoop()


if __name__ == '__main__':
    try:        
        main()
        
    except KeyboardInterrupt:
        MyFrame.Destroy()
