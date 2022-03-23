# -*- coding: utf-8 -*-
"""
Created on Mon Nov  9 16:30:53 2020

The module is for JV data managing for solarcell measurements

Note:
    1.
    

Last editing time: 12/11/2020
@author: Yi-Chun Chin   joe6302413@gmail.com
"""
import numpy as np
import csv
import matplotlib.pyplot as plt
from os.path import split,join

def save_csv_for_origin(data,location,filename=None,datanames=None,header=None):
    '''
    save data sets to csv format for origin.
    data=([x1,x2,...],[y1,y2,...],...) where each element is a list of array
    location string is the location for output file
    string filename will be used as output into filename.csv
    datanames=[[yname1,zname1,...],[yname2,zname2]] names should be for each individual data sets
    header=[[longname X, longname Y,...],[unit X, unit Y,...]]
    '''
    data_dim=len(data)
    assert [len(i) for i in data][1:]==[len(i) for i in data][:-1], 'number of data mismatch'
    assert len(header[0])==data_dim, 'header mismatch data dimension'
    numberofdata=len(data[0])
    data=[j for i in zip(*data) for j in i]
    maxlength=max(len(i) for i in data)
    data=np.transpose([np.append(i,['']*(maxlength-len(i))) for i in data])
    if datanames==None:
        datanames=[[f'data{i}' for i in range(numberofdata) for j in range(data_dim)]]
    else:
        datanames=[[j for i in datanames for j in (['']+i+['']*(data_dim-1-len(i)))]]
    if header==None:
        header=datanames+[['']*numberofdata*data_dim]
    else:
        header=[i*numberofdata for i in header]
    with open(join(location,str(filename)+'.csv'),'w',newline='') as f:
        writer=csv.writer(f)
        writer.writerows(header)
        writer.writerows(datanames)
        writer.writerows(data)

class JV:
    def __init__(self,V,J,name='no_name'):
        '''
        V and J are list of voltage (V) and current density (mA/cm$^{2}$).
        Name is a string.
        '''
        assert len(J)==len(V), 'number of Current-Voltage data not matching'
        self.V,self.J,self.name=np.array(V),np.array(J),name
        self.status={}
        
    def __repr__(self):
        return self.name
    
    def __str__(self):
        summary=f'Name:\t{self.name}\n'
        summary+='\n'.join([f'{i}:\t{j}' for i,j in self.status.items()])+'\n'
        return summary
    
class dark_PV(JV):
    def __init__(self,V,J,name='no_name_dark_PV',p_area=0.045,**kwargs):
        '''
        V and J are list of voltage (V) and current density (mA/cm$^{2}$).
        Name is a string. p_area is pixel area in unit of cm$^{2}$.
        '''
        if all(np.diff(V)>0):
            self.direction='forward'
        elif all(np.diff(V)<0):
            self.direction='reverse'
        else:
            raise Exception('all PV scans must be one single direction scan!')
        super().__init__(V,J,name)
        self.p_area=p_area
        self.status={'direction': self.direction,
                     'pixel area': f'{p_area} cm^2'}
        self.__dict__.update(kwargs)
    
    def plot(self):
        plt.grid(True,which='both',axis='x')
        plt.plot(self.V,np.abs(self.J),label=self.name)
        plt.legend()
        plt.xlabel('Voltage (V)')
        plt.ylabel('Current Density (mA/cm$^{2}$)')
        plt.yscale('log')
        plt.autoscale(enable=True,axis='both',tight=True)
        
    def _I_to_J(self):
        '''
        Convert current (A) to current density (mA/cm^2). This is a feature 
        only used when the original input is in wrong unit. 
        (aim for Gihan's old software)
        '''
        self.J*=1e3/self.p_area
        
class light_PV(dark_PV):
    def __init__(self,V,J,name='no_name_light_PV',p_area=0.045,power_in=100,
                 **kwargs):
        '''
        V and J are list of voltage (V) and current density (mA/cm$^{2}$).
        Name is a string. Power_in is the input power in unit of mW/cm^2 
        and size is in unit of cm$^{2}$.
        '''
        # assert direction in ('forward','reverse'), 'direction has to be either forward or reverse'
        super().__init__(V,J,name,p_area,**kwargs)
        self.power_in=power_in
        self.status.update({'power input': f'{power_in} mW/cm^2'})
        self.find_characters()
    
    @property
    def characters(self):
        return {'name':self.name,'time':self.time,'Voc':self.Voc,'Jsc':self.Jsc,
                'FF':self.FF,'PCE':self.PCE}
    
    def update_characters_status(self):
        self.status.update({'Jsc':f'{self.Jsc:.2f} mA/cm^2',
                     'Voc': f'{self.Voc:.2f} V','FF':f'{self.FF:.2f}',
                     'PCE': f'{self.PCE:.2f}%'})
        
    def find_characters(self):
        # Find Jsc & Voc
        if self.status['direction']=='forward':
            self.Jsc=-self.find_zero_intersect(self.J[::-1],self.V[::-1])
            self.Voc=self.find_zero_intersect(self.V[::-1], self.J[::-1])
        else:
            self.Jsc=-self.find_zero_intersect(self.J, self.V)
            self.Voc=self.find_zero_intersect(self.V, self.J)
        # [self.Rsh,_],[[cov,_],[_,_]]=np.polyfit(1e-3*self.J[minindex:maxindex],self.V[minindex:maxindex],1,cov=True)
        # self.std_Rsh=cov**0.5   
        
        # Find PCE
        self.PCE=0
        self.FF=0
        for i in self.J*self.V:
            if -i/self.power_in*100>self.PCE:
                self.PCE=-i/self.power_in*100
                # Find FF
                self.FF=-i/self.Voc/self.Jsc*100
        self.update_characters_status()
        
    def plot(self):
        plt.grid(True,which='both',axis='x')
        plt.plot(self.V,self.J,label=self.name)
        plt.legend()
        plt.xlabel('Voltage (V)')
        plt.ylabel('Current Density (mA/cm$^{2}$)')
        plt.autoscale(enable=True,axis='both',tight=True)
    
    def _I_to_J(self):
        super()._I_to_J()
        self.find_characters()
        
    @staticmethod
    def find_zero_intersect(x,y):
        '''find the intersect of x when y=0 backwardly.'''
        # try:
        #     index=next(p for p,q in enumerate(y) if q>0)
        #     x0,x1,y0,y1=x[index-1],x[index],y[index-1],y[index]
        #     return (y0*x1-y1*x0)/(-y0+y1)
        # except StopIteration:
        #     return np.nan
        try:
            index=next(p for p,q in enumerate(y) if q<0)
            x0,x1,y0,y1=x[index],x[index-1],y[index],y[index-1]
            return (-y0*x1+y1*x0)/(-y0+y1)
        except StopIteration:
            return np.nan
        
class dark_PVdevice:
    func=dark_PV
    def __init__(self,pixels,device_name='dark_device',direction='forward',p_area=0.045):
        assert isinstance(pixels,(list,tuple)),'device must be a tuple or list'
        assert all(isinstance(i,dark_PV) for i in pixels), 'dark_PVdevice only takes list(tuple) of dark_PV objects'
        assert direction in ('forward','reverse','both'), 'direction must be forward, reverse or both'
        if direction!='both':
            assert all([i.status['direction']==pixels[0].status['direction'] 
                        for i in pixels[1:]]), 'same device must have the same direction'
            if not pixels[0].status['direction']==direction:
                direction=pixels[0].status['direction']
                print('Correcting direction for '+device_name+'!')
        else:
            assert all([i.status['direction']==pixels[0].status['direction'] 
                        for i in pixels[2::2]]), 'even pixels are not having the same direction'
            assert all([i.status['direction']==pixels[1].status['direction'] 
                        for i in pixels[3::2]]), 'odd pixels are not having the same direction'
            assert pixels[0].status['direction']!=pixels[1].status['direction'], 'This device is not scanned in both directions'
        self.direction,self.pixels,self.name=direction,pixels,device_name
        self.pix_n=len(pixels) if direction in ('forward','reverse') else len(pixels)/2
        self.status={'direction': direction,'number of pixels': self.pix_n,
                     'pixel area': f'{p_area} cm^2'}
        
    def __repr__(self):
        return self.name
    
    def __str__(self):
        summary='Name:\t'+self.name+'\n'
        summary+='\n'.join([f'{i}:\t{j}' for i,j in self.status.items()])+'\n'
        summary+='Contains:\n'+'\n'.join([i.name for i in self.pixels])+'\n'
        return summary
    
    def plot(self):
        for pixel in self.pixels:
            pixel.plot()
    
    def save_device_csv(self,location):
        filename=self.name
        datanames=[[i.name] for i in self.pixels]
        origin_header=[['Voltage','Current Density'],['V','mA/cm\\+(2)']]
        x,y=[i.V for i in self.pixels],[i.J for i in self.pixels]
        save_csv_for_origin((x,y),location,filename,datanames,origin_header)

    def save_all(self,location):
        self.save_device_csv(location)

    @classmethod
    def import_from_files(cls,filenames,direction='forward',header_length=3,
                          p_area=0.045,trunc=-4,**kwargs):
        devices=[]
        for i in filenames:
            filename=split(i)[1][:trunc]
            pixels=[]
            V,J,name=cls.read_file(i,direction,header_length,trunc)
            for v,j,n in zip(V,J,name):
                pixels.append(cls.func(v,j,n,p_area,**kwargs))
            devices.append(cls(pixels,filename,direction,p_area,**kwargs))
        return devices
    
    @staticmethod
    def _calibrate_Gihan_devices(devices):
        for device in devices:
            for pixel in device.pixels:
                pixel._I_to_J()
        return devices
    
    @staticmethod
    def read_file(filename,direction='forward',header_length=3,trunc=-4,):
        with open(filename,'r',newline='') as f:
            filename_no_abs=split(filename)[1][:trunc]
            reader=csv.reader(list(f)[header_length:],quoting=csv.QUOTE_NONNUMERIC)
            data=np.array(list(reader))
            V,J,name=[],[],[]
            for n in range(np.size(data,1)//2):
                diff=np.diff(data[:,2*n])
                diffprod=diff[:-1]*diff[1:]
                if direction=='both':
                    if any(diffprod<0):
                        #fixing mixing backward forward scan from Gihan old software
                        index=np.where(diffprod<0)[0][0]
                        direction0,direction1=('forward','reverse') if diff[0]>0 else ('reverse','forward')
                        V.append(data[:index+1,2*n])
                        V.append(data[index+1:,2*n])
                        J.append(data[:index+1,2*n+1])
                        J.append(data[index+1:,2*n+1])
                        name.append(f'{filename_no_abs}_p{n}_{direction0}')
                        name.append(f'{filename_no_abs}_p{n}_{direction1}')
                    else:
                        V.append(data[:,2*n])
                        J.append(data[:,2*n+1])
                        pix_direction='forward' if diff[0]>0 else 'reverse'
                        name.append(f'{filename_no_abs}_p{n//2}_{pix_direction}')
                else:
                    V.append(data[:,2*n])
                    J.append(data[:,2*n+1])
                    name.append(f'{filename_no_abs}_p{n}_{direction}')
        return V,J,name
    
    
    
class light_PVdevice(dark_PVdevice):
    func=light_PV
    def __init__(self,pixels,device_name='light_device',direction='forward',
                 p_area=0.045,power_in=100):
        assert all(isinstance(i,light_PV) for i in pixels), \
            'light_PVdevice only takes list(tuple) of light_PV objects'
        super().__init__(pixels,device_name,direction,p_area)
        self.status.update({'power_in': f'{power_in} mW/cm^2'})
    
    @property
    def characters(self):
        return {pixel.name: pixel.characters for pixel in self.pixels}
    
    def save_device_summary_csv(self,location):
        origin_header=[['Pixels']+[None]*4,
                       [None,'V','mA/cm\\+(2)','%','%']]
        datanames=[['V\\-(OC)','J\\-(SC)','FF','PCE']]
        #making the arrays of each element
        x,Voc,Jsc,FF,PCE=[],[],[],[],[]
        for i in self.pixels:
            x.append(i.name)
            Voc.append(i.Voc)
            Jsc.append(i.Jsc)
            FF.append(i.FF)
            PCE.append(i.PCE)
        if self.direction=='both':
            filename=f"{self.name}_summary_{self.pixels[0].status['direction']}"
            #making each element into 2D arrays
            data=([x[::2]],[Voc[::2]],[Jsc[::2]],[FF[::2]],[PCE[::2]])
            save_csv_for_origin(data,location,filename,datanames,origin_header)
            filename=f"{self.name}_summary_{self.pixels[1].status['direction']}"
            #making each element into 2D arrays
            data=([x[1::2]],[Voc[1::2]],[Jsc[1::2]],[FF[1::2]],[PCE[1::2]])
            save_csv_for_origin(data,location,filename,datanames,origin_header)
        else:
            filename=f'{self.name}_summary'
            #making each element into 2D arrays
            data=([x],[Voc],[Jsc],[FF],[PCE])
            save_csv_for_origin(data,location,filename,datanames,origin_header)
    
    def save_all(self,location):
        super().save_all(location)
        self.save_device_summary_csv(location)
