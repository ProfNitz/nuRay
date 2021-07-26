# -*- coding: utf-8 -*-
"""
Created on Wed Jul  3 17:17:10 2019

@author: Nitzsche
"""

import serial
import serial.tools.list_ports

from Comm.nuRLL import nuRLL


#NiNa: class for serial Communication between nuRay and controller
class nuRSerial(object):
    def __init__(self):
        self.s = None
        self.port = None
    
        
    #NiNa: initialize serial port, baudrate, timeout, dataterminalready, ...
    def connect(self):
        self.s = serial.Serial()
        self.s.port = self.port
        self.s.baudrate = 115200
        self.s.timeout = 2
        self.s.dtr = False
        try:
            self.s.open()
        except:
            self.s.port = None
        pass
   
    #NiNa: write to controller with defined pack in nuRLL.py
    def write(self,rw,pset,pidx,val,dt):
        buf = nuRLL.pack(((rw<<3)+(pset<<2)+(pidx<<4)),val,dt)
        print(buf)
        self.s.write(buf)
    
    #NiNa: read a set number of incoming bytes
    def read(self,bytestoread):
        return self.s.read(bytestoread)
    
    #NiNa: read an incoming line 
    def readline(self):
        return self.s.readline()
    
    #NiNa: return True if the serial port is open and ready to receive data    
    def is_open(self):
        return self.s.is_open
    
    #NiNa: close the serial port
    def close(self):
        self.s.close()

    #NiNa: list all available ports
    @classmethod
    def listPorts(cls):
        all_ports = serial.tools.list_ports.comports()
        for c in all_ports:
            print(c)
        return [str(c) for c in all_ports]

