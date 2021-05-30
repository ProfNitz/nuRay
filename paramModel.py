# -*- coding: utf-8 -*-
"""
Created on Wed Jun 12 13:24:32 2019

@author: Nitzsche
"""

from PyQt5.QtCore import Qt, QObject
from PyQt5.QtCore import QAbstractTableModel, QModelIndex
from PyQt5.QtGui import QColor, QFont, QIcon, QPixmap
import re

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
    def save(self):
        res = ''
        for p in self.properties:#export all relevant members
            res+=(str(self.__dict__[p])+';')
        res=res[:-1]+'\n'#replace trailing ; by \n
        #print(res)
        return res
    def fillProps(self,txt):
        #don't set name, since ParamModel is responsible for avoiding duplicates
        ps = txt.split(';')
        for p in range(1,len(ps)):
            self.__dict__[self.properties[p]]=self.pTypes[p](ps[p])
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
    header=['Param Set','Param Nr','Name','Data Type','Min','Max']#Human readable names of members of mRayParam
    properties=['paramset','paramnr','name','dataType','min','max']#relevant members of mRayParam (verbatim!)
    pTypes=[int,int,str,str,float,float]
    def __init__(self,name):
        super().__init__()
        self.name=name
        self.paramset = 1
        self.min=0.0
        self.max=1.0
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
    def itemNames(self):
        return [x.name for x in self.items] #wow, my first list comprehension
    def flags(self,idx):
        return Qt.ItemIsSelectable|Qt.ItemIsEditable|Qt.ItemIsEnabled
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
                
        self.beginInsertRows(QModelIndex(),self.numI,self.numI)#parent is a default (empty) QModelIndex? Copied from an example
        newItem = self.itemClass(Name)
        newItem.paramnr = self.numI
        self.items.append(newItem)
        self.numI+=1
        self.endInsertRows()
    def sort(self):
        self.beginResetModel()#inform view that everthing is about to change
        self.items.sort(key = lambda x: x.name)
        self.endResetModel()
            
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
            self.items[idx.row()].__dict__[self.itemClass.properties[idx.column()]]=val
        return True

    def save(self):
        res = '<'+self.saveTag+'>\n'
        for p in self.items:
            res+=p.save()
        res += '<\\'+self.saveTag+'>\n'
        return res
    def load(self,txt):
        self.beginResetModel()#inform view that everthing is about to change
        self.items = []
        myr = re.compile(r'<'+self.saveTag+r'>\n(.+)<\\'+self.saveTag+r'>',re.DOTALL)#the dot also matches newlines
        res=myr.search(txt)
        if res:
            paramSettings = res.group(1)
            for l in paramSettings.splitlines():
                name = l.split(';')[2]
                if name not in [i.name for i in self.items]:#avoid duplicates
                    self.newItem(l.split(';')[2])#name must always be first in itemClass.properties
                    self.items[-1].fillProps(l)
        self.endResetModel()
    
        

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
