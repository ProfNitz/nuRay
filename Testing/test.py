# -*- coding: utf-8 -*-
"""
Created on Wed Apr 28 21:32:03 2021

@author: Nithu
"""
import json
from Comm.nuRSerialConn import nuRSerial
from testdatagenerator import generate

def Test(parametercount):
    generate(parametercount)
    with open ('testdata.json','r') as g:
        inputdata = json.load(g)
    if __name__=='__main__':
        nuRSerial.listPorts()
        s = nuRSerial()
        s.port='COM8'
        s.connect()
        i = 0
        while i < parametercount:
            setidx = inputdata['setidx'][i]
            pidx = inputdata['pidx'][i]
            val = inputdata['val'][i]
            dt = inputdata['dt'][i]
            s.write(setidx,pidx,val,dt)
            i += 1
        s.close()

#Test(7)