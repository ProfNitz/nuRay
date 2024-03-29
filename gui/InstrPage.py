# -*- coding: utf-8 -*-
"""
Created on Wed Jun  5 23:35:26 2019

@author: Nitzsche
"""

import inspect #for debugging
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QDialog, QWidget, QAction, QAbstractSlider, QDoubleSpinBox
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
        self.ConnChange = False
                
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
        
    
    #NiNa: create connection file names
    def connFileName(self):
        d,f=os.path.split(self.uiFile)
        n,e=os.path.splitext(f)
        return d+'\\'+n+'.conn'      


    #NiNa: process connection files, set paramname label to instrWidget
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

    
    #NiNa: save current conncetion in conn file
    def save(self):
        with io.open(self.connFileName(),'w',encoding='utf8') as f:
            for i in self.instrList:
                if type(i.Param) != str:
                    f.write(i.instrWidget.objectName()+':'+str(i.Param)+'\n')
     
        
    #NiNa: connect instrWidgets with labels to params that are declared in red label of instrWidget   
    def reconnectAll(self):
        #the cParamTableModel with all Parameters of type nuRayParam
        allParams = self.parent.AllMyParams
        for i in self.instrList:
            p = next((p for p in allParams.items if p.name==str(i.Param)),None)
            if p:
                #NiNa: connect each instrWidget, that has a suiting param
                i.connectToParam(p)


    #avoid close on ESC
    def keyPressEvent(self,event):
        if event.key()!=Qt.Key_Escape:
            super().keyPressEvent(event)
    
    
    #NiNa: closeEvent: if a paramlabel is changed, a messagebox appears 
    def closeEvent(self,ev):
            with io.open(self.connFileName(),'r',encoding='utf8') as f:
                conn = f.read()
            for l in conn.splitlines():
                x = l.split(':')
                #find the widget
                p=next((p for p in self.instrList if p.instrWidget.objectName()==x[0]),None)
                #if found, set ParamName
                if p:
                    if str(p.Param) != x[1]:
                        #NiNa: connected param has been changed --> ConnChange = True
                        self.ConnChange = True
            if self.ConnChange == True:
                        buttonReply = QMessageBox.question(self,
                                                       'Close InstrPage',
                                                       "Do you want to save Connections before you quit?",
                                                       QMessageBox.Yes | QMessageBox.No,
                                                       QMessageBox.Yes)
                        if buttonReply == QMessageBox.Yes:
                            self.save()
                            ev.accept()
                        else:
                            ev.accept()
            else:
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
     

#NiNa: class of an instrument, child of instrPage
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
        #NiNa: list to store the initial stepvalue of widget
        self.singleStepList = []

        #add slots for user input
        if isinstance(InstrWidget,QAbstractSlider):
            InstrWidget.sliderMoved.connect(self.valueChanged)
        InstrWidget.valueChanged.connect(self.valueChanged)
        
        #add context menu
        #parent is the instrument widget so the handler (InstrConnect) knows who triggered
        act = QAction("Connect to parameter",InstrWidget)
        act.triggered.connect(self.InstrConnectParam)
        InstrWidget.addAction(act)        
        act = QAction("Disconnect",InstrWidget)
        act.triggered.connect(self.disconnectFromParam)
        InstrWidget.addAction(act)
        InstrWidget.setContextMenuPolicy(Qt.ActionsContextMenu)
        
    
    #NiNa: add valueChanged method for instrWidgets
    def valueChanged(self):
        #update all widgets with the same Parameter connected
        if type(self.Param)!=str:
            for i in self.Param._instrList:
                if i!=self:
                    i.instrWidget.setValue(self.instrWidget.value())
    
        
    #NiNa: disconnect parameter from instrument
    def disconnectFromParam(self):
        if type(self.Param) != str:    
            self.Param.removeInstr(self)
        self.Param=str(self.Param)
        self.label.setPalette(self.Page.paletteRed)
        self.label.setText(self.Param)
        
    
    #NiNa: detect if the name of a parameter has been changed
    def ParamNameChanged(self):
        self.label.setText(self.Param.name)
        
        
    # Conetxt Menu Handler, connect Instr to a Parameter
    def InstrConnectParam(self):
        #NiNa: if there arent any params: QMessageBox
        if self.Page.parent.AllMyParams.rowCount(self.Page.parent) == 0:
            self.ListEmpty = QMessageBox()
            self.ListEmpty.setIcon(QMessageBox.Information)
            self.ListEmpty.setText("Please add parameters first!")
            self.ListEmpty.setInformativeText("<parameter list is empty>")
            self.ListEmpty.setWindowTitle("parameters")
            self.ListEmpty.setStandardButtons(QMessageBox.Ok)
            self.ListEmpty.show()
        #NiNa: show list of existing params, if doubleclicked connect to param
        else:
            self.ParamConnList = ParamSelectListWidget(self.Page)
            self.ParamConnList.itemDoubleClicked.connect(self.paramSelected)
            for i in self.Page.parent.AllMyParams.itemNames():
                self.ParamConnList.addItem(QListWidgetItem(i))
            self.ParamConnList.show()
    
        
    #NiNa: connection to parameter, turn label black and set paramname, take min and max val of param, ...
    def connectToParam(self,param):
        if type(self.Param)!=str:
            self.Param.removeInstr(self)
        self.Param = param
        self.Param.addInstr(self)
        self.label.setText(self.Param.name)
        self.label.setPalette(self.Page.paletteBlack)
        self.instrWidget.blockSignals(True)
        self.instrWidget.setMinimum(self.Param.min)
        self.instrWidget.setMaximum(self.Param.max)
        self.instrWidget.blockSignals(False)
        if self.Param.paramset == 0:
            self.instrWidget.setValue(self.Param.valset0)
        if self.Param.paramset == 1:
            self.instrWidget.setValue(self.Param.valset1)
        if isinstance(self.instrWidget,QDoubleSpinBox):
            #NiNa: store the stepvalue of instrument (set on QtDesigner)
            self.singleStepList.append(self.instrWidget.singleStep())
            if not self.Param.dataType == 'float32':
                #NiNa: set stepvalue to 1 if type isn't float
                self.instrWidget.setSingleStep(1)
            else:
                #NiNa: take initial stepvalue (set on QtDesigner) if float
                self.instrWidget.setSingleStep(self.singleStepList[0])
        #NiNa: keep parameterdata updated 
        self.instrWidget.valueChanged.connect(self.setParamVal) 
        if self.Page.parent.ParamSettingsDialog != None:
            self.Page.parent.ParamSettingsDialog.activateWindow()
        self.Page.activateWindow()
    
        
    #NiNa:position of paramlabel of the instruments
    def centerLabel(self):
        me = self.instrWidget.geometry()
        cx = round(me.x()+me.width()*0.5)
        y =me.y()+me.height()+2
        label = self.label.geometry()
        x = round(cx-label.width()*0.5)
        self.label.setGeometry(QRect(x-20,y,label.width()+40,label.height()))

    
    #NiNa: if a parameter from ParamConnList is selected: connect instrument to param and close the ParamConnList
    def paramSelected(self):
        param = self.Page.parent.AllMyParams.items[self.ParamConnList.currentRow()]
        self.ParamConnList.close()
        self.connectToParam(param)
        
        
    #NiNa: if the value of the instrument changes, the connected parameter value is changed as well    
    def setParamVal(self):
        if type(self.Param) != str:
            self.Param.val = self.instrWidget.value()
            if self.Param.paramset == 0:
                self.Param.valset0 = self.Param.val
            if self.Param.paramset == 1:
                self.Param.valset1 = self.Param.val
                

    #NiNa: writing Data is active, nuRay is Master and instruments are ready to send data to controller           
    def WriteData(self):
        try:
            print("SCHREIBEN")
            self.instrWidget.valueChanged.connect(self.setParamVal)
            if isinstance(self.instrWidget,QDoubleSpinBox):
                self.instrWidget.setKeyboardTracking(False)
                self.instrWidget.valueChanged.connect(self.sendVal)
            else:
                self.instrWidget.valueChanged.connect(self.sendVal)
        except:
            self.Page.parent.radioButtonDisconnect.click()


    #NiNa: instruments are connected to sending Value
    def sendVal(self):
            try:
                if not self.Param.dataType == 'float32':
                    self.Param.val = int(self.Param.val)
                print(self.Param.val)
                self.livesend.write(1,self.Param.paramset,self.Param.paramnr,self.Param.val,self.Param.dataType)  
            except AttributeError:
                print("<offline>")
            except:
                self.Page.parent.radioButtonDisconnect.click()

             
        
        