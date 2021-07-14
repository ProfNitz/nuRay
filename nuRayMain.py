# -*- coding: utf-8 -*-
"""
Created on Thu May 30 12:32:24 2019

@author: Nitzsche
"""

import sys
import os
import io
import inspect #for debugging
from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QMessageBox, QDialog, QLabel, QAbstractButton, QPushButton
from PyQt5.QtCore import QPoint,Qt,QTimer
import re
import time
import struct


#my own modules 
from gui.InstrPage import cInstrPage
from gui.ParamView import ParamSettingsWindow, SignalSettingsWindow
from gui.PlotWin import cPlotterWindow
from paramModel import cParamTableModel, cSignalTableModel, ParamSelectWindow
from CodeGen.codegen import nuRCodeGenerator
from Comm.nuRSerialConn import nuRSerial
import globalThings as G
from gui.SwitchCustomWidget import CustomSwitch, statusLED


#NoNi: load main window ui from QtDesigner file
nuRMainWindow, QtBaseClass = uic.loadUiType("nuRMainWindow.ui")
nuRConnSetDialogUi, QtBaseClass = uic.loadUiType("nuRConnSettingsDialog.ui")
       
#NoNi: get directory of this python file, here other modules will look for their stuff
G.nuRDir,_ = os.path.split(__file__)

class nuRConnSettingsDialog(QDialog, nuRConnSetDialogUi):
    def __init__(self,parent):
        QDialog.__init__(self)
        nuRConnSetDialogUi.__init__(self)
        self.parent = parent
        self.setupUi(self)
        c_long = nuRSerial.listPorts()
        #print(c_long)
        # NoNi: + concatenates lists;
        # so we get an empty item [' '] and everthing from c_long
        self.comboBox.addItems([' ']+c_long)
        #c_short = [re.findall('^COM\d+',c)[0] for c in c_long]
        c_short = []
        c_short = [re.findall('^COM\d+',c)[0] for c in c_long if "COM" in c]
        c_short = [re.findall('^/dev\S+',c)[0] for c in c_long if "/dev" in c]
        #print(c_short)
        #c_short = []
        if self.parent.Serial.port in c_short:
            idx = c_short.index(self.parent.Serial.port)
            # NoNi: idx is index into c_short. comboBox, however, has an extra empty
            # item at idx = 0
            self.comboBox.setCurrentIndex(idx+1)
        #NoNi: connect method setPort to the event currentIndexChanged
        self.comboBox.currentIndexChanged.connect(self.setPort)
        self.show()

    
    def setPort(self):
        c = self.comboBox.currentText()
        #if c == " ":
           # self.parent.radioButtonDisconnect.click()
        try:
            self.parent.Serial.port = re.findall('^COM\d+',c)[0] 
            #self.parent.Serial.port = c_port
        except:
            try:
                self.parent.Serial.port = re.findall('^/dev\S+',c)[0]
            except:
                self.parent.Serial.port = None;
                self.parent.radioButtonDisconnect.click()
        print(str(self.parent.Serial.port)+' selected.')
        self.parent.LEDLabel.setText(str(self.parent.Serial.port))
        self.close()

 
class MyApp(QMainWindow, nuRMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        nuRMainWindow.__init__(self)
        self.setupUi(self)
        
        #NoNi: register all actions (Menu and Connect/Disconnect)
        self.actionOpen_Instruments.triggered.connect(self.OpenInstr)
        self.actionParameters.triggered.connect(self.ParamSettings)
        self.actionSignals.triggered.connect(self.SignalSettings)
        self.actionOpen_Plotter.triggered.connect(self.OpenPlotter)
        
        self.actionSave.triggered.connect(self.SaveProject)
        self.actionSave_As.triggered.connect(self.SaveProjectAs)
        self.actionOpen.triggered.connect(self.OpenProject)
        self.actionGenerate_Code.triggered.connect(self.CodeGen)
        
        self.actionParameters_2.triggered.connect(self.ParamSettings)
        self.actionSave_Parameters.triggered.connect(self.SaveParams)
        self.actionLoad_Parameters.triggered.connect(self.ParamSelectWindow)
        #self.actionGenerate_Parameters.triggered.connect(self.GenerateParams)
        
        self.actionClose_Project.triggered.connect(self.closeEverything)
        
        self.actionConnection_Settings.triggered.connect(self.ConnSettings)
        self.ConnSetDlg = None
        
        
        self.radioButtonConnect.clicked.connect(self.Connect)
        self.radioButtonDisconnect.clicked.connect(self.Disconnect)
        self.connected = False
        self.radioButtonDisconnect.setChecked(True)
        
        self.ActiveSet = CustomSwitch("SET0","SET1")
        self.SyncedSet = CustomSwitch("SET0","SET1")
        self.nuRayIsMaster = False
        self.muConIsMaster = True
        self.syncset = 0
        self.ActiveSet.setDisabled(True)
                            
        self.ActiveSetSwitch.addWidget(self.ActiveSet)
        self.SyncedSetSwitch.addWidget(self.SyncedSet)
        #self.syncDirection.addWidget(self.SyncDir)
        
        self.ActiveSet.clicked.connect(self.ActivateSet)
        self.SyncedSet.clicked.connect(self.SyncSet)
        #self.SyncDir.clicked.connect(self.changeSyncDir)
        
        self.statusLED = statusLED(self)
        self.ConnectionStatus.addWidget(self.statusLED)
        
        self.LEDLabel = QLabel()
        self.ConnectionStatus.addWidget(self.LEDLabel)
             
        #self.ChangeSet.clicked.connect(self.SyncSet)              
            
        #NoNi: keep track of the open child windows
        #NoNi: we can have several InstrPages and several Plotters...        
        self.InstrPageList=[]
        self.PlotterList=[]
        #NoNi: ...but only one Params and one Signals Page
        self.ParamSettingsDialog = None
        self.SignalSettingsDialog = None
        self.ConnSetDlg = None
                

        self.projectFile = 'untitled Project'
        self.paramFile = 'untitled Params'
        self.setTitle()
        
        self.AllMyParams = cParamTableModel(None) #table model so it can be processed by QTableView
        self.AllMySignals = cSignalTableModel(None)
        self.Serial = nuRSerial()

        
        
        #self.AllMyParams.dataChanged.emit(index_1,index_2,[Qt.DisplayRole])
               
             
    def Connect(self):   
        if not self.connected:
            self.Serial.connect()
            if self.Serial.is_open():
                self.ActiveSet.setDisabled(False)
                #for i in self.InstrPageList:
                   # for x in i.instrList:
                     #   x.instrWidget.setEnabled(True)
                self.statusLED.ledcolor = Qt.green
                self.statusLED.repaint()
                self.connected=True
                self.Serial.write(1,1,29,255,'uint8')         
                self.ReadActiveSet() 
                self.ReadDataFromMuCon() 
                self.SyncInstr()
                self.WriteDataToMuCon()                
            else:
                PortInfo = QMessageBox.information(self,
                                                     'No valid port chosen.',
                                                     'Please choose port first!',
                                                     QMessageBox.Ok)
                if self.ConnSetDlg == None:
                    self.radioButtonDisconnect.click()
                    self.ConnSettings()
                else:
                    self.radioButtonDisconnect.click()
                    self.ConnSetDlg.show()             
        pass
        
    def Disconnect(self):
        #for i in self.InstrPageList:
            #for x in i.instrList:
               # x.instrWidget.setEnabled(False)
        self.ActiveSet.setDisabled(True)
        self.statusLED.ledcolor = Qt.red
        self.statusLED.repaint()
        if self.connected:
            self.Serial.close()
        print("disconnected")   
        self.connected = False
        if self.Serial.is_open():
            print('noch offen')
 
    def SyncSet(self):
        if self.SyncedSet.isChecked():
            print("SET1 is selected.")
            self.syncset = 1
            for x in self.AllMyParams.items:
                x.paramset = 1
        else:
            print("SET0 is selected.")
            self.syncset = 0
            for x in self.AllMyParams.items:
                x.paramset = 0
        self.SyncInstr()

                
    def ActivateSet(self):
        try:
            if self.ActiveSet.isChecked():
                self.Serial.write(1,1,0,1,'ctrl')
                print('SET1 is active')
            else:
                self.Serial.write(1,1,0,0,'ctrl')
                print('SET0 is active') 
        except:
            self.radioButtonDisconnect.click()


    def SyncInstr(self):
        for i in self.InstrPageList:
            for x in i.instrList:
                if type(x.Param) != str:
                    if self.syncset == 0:
                        if not x.Param.dataType == 'float32':
                            x.Param.valset0 = int(x.Param.valset0)
                        x.instrWidget.setValue(x.Param.valset0)
                    if self.syncset == 1:
                        if not x.Param.dataType == 'float32':
                            x.Param.valset1 = int(x.Param.valset1)
                        x.instrWidget.setValue(x.Param.valset1)

    def WriteDataToMuCon(self):
     try:
        for i in self.InstrPageList:
            for x in i.instrList:
                if type(x.Param) != str:
                    x.WriteData()
     except:
         self.radioButtonDisconnect.click()
       
    def ReadActiveSet(self):     
        self.Serial.write(0,1,0,0,'ctrl')
        self.readActiveB = self.Serial.read(1)
        print(self.readActiveB)
        if self.readActiveB == b'':
            self.radioButtonDisconnect.click()
        else:
            self.readActive = int.from_bytes(self.readActiveB,"big")
            print("Auf Arduino ist grad SET " + str(self.readActive) + " aktiv.")
            if self.readActive == 1 and not self.ActiveSet.isChecked() or self.readActive == 0 and self.ActiveSet.isChecked():
                self.ActiveSet.click()
        
    def ReadDataFromMuCon(self):          
        for x in self.AllMyParams.items:
            k = 0
            while k < 2:
                self.Serial.write(0,k,x.paramnr,0,x.dataType)
                if x.dataType == 'float32':
                    y = self.Serial.read(4)
                    [z] = struct.unpack('<f', y)
                if x.dataType == 'int16':
                    y = self.Serial.read(2)
                    z = int.from_bytes(y, "big")
                if x.dataType == 'uint8':
                    y = self.Serial.read(1)
                    z = int.from_bytes(y, "big")
                if k == 0:
                    x.valset0 = z
                if k == 1:
                    x.valset1 = z
                k += 1
        
    #NoNi: first rudimental reaction on Connection settings
    def ConnSettings(self):
        if self.ConnSetDlg == None:
            self.ConnSetDlg = nuRConnSettingsDialog(self)
        else:
            self.ConnSetDlg.show()

        
        
    def CodeGen(self):
        if self.projectFile=='untitled Project':
            buttonReply = QMessageBox.information(self,
                                   'Code Gen',
                                   "Please save your project first!",
                                   QMessageBox.Ok)
        else:
            d,f=os.path.split(self.projectFile)
            nuRCodeGenerator.genCode(d,self.AllMyParams.items,self.AllMySignals.items)

                

    def projectName(self):
        d,f=os.path.split(self.projectFile)
        n,e=os.path.splitext(f)
        return n
    
    def paramName(self):
        d,f=os.path.split(self.projectFile)
        n,e=os.path.splitext(f)
        return n
        
    def setTitle(self):
            self.setWindowTitle('nuRay - '+self.projectName())
            
        
    def SaveProjectAs(self):
        file,_ = QFileDialog.getSaveFileName(self,
                                             "Save Project As",
                                             "",
                                             "nuRay Project (*.nrpr);;All Files (*)")
        if file:
            print(file)
            self.projectFile = file
            self.setTitle()
            self.SaveProject()
        
    def SaveProject(self):
        if self.projectFile=='untitled Project':
            self.SaveProjectAs()
        else:
            with io.open(self.projectFile,'w',encoding='utf8') as f:
                f.write(self.AllMyParams.save())
                f.write(self.AllMySignals.save())
                f.write(self.saveInstrPages())
                #f.write(self.saveSyncedSet())
                
    def SaveParamsAs(self):
        file,_ = QFileDialog.getSaveFileName(self,
                                             "Save Params As",
                                             "("+str(self.syncset)+')',
                                             "nuRay Params (*.nrpa);;All Files(*)")
        if file:
            print(file)
            self.paramFile = file
            #self.setTitle()
            self.SaveParams()
            
    def SaveParams(self):
        if self.paramFile == 'untitled Params':
            self.SaveParamsAs()
        else:
            with io.open(self.paramFile,'w',encoding = 'utf8') as f:
                f.write(self.AllMyParams.saveP())
            
                
    def saveInstrPages(self):
        res='<Instrument Pages>\n'
        #clean up list first
        self.InstrPageList[:]=[x for x in self.InstrPageList if x.isVisible()]
        for p in self.InstrPageList:
            pos = p.pos()
            abspath = p.uiFile
            start =  os.getcwd()           
            res+=os.path.relpath(abspath,start) +';'+str(pos.x())+';'+str(pos.y())+'\n'
        res+='<\Instrument Pages>\n'
        print (res)
        return res
            
    def loadInstrPages(self,txt):
        #process <Instrument Pages>-tag from project file and open them all
        #cwd = os.getcwd()
        myr = re.compile(r'<Instrument Pages>\n(.+)<\\Instrument Pages>',re.DOTALL)#the dot also matches newlines
        res=myr.search(txt)
        if res:
            pageSettings = res.group(1)
            print(pageSettings)
            for l in pageSettings.splitlines():
                ps = l.split(';')
                try:
                    self.loadInstrPage(ps[0],QPoint(int(ps[1]),int(ps[2])))
                except FileNotFoundError:
                    try:
                        psmacOs = ps[0].replace("\\","/")
                        self.loadInstrPage(psmacOs,QPoint(int(ps[1]),int(ps[2])))
                    except FileNotFoundError:
                        _,fn=os.path.split(ps[0])
                        SearchInfo = QMessageBox.information(self,
                                                             'File '+ fn +' not found',
                                                             'Project wants to open the Instrument Page:\n\n'+
                                                             fn+
                                                             '\n\nPlease help to find this file!',
                                                             QMessageBox.Ok)
                        self.OpenInstr()
                            
    def OpenProject(self):
        file,_ = QFileDialog.getOpenFileName(self,
                                             "Open Project",
                                             "",
                                             "nuRay Project (*.nrpr);;All Files (*)")
        if file:
            self.projectFile = file
            with io.open(file,'r',encoding='utf8') as f:
                projSet=f.read()
                
            self.AllMyParams.load(projSet)
            self.ParamSettings()
            self.AllMySignals.load(projSet)
            self.loadInstrPages(projSet)
            #self.loadSyncedSet(projSet)
            self.setTitle()            
        
    def ParamSelectWindow(self):
        file,_ = QFileDialog.getOpenFileNames(self,
                                              "Load Parameters",
                                              "",
                                              "nuRay Params (*.nrpa);;All Files (*)")
        if file:
            self.paramFile = file[0]
            print(self.paramFile)
            with io.open(self.paramFile,'r',encoding='utf8') as f:
                paramSet = f.read()
            #self.radioButtonDisconnect.click()
            self.paramnamelist = self.AllMyParams.loadList(paramSet)[0]
            self.valuelist = self.AllMyParams.loadList(paramSet)[1]
            self.ParamNameListWindow = ParamSelectWindow(self,self.paramnamelist,self.valuelist)
            self.ParamNameListWindow.show()
            for i in range(0,len(self.ParamNameListWindow.checkboxlist)):
                if self.ParamNameListWindow.checkboxlist[i].text() in [i.name for i in self.AllMyParams.items]:
                    self.ParamNameListWindow.checkboxlist[i].setChecked(True)

    def LoadParams(self):
            with io.open(self.paramFile,'r',encoding='utf8') as f:
                paramSet = f.read()
            self.AllMyParams.loadP(paramSet,self.ParamNameListWindow.checkedparams)
            self.SyncInstr()
            
    def OpenPlotter(self):
        newPlotter=cPlotterWindow(self)
        newPlotter.show()
        #cleanup List before adding
        self.PlotterList[:]=[x for x in self.PlotterList if x.isVisible()]
        self.PlotterList.append(newPlotter)
        
    def ParamSettings(self):
        if self.ParamSettingsDialog==None or not self.ParamSettingsDialog.isVisible():
            self.ParamSettingsDialog = ParamSettingsWindow(self,self.AllMyParams)
            self.ParamSettingsDialog.show()
        else:
            self.ParamSettingsDialog.activateWindow()
        self.ParamSettingsDialog.setWindowTitle("parameters")
        self.AllMyParams.sendparam = self.Serial


    def SignalSettings(self):
        if self.SignalSettingsDialog==None or not self.SignalSettingsDialog.isVisible():
            self.SignalSettingsDialog = SignalSettingsWindow(self,self.AllMySignals)
            self.SignalSettingsDialog.show()
        else:
            self.SignalSettingsDialog.activateWindow()
        self.SignalSettingsDialog.setWindowTitle("signals")
        
    def closeEvent(self,ev):
        
        #cleanup lists
        self.InstrPageList[:]=[x for x in self.InstrPageList if x.isVisible()]
        self.PlotterList[:]=[x for x in self.PlotterList if x.isVisible()]
        
        if self.ParamSettingsDialog != None and len(self.InstrPageList)>0:
            buttonReply = QMessageBox.question(self,
                                               'Close nuRay',
                                               "Do you want to save project first?",
                                               QMessageBox.Yes | QMessageBox.No,
                                               QMessageBox.Yes)
            
            if buttonReply == QMessageBox.Yes:
                self.SaveProject()
                self.closeAllChildren()
                ev.accept()
            else:
                self.closeAllChildren()
                ev.accept()
        else:
            self.closeAllChildren()
            ev.accept()
            
    def closeAllChildren(self):
        #close windows
        for i in self.InstrPageList:
            if i.isVisible():
                i.close()
        if self.ParamSettingsDialog!=None:
            self.ParamSettingsDialog.close()
        if self.SignalSettingsDialog!=None:
            self.SignalSettingsDialog.close()
        if self.ConnSetDlg!=None:
            self.ConnSetDlg.close()
        for i in self.PlotterList:
            if i.isVisible():
                i.close()
        try:
            if self.Serial.is_open():
                self.Serial.close()
        except:
            pass
    
    def closeEverything(self):
        self.close()
                
    def loadInstrPage(self,fn,pos=QPoint(0,0)):
        # fn..filename
        # pos..position on screen
        # load an InstrumentPage (file name (fn) already known either form project file or 
        # from call to OpenInstr, which opens a file open dialog to fetch the file name)
        # cleanup list (copy only the ones Visible)
        self.InstrPageList[:]=[x for x in self.InstrPageList if x.isVisible()]
        
        #check if not open already (if so, activate, else load, list, show)
        ip = next((ip for ip in self.InstrPageList if ip.uiFile==fn),None)
        if ip:
            ip.activateWindow()
        else:
            self.newInstrP = cInstrPage(self,fn,pos)
            self.InstrPageList.append(self.newInstrP)       
            for i in self.InstrPageList:
                for x in i.instrList:
                    x.livesend = self.Serial
            self.radioButtonDisconnect.click()
            self.newInstrP.show()
        
    def OpenInstr(self):
        # cleanup list before adding
        # this is done in loadInstrPage again, but only if a file is actually opened
        # TODO: rethink how we can keep this list uptodate
        self.InstrPageList[:]=[x for x in self.InstrPageList if x.isVisible()]
        
        
        files,_ = QFileDialog.getOpenFileNames(self,
                                             "Select UI",
                                             "",
                                             "Instrumentation UI (*.ui);;All Files (*)")
        if files:
            print(files)
            for f in files:
                self.loadInstrPage(f)

        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())