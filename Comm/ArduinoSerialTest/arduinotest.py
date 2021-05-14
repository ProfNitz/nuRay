# -*- coding: utf-8 -*-
"""
Created on Thu May 13 17:27:50 2021

@author: Nithu
"""

import serial
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5 import uic
import sys
   

class UI(QWidget):
    arduinoNano = serial.Serial('COM10',115200)
    def __init__(self):
        QWidget.__init__(self)
        uic.loadUi("ArduinoTest.ui",self)
        self.setWindowTitle("ArduinoTest")
        self.initLED1()
        self.initLED2()
        self.show()
        
    def initLED1(self):
        self.pushButton_2.clicked.connect(self.led_On)
        self.pushButton.clicked.connect(self.led_Off)
    
    def initLED2(self):
        self.dial.setMinimum(0)
        self.dial.setMaximum(255)
        self.dial.setNotchesVisible(True)
        self.dial.valueChanged.connect(self.spinBox.setValue)
        self.dial.valueChanged.connect(self.led_ctrl)
        self.spinBox.setMinimum(0)
        self.spinBox.setMaximum(255)
        self.spinBox.valueChanged.connect(self.dial.setValue)
        self.spinBox.valueChanged.connect(self.led_ctrl)

    def led_On(self):
        self.arduinoNano.write(b'a')
        self.arduinoNano.write(bytes([1]))
        print("1 has been sent to arduino")

    def led_Off(self):
        self.arduinoNano.write(b'a')
        self.arduinoNano.write(bytes([0]))
        print("0 has been sent to arduino")
        
    def led_ctrl(self):
        self.arduinoNano.write(b'b')
        self.arduinoNano.write(bytes([self.dial.value()]))
        
    def closeEvent(self,event):
        self.arduinoNano.close()

app = QApplication(sys.argv)
UIWindow = UI()
app.exec_()



    