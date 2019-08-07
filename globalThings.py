# -*- coding: utf-8 -*-
"""
Created on Tue Jun 25 13:10:00 2019

@author: Nitzsche
"""

# do not import as "from globalThings import xyz", just do "import globalThings as G" and subsequent "G.xyz"
# this is espacially important for nuRDir, which changes during run time


#these are the supported datatypes of params and signals
#this should be the only place where you make changes

#Names in mRay as keys, corresponding length in bytes, corresponding C-Type
nuRDataTypes={'float32':{'len':4,'ctype':'float','packtype':'f'},
    'uint8':{'len':1,'ctype':'uint8_t','packtype':'B'},
    'int16':{'len':2,'ctype':'int16_t','packtype':'H'}}

# here the main module will store its directory, so other modules can
# look for their stuff there
nuRDir = ''

nuRPlatforms = {'Arduino Serial':{'code_template':'nuRay_arduino_serial.c'}}


