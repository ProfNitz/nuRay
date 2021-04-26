# -*- coding: utf-8 -*-
"""
Created on Mon Jul 15 16:55:56 2019

@author: Nitzsche
"""
from Comm.nuRSerialConn import nuRSerial

#for testing
if __name__=='__main__':
    nuRSerial.listPorts()
    s = nuRSerial()
    s.port='COM8'
    s.connect()
    s.write(1,0,0,'uint8')#a first package, which will be ignored because no preceding 0xff
    #a simple example
    s.write(0,1,-125,'float32')
    # a tricky example, because payload contains stopflag 0xff
    s.write(1,2,3.57331108403e-43,'float32')
    # another tricky example, because payload contains startflag 0xffe
    s.write(1,2,9.11180313443e-41,'float32')
    
    for k in range(30):
        s.write(1,0,k,'float32')
    
    s.write(1,1,12345,'int16')
    s.write(0,1,-12345,'int16')
    s.write(1,1,5,'uint8')
    
    s.close()
    