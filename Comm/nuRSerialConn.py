# -*- coding: utf-8 -*-
"""
Created on Wed Jul  3 17:17:10 2019

@author: Nitzsche
"""

import serial
import serial.tools.list_ports
from Comm.nuRLL import nuRLL
import time

class nuRSerial(object):
    def __init__(self):
        self.s = None
        self.port = None
        
    def connect(self):
        self.s = serial.Serial()
        self.s.port = self.port
        self.s.baudrate = 115200
        #self.s.timeout = 1
        self.s.setDTR(False)
        try:
            self.s.open()
        except:
            self.s.port = None
        #print('connected')
        #self.s=serial.Serial(port=self.port,baudrate=115200,rtscts = True, dsrdtr = True, xonxoff = True)
        pass
    
    def write(self,rw,pset,pidx,val,dt):
        buf = nuRLL.pack(((rw<<3)+(pset<<2)+(pidx<<4)),val,dt)
        print(buf)
        self.s.write(buf)
    
    def read(self):
        self.s.read(4)
        
    def is_open(self):
        return self.s.is_open
    
    def close(self):
        self.s.close()

    @classmethod
    def listPorts(cls):
        all_ports = serial.tools.list_ports.comports()
        for c in all_ports:
            print(c)
        return [str(c) for c in all_ports]

