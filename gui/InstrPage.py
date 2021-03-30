# -*- coding: utf-8 -*-
"""
Created on Wed Jun  5 23:35:26 2019

@author: Nitzsche
"""

import inspect #for debugging
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QWidget, QAction, QAbstractSlider
from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QLabel, QMessageBox
from PyQt5.QtGui import QPalette, QBrush, QColor
from PyQt5.QtCore import QObject, QRect
import os
import io


#generic page filled with pyqt designer ui
class cInstrPage(QDialog):
    def __init__(self,parent,InstrUIFile,pos):
        #parent is the main Window (MyApp) which stores AllMyParams, for instance
        super().__init__(parent)

        self.uiFile = InstrUIFile

        InstrUI,_=uic.loadUiType(InstrUIFile)
        self.ui = InstrUI()
        self.ui.setupUi(self)
        self.parent = parent
        
        
        d,f=os.path.split(self.uiFile)
        n,e=os.path.splitext(f)
        self.setWindowTitle(n)
        
        self.setFixedSize(self.size())        
        
        self.instrList=[]
        
        
        
        #create palettes for labels (black and red)
        self.paletteRed = QPalette()
        brush = QBrush(QColor(200, 120, 120))
        brush.setStyle(Qt.SolidPattern)
        self.paletteRed.setBrush(QPalette.Active, QPalette.WindowText, brush)
        self.paletteRed.setBrush(QPalette.Inactive, QPalette.WindowText, brush)
        self.paletteRed.setBrush(QPalette.Disabled, QPalette.WindowText, brush)

        self.paletteBlack = QPalette()
        brush = QBrush(QColor(0, 0, 0))
        brush.setStyle(Qt.SolidPattern)
        self.paletteBlack.setBrush(QPalette.Active, QPalette.WindowText, brush)
        self.paletteBlack.setBrush(QPalette.Inactive, QPalette.WindowText, brush)
        self.paletteBlack.setBrush(QPalette.Disabled, QPalette.WindowText, brush)


        #find all instruments and process them
        instrWidgets = self.findChildren(QWidget)
        for i in instrWidgets:
            if self.objectName()==i.parent().objectName():
                #print(i.objectName() + ' : ' + i.parent().objectName())
                nuRInstr = nuRayInstr(i,self)
                self.instrList.append(nuRInstr)

        #contextMenu
        saveAct = QAction('Save Connections',self)
        saveAct.triggered.connect(self.save)
        self.addAction(saveAct)
        reconnAct = QAction('Reconnect All',self)
        reconnAct.triggered.connect(self.reconnectAll)
        self.addAction(reconnAct)
        self.setContextMenuPolicy(Qt.ActionsContextMenu)
        
        self.loadConnections()
        self.reconnectAll()
        
        self.move(pos)
        #self.move(20,20)

    def connFileName(self):
        d,f=os.path.split(self.uiFile)
        n,e=os.path.splitext(f)
        return d+'\\'+n+'.conn'      

    def loadConnections(self):
        if os.path.isfile(self.connFileName()):
            with io.open(self.connFileName(),'r',encoding='utf8') as f:
                conn = f.read()
            for l in conn.splitlines():
                x = l.split(':')
                #find the widget
                i=next((i for i in self.instrList if i.instrWidget.objectName()==x[0]),None)
                #if found, set ParamName
                if i:
                    i.Param=x[1]
                    i.label.setText(i.Param)
                    i.label.setPalette(self.paletteRed)

    
    def save(self):
        with io.open(self.connFileName(),'w',encoding='utf8') as f:
            for i in self.instrList:
                f.write(i.instrWidget.objectName()+':'+str(i.Param)+'\n')
        
        
    def reconnectAll(self):
        allParams = self.parent.AllMyParams#the cParamTableModel with all Parameters of type nuRayParam)
        for i in self.instrList:
            p = next((p for p in allParams.items if p.name==str(i.Param)),None)
            if p:
                i.connectToParam(p)
                
    #avoid close on ESC
    def keyPressEvent(self,event):
        if event.key()!=Qt.Key_Escape:
            super().keyPressEvent(event)
    
    def closeEvent(self,ev):
        self.save()
        ev.accept()
       
#override QListWidget to react on ESC        
class ParamSelectListWidget(QListWidget):
    def __init__(self,parent):
        super().__init__(parent)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus(Qt.OtherFocusReason)
    def keyPressEvent(self,event):
        if event.key()==Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)
        

class nuRayInstr(QObject):
    notConnected='<not connected>'
    def __init__(self,InstrWidget,InstrPage):
        super().__init__()
        self.instrWidget = InstrWidget
        self.Page = InstrPage
        self.label = QLabel('',InstrPage)
        self.label.setAlignment(Qt.AlignHCenter)
        self.centerLabel()

        self.Param=self.notConnected
        self.disconnectFromParam()

        #add slots for user input
        if isinstance(InstrWidget,QAbstractSlider):
            #print('Slider: '+InstrWidget.objectName())
            InstrWidget.sliderMoved.connect(self.valueChanged)
        InstrWidget.valueChanged.connect(self.valueChanged)

        

        #add context menu
        act = QAction("Connect to ...",InstrWidget) #parent is the instrument widget so the handler (InstrConnect) knows who triggered
        act.triggered.connect(self.InstrConnect)
        InstrWidget.addAction(act)
        InstrWidget.setContextMenuPolicy(Qt.ActionsContextMenu)
    
    def valueChanged(self):
        #print('sliderMoved to pos: '+str(self.instrWidget.sliderPosition())+' val: '+str(self.instrWidget.value()))
        #update all widgets with the same Parameter connected
        if type(self.Param)!=str:
            for i in self.Param._instrList:
                if i!=self:
                    i.instrWidget.setValue(self.instrWidget.value())
        
    def disconnectFromParam(self):
        self.Param=str(self.Param)
        self.label.setPalette(self.Page.paletteRed)
        self.label.setText(self.Param)
        
    # Conetxt Menu Handler, connect Instr to a Parameter
    def InstrConnect(self):
        if self.Page.parent.AllMyParams.rowCount(self.Page.parent) == 0:
            self.ListEmpty = QMessageBox()
            self.ListEmpty.setIcon(QMessageBox.Information)
            self.ListEmpty.setText("Please add parameters first!")
            self.ListEmpty.setInformativeText("<parameter list is empty>")
            self.ListEmpty.setWindowTitle("parameters")
            self.ListEmpty.setStandardButtons(QMessageBox.Ok)
            self.ListEmpty.show()
        self.ParamConnList = ParamSelectListWidget(self.Page)
        self.ParamConnList.itemDoubleClicked.connect(self.paramSelected)
        for i in self.Page.parent.AllMyParams.itemNames():
            self.ParamConnList.addItem(QListWidgetItem(i))
        self.ParamConnList.show()
        
    def connectToParam(self,param):
        if type(self.Param)!=str:
            self.Param.removeInstr(self)
        self.Param = param
        self.Param.addInstr(self)
        self.label.setText(self.Param.name)
        self.label.setPalette(self.Page.paletteBlack)
        
        #print(self.Param.name)
        
    def centerLabel(self):
        me = self.instrWidget.geometry()
        cx = round(me.x()+me.width()*0.5)
        y =me.y()+me.height()+2
        label = self.label.geometry()
        x = round(cx-label.width()*0.5)
        self.label.setGeometry(QRect(x,y,label.width(),label.height()))
        
        
        
    def paramSelected(self):
        param = self.Page.parent.AllMyParams.items[self.pc.currentRow()]
        self.pc.close()
        self.connectToParam(param)
        
        
        