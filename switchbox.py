# -*- coding: utf-8 -*-
"""
Created on Wed Dec  1 15:05:13 2021

@author: yc6017
"""
import serial

class switchbox_map:
    sixXfour=[[(j,i)  for j in range(1,3) for i in range(1,5)],
               [(j,i) for j in range(3,5) for i in range(1,5)],
               [(j,i) for j in range(5,7) for i in range(1,5)],
               [(i) for i in range(1,7)]]
    
    twoXsix=[[(1,1),(1,2),(1,3),(1,4),(1,5),(1,6),(),(1)],
              [(2,1),(2,2),(2,3),(2,4),(2,5),(2,6),(),(2)]]
    
    nineXtwo=[[(7,2),(7,3),(4,2),(4,3),(1,2),(1,3),(),()],
              [(8,2),(8,3),(5,2),(5,3),(2,2),(2,3),(),()],
              [(9,2),(9,3),(6,2),(6,3),(3,2),(3,3),(),(9)],
              [(1),(2),(3),(4),(5),(6),(7),(8)]]

class switchbox:
    _on_comm=[b'\x65', b'\x66', b'\x67', b'\x68', b'\x69', b'\x6a', b'\x6b',
              b'\x6c']
    _off_comm=[b'\x6f', b'\x70', b'\x71', b'\x72', b'\x73', b'\x74', b'\x75',
               b'\x76']
    
    def __init__(self,switchbox_map,ports):
        assert len(switchbox_map)==len(ports), \
            'map doesn\'t match with number of ports'
        self.map=switchbox_map
        self.ports=ports
        self._on_list=()
            
    @property
    def status(self):
        if self._on_list:
            print(f'Device {self._on_list[0]} - pixel {self._on_list[1]} is on.')
        else:
            print('No pixel is turned on.')
    
    def find_pix_port_comm_n(self,dev_n,pix_n):
        try:
            indices=next((i,j) for i,row in enumerate(self.map) for j,value in \
                    enumerate(row) if value==(dev_n,pix_n))
        except StopIteration:
            raise ValueError('Input doesn\'t match. Please make sure the '
                             'inputs are integers within number of devices and '
                             'pixels.')
        return indices
        
    def find_dev_port_comm_n(self,dev_n):
        try:
            indices=next((i,j) for i,row in enumerate(self.map) for j,value in \
                        enumerate(row) if value==(dev_n))
        except StopIteration:
            raise ValueError('Input doesn\'t match. Please make sure the '
                             'inputs are integers within number of devices')
        return indices
        
    def switch(self,dev_n,pix_n,on=0):
        if on:
            if (dev_n,pix_n)==self._on_list:
                raise Exception(f'Device {dev_n} - pixel {pix_n} is already on!')
            if self._on_list:
                raise Exception('Should not turn on multiple pixels.')
            (port_n,comm_n)=self.find_pix_port_comm_n(dev_n,pix_n)
            with serial.Serial(self.ports[port_n]) as pix_ser:
                pix_ser.write(self._on_comm[comm_n])
            (port_n,comm_n)=self.find_dev_port_comm_n(dev_n)
            with serial.Serial(self.ports[port_n]) as dev_ser:
                dev_ser.write(self._on_comm[comm_n])
            self._on_list=(dev_n,pix_n)
        else:
            if not (dev_n,pix_n)==self._on_list:
                raise Exception(f'Device {dev_n} - pixel {pix_n} is not on yet!')
            (port_n,comm_n)=self.find_pix_port_comm_n(dev_n,pix_n)
            with serial.Serial(self.ports[port_n]) as pix_ser:
                pix_ser.write(self._off_comm[comm_n])
            (port_n,comm_n)=self.find_dev_port_comm_n(dev_n)
            with serial.Serial(self.ports[port_n]) as dev_ser:
                dev_ser.write(self._off_comm[comm_n])
            self._on_list=()
            
    def reset(self):
        for port in self.ports:
            for comm in self._off_comm:
                with serial.Serial(port) as ser:
                    ser.write(comm)
        self._on_list=()
