# -*- coding: utf-8 -*-
"""
Created on Thu Jun  6 00:04:08 2019

@author: Nitzsche
"""

from PyQt5.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout, QPushButton
from PyQt5.QtCore import QTimer, QObject
import pyqtgraph as pg
import random
import numpy as np
import time

class nuRLine(QObject):
    def __init__(self,pw,color):
        super().__init__()
        self.DataItem = pw.plot(clickable=True) #empty plot in PlotWidget pw
        self.DataItem.curve.setClickable(True)
        self.DataItem.setPen(color)
        self.DataItem.sigClicked.connect(self.clicked)
#        self.DataItem.sigClicked.connect(lambda: print('clicked'))
    def clicked(self):
        print('clicked line')

class myPlotW(pg.PlotWidget):
    def contextMenuEvent(self,event):
        super().contextMenuEvent(event)
        #tried to add my own actions, no succes so far

class cPlotterWindow(QDialog):
    def __init__(self,parent):
        super().__init__(parent)
        
        
        self.layout = QHBoxLayout()
        self.toolsLayout=QVBoxLayout()

        buStart=QPushButton('Start')
        buStart.setMinimumWidth(200)
        buStart.setEnabled(True)
        buStart.pressed.connect(self.Start)
        self.toolsLayout.addWidget(buStart)
        self.buStart = buStart

        buStop=QPushButton('Stop')
        buStop.setMinimumWidth(200)
        buStop.setEnabled(False)
        buStop.pressed.connect(self.Stop)
        self.toolsLayout.addWidget(buStop)
        self.buStop=buStop
        
        self.toolsLayout.addStretch(1)
        
        
        self.resize(900,600)
        
        self.plotWidget = myPlotW(self)
        #self.plotWidget.setGeometry(5,5,700,490)
        self.plotWidget.show()
        self.plotWidget.showButtons()#Autoscale at bottom left
        self.plotWidget.showGrid(x=True,y=True,alpha=1)
        self.plotWidget.setLabel('bottom', 'Time', units='s')

        
        self.layout.addWidget(self.plotWidget)
        self.layout.addLayout(self.toolsLayout)
        self.setLayout(self.layout)
        
                
        self.setMinimumSize(500,200)
        
        
    def timerHandler(self):
#        t=time.time()
#        print(t-self.tStart)
#        self.tStart=t
        self.line.DataItem.setData(self.x[self.cnt:self.cnt+10000],self.y[self.cnt:self.cnt+10000])
        self.cnt+=10
        if self.cnt==10000:
            self.cnt=0
            print('overflow')
        if self.online:
            self.timer.start(0)
        
    def Start(self):
        self.online=True
        self.cnt=0;
        self.tStart=time.time()
        self.x=[x/10000*5 for x in range(0,20000)]
        self.y=[np.sin(x*2*np.pi*2) for x in self.x];
        self.line = nuRLine(self.plotWidget,(255,255,0))
        self.buStart.setEnabled(False)
        self.buStop.setEnabled(True)
        self.timer=QTimer()
        self.timer.timeout.connect(self.timerHandler)
        self.timer.setSingleShot(True)
        self.timer.start()
        
#        for i in range(0,1000):
#            line.DataItem.setData(y[i:9999+i])
        
    def Stop(self):
        self.online=False
        self.buStart.setEnabled(True)
        self.buStop.setEnabled(False)
        self.plotWidget.getPlotItem().removeItem(self.line.DataItem)#use clear for all items
        
        