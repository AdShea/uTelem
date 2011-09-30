#!/usr/bin/env python

import os
import os.path
import sys
import serial
import socket
import signal
import threading
import Queue
import time
import atexit    

class PacketPlumber:
    def __init__(self):
        #declare a locks and pipe list
        self.pipeLock = threading.Lock()
        self.pipes = []
    
    def createPipe(self):
        self.pipeLock.acquire()
        newpipe = Queue.Queue()
        self.pipes.append(newpipe)
        self.pipeLock.release()
        return newpipe

    def pushData(self, packet):
        self.pipeLock.acquire()
        for p in self.pipes:
            p.put(packet)
        self.pipeLock.release()

    def destroyPipe(self, pipe):
        self.pipeLock.acquire()
        self.pipes.remove(pipe)
        self.pipeLock.release()

class Packet:
    def __init__(self, data=()):
        self.time = '%.3f' % time.time()
        self.data = data

    def __str__(self):
        output = self.time + ','
        for byte in self.data:
            output += '%02x,' % byte
        output += 'end\r\n'
        return output

class FileLogger(threading.Thread):
    def __init__(self, filename, plumbing, quitting):
        self.quitting = quitting
        #open the file and seek to it's end
        self.file = open(filename, 'a')
        print 'Opened file ' + filename + ' to write log'
        #connect the plumbing
        self.pipe = plumbing.createPipe()
        self.plumbing = plumbing
        super(FileLogger, self).__init__()

    def run(self):
        #Loop while the quit flag isn't set
	counter = 0
        while not self.quitting.isSet():
	    counter += 1
	    if counter > 10:
	        self.file.flush()
	        counter = 0
            try:
                packet = self.pipe.get(True, 1)
            except Queue.Empty:
		continue
            self.file.write(str(packet))
        self.file.close()
        self.plumbing.destroyPipe(self.pipe)

class SerialListener(threading.Thread):
    def __init__(self, deviceName, telemMode, plumbing, quitEvent):
        self.quitting = quitEvent
        self.telemMode = telemMode
        self.port = deviceName
        self.pipes = plumbing
        super(SerialListener, self).__init__()

    def run(self):
        #Open the serial port
        if self.telemMode == 'B3':
            self.ser = serial.Serial(port=self.port, baudrate=9600,
            bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE, timeout=None, xonxoff=0, rtscts=0)
            print 'Opened port "' + self.ser.portstr + '" at ' + str(self.ser.baudrate)
        elif self.telemMode == 'C1':
            self.ser = serial.Serial(port=self.port, baudrate=9600,
            bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE, timeout=None, xonxoff=0, rtscts=0)
            print 'Opened port "' + self.ser.portstr + '" at ' + str(self.ser.baudrate)
        elif self.telemMode == 'file' or self.telemMode == 'File':
            self.ser = open(self.port,'r')
            print 'Opened file "' + self.port + '" for input'
        else:
            print 'Invalid telemetry serial format! quitting'
            self.quitting.set()
            return
        while not self.quitting.isSet():
            if self.telemMode == 'B3':
                data = []
                byte = ''
                while byte != chr(0xDD):
                    byte = self.ser.read(1)
                    print 'byte',byte
                    if byte:
                        data.append(ord(byte))
                packet = Packet(tuple(data))
            elif self.telemMode == 'C1':
		data = self.ser.readline()
                data = data.strip()
                if (len(data) % 2) != 0:
                    continue
                bytes = []
                for i in xrange(len(data)/2):
		    try:
			bytes.append(int(data[2*i:2*i + 2],16))
		    except:
			continue
                packet = Packet(tuple(bytes))
            elif self.telemMode == 'file' or self.telemMode == 'File':
                data = self.ser.readline().strip().split(',')
                if data[0] == '':
                    break
                date = data[0]
                if data[-1] == 'end':
                    data = data[:-1]
                data = map(lambda a:int(a, 16), data[1:])
                packet = Packet(tuple(data))
                packet.time = date
                time.sleep(.1)
            self.pipes.pushData(packet)
        self.ser.close()
        self.quitting.set()

class NetHandler(threading.Thread):
    def __init__(self, socket, address, plumbing, quitting):
        self.socket = socket
        self.quitting = quitting
        self.pipe = plumbing.createPipe()
        self.plumbing = plumbing
        self.address = address
        print time.ctime() + ' : New client connected from ' + address[0] + ':' + str(address[1])
        super(NetHandler, self).__init__()

    def run(self):
        closed = False
        while not self.quitting.isSet() and not closed:
            try:
                packet = str(self.pipe.get(True, 5))
            except Queue.Empty:
                continue
            totalsent = 0
            while totalsent < len(packet):
                try:
                    sent = self.socket.send(packet[totalsent:])
                except:
                    closed = True
                if sent == 0:
                    closed = True
                totalsent += sent
        self.socket.close()
        print time.ctime() + ' : ' + self.address[0] + ':' + str(self.address[1]) + ' disconnected'
        self.plumbing.destroyPipe(self.pipe)


#First parse the command line args
if '-h' in sys.argv or '--help' in sys.argv or (len(sys.argv) == 1):
    print 'netTelem is a telemetry server that takes data from a serial'
    print 'port, logs it, and serves it out for clients on a network.\n'
    print 'USAGE: netTelem [options]\n'
    print '-h, --help               Show this help message.\n'
    print "-p, --port <number>      Set the server's port.  Default is 8192.\n"
    print "-s, --serial <device>    Serial port device.  Tries using the first availiable.\n"
    print "-f, --file <filename>    Enable logging to a specified file.\n"
    print "-m, --mode <format>      Data input format.  Valid options are B3, C1, and File."
    sys.exit()


serverPort = 8192
if '-p' in sys.argv:
    serverPort = sys.argv[sys.argv.index('-p') + 1]
if type(serverPort) != int:
    serverPort = 8192
   
if '--port' in sys.argv:
    serverPort = sys.argv[sys.argv.index('--port') + 1]
if type(serverPort) != int:
    serverPort = 8192

serialDevice = 0
if '-s' in sys.argv:
    serialDevice = sys.argv[sys.argv.index('-s') + 1]

if '--serial' in sys.argv:
    serialDevice = sys.argv[sys.argv.index('--serial') + 1]

if '-f' in sys.argv:
    logFilename = sys.argv[sys.argv.index('-f') + 1]

if '--file' in sys.argv:
    logFilename = sys.argv[sys.argv.index('--file') + 1]

if '-m' in sys.argv:
    telemMode = sys.argv[sys.argv.index('-m') + 1]

if '--mode' in sys.argv:
    telemMode = sys.argv[sys.argv.index('--mode') + 1]

plumbing = PacketPlumber()
web = []

#set up the signal handler
quit = threading.Event()
atexit.register(quit.set)
signal.signal(signal.SIGTERM, quit.set)

#Fork the file logger
flogger = FileLogger(logFilename, plumbing, quit)
    
#Fork the serial port listener
slistener = SerialListener(serialDevice, telemMode, plumbing, quit)

#Start those threads
flogger.start()
slistener.start()

#Setup the server
serverSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSock.bind(('', serverPort))
serverSock.listen(5)

atexit.register(serverSock.close)

#Begin the server loop
while not quit.isSet():
        #Accept a connection
        (clientsocket, address) = serverSock.accept()
    #Give it a thread
        newThread = NetHandler(clientsocket, address, plumbing, quit)
        newThread.start()
        web.append(newThread)
