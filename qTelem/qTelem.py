#!/usr/bin/env python

import sys

import PySide

from PySide.QtCore import QRect, QMetaObject, QObject, Qt
from PySide.QtGui  import (QApplication, QMainWindow, QWidget, 
                           QGridLayout, QTabWidget, QPlainTextEdit,
                           QMenuBar, QMenu, QStatusBar, QAction, 
                           QIcon, QFileDialog, QMessageBox, QFont,
                           QLabel, QLineEdit)

class ConnectionTab(QWidget):
    def __init__(self, parent=None):
        super(ConnectionTab, self).__init__(parent)
        self.grid = QGridLayout(self)
        self.statusLabel = QLabel('Not Connected')
        self.statusLabel.setAlignment(Qt.AlignCenter)
        self.grid.addWidget(self.statusLabel,0,0,1,2)
        self.grid.addWidget(QLabel('Address'),1,0,1,1)
        self.address = QLineEdit('localhost')
        self.grid.addWidget(self.address,1,1,1,1)
        self.grid.addWidget(QLabel('Specification'),2,0,1,1)

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        #self.resize(840,480)
        centralwidget = QWidget(self)
        gridLayout = QGridLayout(centralwidget)
        self.tabWidget = QTabWidget(centralwidget)
        self.connection = ConnectionTab()
        self.tabWidget.addTab(self.connection, "Connection") 


        gridLayout.addWidget(self.tabWidget)
        self.setCentralWidget(centralwidget)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    frame = MainWindow()
    frame.show()
    sys.exit(app.exec_())
