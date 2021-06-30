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
from PyQt5.QtCore import QPoint,Qt
import re
import time


#my own modules 
from gui.InstrPage import cInstrPage
from gui.ParamView import ParamSettingsWindow, SignalSettingsWindow
from gui.PlotWin import cPlotterWindow
from paramModel import cParamTableModel, cSignalTableModel
from CodeGen.codegen import nuRCodeGenerator
from Comm.nuRSerialConn import nuRSerial
import globalThings as G
from SwitchCustomWidget import CustomSwitch, statusLED


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
        
        self.actionConnection_Settings.triggered.connect(self.ConnSettings)
        self.ConnSetDlg = None
        
        
        self.radioButtonConnect.clicked.connect(self.Connect)
        self.radioButtonDisconnect.clicked.connect(self.Disconnect)
        self.connected = False
        self.radioButtonDisconnect.setChecked(True)
        
        self.nyu = chr(0x03b7)
        self.myu = chr(0x03bc)
        self.rArrow = chr(0x2192)
        self.lArrow = chr(0x2190)
        self.ActiveSet = CustomSwitch("SET0","SET1")
        self.SyncedSet = CustomSwitch("SET0","SET1")
        self.nuRayText.addWidget(QLabel(self.nyu+"Ray"))
        self.muConText.addWidget(QLabel(self.myu+"Con"))
        self.SyncDir = QPushButton(self.lArrow)
        self.nuRayIsMaster = False
        self.muConIsMaster = True
        self.syncset = 0
                    
        
        self.ActiveSetSwitch.addWidget(self.ActiveSet)
        self.SyncedSetSwitch.addWidget(self.SyncedSet)
        self.syncDirection.addWidget(self.SyncDir)
        
        self.ActiveSet.clicked.connect(self.ActivateSet)
        self.SyncedSet.clicked.connect(self.SyncSet)
        self.SyncDir.clicked.connect(self.changeSyncDir)
        
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
        self.setTitle()
        
        self.AllMyParams = cParamTableModel(None) #table model so it can be processed by QTableView
        self.AllMySignals = cSignalTableModel(None)
        self.Serial = nuRSerial()
               
             
    def Connect(self):   
        if not self.connected:
            self.Serial.connect()
            if self.Serial.is_open():
                self.statusLED.ledcolor = Qt.green
                self.statusLED.repaint()
                self.connected=True
                self.InstrReadWrite()                   
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
        self.connected = False       
        self.statusLED.ledcolor = Qt.red
        self.statusLED.repaint()
        
        self.Serial.close()
        print("disconnected")   
 
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
                
    def ActivateSet(self):
        if self.ActiveSet.isChecked():
            self.Serial.write(1,1,0,0,'ctrl')
            print('SET1 is active')
        else:
            self.Serial.write(1,0,0,0,'ctrl')
            print('SET0 is active') 
            
    def changeSyncDir(self):
        if self.SyncDir.text() == self.rArrow:
            self.SyncDir.setText(self.lArrow)
            self.nuRayIsMaster = False
            self.muConIsMaster = True
        else:
            self.SyncDir.setText(self.rArrow)
            self.nuRayIsMaster = True
            self.muConIsMaster = False
        self.InstrReadWrite()

    def InstrReadWrite(self):
        for i in self.InstrPageList:
                for x in i.instrList:
                    if type(x.Param) != str:
                        if self.nuRayIsMaster == True:
                            x.writeNtoM = True
                        else:
                            x.writeNtoM = False
                        x.readWriteData()
        
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
        
    def setTitle(self):
            self.setWindowTitle('nuRay - '+self.projectName())
            
        
    def SaveProjectAs(self):
        file,_ = QFileDialog.getSaveFileName(self,
                                             "Save Project As...",
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
                f.write(self.saveSyncedSet())
                
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
    
    def saveSyncedSet(self):
        res='<SyncedSet>\n'
        res+=str(self.syncset)
        res+='<\SyncedSet>\n'
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
                    
    def loadSyncedSet(self,txt):
        myr = re.compile(r'<SyncedSet>\n(.+)<\\SyncedSet>',re.DOTALL)
        res=myr.search(txt)
        if res:
            print(res.group(1))
            if int(res.group(1)) == self.syncset:
                pass
            else:
                self.SyncedSet.click()
    
    def OpenProject(self):
        file,_ = QFileDialog.getOpenFileName(self,
                                             "Open Project...",
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
            self.loadSyncedSet(projSet)
            self.setTitle()            
        
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
        
        if len(self.InstrPageList)>0:
            buttonReply = QMessageBox.question(self,
                                               'Close nuRay',
                                               "Do you really want to quit?",
                                               QMessageBox.Yes | QMessageBox.No,
                                               QMessageBox.Yes)
            if buttonReply == QMessageBox.Yes:
                self.closeAllChildren()
                ev.accept()
            else:
                ev.ignore()
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
            self.newInstrP.show()
            if self.connected:
                self.InstrReadWrite()
        
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