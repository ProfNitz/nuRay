# -*- coding: utf-8 -*-
"""
Created on Mon Jul  5 15:34:19 2021

@author: Nithu
"""

from Comm.nuRSerialConn import nuRSerial
serial = nuRSerial()
serial.port = 'COM6'
serial.connect()
i = 0
k = 0
while i < 400:
    serial.write(1,1,1,i,'float32')
    x = serial.read(1)
    y = int.from_bytes(x, "big")
    print(y)
    if not y == 6:
        print(k)
    i += 0.25
    k += 7
serial.close()