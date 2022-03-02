# -*- coding: utf-8 -*-
"""
Created on Fri Feb  4 14:40:43 2022

@author: yc6017
"""
import threading
import time

class mythread(threading.Thread):
    def __init__(self,event,period,target,*args):
        super().__init__()
        self.stopFlag=event
        self.period=period
        self.target=target
        self.args=args
        
    def run(self):
        t1=time.perf_counter()
        x=threading.Thread(target=self.target,args=self.args)
        counter=0
        while not self.stopFlag.wait(self.period) and not x.is_alive():
            t2=time.perf_counter()
            # print('mythread')
            x=threading.Thread(target=self.target,args=self.args)
            x.start()
            counter+=1
            print((t2-t1-counter*self.period)/t2)
    
    # def run(self):
    #     t1=time.perf_counter()
    #     # x=threading.Thread(target=self.target,args=(self.stopFlag,self.time))
    #     while not self.stopFlag.wait(self.period):
    #         t2=time.perf_counter()
    #         # print('mythread')
    #         func(self.time)
    #         print(t2-t1)
    #         t1=t2
            
def func(t):
    print('start')
    time.sleep(t)
    print('stop')
    
stopFlag=threading.Event()
thread=mythread(stopFlag,30,func,1)
thread.start()

# t1=time.perf_counter()
# def func(t,event):
#   t2=time.perf_counter()
#   if not event.is_set():
#     threading.Timer(t, func,args=(t,event)).start()
#     print('new thread')
#   print("Hello, World!")
  
#   print(t2-t1)
#   t2=t1

# func(1,stopFlag)