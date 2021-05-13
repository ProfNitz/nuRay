# -*- coding: utf-8 -*-
"""
Created on Thu May 13 17:27:50 2021

@author: Nithu
"""

import serial
import time

arduinoNano = serial.Serial('COM10',115200)

def led_On():
    time.sleep(3)
    arduinoNano.write(b'1')
    print("1 has been sent to arduino")

def led_Off():
    time.sleep(3)
    arduinoNano.write(b'0')
    print("0 has been sent to arduino")
    
led_On()


    