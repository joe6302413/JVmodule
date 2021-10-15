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
        datanames=[['data'+str(i) for i in range(numberofdata) for j in range(data_dim)]]
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
    def __init__(self,V,J,name='no_name',direction='forward',power=100):
        assert len(J)==len(V), 'number of Current-Voltage data not matching'
        assert direction in ('forward','reverse'), 'direction has to be either forward or reverse'
        self.J,self.V,self.name,self.power=np.array(J),np.array(V),name,power
        self.status={'direction': direction,'power': str(power)+'mW/cm^2'}
        self.find_characters()
        self.status.update({'Jsc':self.Jsc,
                     'Voc': self.Voc,'FF':self.FF, 'PCE': self.PCE})
                     # 'Rs': self.Rs, 'Rsh': self.Rsh})
        
    def __repr__(self):
        return self.name
    
    def __str__(self):
        summary='Name:\t'+self.name+'\n'
        summary+='\n'.join([i+':\t'+str(j) for i,j in self.status.items()])+'\n'
        return summary
    
    def find_characters(self):
        # Find Jsc and Shunt resistance
        if self.status['direction']=='forward':
            index=next(p for p,q in enumerate(self.V) if q>0)
            J0,J1,V0,V1=self.J[index-1],self.J[index],self.V[index-1],self.V[index]
            # minindex=next(p for p,q in enumerate(self.V) if q>1e-2)
            # maxindex=next(p for p,q in enumerate(self.V) if q>-1e-2)
        else:
            index=next(p for p,q in enumerate(self.V) if q<0)
            J0,J1,V0,V1=self.J[index],self.J[index-1],self.V[index],self.V[index-1]
            # minindex=next(p for p,q in enumerate(self.V) if q<1e-2)
            # maxindex=next(p for p,q in enumerate(self.V) if q<-1e-2)
        self.Jsc=-(-V0*J1+V1*J0)/(-V0+V1)
        # [self.Rsh,_],[[cov,_],[_,_]]=np.polyfit(1e-3*self.J[minindex:maxindex],self.V[minindex:maxindex],1,cov=True)
        # self.std_Rsh=cov**0.5
        # Find Voc
        if self.status['direction']=='forward':
            index=next(p for p,q in enumerate(self.J) if q>0)
            J0,J1,V0,V1=self.J[index-1],self.J[index],self.V[index-1],self.V[index]
        else:
            index=next(p for p,q in enumerate(self.J) if q<0)
            J0,J1,V0,V1=self.J[index],self.J[index-1],self.V[index],self.V[index-1]
        self.Voc=(V0*J1-V1*J0)/(-J0+J1)
        # Find PCE
        self.PCE=0
        for i,j in zip(self.J,self.V):
            if -i*j/self.power*100>self.PCE:
                self.PCE=-i*j/self.power*100
                # Find FF
                self.FF=-i*j/self.Voc/self.Jsc*100
        
    
    def plot(self):
        plt.grid(True,which='both',axis='x')
        plt.plot(self.V,self.J,label=self.name)
        plt.legend()
        plt.xlabel('Voltage (V)')
        plt.ylabel('Current Density (mA/cm^2)')
        plt.autoscale(enable=True,axis='both',tight=True)
        

class deviceJV:
    def __init__(self,pixels,device_name='device',direction='forward',power=100):
        assert isinstance(pixels,(list,tuple)),'device must be a tuple or list'
        assert all(isinstance(i,JV) for i in pixels), 'deviceJV only takes list(tuple) of JV objects'
        assert direction in ('forward','reverse','both'), 'direction must be forward, reverse or both'
        self.direction=direction
        self.pix_n=len(pixels) if direction in ('forward','reverse') else len(pixels)/2
        self.pixels,self.name=pixels,device_name
    def __repr__(self):
        return self.name
    
    def __str__(self):
        summary='Name:\t'+self.name+'\nContains:\n'
        summary+='\n'.join([i.name for i in self.pixels])+'\n'
        return summary
    
    def plot(self):
        for i in self.pixels:
            i.plot()
    
    def save_device_csv(self,location):
        filename=self.name
        datanames=[[i.name] for i in self.pixels]
        origin_header=[['Voltage','Current Density'],['V','mA/cm\\+(2)']]
        x,y=[i.V for i in self.pixels],[i.J for i in self.pixels]
        save_csv_for_origin((x,y),location,filename,datanames,origin_header)
        
    def save_device_summary_csv(self,location):
        filename=self.name+'_summary'
        origin_header=[['Pixels','V\\-(oc)','J\\-(sc)','FF','PCE'],[None,'V','mA/cm\\+(2)','','%']]
        datanames=[['V\\-(oc)','J\\-(sc)','FF','PCE']]
        # datanames=['V\\-(oc)']
        x,Voc,Jsc,FF,PCE=[],[],[],[],[]
        for i in self.pixels:
            x.append(i.name)
            Voc.append(i.Voc)
            Jsc.append(i.Jsc)
            FF.append(i.FF)
            PCE.append(i.PCE)
        save_csv_for_origin(([x],[Voc],[Jsc],[FF],[PCE]),location,filename,datanames,origin_header)
        
    @classmethod
    def import_from_files(cls,filenames,direction='forward',header_length=3,power=100,trunc=-4):
        devices=[]
        for i in filenames:
            filename=split(i)[1][:trunc]
            with open(i,'r',newline='') as f:
                reader=csv.reader(list(f)[header_length:],quoting=csv.QUOTE_NONNUMERIC)
                data=np.array(list(reader))
                pixels=[]
                for n in range(np.size(data,1)//2):
                    diff=np.diff(data[:,2*n])
                    if direction=='both':
                        if any(diff==0):    #fixing mixing backward forward scan from Gihan old software
                            index=np.where(diff==0)[0][0]
                            direction0,direction1=('forward','reverse') if diff[0]>0 else ('reverse','forward')
                            V0,V1=data[:index+1,2*n],data[index+1:,2*n]
                            J0,J1=data[:index+1,2*n+1],data[index+1:,2*n+1]
                            name0=filename+'_p'+str(n)+'_'+direction0
                            name1=filename+'_p'+str(n)+'_'+direction1
                            pixels.append(JV(V0,J0,name0,direction0,power))
                            pixels.append(JV(V1,J1,name1,direction1,power))
                        else:
                            V,J=data[:,2*n],data[:,2*n+1]
                            pix_direction='forward' if V[1]-V[0]>0 else 'reverse'
                            name=filename+'_p'+str(n//2)+'_'+pix_direction
                            pixels.append(JV(V,J,name,pix_direction,power))
                    else:
                        V,J=data[:,2*n],data[:,2*n+1]
                        name=filename+'_p'+str(n)+'_'+direction
                        pixels.append(JV(V,J,name,direction,power))
                devices.append(deviceJV(pixels,filename,direction,power))
        return devices

