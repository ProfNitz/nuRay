# -*- coding: utf-8 -*-
"""
Created on Thu May 13 17:27:50 2021

@author: Nithu
"""

import serial

arduinoNano = serial.Serial('COM7',115200)

def led_On():
    arduinoNano.write(b'1')
    print("1 has been sent to arduino")

def led_Off():
    arduinoNano.write(b'0')
    print("0 has been sent to arduino")
    
led_On()


    