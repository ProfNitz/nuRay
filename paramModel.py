# -*- coding: utf-8 -*-
"""
Created on Wed Jun 12 13:24:32 2019

@author: Nitzsche
"""

from PyQt5.QtCore import Qt, QObject
from PyQt5.QtCore import QAbstractTableModel, QModelIndex
from PyQt5.QtGui import QColor, QFont, QIcon, QPixmap
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QCheckBox, QPushButton, QFrame, QLabel, QMessageBox
import re
from math import log10, floor
#from Comm.nuRSerialConn import nuRSerial

class mRColor(QColor):
    def __init__(self,data):
        if isinstance(data,QColor):             #NiNa: data = QColor(50,50,50) 
            QColor.__init__(self,data)
        elif isinstance(data,str):              #NiNa: data = "(50,50,50)"
            data=data[1:-1]#strip ( )
            rgb=data.split(',')
            QColor.__init__(self,int(rgb[0]),int(rgb[1]),int(rgb[2]))
        
    def __str__(self):
        r,g,b,_=self.getRgb()
        return '('+str(r)+','+str(g)+','+str(b)+')'

#NiNa: x = mRColor("(50,50,50)")
#NiNa: print(x)
class mRayAbstractItem(QObject):
    def roundToTwo(self,x):
        return round(x, -int(floor(log10(abs(x))))+1)
        
    def save(self):
        res = ''
        for p in self.properties:#export all relevant members
            if not (p == 'valset0' or p == 'valset1'):
                res+=(str(self.__dict__[p])+';')
        res=res[:-1]+'\n'#replace trailing ; by \n
        return res
    
    def savePS0(self):
        res = ''
        res+=(str(self.__dict__['name'])+';')
        res+=(str(self.__dict__['valset0'])+'\n')
        return res
    
    def savePS1(self):
        res = ''
        res+=(str(self.__dict__['name'])+';')
        res+=(str(self.__dict__['valset1'])+'\n')
        return res
        
    def fillProps(self,txt):
        #don't set name, since ParamModel is responsible for avoiding duplicates
        ps = txt.split(';')
        print(ps)
        for p in range(2,len(ps)):
            self.__dict__[self.properties[p]]=self.pTypes[p](ps[p])
        self.__dict__[self.properties[0]]=self.pTypes[0](ps[0])

            
    def fillValuesS0(self,value,pGen):
        #if float(value) <= self.__dict__[self.properties[4]] and float(value) >= self.__dict__[self.properties[3]]:
            if self.__dict__[self.properties[2]] == 'float32':
                self.__dict__[self.properties[5]] = float(value)
                if pGen == True:
                    if (float(value)) > 0:
                        self.__dict__[self.properties[4]] = float(self.roundToTwo((2*float(value))))
                        self.__dict__[self.properties[3]] = float(0)
                    if (float(value)) < 0:
                        self.__dict__[self.properties[3]] = float(self.roundToTwo((2*float(value))))
                        self.__dict__[self.properties[4]] = float(0)
            else:
                self.__dict__[self.properties[5]] = int(float(value))

    
    def fillValuesS1(self,value,pGen):
        if self.__dict__[self.properties[2]] == 'float32':
            self.__dict__[self.properties[6]] = float(value)
            if pGen == True:
                if float(value) > 0:
                    self.__dict__[self.properties[4]] = float(self.roundToTwo((2*float(value))))
                    self.__dict__[self.properties[3]] = float(0)
                if float(value) < 0:
                    self.__dict__[self.properties[3]] = float(self.roundToTwo((2*float(value))))
                    self.__dict__[self.properties[4]] = float(0)
        else:
            self.__dict__[self.properties[6]] = int(float(value))
        
    def __str__(self):
        return self.name
    
class mRaySignal(mRayAbstractItem):
    
    #these three memebers describe the interface to a Signal object
    #this should be the only place where you change it
    header=['Name','Data Type','Zero At','Scale','Color']#Human readable names of members of mRayParam
    properties=['name','dataType','zeroAt','scale','color']#relevant members of mRayParam (verbatim!)
    pTypes=[str,str,float,float,mRColor]
    
    
    def __init__(self,name):
        super().__init__()
        self.name = name
        self.dataType='float32'
        self.zeroAt = 0.0
        self.scale = 1.0
        self.color = mRColor(QColor(50,50,50))
               
#NiNa: x = mRaySignal("SIGNAL")
#NiNa: x.save()
#NiNa: x.fillProps("SIGNAL;int16;-20;20;(30,40,50)")
#NiNa: x.save()
#NiNa: print(x)  

class mRayParam(mRayAbstractItem):

    #these three memebers describe the interface to a Signal object
    #this should be the only place where you change it
    header=['Param Nr','Name','Data Type','Min','Max','Value_Set0','Value_Set1']#Human readable names of members of mRayParam
    properties=['paramnr','name','dataType','min','max','valset0','valset1']#relevant members of mRayParam (verbatim!)
    pTypes=[int,str,str,float,float,float,float]
    def __init__(self,name):
        super().__init__()
        self.name=name
        self.paramset = 0
        self.min=0.0
        self.max=1.0
        self.valset0 = self.min
        self.valset1 = self.min
        self.val = self.min
        self.dataType='float32'
        self._instrList=[]
    def removeInstr(self,Instr):
        self._instrList[:] = [i for i in self._instrList if i!=Instr]
    def addInstr(self,Instr):
        self._instrList.append(Instr)
    def disconnect(self):
        for i in self._instrList:
            i.disconnectFromParam()
        
        


class cMRTableModel(QAbstractTableModel):
    def __init__(self,parent):
        super().__init__(parent)
        self.items=[]
        self.numI=0
        self.paramnrlist = []
    def itemNames(self):
        return [x.name for x in self.items] #wow, my first list comprehension
    def flags(self,idx):
        if idx.column() in range(0,5,1):
            return Qt.ItemIsSelectable|Qt.ItemIsEditable|Qt.ItemIsEnabled
        if idx.column() in range(5,7,1):
            return Qt.ItemIsEnabled
    def removeItem(self,row):
        self.beginRemoveRows(QModelIndex(),row,row)
        self.items[row].disconnect()
        self.items.pop(row)
        self.numI-=1
        self.endRemoveRows()
    def newItem(self,Name):
        while Name in self.itemNames():
            #append 2 to name or increment number at the end
            myr = re.compile('(\d+)$')#get number from end of Name
            res=myr.search(Name)
            if res:
                Name = Name[0:res.start()]+str(int(res.group())+1)
            else:
                Name += '2'
                
        self.currentparamnr = 0
        if self.numI == 0:
            pass
        else:
            while self.currentparamnr in [p.paramnr for p in self.items]:
                self.currentparamnr += 1
        
        self.beginInsertRows(QModelIndex(),self.numI,self.numI)#parent is a default (empty) QModelIndex? Copied from an example
        newItem = self.itemClass(Name)
        self.items.append(newItem)
        newItem.paramnr = self.currentparamnr
        self.numI+=1
        
        self.endInsertRows()
    def sort(self):
        self.beginResetModel()#inform view that everthing is about to change
        self.items.sort(key = lambda x: x.name)
        self.endResetModel()
    
    def send(self):
        for i in self.items:
            if not i.dataType == 'float32':
                i.val = int(i.val)
            print(i.paramset)
            print(i.paramnr)
            print(i.val)
            print(i.dataType)
            self.sendparam.write(i.paramset,i.paramnr,i.val,i.dataType)
            
    def columnCount(self,parent):
        return len(self.itemClass.properties)
        
    def rowCount(self,parent):
        return self.numI

    def headerData(self,sec,orientation,role=Qt.DisplayRole):
        if orientation==Qt.Horizontal:
            #print(role)
            if role==Qt.DisplayRole:
                return self.itemClass.header[sec]
            elif role==Qt.BackgroundRole:
                return QColor(100,100,100)
            elif role==Qt.TextAlignmentRole:
                return Qt.AlignCenter
            else:
                return QAbstractTableModel.headerData(self,sec,orientation,role)
        else:
            return None
    def data(self,idx,role):
        if role in [Qt.DisplayRole,Qt.EditRole]:
            entry = self.items[idx.row()].__dict__[self.itemClass.properties[idx.column()]]
            #print(type(entry))
            return entry
        elif role==Qt.BackgroundRole:
            if idx.row()%2==0:
                return QColor(240,240,240)
            else:
                return QColor(220,220,220)
        elif role==Qt.FontRole:
            return QFont('courier')
        else:
            return None
    def setData(self,idx,val,role=Qt.EditRole):
        if role == Qt.EditRole:
            if idx.column() == 0:
                self.paramnumbers = [p.paramnr for p in self.items]
                if val in self.paramnumbers:
                    self.bool = False
                else: 
                    self.items[idx.row()].__dict__[self.itemClass.properties[idx.column()]]=val
                    self.bool = True
            if idx.column() == 1:
                self.paramnames = [p.name for p in self.items]
                if val in self.paramnames:
                    self.bool = False
                else:
                    self.items[idx.row()].__dict__[self.itemClass.properties[idx.column()]]=val
                    for i in self.items[idx.row()]._instrList:
                        i.ParamNameChanged()
                    self.bool = True
            if idx.column() == 2:
                for i in self.items[idx.row()]._instrList:
                    i.disconnectFromParam()
                self.items[idx.row()].__dict__[self.itemClass.properties[idx.column()]]=val
                if val == 'float32':
                    for j in range(3,7,1):
                        self.items[idx.row()].__dict__[self.itemClass.properties[j]] = float(self.items[idx.row()].__dict__[self.itemClass.properties[j]])
                else:
                    for j in range(3,7,1):
                        self.items[idx.row()].__dict__[self.itemClass.properties[j]] = int(float(self.items[idx.row()].__dict__[self.itemClass.properties[j]]))
                self.bool = True
            if idx.column() == 3:
                self.pvals0 = self.items[idx.row()].__dict__[self.itemClass.properties[5]]
                self.pvals1 = self.items[idx.row()].__dict__[self.itemClass.properties[6]]                
                self.maxval = self.items[idx.row()].__dict__[self.itemClass.properties[4]]
                if val >= self.maxval:
                    self.bool = False
                if self.pvals0 < val or self.pvals1 < val:
                    self.bool = False
                else:
                    if self.items[idx.row()].__dict__[self.itemClass.properties[2]] == 'float32':
                        self.items[idx.row()].__dict__[self.itemClass.properties[idx.column()]]=float(val)
                    else:
                        self.items[idx.row()].__dict__[self.itemClass.properties[idx.column()]]=int(float(val))
                    self.bool = True
            if idx.column() == 4:
                self.pvals0 = self.items[idx.row()].__dict__[self.itemClass.properties[5]]
                self.pvals1 = self.items[idx.row()].__dict__[self.itemClass.properties[6]] 
                self.minval = self.items[idx.row()].__dict__[self.itemClass.properties[3]]
                if val <= self.minval:
                    self.bool = False
                if self.pvals0 > val or self.pvals1 > val:
                    self.bool = False                    
                else:
                    if self.items[idx.row()].__dict__[self.itemClass.properties[2]] == 'float32':
                        self.items[idx.row()].__dict__[self.itemClass.properties[idx.column()]]=float(val)
                    else:
                        self.items[idx.row()].__dict__[self.itemClass.properties[idx.column()]]=int(float(val))
                    self.bool = True
        return self.bool

    def save(self):
        res = '<'+self.saveTag+'>\n'
        for p in self.items:
            res+=p.save()
        res += '<\\'+self.saveTag+'>\n'
        return res
    
    def savePS0(self):
        res = '<pValues>\n'
        for p in self.items:
            res+=p.savePS0() 
        res += '<\pValues>\n'
        return res
    
    def savePS1(self):
        res = '<pValues>\n'
        for p in self.items:
            res+=p.savePS1() 
        res += '<\pValues>\n'
        return res
    
    def loadPS0(self,txt):
        self.pValues = []
        myr = re.compile(r'<pValues>\n(.+)<\\pValues>',re.DOTALL)#the dot also matches newlines
        res=myr.search(txt)
        if res:
            j = 0
            paramValues = res.group(1)
            print(paramValues)
            for l in paramValues.splitlines():
                value = l.split(';')[-1]
                self.pValues.append(value)
            print(self.pValues)
            for i in self.items:
                i.fillValuesS0(self.pValues[j]) 
                j += 1
            
    def loadPS1(self,txt):
        self.pValues = []
        myr = re.compile(r'<pValues>\n(.+)<\\pValues>',re.DOTALL)#the dot also matches newlines
        res=myr.search(txt)
        if res:
            j = 0
            paramValues = res.group(1)
            print(paramValues)
            for l in paramValues.splitlines():
                value = l.split(';')[-1]
                self.pValues.append(value)
            print(self.pValues)
            for i in self.items:
                i.fillValuesS1(self.pValues[j])
                j += 1

       
    def loadList (self,txt):
        self.paramnamelist = []
        self.valuelist = []
        myr = re.compile(r'<pValues>\n(.+)<\\pValues>',re.DOTALL)#the dot also matches newlines
        res=myr.search(txt)
        if res:
            paramValues = res.group(1)
            for l in paramValues.splitlines():
                name = l.split(';')[0]
                value = l.split(';')[-1]
                self.paramnamelist.append(name)
                self.valuelist.append(value)
        return self.paramnamelist, self.valuelist
        
    
    def load(self,txt):
        self.beginResetModel()#inform view that everthing is about to change
        #self.items = []
        while self.numI > 0:
            self.removeItem(self.numI-1)
        myr = re.compile(r'<'+self.saveTag+r'>\n(.+)<\\'+self.saveTag+r'>',re.DOTALL)#the dot also matches newlines
        res=myr.search(txt)
        if res:
            paramSettings = res.group(1)
            for l in paramSettings.splitlines():
                #name = l.split(';')[1]
                #print(name)
                #print([i.name for i in self.items])
                #if name in [i.name for i in self.items]:#avoid duplicates
                    #self.newItem(l.split(';')[1])#name must always be first in itemClass.properties
                #    self.items[[i.name for i in self.items].index(name)].fillProps(l)
                #else:
                self.newItem(l.split(';')[1])#name must always be first in itemClass.properties
                self.items[-1].fillProps(l)                                              
        self.endResetModel()
        
        
    def loadP(self,txt,checkedparams):
        #self.beginResetModel()#inform view that everthing is about to change
        #self.items = []
        myr = re.compile(r'<pValues>\n(.+)<\\pValues>',re.DOTALL)#the dot also matches newlines
        res=myr.search(txt)
        if res:
            paramSettings = res.group(1)
            for l in paramSettings.splitlines():
                name = l.split(';')[0]
                pvalue = l.split(';')[1]
                print(name)
                if name in checkedparams:
                #print([i.name for i in self.items])
                    if name in [i.name for i in self.items]:#avoid duplicates
                        pGen = False
                    #self.newItem(l.split(';')[1])#name must always be first in itemClass.properties
                        if 0 in [i.paramset for i in self.items]:
                            self.items[[i.name for i in self.items].index(name)].fillValuesS0(pvalue,pGen)
                        if 1 in [i.paramset for i in self.items]:
                            self.items[[i.name for i in self.items].index(name)].fillValuesS1(pvalue,pGen)
                    else:
                        pGen = True
                        self.newItem(name)#name must always be first in itemClass.properties
                        if 0 in [i.paramset for i in self.items]:
                            self.items[-1].fillValuesS0(pvalue,pGen)
                        if 1 in [i.paramset for i in self.items]:
                            self.items[-1].fillValuesS1(pvalue,pGen)
                        
        #self.endResetModel()
                                                          


class cParamTableModel(cMRTableModel):
    def __init__(self,parent):
        super().__init__(parent)
        self.itemClass = mRayParam#store name of param Class
        self.saveTag = 'Parameters'

        
    def listParamsInstr(self,row):
        param = self.items[row]
        for i in param._instrList:
            print(i.instrWidget.objectName())
    
class cSignalTableModel(cMRTableModel):
    defaultColors=[QColor(250,0,0),
                   QColor(0,220,0),
                   QColor(120,120,255),
                   QColor(220,0,220),
                   QColor(0,200,200),
                   QColor(250,180,0)]
    def __init__(self,parent):
        super().__init__(parent)
        self.itemClass = mRaySignal#store name of param Class
        self.saveTag = 'Signals'
    def newItem(self,Name):
        super().newItem(Name)
        #the newly created item needs a color
        idx = len(self.items)-1
        num = len(self.defaultColors)
        self.items[idx].color=mRColor(self.defaultColors[idx % num])
    def data(self,idx,role):
        #print(role)
        if role in [Qt.DisplayRole,Qt.EditRole]:
            entry = self.items[idx.row()].__dict__[self.itemClass.properties[idx.column()]]
            #print(type(entry))
            if isinstance(entry,QColor):
                if role == Qt.EditRole:
                    return entry
                else:
                    return None
            else:
                return entry
        elif role==Qt.DecorationRole:
            entry = self.items[idx.row()].__dict__[self.itemClass.properties[idx.column()]]
            if isinstance(entry,QColor):
                pixmap = QPixmap(10,10)
                pixmap.fill(entry)
                return pixmap
            else:
                return None
        else:
            super().data(idx,role)
    def setData(self,idx,val,role=Qt.EditRole):
        if role == Qt.EditRole:
            if isinstance(val,QColor):
                self.items[idx.row()].__dict__[self.itemClass.properties[idx.column()]]=mRColor(val)
            else:
                self.items[idx.row()].__dict__[self.itemClass.properties[idx.column()]]=val
        return True
    
class ParamSelectWindow(QDialog):  
    def __init__(self,parent,paramnamelist,valuelist):
        super().__init__(parent)
        self.layoutlist = []
        self.checkedparams = []
        self.checkboxlist = []
        self.checkboxvalues = []
        self.paramnamelist = paramnamelist
        self.valuelist = valuelist
        self.sublayout = QHBoxLayout()
        self.layout = QVBoxLayout()
        self.seperator = QFrame()
        self.seperator.setFrameShape(QFrame.HLine)
        self.loadbutton = QPushButton("Load")
        self.selectall = QCheckBox("Select All",self)
        for i in self.paramnamelist:
            self.layoutlist.append(QHBoxLayout())
            self.checkboxlist.append(QCheckBox(str(i),self)) 
        for i in self.valuelist:
            self.checkboxvalues.append(QLabel(str(i)))
        self.setLayout(self.layout)
        self.layout.addWidget(self.selectall)
        self.layout.addWidget(self.seperator)
        
        for i in self.layoutlist:
            self.layout.addLayout(i)
        
        for x in range(0,len(self.layoutlist)):  
            self.layoutlist[x].addWidget(self.checkboxlist[x])
            self.layoutlist[x].addWidget(self.checkboxvalues[x])
            

       # for i in self.checkboxlist:
        #    self.layout.addWidget(i)
        self.layout.addLayout(self.sublayout)
        self.sublayout.addWidget(self.loadbutton)
        self.selectall.toggled.connect(self.checkall)
        self.loadbutton.clicked.connect(self.checkedparamlist)

    def checkall(self):
        for x in self.checkboxlist:
            x.setChecked(True)
            
    def checkedparamlist(self):
        for i in range(0,len(self.checkboxlist)):
            if self.checkboxlist[i].isChecked():
                self.checkedparams.append(self.checkboxlist[i].text()) 
        self.parent().LoadParams()
        self.close()
            

        