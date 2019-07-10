# -*- coding: utf-8 -*-
"""
Created on Tue Jun 25 13:10:00 2019

@author: Nitzsche
"""

#these are the supported datatypes of params and signals
#this should be the only place where you make changes

#Names in mRay as keys, corresponding length in bytes, corresponding C-Type
nuRDataTypes={'float32':{'len':4,'ctype':'float'},
    'uint8':{'len':1,'ctype':'uint8_t'},
    'int16':{'len':2,'ctype':'int16_t'}}

# here the main module will store its directory, so other modules can
# look for their stuff there
nuRDir = ''

nuRPlatforms = {'Arduino Serial':{'code_template':'nuRay_arduino_serial.c'}}


