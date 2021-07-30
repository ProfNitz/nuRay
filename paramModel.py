# -*- coding: utf-8 -*-
"""
Created on Wed Jun 12 13:24:32 2019

@author: Nitzsche
"""

from PyQt5.QtCore import Qt, QObject
from PyQt5.QtCore import QAbstractTableModel, QModelIndex
from PyQt5.QtGui import QColor, QFont, QPixmap
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QCheckBox, QPushButton, QFrame, QLabel, QMessageBox, QDoubleSpinBox, QGridLayout
import re
from math import log10, floor


class mRColor(QColor):
    def __init__(self,data):
        if isinstance(data,QColor):             
            QColor.__init__(self,data)
        elif isinstance(data,str):             
            data=data[1:-1]#strip ( )
            rgb=data.split(',')
            QColor.__init__(self,int(rgb[0]),int(rgb[1]),int(rgb[2]))
        
    def __str__(self):
        r,g,b,_=self.getRgb()
        return '('+str(r)+','+str(g)+','+str(b)+')'


class mRayAbstractItem(QObject):
  
    #NiNa: round to two significant values
    def roundToTwo(self,x):
        return round(x, -int(floor(log10(abs(x))))+1)
    
    #NiNa: only save everything except value    
    def save(self):
        res = ''
        for p in self.properties:#export all relevant members
            if not (p == 'valset0' or p == 'valset1'):
                res+=(str(self.__dict__[p])+';')
        res=res[:-1]+'\n'#replace trailing ; by \n
        return res
    
    #NiNa: save values from set 0
    def savePS0(self):
        res = ''
        res+=(str(self.__dict__['name'])+';')
        res+=(str(self.__dict__['valset0'])+'\n')
        return res
    
    #NiNa: save values from set 1
    def savePS1(self):
        res = ''
        res+=(str(self.__dict__['name'])+';')
        res+=(str(self.__dict__['valset1'])+'\n')
        return res
    
    #NiNa: borderviolation option: set new Min    
    def fillMin(self,val):
        if self.__dict__[self.properties[2]] == 'float32':
            self.__dict__[self.properties[3]] = float(val)
        else:
            if self.__dict__[self.properties[2]] == 'uint8' and float(val) < 0:
                self.__dict__[self.properties[2]] ='int16'
            self.__dict__[self.properties[3]] = int(float(val))
            
    #NiNa: borderviolation option: set new Max        
    def fillMax(self,val):
        if self.__dict__[self.properties[2]] == 'float32':
            self.__dict__[self.properties[4]] = float(val)
        else:
            if self.__dict__[self.properties[2]] == 'uint8' and float(val) < 0:
                self.__dict__[self.properties[2]] = 'int16'
            self.__dict__[self.properties[4]] = int(float(val))
    
    #NiNa: set value set 0 to val, borders already checked
    def setValS0(self,val):
        if self.__dict__[self.properties[2]] == 'float32':
            self.__dict__[self.properties[5]] = float(val)
        else:
            if self.__dict__[self.properties[2]] == 'uint8' and float(val) < 0:
                self.__dict__[self.properties[2]] = 'int16'
            self.__dict__[self.properties[5]] = int(float(val))
    
    #NiNa: set value set 1 to val, borders already checked
    def setValS1(self,val):
        if self.__dict__[self.properties[2]] == 'float32':
            self.__dict__[self.properties[6]] = float(val)
        else:
            if self.__dict__[self.properties[2]] == 'uint8' and float(val) < 0:
                self.__dict__[self.properties[2]] = 'int16'
            self.__dict__[self.properties[6]] = int(float(val))
    
    #NiNa: fill every property except values
    def fillProps(self,txt):
        #don't set name, since ParamModel is responsible for avoiding duplicates
        ps = txt.split(';')
        print(ps)
        for p in range(2,len(ps)):
            self.__dict__[self.properties[p]]=self.pTypes[p](ps[p])
        self.__dict__[self.properties[0]]=self.pTypes[0](ps[0])

    #NiNa: generate params if not in list, add values, check borders, set borders of generated params, load values set 0        
    def fillValuesS0(self,value,pGen):
        if pGen == False:
            if float(value) < self.__dict__[self.properties[3]]:
                return -1,self.__dict__[self.properties[3]]
            if float(value) > self.__dict__[self.properties[4]]:
                return 1,self.__dict__[self.properties[4]]
            else:
                if self.__dict__[self.properties[2]] == 'float32':
                    self.__dict__[self.properties[5]] = float(value)
                else:
                    if self.__dict__[self.properties[2]] == 'uint8' and float(value) < 0:
                        self.__dict__[self.properties[2]] = 'int16'
                    self.__dict__[self.properties[5]] = int(float(value))
                return 0, None
                    
        if pGen == True:
            if float(value) > 0:
                self.__dict__[self.properties[4]] = float(self.roundToTwo((2*float(value))))
                self.__dict__[self.properties[3]] = float(0)
            if float(value) < 0:
                self.__dict__[self.properties[3]] = float(self.roundToTwo((2*float(value))))
                self.__dict__[self.properties[4]] = float(0)
            else:
                if self.__dict__[self.properties[2]] == 'uint8' and float(value) < 0:
                    self.__dict__[self.properties[2]] = 'int16'
                self.__dict__[self.properties[5]] = int(float(value))

    #NiNa: generate params if not in list, add values, check borders, set borders of generated params, load values set 1   
    def fillValuesS1(self,value,pGen):
        if pGen == False:
            if float(value) < self.__dict__[self.properties[3]]:
                return -1,self.__dict__[self.properties[3]]
            if float(value) > self.__dict__[self.properties[4]]:
                return 1,self.__dict__[self.properties[4]]
            else:
                if self.__dict__[self.properties[2]] == 'float32':
                    self.__dict__[self.properties[6]] = float(value)
                else:
                    if self.__dict__[self.properties[2]] == 'uint8' and float(value) < 0:
                        self.__dict__[self.properties[2]] = 'int16'
                    self.__dict__[self.properties[6]] = int(float(value))
                return 0, None
                    
        if pGen == True:
            if float(value) > 0:
                self.__dict__[self.properties[4]] = float(self.roundToTwo((2*float(value))))
                self.__dict__[self.properties[3]] = float(0)
            if float(value) < 0:
                self.__dict__[self.properties[3]] = float(self.roundToTwo((2*float(value))))
                self.__dict__[self.properties[4]] = float(0)
            else:
                if self.__dict__[self.properties[2]] == 'uint8' and float(value) < 0:
                    self.__dict__[self.properties[2]] = 'int16'
                self.__dict__[self.properties[6]] = int(float(value))
        
    def __str__(self):
        return self.name
 

#NiNa: defining a single signal item    
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
               

#NiNa: defining a single param item
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
    
    #NiNa: menu actions for each param item
    def removeInstr(self,Instr):
        self._instrList[:] = [i for i in self._instrList if i!=Instr]
        
    def addInstr(self,Instr):
        self._instrList.append(Instr)
        
    def disconnect(self):
        for i in self._instrList:
            i.disconnectFromParam()
        
#NiNa: class for handling every item in table        
class cMRTableModel(QAbstractTableModel):
    def __init__(self,parent):
        super().__init__(parent)
        self.items=[]
        self.numI=0
        self.paramnrlist = []
        self.minviolationvalues = []
        self.maxviolationvalues = []
        self.minviolationnames = []
        self.maxviolationnames = []
    
    #NiNa: return the names of the items
    def itemNames(self):
        return [x.name for x in self.items] #wow, my first list comprehension
    
    #NiNa: set which columns should be editable
    def flags(self,idx):
        if idx.column() in range(0,5,1):
            return Qt.ItemIsSelectable|Qt.ItemIsEditable|Qt.ItemIsEnabled
        if idx.column() in range(5,7,1):
            return Qt.ItemIsEnabled
    
    #NiNa: removing item from table
    def removeItem(self,row):
        self.beginRemoveRows(QModelIndex(),row,row)
        self.items[row].disconnect()
        self.items.pop(row)
        self.numI-=1
        self.endRemoveRows()
    
    #NiNa: adding new item to table
    def newItem(self,Name):
        while Name in self.itemNames():
            #append 2 to name or increment number at the end
            myr = re.compile('(\d+)$')#get number from end of Name
            res=myr.search(Name)
            #NiNa: avoiding name duplicates
            if res:
                Name = Name[0:res.start()]+str(int(res.group())+1)
            else:
                Name += '2'
        #NiNa: generate parameter numbers        
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
    
    #NiNa: sort table by name
    #TODO: sort table by other
    def sort(self):
        self.beginResetModel()#inform view that everthing is about to change
        self.items.sort(key = lambda x: x.name)
        self.endResetModel()
    
    #NiNa: returns number of columns of table        
    def columnCount(self,parent):
        return len(self.itemClass.properties)
    
    #NiNa: returns number of rows of table
    def rowCount(self,parent):
        return self.numI

    #NiNa: set appearance of head row of table
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

    #NiNa: set appearance of data in table   
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
    
    #NiNa: define what happens if table cells are edited
    def setData(self,idx,val,role=Qt.EditRole):
        if role == Qt.EditRole:
            
            #NiNa: if paramnumbers are edited, take care of duplicates
            if idx.column() == 0:
                self.paramnumbers = [p.paramnr for p in self.items]
                if val in self.paramnumbers:
                    self.bool = False
                else: 
                    self.items[idx.row()].__dict__[self.itemClass.properties[idx.column()]]=val
                    self.bool = True
            
            #NiNa: if paramnames are edited, take care of duplicates
            if idx.column() == 1:
                self.paramnames = [p.name for p in self.items]
                if val in self.paramnames:
                    self.bool = False
                else:
                    self.items[idx.row()].__dict__[self.itemClass.properties[idx.column()]]=val
                    for i in self.items[idx.row()]._instrList:
                        i.ParamNameChanged()
                    self.bool = True
                    
            #NiNa: if datatypes are edited, change type of other members in same row
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
                
            #NiNa: handle which Minima can be set
            if idx.column() == 3:
                self.pvals0 = self.items[idx.row()].__dict__[self.itemClass.properties[5]]
                self.pvals1 = self.items[idx.row()].__dict__[self.itemClass.properties[6]]                
                self.maxval = self.items[idx.row()].__dict__[self.itemClass.properties[4]]
                #NiNa: don't set Min if it is bigger than current Max
                if val >= self.maxval:
                    self.bool = False
                #NiNa: don't set Min if it is bigger than current values
                if self.pvals0 < val or self.pvals1 < val:
                    self.bool = False
                else:
                    if self.items[idx.row()].__dict__[self.itemClass.properties[2]] == 'float32':
                        self.items[idx.row()].__dict__[self.itemClass.properties[idx.column()]]=float(val)
                    else:
                        self.items[idx.row()].__dict__[self.itemClass.properties[idx.column()]]=int(float(val))
                    self.bool = True
                    
            #NiNa: handle which Maxima can be set
            if idx.column() == 4:
                self.pvals0 = self.items[idx.row()].__dict__[self.itemClass.properties[5]]
                self.pvals1 = self.items[idx.row()].__dict__[self.itemClass.properties[6]] 
                self.minval = self.items[idx.row()].__dict__[self.itemClass.properties[3]]
                #NiNa: don't set Max if it is smaller than current Min
                if val <= self.minval:
                    self.bool = False
                #NiNa: don't set Max if it is smaller than current values
                if self.pvals0 > val or self.pvals1 > val:
                    self.bool = False                    
                else:
                    if self.items[idx.row()].__dict__[self.itemClass.properties[2]] == 'float32':
                        self.items[idx.row()].__dict__[self.itemClass.properties[idx.column()]]=float(val)
                    else:
                        self.items[idx.row()].__dict__[self.itemClass.properties[idx.column()]]=int(float(val))
                    self.bool = True
                    
        return self.bool

    #NiNa: for each item: item.save(), saves everything except value
    def save(self):
        res = '<'+self.saveTag+'>\n'
        for p in self.items:
            res+=p.save()
        res += '<\\'+self.saveTag+'>\n'
        return res
    
    #NiNa: save parametervalues of set 0
    def savePS0(self):
        res = '<pValues>\n'
        for p in self.items:
            res+=p.savePS0() 
        res += '<\pValues>\n'
        return res
    
    #NiNa: save parametervalues of set 1
    def savePS1(self):
        res = '<pValues>\n'
        for p in self.items:
            res+=p.savePS1() 
        res += '<\pValues>\n'
        return res
    
    #NiNa: load parametervalues of set 0
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
                i.fillValuesS0(self.pValues[j],False) 
                j += 1
    
    #NiNa: load parametervalues of set 1
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
                i.fillValuesS1(self.pValues[j],False)
                j += 1
 
    #NiNa: when parameters are loaded this method returns the names and values of checked parameter as lists
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
    
    #NiNa: loading and filling the members of parameters except value when project is opened
    def load(self,txt):
        self.beginResetModel()#inform view that everthing is about to change
        while self.numI > 0:
            self.removeItem(self.numI-1)
        myr = re.compile(r'<'+self.saveTag+r'>\n(.+)<\\'+self.saveTag+r'>',re.DOTALL)#the dot also matches newlines
        res=myr.search(txt)
        if res:
            paramSettings = res.group(1)
            for l in paramSettings.splitlines():
                self.newItem(l.split(';')[1])#name must always be first in itemClass.properties
                self.items[-1].fillProps(l)                                              
        self.endResetModel()
     
    #NiNa: borderviolation option: set new Minimum and load value
    def fillMin(self,pset,pname,pmin,pval):
        if pname in [i.name for i in self.items]:
            self.items[[i.name for i in self.items].index(pname)].fillMin(pmin)
            if pset == 0:
                self.items[[i.name for i in self.items].index(pname)].setValS0(pval)
            if pset == 1:
                self.items[[i.name for i in self.items].index(pname)].setValS1(pval)
    
    #NiNa: borderviolation option: set new Maximum and load value
    def fillMax(self,pset,pname,pmax,pval):
        if pname in [i.name for i in self.items]:
            self.items[[i.name for i in self.items].index(pname)].fillMax(pmax)
            if pset == 0:
                self.items[[i.name for i in self.items].index(pname)].setValS0(pval)
            if pset == 1:
                self.items[[i.name for i in self.items].index(pname)].setValS1(pval)
     
    #NiNa: borderviolation option: set value to existing Border
    def setValtoBorder(self,pset,pname,cborder):
        if pname in [i.name for i in self.items]:
            if pset == 0:
                self.items[[i.name for i in self.items].index(pname)].setValS0(cborder)
            if pset == 1:
                self.items[[i.name for i in self.items].index(pname)].setValS1(cborder)
            
    #NiNa: load parameters that were checked, avoid name duplicates, handle loading and generating differently
    def loadP(self,txt,checkedparams):
        #self.beginResetModel()#inform view that everthing is about to change
        self.minviolationnames = []
        self.minviolationvalues = []
        self.maxviolationnames = []
        self.maxviolationvalues = []
        self.currentmin = []
        self.currentmax = []        
        myr = re.compile(r'<pValues>\n(.+)<\\pValues>',re.DOTALL)#the dot also matches newlines
        res=myr.search(txt)
        if res:
            paramSettings = res.group(1)
            for l in paramSettings.splitlines():
                name = l.split(';')[0]
                pvalue = l.split(';')[1]
                print(name)
                if name in checkedparams:
                    if name in [i.name for i in self.items]:#avoid duplicates
                        #NiNa: parameters are not generated
                        pGen = False
                        if self.items[[i.name for i in self.items].index(name)].fillValuesS0(pvalue,pGen)[0] == -1:
                            self.minviolationnames.append(name)
                            self.minviolationvalues.append(pvalue)
                            self.currentmin.append(self.items[[i.name for i in self.items].index(name)].fillValuesS0(pvalue,pGen)[1])
                        if self.items[[i.name for i in self.items].index(name)].fillValuesS0(pvalue,pGen)[0] == 1:
                            self.maxviolationnames.append(name)
                            self.maxviolationvalues.append(pvalue)
                            self.currentmax.append(self.items[[i.name for i in self.items].index(name)].fillValuesS0(pvalue,pGen)[1])
                        else:
                            if 0 in [i.paramset for i in self.items]:
                                self.items[[i.name for i in self.items].index(name)].fillValuesS0(pvalue,pGen)
                            if 1 in [i.paramset for i in self.items]:
                                self.items[[i.name for i in self.items].index(name)].fillValuesS1(pvalue,pGen)
                    else:
                        #NiNa: parameters have to be generated
                        pGen = True
                        self.newItem(name)#name must always be first in itemClass.properties
                        if 0 in [i.paramset for i in self.items]:
                            self.items[-1].fillValuesS0(pvalue,pGen)
                        if 1 in [i.paramset for i in self.items]:
                            self.items[-1].fillValuesS1(pvalue,pGen)
        return self.minviolationnames,self.minviolationvalues,self.maxviolationnames,self.maxviolationvalues,self.currentmin,self.currentmax                  
        #self.endResetModel()
                                                          

#NiNa: add saveTag 'Parameters' to specify ParamTableModel
class cParamTableModel(cMRTableModel):
    def __init__(self,parent):
        super().__init__(parent)
        self.itemClass = mRayParam#store name of param Class
        self.saveTag = 'Parameters'

    #NiNa: lists the instruments connected to a single param
    def listParamsInstr(self,row):
        param = self.items[row]
        for i in param._instrList:
            print(i.instrWidget.objectName())
    
    
#NiNa: add saveTag 'Signals' to specify SignalTableModel, Colorselection for signal possible
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
    
#NiNa: selection window to check which params are needed   
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

        self.layout.addLayout(self.sublayout)
        self.sublayout.addWidget(self.loadbutton)
        self.selectall.clicked.connect(self.actionall)
        self.loadbutton.clicked.connect(self.checkedparamlist)
        
        for x in self.checkboxlist:
            x.toggled.connect(self.unselectselectall)

    def actionall(self):
        for x in self.checkboxlist:
            x.blockSignals(True)
        if self.selectall.isChecked():
            for x in self.checkboxlist:
                x.setChecked(True)
        else:
            for x in self.checkboxlist:
                x.setChecked(False)
        for x in self.checkboxlist:
            x.blockSignals(False)
    
    def unselectselectall(self):
        templist = []
        for x in self.checkboxlist:
            if x.isChecked():
                templist.append(x)
        if len(templist) != len(self.checkboxlist):
            self.selectall.setChecked(False)       
        else:
            self.selectall.setChecked(True)
        
    def checkedparamlist(self):
        for i in range(0,len(self.checkboxlist)):
            if self.checkboxlist[i].isChecked():
                self.checkedparams.append(self.checkboxlist[i].text()) 
        self.parent().LoadParams()
        self.close()
        
#NiNa: class to handle the parameters that violate borders when being checked and loaded       
class BorderViolationsWindow(QDialog):
    def __init__ (self,parent,maxviolationvalues,maxviolationnames,minviolationvalues,minviolationnames,currentmax,currentmin):
        super().__init__(parent)
        self.minviolationnames = minviolationnames
        self.allviolationnames = minviolationnames + maxviolationnames
        self.allviolationvalues = minviolationvalues + maxviolationvalues
        self.currentborders = currentmin + currentmax
        
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.layout.setVerticalSpacing(50)
        self.layout.setHorizontalSpacing(30)
        
        self.setminmaxlayouts = []        
        self.setminmaxspinboxes = []
        self.setnewcheckboxes = []
        self.valtocheckboxes = []
        self.dontloadvaluecheckboxes = []
        
        self.allparamnames = [x.name for x in self.parent().AllMyParams.items]
        self.violationdataTypes = []

        for i in self.allviolationnames:
            if i in self.allparamnames:
                idx = self.allparamnames.index(i)
                self.violationdataTypes.append(self.parent().AllMyParams.items[idx].dataType)
        
        self.applyPushButton = QPushButton("Apply")
        
        for i in range(0,len(self.allviolationnames)):
            #self.layout.setRowMinimumHeight(i, 200)
            self.setminmaxlayouts.append(QVBoxLayout())
            self.setminmaxspinboxes.append(QDoubleSpinBox())
            self.dontloadvaluecheckboxes.append(QCheckBox("Don't Load Value"))
            self.layout.addWidget(QLabel(str(self.allviolationvalues[i])),i,1)
            self.layout.addLayout(self.setminmaxlayouts[i],i,2)
            self.layout.addWidget(self.dontloadvaluecheckboxes[i],i,4)
            self.dontloadvaluecheckboxes[i].setChecked(True)
            self.setminmaxspinboxes[i].setDisabled(True)       
            
        for i in range(0,len(self.minviolationnames)):
            self.setnewcheckboxes.append(QCheckBox("Set new Min and Load"))
            self.valtocheckboxes.append(QCheckBox("Set Value to Min and Load"))
            self.layout.addWidget(QLabel(str(self.allviolationnames[i])+' (Min: '+str(self.currentborders[i])+')'),i,0)        
            if self.checkDataType(i) == True:
                self.setminmaxlayouts[i].addWidget(self.setnewcheckboxes[i])
                self.setminmaxlayouts[i].addWidget(self.setminmaxspinboxes[i])
                self.setminmaxspinboxes[i].setMaximum(float(self.allviolationvalues[i]))
                #NiNa: set Min and Max of displayed doublespinboxes <- for setting new max/min
                if float(self.allviolationvalues[i]) < 0:
                    self.setminmaxspinboxes[i].setMinimum((10)*(float(self.allviolationvalues[i])))
                else:
                    self.setminmaxspinboxes[i].setMinimum((-10)*(float(self.allviolationvalues[i])))
                self.setminmaxspinboxes[i].setValue(float(self.allviolationvalues[i]))
            if self.checkDataType(i) == False:
                self.setminmaxlayouts[i].addWidget(QLabel("Loading current value violates datatype."))               
            self.layout.addWidget(self.valtocheckboxes[i],i,3)
                     
        for i in range(len(self.minviolationnames),len(self.allviolationnames)):
            self.setnewcheckboxes.append(QCheckBox("Set new Max and Laod"))
            self.valtocheckboxes.append(QCheckBox("Set Value to Max and Laod"))
            self.layout.addWidget(QLabel(str(self.allviolationnames[i])+' (Max: '+str(self.currentborders[i])+')'),i,0)            
            if self.checkDataType(i) == True:
                self.setminmaxlayouts[i].addWidget(self.setnewcheckboxes[i])
                self.setminmaxlayouts[i].addWidget(self.setminmaxspinboxes[i])
                self.setminmaxspinboxes[i].setMinimum(float(self.allviolationvalues[i]))
                self.setminmaxspinboxes[i].setMaximum(10*(float(self.allviolationvalues[i])))
                self.setminmaxspinboxes[i].setValue(float(self.allviolationvalues[i]))                
            if self.checkDataType(i) == False:    
                self.setminmaxlayouts[i].addWidget(QLabel("Loading current value violates datatype."))                 
            self.layout.addWidget(self.valtocheckboxes[i],i,3)
                  
        self.layout.addWidget(self.applyPushButton)
        self.applyPushButton.clicked.connect(self.takeAction)
                       
        for i in range(0,len(self.allviolationnames)):
            self.setnewcheckboxes[i].stateChanged.connect(self.disableOthers1)
            self.valtocheckboxes[i].stateChanged.connect(self.disableOthers2)
            self.dontloadvaluecheckboxes[i].stateChanged.connect(self.disableOthers3)       
            
    #NiNa: checking datatype violations
    def checkDataType(self,i):
        if self.violationdataTypes[i] == 'uint8' and (float(self.allviolationvalues[i]) < 0 or float(self.allviolationvalues[i]) > 255):
            return False
        if self.violationdataTypes[i] == 'int16' and (float(self.allviolationvalues[i]) < -32768 or float(self.allviolationvalues[i]) > 32768):
            return False
        else:
            if self.violationdataTypes[i] != 'float32':
                try:
                    int(self.allviolationvalues[i])
                    return True
                except:
                    return False
            else:
                return True
    
    #NiNa: making sure only one option is selected in each row
    def disableOthers1(self):
        for i in range(0,len(self.allviolationnames)):
            if self.setnewcheckboxes[i].isChecked():
                self.setminmaxspinboxes[i].setDisabled(False)
                self.valtocheckboxes[i].setChecked(False)
                self.dontloadvaluecheckboxes[i].setChecked(False)
                
    def disableOthers2(self):
        for i in range(0,len(self.allviolationnames)):
            if self.valtocheckboxes[i].isChecked():
                self.setminmaxspinboxes[i].setDisabled(True)
                self.setnewcheckboxes[i].setChecked(False)
                self.dontloadvaluecheckboxes[i].setChecked(False)
    
    def disableOthers3(self):
        for i in range(0,len(self.allviolationnames)):
            if self.dontloadvaluecheckboxes[i].isChecked():
                self.setminmaxspinboxes[i].setDisabled(True)
                self.valtocheckboxes[i].setChecked(False)
                self.setnewcheckboxes[i].setChecked(False)
    
    #NiNa: handling the violations according to selected options
    def takeAction(self):    
        x = True
        #NiNa: set new Min and load value
        for i in range(0,len(self.minviolationnames)):
            if self.setnewcheckboxes[i].isChecked():
                if self.parent().syncset == 0:
                    self.parent().AllMyParams.fillMin(0,self.allviolationnames[i],self.setminmaxspinboxes[i].value(),self.allviolationvalues[i])
                if self.parent().syncset == 1:
                    self.parent().AllMyParams.fillMin(1,self.allviolationnames[i],self.setminmaxspinboxes[i].value(),self.allviolationvalues[i])
                self.parent().SyncInstr()
        #NiNa: set new Max and load value
        for i in range(len(self.minviolationnames),len(self.allviolationnames)):
            if self.setnewcheckboxes[i].isChecked():
                if self.parent().syncset == 0:
                    self.parent().AllMyParams.fillMax(0,self.allviolationnames[i],self.setminmaxspinboxes[i].value(),self.allviolationvalues[i])
                if self.parent().syncset == 1:
                    self.parent().AllMyParams.fillMax(1,self.allviolationnames[i],self.setminmaxspinboxes[i].value(),self.allviolationvalues[i])
                self.parent().SyncInstr()
        #NiNa: set value to existing border
        for i in range(0,len(self.allviolationnames)):
            if self.valtocheckboxes[i].isChecked():
                if self.parent().syncset == 0:
                    self.parent().AllMyParams.setValtoBorder(0,self.allviolationnames[i],self.currentborders[i])
                if self.parent().syncset == 1:
                    self.parent().AllMyParams.setValtoBorder(1,self.allviolationnames[i],self.currentborders[i])
                self.parent().SyncInstr()  
            #NiNa: do nothing
            if self.dontloadvaluecheckboxes[i].isChecked():
                pass
            #NiNa: make sure that one option is selected each row
            if not self.setnewcheckboxes[i].isChecked() and not self.valtocheckboxes[i].isChecked() and not self.dontloadvaluecheckboxes[i].isChecked():
                ErrorInfo = QMessageBox.information(self,
                                                    'No option chosen.',
                                                    'Please choose an option for every parameter first!',
                                                    QMessageBox.Ok)
                x = False
                break
        if x == True:
            self.close()