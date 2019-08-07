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
    s.write(12,125,'float32')
    s.close()
    