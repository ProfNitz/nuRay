# -*- coding: utf-8 -*-
"""
Created on Wed Apr 28 21:32:03 2021

@author: Nithu
"""
import json
from Comm.nuRSerialConn import nuRSerial
import datetime as dtime
import random
import numpy as np
from PyQt5.QtWidgets import QFileDialog, QWidget


time_script_run = dtime.datetime.now().strftime('%d-%m-%Y %H-%M-%S')

def GenerateData(parametercount,valrange):
    i = 0
    setidx = []
    paramname = []
    val = []
    datatype = []
    while i < parametercount:
        i += 1
        j = random.randint(0,1)
        randomgenerator = random.randint(1,3)
        if randomgenerator == 1:
            k = np.float32(np.random.random())
        if randomgenerator == 2:
            k = np.uint8(np.random.randint(0,1000))
        if randomgenerator == 3:
            k = np.int16(np.random.randint(-valrange,valrange))
        l = k.item()
        paramname.append(i)
        setidx.append(j)
        val.append(l)
        datatype.append(str(k.dtype))
    inputdata = {'setidx':setidx,'pidx':paramname,'val':val,'dt':datatype}
    with open('testdata_{}.json'.format(time_script_run), 'w') as f:
        json.dump(inputdata,f, indent=2)

def GenerateAndTest(parametercount,valrange):
    GenerateData(parametercount,valrange)
    with open('testdata_{}.json'.format(time_script_run),'r') as g:
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

def TestExistingFile():
    class App(QWidget):
        def __init__(self):
            super().__init__()
            self.openFileNameDialog()   
        def openFileNameDialog(self):
            fileName, _ = QFileDialog.getOpenFileName(self,"Select Json File", "","json files (*.json)")
            if fileName:
                with open(fileName,'r') as g:
                    inputdata = json.load(g)
                if __name__=='__main__':
                    nuRSerial.listPorts()
                    s = nuRSerial()
                    s.port='COM8'
                    s.connect()
                    i = 0
                    parametercount = len(inputdata['setidx'])
                    while i < parametercount:
                        setidx = inputdata['setidx'][i]
                        pidx = inputdata['pidx'][i]
                        val = inputdata['val'][i]
                        dt = inputdata['dt'][i]
                        s.write(setidx,pidx,val,dt)
                        i += 1
                    s.close() 
    if __name__ == '__main__':
        ex = App()
        ex.close()  

#TestData(300,300000)
#GenerateAndTest(300,300000)
#TestExistingFile()
nuRSerial.listPorts()
s = nuRSerial()
s.port='COM7'
s.connect()
s.write(0,0,0,'uint8')
s.write(1,24,121,'uint8')
s.close()