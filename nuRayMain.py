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
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QMessageBox, QDialog, QLabel
from PyQt5.QtCore import QPoint,Qt
import re
import struct

#my own modules 
from gui.InstrPage import cInstrPage
from gui.ParamView import ParamSettingsWindow, SignalSettingsWindow
from gui.PlotWin import cPlotterWindow
from paramModel import cParamTableModel, cSignalTableModel, ParamSelectWindow, BorderViolationsWindow
from CodeGen.codegen import nuRCodeGenerator
from Comm.nuRSerialConn import nuRSerial
import globalThings as G
from gui.SwitchCustomWidget import CustomSwitch, statusLED


#NoNi: load main window and connection settings dialog ui from QtDesigner file
nuRMainWindow, QtBaseClass = uic.loadUiType("nuRMainWindow.ui")
nuRConnSetDialogUi, QtBaseClass = uic.loadUiType("nuRConnSettingsDialog.ui")
       
#NoNi: get directory of this python file, here other modules will look for their stuff
G.nuRDir,_ = os.path.split(__file__)

#NiNa: class for connection settings dialog window
class nuRConnSettingsDialog(QDialog, nuRConnSetDialogUi):
    def __init__(self,parent):
        QDialog.__init__(self)
        nuRConnSetDialogUi.__init__(self)
        self.parent = parent
        self.setupUi(self)
        #NiNa: Full Name of available ports
        c_long = nuRSerial.listPorts()
        self.comboBox.addItems([' ']+c_long)
        c_short = []
        #NiNa: Short Name List of Windows-Ports
        c_short = [re.findall('^COM\d+',c)[0] for c in c_long if "COM" in c]
        #NiNa: Short Name List of MacOs-Ports
        c_short = [re.findall('^/dev\S+',c)[0] for c in c_long if "/dev" in c]
        if self.parent.Serial.port in c_short:
            idx = c_short.index(self.parent.Serial.port)
            self.comboBox.setCurrentIndex(idx+1)
        self.comboBox.currentIndexChanged.connect(self.setPort)
        self.show()

    #NiNa: set port of Serial to the currently selected port
    def setPort(self):
        c = self.comboBox.currentText()
        try:
            self.parent.Serial.port = re.findall('^COM\d+',c)[0] 
        except:
            try:
                self.parent.Serial.port = re.findall('^/dev\S+',c)[0]
            except:
                self.parent.Serial.port = None;
                self.parent.radioButtonDisconnect.click()
        print(str(self.parent.Serial.port)+' selected.')
        self.parent.LEDLabel.setText(str(self.parent.Serial.port))
        self.close()

#NiNa: MainWindow
class MyApp(QMainWindow, nuRMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        nuRMainWindow.__init__(self)
        self.setupUi(self)
        
        #NiNa: all possible menu actions are connected to methods
        self.actionOpen_Instruments.triggered.connect(self.OpenInstr)
        self.actionParameters.triggered.connect(self.ParamSettings)
        self.actionSignals.triggered.connect(self.SignalSettings)
        self.actionOpen_Plotter.triggered.connect(self.OpenPlotter)
        
        self.actionNew_Project.triggered.connect(self.NewProject)
        self.actionSave.triggered.connect(self.SaveProject)
        self.actionSave_As.triggered.connect(self.SaveProjectAs)
        self.actionOpen.triggered.connect(self.OpenProject)
        self.actionGenerate_Code.triggered.connect(self.CodeGen)
        
        self.actionParameters_2.triggered.connect(self.ParamSettings)
        self.actionSave_Parameters.triggered.connect(self.SaveParams)
        self.actionSave_Parameters_As.triggered.connect(self.SaveParamsAs)
        self.actionLoad_Parameters.triggered.connect(self.ParamSelectWindow)
        
        self.actionClose.triggered.connect(self.closeEverything)
        
        self.actionConnection_Settings.triggered.connect(self.ConnSettings)
        self.ConnSetDlg = None
        
        
        self.radioButtonConnect.clicked.connect(self.Connect)
        self.radioButtonDisconnect.clicked.connect(self.Disconnect)
        self.connected = False
        self.radioButtonDisconnect.setChecked(True)
        
        
        #NiNa: Loading Custom Switch Widgets to the MainWindow
        self.ActiveSet = CustomSwitch("SET0","SET1")
        self.SyncedSet = CustomSwitch("SET0","SET1")
        #NiNa: Position of the SyncedSet Switch
        self.syncset = 0
        self.ActiveSet.setDisabled(True)      
                 
        self.ActiveSetSwitch.addWidget(self.ActiveSet)
        self.SyncedSetSwitch.addWidget(self.SyncedSet)
        
        self.ActiveSet.clicked.connect(self.ActivateSet)
        self.SyncedSet.clicked.connect(self.SyncSet)
        
        self.statusLED = statusLED(self)
        self.ConnectionStatus.addWidget(self.statusLED)
        
        self.LEDLabel = QLabel()
        self.ConnectionStatus.addWidget(self.LEDLabel)
        

        #NoNi: we can have several InstrPages and several Plotters...        
        self.InstrPageList=[]
        self.PlotterList=[]
        #NoNi: ...but only one Params and one Signals Page
        self.ParamSettingsDialog = None
        self.SignalSettingsDialog = None
        self.ConnSetDlg = None          

        self.projectFile = 'untitled Project'
        self.paramFile = 'untitled Params'
        self.savebothsets = False
        self.setTitle()
        
        #NoNi: table model so it can be processed by QTableView
        self.AllMyParams = cParamTableModel(None) 
        self.AllMySignals = cSignalTableModel(None)
        self.Serial = nuRSerial()    
   
            
    #NiNa: method connected to radioButtonConnect            
    def Connect(self):   
        if not self.connected:          
            self.Serial.connect()
            #NiNa: check if serial port is accessable
            if self.Serial.is_open():
                self.connected=True
                #NiNa: asking user to save project first because data is going to be overwritten
                #NiNa: self.SaveMessages() returns False only when I cancel
                if self.SaveMessages("CONNECT"):
                    self.ActiveSet.setDisabled(False)
                    self.statusLED.ledcolor = Qt.green
                    self.statusLED.repaint()
                    #NiNa: random package sent because else first startflag is not detected
                    self.Serial.write(1,1,29,255,'uint8')         
                    self.ReadActiveSet() 
                    self.ReadDataFromMuCon() 
                    self.SyncInstr()
                    self.WriteDataToMuCon()       
            #NiNa: empty or nonvalid port chosen
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
 
    
    #NiNa: method connected to radioButtonDisconnect           
    def Disconnect(self):
        self.ActiveSet.setDisabled(True)
        self.statusLED.ledcolor = Qt.red
        self.statusLED.repaint()
        #NiNa: close existing serial connection if connected
        if self.connected:
            self.Serial.close()
        print("disconnected")   
        self.connected = False
  
    
    #NiNa: method handling when saveMessages should pop up  
    #NiNa: two saveEvents: "CONNECT" and "NEWPROJECT"     
    def SaveMessages(self,saveEvent):
        self.saveEvent = saveEvent
        #NiNa: cleanup list first
        self.InstrPageList[:]=[x for x in self.InstrPageList if x.isVisible()]
        #NiNa: first case
        if self.ParamSettingsDialog != None and len(self.InstrPageList)>0:
            buttonReply = QMessageBox.question(self,
                                               'Data is going to be overwritten',
                                               "Do you want to save project first?",
                                               QMessageBox.Yes | QMessageBox.No |
                                               QMessageBox.Cancel)
            if buttonReply == QMessageBox.Yes:
                self.SaveProject() 
                return True
            if buttonReply == QMessageBox.No:
                pass
                return True
            #NiNa: if I press connect,existing data is going to be overwritten --> disconnect, if cancel
            else:
                if self.saveEvent == "CONNECT":
                    self.radioButtonDisconnect.click()
                return False
        #NiNa: second case                
        if self.ParamSettingsDialog != None and len(self.InstrPageList) == 0:
            buttonReply = QMessageBox.question(self,
                                               'Data is going to be overwritten',
                                               "Do you want to save parameters first?",
                                               QMessageBox.Yes | QMessageBox.No |
                                               QMessageBox.Cancel)
            if buttonReply == QMessageBox.Yes:
                self.SaveParamsAs()
                return True
            if buttonReply == QMessageBox.No:
                pass
                return True
            #NiNa: if I press connect,existing data is going to be overwritten --> disconnect, if cancel
            else:
                if self.saveEvent == "CONNECT":
                    self.radioButtonDisconnect.click()
                return False
        else:
            pass
            return True
 
   
    #NiNa: the synced set decides which paramset should be changed when writing 
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

    
    #NiNa: decide which set should be active on microcontroller: 0 or 1
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


    #NiNa: the instruments are getting synced with connected params
    def SyncInstr(self):
        for i in self.InstrPageList:
            for x in i.instrList:
                if type(x.Param) != str:
                    x.instrWidget.setMinimum(x.Param.min)
                    x.instrWidget.setMaximum(x.Param.max)
                    if self.syncset == 0:
                        if not x.Param.dataType == 'float32':
                            x.Param.valset0 = int(x.Param.valset0)
                        x.instrWidget.setValue(x.Param.valset0)
                    if self.syncset == 1:
                        if not x.Param.dataType == 'float32':
                            x.Param.valset1 = int(x.Param.valset1)
                        x.instrWidget.setValue(x.Param.valset1)
    
    
    #NiNa: set nuRay as Master and write data by instruments to microcontroller
    def WriteDataToMuCon(self):
     try:
        for i in self.InstrPageList:
            for x in i.instrList:
                if type(x.Param) != str:
                    x.WriteData()
     except:
         self.radioButtonDisconnect.click()
    
    
    #NiNa: receive information about the currently active set on microcontroller
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
    
    
    #NiNa: set microcontroller as master and read data from microcontroller only at initial connection
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

    
    #TODO: Codegeneration of existing parameters and signals           
    def CodeGen(self):
        if self.projectFile=='untitled Project':
            buttonReply = QMessageBox.information(self,
                                   'Code Gen',
                                   "Please save your project first!",
                                   QMessageBox.Ok)
        else:
            d,f=os.path.split(self.projectFile)
            nuRCodeGenerator.genCode(d,self.AllMyParams.items,self.AllMySignals.items)

                
    #NiNa: returns the name of the project
    def projectName(self):
        d,f=os.path.split(self.projectFile)
        n,e=os.path.splitext(f)
        return n
    
    
    #NiNa: sets the title of the MainWindow to the projectName    
    def setTitle(self):
            self.setWindowTitle('nuRay - '+self.projectName())
            
    
    #NiNa: chose saving location and projectname
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
    
    
    #NiNa: when name already set, save everything, else -> SaveProjectAs
    def SaveProject(self):
        if self.projectFile=='untitled Project':
            self.SaveProjectAs()
        else:
            self.SaveParams()
            with io.open(self.projectFile,'w',encoding='utf8') as f:
                f.write(self.AllMyParams.save())
                f.write(self.AllMySignals.save())
                f.write(self.saveInstrPages())
                f.write(self.ParamFilePaths())
                
    #NiNa: if (project is untitled and "Save Params") or "Save Params As": SaveParamAs()
    def SaveParamsAs(self):
        file,_ = QFileDialog.getSaveFileName(self,
                                             "Save Params As",
                                             "("+'Set'+str(self.syncset)+')',
                                             "nuRay Params (*.nrpa);;All Files(*)")
        if file:
            print(file)
            self.paramFile = file
            self.SaveSingleSet()
    
    
    #NiNa: generate two paramfiles if a project is created
    #NiNa: by changing parameters within a project, existing paramfiles are overwritten
    def SaveParams(self):
        if self.projectFile == 'untitled Project':
                self.SaveParamsAs()
        else:
            self.paramFile = self.projectFile[:-5] + ' ('+'Set'+str(0)+')' + '.nrpa'
            with io.open(self.paramFile,'w',encoding = 'utf8') as f:
                f.write(self.AllMyParams.savePS0())
            self.paramFile = self.projectFile[:-5] + ' ('+'Set'+str(1)+')' + '.nrpa'
            with io.open(self.paramFile,'w',encoding = 'utf8') as f:
                f.write(self.AllMyParams.savePS1())
                
    
    #NiNa: saving the parameters as a single set
    def SaveSingleSet(self):
        with io.open(self.paramFile,'w',encoding = 'utf8') as f:
            if self.syncset == 0:
                f.write(self.AllMyParams.savePS0())
            if self.syncset == 1:
                f.write(self.AllMyParams.savePS1())
                
                
    #NiNa: saving the paths of the generated paramfiles into projectfile                
    def ParamFilePaths(self):
        res = '<pValues>\n'
        res += self.projectFile[:-5] + ' ('+'Set'+str(0)+')' + '.nrpa'
        res += '\n'
        res += self.projectFile[:-5] + ' ('+'Set'+str(1)+')' + '.nrpa'
        res += '\n'
        res += '<\pValues>\n'
        return res
    
        
    #NiNa: saving the paths of the currently visible Instrument Pages into projectfile     
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
    

    #NiNa: loading instrument pages from projectfile
    #NiNa: trying to make it work for MacOs        
    def loadInstrPages(self,txt):
        #NiNa: process <Instrument Pages>-tag from project file and open them all
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
    
    
    #NiNa: saveMessage("NEWPROJECT") <-- radioButtonDisconnect isnt clicked because saveTag isn't "CONNECT"
    #NiNa: close everything that is open, set projectname to untitled Project
    def NewProject(self):
        if self.SaveMessages("NEWPROJECT"):     
            self.projectFile = 'untitled Project'
            self.closeAllChildren()
            self.ParamSettingsDialog = None
            self.AllMyParams = cParamTableModel(None)
            self.OpenInstr()
        else:
            pass
        
    
    #NiNa: Select projectfile, load Parameters, load Signals, Open Parameterlist, Open Instruments, Sync Instruments, setWindowTitle and projectname to filename
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
            self.InsertpValues(projSet)
            self.SyncInstr()
            self.setTitle()   
    
    
    #NiNa: both set param values are inserted reading the adress from projectfil
    def InsertpValues(self,txt):
        myr = re.compile(r'<pValues>\n(.+)<\\pValues>',re.DOTALL)#the dot also matches newlines
        res=myr.search(txt)
        if res:
            paramValues = res.group(1)
            paramValues = paramValues.splitlines()
            print(paramValues)
            with io.open(paramValues[0],'r',encoding='utf-8') as p:
                paramSet = p.read()
                self.AllMyParams.loadPS0(paramSet)
            with io.open(paramValues[1],'r',encoding='utf-8') as p:
                paramSet = p.read()
                self.AllMyParams.loadPS1(paramSet)
                    
                                  
    #NiNa: if a SingleSetParam is loaded a ParamSelectWindow is opened, selected params are loaded / generated    
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

    
    #NiNa: the parameters that were checked on ParamSelectWindow are loaded/generated
    def LoadParams(self):
            with io.open(self.paramFile,'r',encoding='utf8') as f:
                paramSet = f.read()
            x = self.AllMyParams.loadP(paramSet,self.ParamNameListWindow.checkedparams)
            self.minviolationnames = x[0]
            self.minviolationvalues = x[1]
            self.maxviolationnames = x[2]
            self.maxviolationvalues = x[3]
            self.currentmin = x[4]
            self.currentmax = x[5]
            #NiNa: if parameters violate borders a window is opened to handle the borderviolations
            if len(self.minviolationnames) != 0 or len(self.maxviolationnames) != 0:   
                self.BorderViolation = BorderViolationsWindow(self,self.maxviolationvalues,self.maxviolationnames,self.minviolationvalues,self.minviolationnames,self.currentmax,self.currentmin)
                self.BorderViolation.setWindowTitle("Border Violations")
                self.BorderViolation.show()
                ErrorInfo = QMessageBox.information(self,
                                                     'Border Violations',
                                                     'Some Values are violating existing borders. Please choose how to handle those violations!',
                                                     QMessageBox.Ok)
            self.SyncInstr()
    
    
    #NiNa: open plotterwindows
    def OpenPlotter(self):
        newPlotter=cPlotterWindow(self)
        newPlotter.show()
        self.PlotterList[:]=[x for x in self.PlotterList if x.isVisible()]
        self.PlotterList.append(newPlotter)
        
    
    #NiNa: ParamSettingsDialog is opened with all existing parameters
    def ParamSettings(self):
        if self.ParamSettingsDialog==None or not self.ParamSettingsDialog.isVisible():
            self.ParamSettingsDialog = ParamSettingsWindow(self,self.AllMyParams)
            self.ParamSettingsDialog.show()
        else:
            self.ParamSettingsDialog.activateWindow()
        self.ParamSettingsDialog.setWindowTitle("parameters")
        self.AllMyParams.sendparam = self.Serial


    #NiNa: SignalSettingsDialog is opened with all existing signals
    def SignalSettings(self):
        if self.SignalSettingsDialog==None or not self.SignalSettingsDialog.isVisible():
            self.SignalSettingsDialog = SignalSettingsWindow(self,self.AllMySignals)
            self.SignalSettingsDialog.show()
        else:
            self.SignalSettingsDialog.activateWindow()
        self.SignalSettingsDialog.setWindowTitle("signals")
        
        
    #NiNa: No SaveMessages(). save messages handled by closeEvent because of ev.accept and ev.ignore
    #NiNa: SaveMessages(): "NEWPROJECT", "CONNECT" and save messages at closeEvent (3 events for save messages)
    def closeEvent(self,ev):     
        #NiNa: cleanup lists first
        self.InstrPageList[:]=[x for x in self.InstrPageList if x.isVisible()]
        self.PlotterList[:]=[x for x in self.PlotterList if x.isVisible()] 
        if self.ParamSettingsDialog != None and len(self.InstrPageList)>0:
            buttonReply = QMessageBox.question(self,
                                               'Close nuRay',
                                               "Do you want to save project first?",
                                               QMessageBox.Yes | QMessageBox.No |
                                               QMessageBox.Cancel)
            if buttonReply == QMessageBox.Yes:
                self.SaveProject()
                self.closeAllChildren()
                ev.accept()
            if buttonReply == QMessageBox.No:
                self.closeAllChildren()
                ev.accept()
            else:
                ev.ignore()             
        if self.ParamSettingsDialog != None and len(self.InstrPageList) == 0:
            buttonReply = QMessageBox.question(self,
                                               'Close nuRay',
                                               "Do you want to save parameters first?",
                                               QMessageBox.Yes | QMessageBox.No |
                                               QMessageBox.Cancel)    
            if buttonReply == QMessageBox.Yes:
                self.SaveParams()
                self.closeAllChildren()
                ev.accept()
            if buttonReply == QMessageBox.No:
                self.closeAllChildren()
                ev.accept()
            else:
                ev.ignore()       
        if self.ParamSettingsDialog == None:
            self.closeAllChildren()
            ev.accept()
    
    
    #NiNa: every window, that is open is closed, ParamSettingsDialog is closed, serial Port
    def closeAllChildren(self):
        #close windows
        for i in self.InstrPageList:
            if i.isVisible():
                i.close()
        if self.ParamSettingsDialog!=None:
            self.ParamSettingsDialog.close()
            self.ParamSettingsDialog = None
        if self.SignalSettingsDialog!=None:
            self.SignalSettingsDialog.close()
            self.SignalSettingsDialog = None
        if self.ConnSetDlg!=None:
            self.ConnSetDlg.close()
            self.ConnSetDlg = None
        for i in self.PlotterList:
            if i.isVisible():
                i.close()
        if self.connected:
            self.radioButtonDisconnect.click()

    #NiNa: method for Close action in menu
    def closeEverything(self):
        self.close()
     
    
    #NiNa: instrumentPageWindow is generated with link in projectfile, InstrPageList is apepended by existing pages           
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
    
    
    #NiNa: File Explorer is opened to select an instrument file if file not already selected/opened
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


#NiNa: starting the whole mainApp         
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())