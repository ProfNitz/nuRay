# -*- coding: utf-8 -*-
"""
Created on Wed Jul  3 17:17:10 2019

@author: Nitzsche
"""

import serial
import serial.tools.list_ports

class nuRSerial(object):
    @classmethod
    def listPorts(cls):
        all_ports = serial.tools.list_ports.comports()
        for c in all_ports:
            print(c)
