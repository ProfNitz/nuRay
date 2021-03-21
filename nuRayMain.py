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
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QMessageBox, QDialog
from PyQt5.QtCore import QPoint
import re


#my own modules 
from gui.InstrPage import cInstrPage
from gui.ParamView import ParamSettingsWindow, SignalSettingsWindow
from gui.PlotWin import cPlotterWindow
from paramModel import cParamTableModel, cSignalTableModel
from CodeGen.codegen import nuRCodeGenerator
from Comm.nuRSerialConn import nuRSerial
import globalThings as G


#load main window ui from QtDesigner file
nuRMainWindow, QtBaseClass = uic.loadUiType("nuRMainWindow.ui")
nuRConnSetDialogUi, QtBaseClass = uic.loadUiType("nuRConnSettingsDialog.ui")
       
#get directory of this python file, here other modules will look for their stuff
G.nuRDir,_ = os.path.split(__file__)


class nuRConnSettingsDialog(QDialog, nuRConnSetDialogUi):
    def __init__(self,parent):
        QDialog.__init__(self)
        nuRConnSetDialogUi.__init__(self)
        self.parent = parent
        self.setupUi(self)
        
        c_long = nuRSerial.listPorts()
        self.comboBox.addItems([' ']+c_long)
        
        c_short = [re.findall('^COM\d+',c)[0] for c in c_long]
        
        if self.parent.Serial.port in c_short:
            idx = c_short.index(self.parent.Serial.port)
            self.comboBox.setCurrentIndex(idx+1)#+1 because 
        
        self.comboBox.currentIndexChanged.connect(self.setPort)
        
        self.show()
        
        
    def setPort(self):
        c = self.comboBox.currentText()
        try:
            self.parent.Serial.port = re.findall('^COM\d+',c)[0]
        except:
            self.parent.Serial.port = None;
        print(self.parent.Serial.port+' selected.')


 
class MyApp(QMainWindow, nuRMainWindow, QDialog):
    def __init__(self):
        QMainWindow.__init__(self)
        nuRMainWindow.__init__(self)
        self.setupUi(self)
        
        # register all actions (Menu and Connect/Disconnect)
        self.actionOpen_Instruments.triggered.connect(self.OpenInstr)
        self.actionParameters.triggered.connect(self.ParamSettings)
        self.actionSignals.triggered.connect(self.SignalSettings)
        self.actionOpen_Plotter.triggered.connect(self.OpenPlotter)
        
        self.actionSave.triggered.connect(self.SaveProject)
        self.actionSave_As.triggered.connect(self.SaveProjectAs)
        self.actionOpen.triggered.connect(self.OpenProject)
        self.actionGenerate_Code.triggered.connect(self.CodeGen)
        
        self.actionConnection_Settings.triggered.connect(self.ConnSettings)
        
        
        self.radioButtonConnect.clicked.connect(self.Connect)
        self.radioButtonDisconnect.clicked.connect(self.Disconnect)
        self.connected = False
        self.radioButtonDisconnect.setChecked(True)
        
        # keep track of the open child windows
        # we can have several InstrPages and several Plotters...        
        self.InstrPageList=[]
        self.PlotterList=[]
        #...but only one Params and one Signals Page
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
            try:
                self.Serial.connect()
                if self.Serial.is_open():
                    self.connected=True
            except:
                pass
        pass
        
    def Disconnect(self):
        self.connected = False
        self.Serial.close()
        
        
        
    #first rudimental reaction on Connection settings
    def ConnSettings(self):
        self.ConnSetDlg = nuRConnSettingsDialog(self)
        
        
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
                
                
    def saveInstrPages(self):
        res='<Instrument Pages>\n'
        #clean up list first
        self.InstrPageList[:]=[x for x in self.InstrPageList if x.isVisible()]
        for p in self.InstrPageList:
            pos = p.pos()
            res+=p.uiFile+';'+str(pos.x())+';'+str(pos.y())+'\n'
        res+='<\Instrument Pages>\n'
        return res
            
    def loadInstrPages(self,txt):
        #process <Instrument Pages>-tag from project file and open them all
        myr = re.compile(r'<Instrument Pages>\n(.+)<\\Instrument Pages>',re.DOTALL)#the dot also matches newlines
        res=myr.search(txt)
        if res:
            pageSettings = res.group(1)
            for l in pageSettings.splitlines():
                ps = l.split(';')
                self.loadInstrPage(ps[0],QPoint(int(ps[1]),int(ps[2])))
                
        
            
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
            self.AllMySignals.load(projSet)
            self.loadInstrPages(projSet)
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
            newInstrP = cInstrPage(self,fn,pos)
            self.InstrPageList.append(newInstrP)
            newInstrP.show()
        
        
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