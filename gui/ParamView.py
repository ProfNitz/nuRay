# -*- coding: utf-8 -*-
"""
Created on Wed Jun  5 23:40:23 2019

@author: Nitzsche
"""


import inspect #for debugging
from PyQt5.QtCore import QRect
from PyQt5.QtGui import QCursor, QColor
from PyQt5.QtWidgets import (QListWidget, QHBoxLayout, QColorDialog,
QAction, QTableView, QDialog, QItemDelegate,QMenu)

#my own modules
from globalThings import nuRDataTypes


class cDataTypeListDelegate(QItemDelegate):

    #TODO: only use visible data types (check visible property of data type)
    Items=nuRDataTypes.keys()

    def __init__(self,parent):
        super().__init__(parent)
        
    def createEditor(self, parent,option,idx):
        editor = QListWidget(parent)
        editor.addItems(self.Items)
        return editor
    def setEditorDate(self,editor,idx):
        idx_of_current_value=self.Items.index(idx.data())
        editor.setCurrentItem(editor.item(idx_of_current_value))
    def setModelData(self,editor,model,idx):
        choice=editor.currentItem().text()
        model.setData(idx,choice)
    def updateEditorGeometry(self, editor, option, index):
        super().updateEditorGeometry(editor,option,index)#places editor in cell
        #now wew want to make it higher, so the list becomes visible
        r=editor.geometry()
        editor.setGeometry(r.x(),r.y(),r.width(),70)
        #editor.setGeometry(200,250)

class cColorListDelegate(QItemDelegate):
    def __init__(self,parent):
        super().__init__(parent)
        
    def createEditor(self, parent,option,idx):
        editor = QColorDialog(parent)
        return editor
    def setEditorDate(self,editor,idx):
        editor.setCurrentColor(idx.data())
        #idx_of_current_value=self.Items.index(idx.data())
        #editor.setCurrentItem(editor.item(idx_of_current_value))
    def setModelData(self,editor,model,idx):
        choice=editor.selectedColor()
        model.setData(idx,choice)
    def updateEditorGeometry(self, editor, option, index):
        super().updateEditorGeometry(editor,option,index)#places editor in cell
        #now wew want to make it higher, so the list becomes visible
        r=editor.geometry()
        editor.setGeometry(0,0,200,200)
        #editor.setGeometry(200,250)


class nuRAbstractTableView(QTableView):
    def addParam(self):
        self.model().newItem('New')
    def removeParam(self,row):
        self.model().removeItem(row)
    def sortParams(self):
        self.model().sort()
    def listParamsInstr(self,row):
        self.model().listParamsInstr(row)
    
class cSignalTableView(nuRAbstractTableView):
    def contextMenuEvent(self, event):
        idx=self.indexAt(event.pos())
        
        #TODO: Add Param Below/Above
        
        self.menu=QMenu(self)
        addAct = QAction('Add Signal',self)
        addAct.triggered.connect(self.addParam)
        self.menu.addAction(addAct)

        if idx.isValid():#user clicked on an existing parameter
            removeAct = QAction('Remove Signal',self)
            removeAct.triggered.connect(lambda: self.removeParam(idx.row()))
            self.menu.addAction(removeAct)


        if self.model().rowCount(self)>1:
            sortAct = QAction('Sort Signals',self)
            sortAct.triggered.connect(self.sortParams)
            self.menu.addAction(sortAct)
            
        
        self.menu.popup(QCursor.pos())
    
    

class cParamTableView(nuRAbstractTableView):
    def contextMenuEvent(self, event):
        idx=self.indexAt(event.pos())
        
        #TODO: Add Param Below/Above
        
        self.menu=QMenu(self)
        addAct = QAction('Add Param',self)
        addAct.triggered.connect(self.addParam)
        self.menu.addAction(addAct)

        if idx.isValid():#user clicked on an existing parameter
            removeAct = QAction('Remove Param',self)
            removeAct.triggered.connect(lambda: self.removeParam(idx.row()))
            self.menu.addAction(removeAct)
            listAct = QAction('List Instrumnts',self)
            listAct.triggered.connect(lambda: self.listParamsInstr(idx.row()))
            self.menu.addAction(listAct)


        if self.model().rowCount(self)>1:
            sortAct = QAction('Sort Params',self)
            sortAct.triggered.connect(self.sortParams)
            self.menu.addAction(sortAct)
            
        
        self.menu.popup(QCursor.pos())



class ParamSettingsWindow(QDialog):
    def __init__(self,parent,AllParams):
        #super(ParamSettingsWindow).__init__(self)
        #QDialog.__init__(self)
        super().__init__(parent)
        self.resize(450,210)
        self.lv = cParamTableView(self)
        self.lv.setGeometry(QRect(5,5,440,200))
        self.lv.setItemDelegateForColumn(1,cDataTypeListDelegate(self.lv))

        self.lv.setModel(AllParams)
        
        self.layout=QHBoxLayout()
        self.layout.addWidget(self.lv)
        self.setLayout(self.layout)
        
class SignalSettingsWindow(QDialog):
    def __init__(self,parent,AllSignals):
        #super(ParamSettingsWindow).__init__(self)
        #QDialog.__init__(self)
        super().__init__(parent)
        self.resize(450,210)
        self.lv = cSignalTableView(self)
        self.lv.setGeometry(QRect(5,5,440,200))
        self.lv.setItemDelegateForColumn(1,cDataTypeListDelegate(self.lv))
        self.lv.setItemDelegateForColumn(4,cColorListDelegate(self.lv))

        self.lv.setModel(AllSignals)

        self.layout=QHBoxLayout()
        self.layout.addWidget(self.lv)
        self.setLayout(self.layout)
 