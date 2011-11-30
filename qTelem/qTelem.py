#!/usr/bin/env python

import sys
from collections import defaultdict
from string import Formatter

import PySide

from PySide.QtCore import (QRect, QMetaObject, QObject, Qt, QThread,
                           Signal)
from PySide.QtGui  import (QApplication, QMainWindow, QWidget, 
                           QGridLayout, QTabWidget, QPlainTextEdit,
                           QMenuBar, QMenu, QStatusBar, QAction, 
                           QIcon, QFileDialog, QMessageBox, QFont,
                           QLabel, QLineEdit, QPushButton,
                           QScrollArea, QSizePolicy)

maxHistory = 100


class ConnectionTab(QWidget):
    def __init__(self, socket, parent=None):
        super(ConnectionTab, self).__init__(parent)
        self.connected = False
        self.client = None
        self.sock = socket
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

    def sockChange(self, state):
        if state is QAbstractSocket.UnconnectedState:
            self.statusLabel.setText('Not Connected')
            self.conButton.setText('&Connect')
            self.address.setDisabled(False)
        elif state is QAbstractSocket.HostLookupState:
            self.statusLabel.setText('Looking up Host')
            self.address.setDisabled(True)
        elif state is QAbstractSocket.ConnectingState:
            self.statusLabel.setText('Connecting')
            self.address.setDisabled(True)
        elif state is QAbstractSocket.ConnectedState:
            self.statusLabel.setText('Connected to '+self.sock.peerName())
            self.conButton.setText('Dis&connect')
            self.address.setDisabled(True)
        elif state is QAbstractSocket.ClosingState:
            self.statusLabel.setText('Closing connection')

    def consume(self, packet):
        pass


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

    def consume(self, packet):
        for control in self.controls:
            control.consume(self.data)


class SystemState():
    def __init__(self, spec=None):
        self.units = {}
        self.data = defaultdict(float)
        self.time = {}
        self.dt = {}
        self.packets = defaultdict(Packet)
        self.handlers = defaultdict(list)
        self.packets['data'] = self.data
        if spec: self.loadSpecification(spec)

    def consume(self, packet):
        print self.data
        self.packets['dt'] = packet.time - self.packets['x{0:08x}_{1:d}'.format(packet.header,
                len(packet.data))].time
        if self.packets['dt'] > 24*60*60: self.packets['dt'] = 0
        self.packets['x{:08x}'.format(packet.header)] = packet
        self.packets['x{0:08x}_{1:d}'.format(packet.header,len(packet.data))] = packet
        dlist = []
        for datum,expression in self.handlers[packet.header]:
            dlist.append(datum)
            expression = expression.strip().format(**self.packets)
            if expression[0] == '+':
                self.data[datum] += eval(expression[1:])
            else:
                self.data[datum] = eval(expression)
            self.time[datum] = packet.time
        for source in dlist:
            for datum,expression in self.handlers[source]:
                expression = expression.strip().format(**self.packets)
                if expression[0] == '+':
                    self.data[datum] += eval(expression[1:])
                else:
                    self.data[datum] = eval(expression)
                self.time[datum] = packet.time
        for callback in self.watchers:
            callback(self)

    def loadSpecification(self, spec):
        self.handlers = defaultdict(list)
        self.data = defaultdict(float)
        self.units = {}
        self.time = {}
        for line in spec:
            self.appendSpecification(line)
        
    def appendSpecification(self, spec):
        spec = spec.strip().split(':')
        self.units[spec[0]] = spec[1]
        f = Formatter()
        fields = (x[1] for x in f.parse(spec[2]))
        for fill in fields:
            if f[0] == 'x':
                idx = min(x.find('_'),x.find('.'))
                if idx < 0:
                    self.handlers[int(x[1:],16)] = (spec[0],spec[2])
                else:
                    self.handlers[int(x[1:idx],16)] = (spec[0],spec[2])


class Packet():
    def __init__(self, text=None):
        if text:
            text = text.strip().split(',')
            self.time = float(text[0])
            self.header = int(text[1],16)
            self.data = [int(x,16) for x in text[2:]]
        else:
            self.time = 0
            self.header = 0
            self.data = []

    def __str__(self):
        return '{0:.3f},{1:08x},{2}\r\n'.format(self.time,self.header,
                ','.join(('{:02x}'.format(x) for x in self.data)))

    def __repr__(self):
        return 'Packet(' + str(self).strip() + ')'

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

    

    def readData(self):
        self.data += self.socket(readAll)

	ind = self.data.find('\n')
	while ind > 0:
            packet = self.data[:ind + 1]
            self.data = self.data[ind + 1:]
            if packet[0] == '!':
                self.readSpec(packet[1:])
                continue
            packet = Packet(packet)
            ind = self.data.find('\n')
            
            self.dataParser.consume(packet)
            for page in (self.tabWidget.widget(x) for x in 
                    xrange(self.tabWidget.count())):
                page.consume(packet)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    frame = MainWindow()
    frame.show()
    sys.exit(app.exec_())
