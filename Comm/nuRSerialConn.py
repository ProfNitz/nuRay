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
        self.s.timeout = 2
        #self.s.xonxoff = False
        #self.s.rtscts = None
        #self.s.dtr = None
        #self.s.setRTS(True)
        #self.s.dsrdtr = None
        #self.s.rtscts = None
        #self.s.dtr = None
        #self.s.rts = None
        #self.s.setDTR(False)
        #self.s.timeout = 2
        #self.s.timeout = 1
        #self.s.setDTR(False)
        #print(self.s._dtr_state)
        #self.s.rtscts = False
        #self.s.dsrdtr = None
        #print(self.s._dsrdtr)
        #self.s.dtr = False
        #self.s.rts = False
        #print(self.s.dtr)
        #print(self.s.rts)
        #self.s.rtscts = True
        #self.s.dsrdtr = None
        #self.s.setDTR(1)
        #self.s.setRTS(1)
        
        #self.s.rtscts = False
        #self.s.dsrdtr = None
        self.s.setDTR(0)
        #self.s.setRTS(0)
        #self.s._dsrdtr = False
        #self.s._rtscts = False
        
        #print(self.s.dtr)
        #print(self.s._dtr_state)
        #print(self.s._dsrdtr)
        #print(self.s.rts)
        #print(self.s._rts_state)
        #print(self.s._rtscts)
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
    
    def read(self,bytestoread):
        return self.s.read(bytestoread)
    
    def readline(self):
        return self.s.readline()
        
    def is_open(self):
        return self.s.is_open
    
    def in_waiting(self):
        return self.s.in_waiting
    def flushInput(self):
        return self.s.flushInput()
    
    def close(self):
        self.s.close()

    @classmethod
    def listPorts(cls):
        all_ports = serial.tools.list_ports.comports()
        for c in all_ports:
            print(c)
        return [str(c) for c in all_ports]

