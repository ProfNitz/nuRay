# -*- coding: utf-8 -*-
"""
Created on Thu May 13 17:27:50 2021

@author: Nithu
"""

import serial
import time
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5 import uic
import sys
   

class UI(QWidget):
    arduinoNano = serial.Serial('COM10',115200)
    def __init__(self):
        QWidget.__init__(self)
        uic.loadUi("ArduinoTest.ui",self)
        self.setWindowTitle("ArduinoTest")
        self.pushButton_2.clicked.connect(self.led_On)
        self.pushButton.clicked.connect(self.led_Off)
        self.show()

    def led_On(self):
        self.arduinoNano.write(b'1')
        print("1 has been sent to arduino")

    def led_Off(self):
        self.arduinoNano.write(b'0')
        print("0 has been sent to arduino")

app = QApplication(sys.argv)
UIWindow = UI()
app.exec_()



    