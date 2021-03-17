# -*- coding: utf-8 -*-
"""
Created on Fri Jul 12 11:06:43 2019

@author: Nitzsche
"""

import struct

from globalThings import nuRDataTypes

class nuRLL(object):
    @classmethod
    def pack(cls,cmd,val,data_type):
        #format:
        # = .. no alignment (for instance floats would otherwise be aligend to multiples of 4 by padding)
        # H .. uint16
        # packtype is either f, B, or h (see gloalThings.py)
        buf = struct.pack('=H'+nuRDataTypes[data_type]['packtype'],cmd,val)
        chk=0;
        for b in buf:
            chk+=b
        chk = chk&0xff #lsb
        
        # pack again, now with chk, len, and STOPFLAG (0xff) (therefor '3B'..3 times uint8)
        return struct.pack('=H'+nuRDataTypes[data_type]['packtype']+'3B',
                           cmd,val,chk,2+nuRDataTypes[data_type]['len'],0xff)
    