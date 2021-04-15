# -*- coding: utf-8 -*-
"""
Created on Wed Jul  3 17:17:10 2019

@author: Nitzsche
"""

import serial
import serial.tools.list_ports

from Comm.nuRLL import nuRLL

class nuRSerial(object):
    def __init__(self):
        self.s = None
        self.port = None
        
    def connect(self):
        print('connected')
        self.s=serial.Serial(port=self.port,baudrate=115200)
        pass

    def write(self,cmd,val,dt):
        buf = nuRLL.pack(cmd,val,dt)
        self.s.write(buf)
        
    def is_open(self):
        return self.s.is_open()
    
    def close(self):
        self.s.close()

    @classmethod
    def listPorts(cls):
        all_ports = serial.tools.list_ports.comports()
        for c in all_ports:
            print(c)
        return [str(c) for c in all_ports]

