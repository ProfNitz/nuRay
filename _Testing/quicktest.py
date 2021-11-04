# -*- coding: utf-8 -*-
"""
Created on Mon Jul  5 15:34:19 2021

@author: Nithu
"""

from Comm.nuRSerialConn import nuRSerial
serial = nuRSerial()
serial.port = 'COM6'
serial.connect()
serial.write(1,1,23,2135,'float32')
serial.close()