#!/usr/bin/env python

import sys

import PySide

from PySide.QtCore import QRect, QMetaObject, QObject, Qt
from PySide.QtGui  import (QApplication, QMainWindow, QWidget, 
                           QGridLayout, QTabWidget, QPlainTextEdit,
                           QMenuBar, QMenu, QStatusBar, QAction, 
                           QIcon, QFileDialog, QMessageBox, QFont,
                           QLabel, QLineEdit, QPushButton,
                           QScrollArea, QSizePolicy)

maxHistory = 100

class ConnectionTab(QWidget):
    def __init__(self, parent=None):
        super(ConnectionTab, self).__init__(parent)
        self.connected = False
        self.client = None
        self.grid = QGridLayout(self)
        self.statusLabel = QLabel('Not Connected')
        self.statusLabel.setAlignment(Qt.AlignCenter)
        self.grid.addWidget(self.statusLabel,0,0,1,2)
        self.grid.addWidget(QLabel('Address'),1,0,1,1)
        self.address = QLineEdit('localhost')
        self.address.returnPressed.connect(self.connect)
        self.grid.addWidget(self.address,1,1,1,1)
        self.grid.addWidget(QLabel('Specification'),2,0,1,1)
        self.conButton = QPushButton("&Connect", self)
        self.grid.addWidget(self.conButton,3,0,1,2)
        self.conButton.clicked.connect(self.connect)

    def connect(self):
        if self.connected:
            #self.client.stop()
            self.statusLabel.setText('Not Connected')
            self.conButton.setText('&Connect')
            self.address.setEnabled(True)
            self.connected = False
        else:
            self.statusLabel.setText('Connected to ' +
                    self.address.text())
            self.conButton.setText('Dis&connect')
            self.address.setDisabled(True)
            self.connected = True


class PacketWatch(QWidget):
    def __init__(self, header=None, parent=None):
        super(PacketWatch, self).__init__(parent)
        self.header = header
        self.history = []
        self.length = None
        self.lasttime = None
        self.grid = QGridLayout(self)
        self.grid.addWidget(QLabel('Time'),0,0,1,1)
        self.delay = QLineEdit('0')
        self.delay.setReadOnly(True)
        self.grid.addWidget(self.delay,0,1,1,1)
        self.grid.addWidget(QLabel('Header'),0,2,1,1)
        self.headerTxt = QLineEdit(str(self.header))
        if self.header:
            self.headerTxt.setReadOnly(True)
        self.grid.addWidget(self.headerTxt,0,3,1,1)
        self.grid.addWidget(QLabel('Payload'),0,4,1,1)
        self.payload = QLineEdit()
        self.payload.setReadOnly(True)
        self.grid.addWidget(self.payload,0,5,1,1)

    def consume(self, packet):
        if packet.header == self.header:
            self.history.insert(0,packet)
            if len(self.history) > maxHistory:
                self.history = self.history[:maxHistory]
            self.lasttime = time()
            self.payload.setText(' '.join(
                ['%02x'.format(x) for x in packet.data]))
            self.delay.setText('0')

    def setHeader(self, header):
        self.header = header
        self.headerTxt.setReadOnly(True)


class TelemTab(QScrollArea):
    def __init__(self, data, parent=None):
        super(TelemTab, self).__init__(parent)
        self.data = data
        self.centralWidget = QWidget()
        self.grid = QGridLayout(self.centralWidget)
        self.addButton = QPushButton("&Add Control")
        self.addButton.clicked.connect(self.addControl)
        self.grid.addWidget(self.addButton)
        self.setWidget(self.centralWidget)
        self.setWidgetResizable(True)
        
        
    def addControl(self):
        self.grid.addWidget(QPushButton("yay"))

    def consume(self):
        for control in self.controls:
            control.consume(self.data)

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        #self.resize(840,480)
        centralwidget = QWidget(self)
        gridLayout = QGridLayout(centralwidget)
        self.tabWidget = QTabWidget(centralwidget)
        self.connection = ConnectionTab()
        self.tabWidget.addTab(self.connection, "Connection") 
        self.tabWidget.addTab(TelemTab(self),"Sensors")

        gridLayout.addWidget(self.tabWidget)
        self.setCentralWidget(centralwidget)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    frame = MainWindow()
    frame.show()
    sys.exit(app.exec_())
