# -*- coding: utf-8 -*-
"""
Created on Wed Apr 28 21:32:03 2021

@author: Nithu
"""
import json
from Comm.nuRSerialConn import nuRSerial
from Testing.testdatagenerator import generate

def Test(parametercount,valrange):
    generate(parametercount,valrange)
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

Test(200,30000)