import socket
import time

def processCur(num):
    if num > 0x8000:
	num = num - 65536
    return num / 320.0

def processPacket(packet):
    packet = packet.split(',')
    pkt = [float(packet[0])]
    pkt.extend([int(x,16) for x in packet[1:-1]])
    return pkt

class TelemClient:
    def __init__(self, address, port):
        self.context = None
	self.addr = socket.getaddrinfo(address,port)[0]
	self.Ah = 0
	self.lastCur = None
	self.means = [0,0,0,0,0]
	self.meanWeights = [10,100,1000,10000,100000]
	self.curCount = 0
        
    def start(self):
        self.socket = socket.socket(self.addr[0], self.addr[1], self.addr[2])
        self.socket.connect(self.addr[4])
        self.socket.settimeout(0)
        self.data = ""

    def ProcessPacket(self, gui):
        try:
            self.data += self.socket.recv(4096)
        except:
            pass
	ind = self.data.find('\n')
	while ind > 0:
            packet = self.data[:ind + 1]
            self.data = self.data[ind + 1:]
            packet = processPacket(packet)
            ind = self.data.find('\n')
    
	    if not self.context:
		self.context = gui.status.get_context_id("Network")

	    if len(packet) < 2:
		continue

	    gui.status.pop(self.context)
	    gui.status.push(self.context,'Last Packet at %.2f  Skew %.3f' % (packet[0] ,time.time() - packet[0]))

	    if packet[1] == 0x10 and len(packet) == 6:
	        gui.Dashboard.set_status(packet[2],packet[3])
		gui.Dashboard.set_throttle(packet[4])
		gui.Dashboard.set_regen(packet[5])

	    elif packet[1] == 0x30 and len(packet) == 7:
		voltage = (packet[2] * 256 + packet[3]) / 500.0
		current = processCur(packet[4] * 256 + packet[5])
		power = voltage * current
		if self.lastCur:
		    self.Ah += current * (packet[0] - self.lastCur) / 3600.0
		self.lastCur = packet[0]
		self.curCount += 1
                for i in xrange(len(self.means)):
                    if self.curCount < self.meanWeights[i]:
                        self.means[i] = ((self.curCount - 1) * self.means[i] + current) / self.curCount
                    else:
                        self.means[i] = ((self.meanWeights[i] - 1) * self.means[i] + current) / self.meanWeights[i]
		gui.Dashboard.set_voltage(voltage)
		gui.Trackers.set_bus_voltage(voltage)
		gui.Dashboard.set_current(current)
		gui.Dashboard.set_calc(power,self.Ah,self.means)

	    elif packet[1] == 0x31 and len(packet) == 10:
		gui.Dashboard.set_battery_stats(
		    (packet[2] * 256 + packet[3]) / 10000.0,
		    (packet[6] * 256 + packet[7]) / 10000.0,
		    (packet[4] * 256 + packet[5]) / 10000.0)
                gui.Battery.set_cell(packet[9],
                    ((packet[2] * 256 + packet[3]) / 10000.0))

	    elif packet[1] == 0x51 and len(packet) == 7:
		gui.Dashboard.set_speed((packet[3] * 256 + packet[4]) / 10.0)

	    elif packet[1] >= 0x40 and packet[1] <= 0x47 and len(packet) == 10:
		offset = (packet[1] & 0x0F) * 4
		for i in range(4):
		    voltage = (packet[2+2*i]*256 + packet[3+2*i]) / 10000.0
		    gui.Battery.set_cell(offset+i,voltage)
		    if offset+i == 30: gui.Dashboard.set_scrutineering_voltage(voltage)
            

	    elif packet[1] >= 0x48 and packet[1] < 0x50 and len(packet) == 6:
		offset = (packet[1] & 0x0F - 8) * 4
		for i in range(4):
		    gui.Battery.set_temp(offset + i, packet[i+2])
		    if offset+i == 30: gui.Dashboard.set_scrutineering_temp(packet[i+2])

	    elif packet[1] == 0x90 and len(packet) == 3:
		gui.Dashboard.set_sec_pack(packet[2] * 0.058823529411764705)

	    elif packet[1] == 0xc0 and len(packet) == 7:
		voltages = [x / 2.51 for x in packet[3:7]]
		gui.Trackers.set_voltages(voltages,packet[2])

	    elif packet[1] == 0xc1 and len(packet) == 7:
		currents = [x / 51.2 for x in packet[3:7]]
		gui.Trackers.set_currents(currents,packet[2])

	    elif packet[1] == 0x70 and len(packet) == 10:
		channel = packet[2] & 0x0F
                state = {0x00:'Initialize', 0x10:'Precharge',
                    0x20:'Curve Trace', 0x30:'Tracking', 0x40:'Voltage Error',
                    0x50:'Current Error', 0x60:'Temp Error', 0x70:'Boost Error',
                    0x80:'Power Error', 0x90:'Restarting', 0xF0:'State Error'}[packet[2] & 0xF0]
		voltageIn = (packet[3]*256 + packet[4]) / 100.0
		currentIn = (packet[5]*256 + packet[6]) / 1000.0
		currentOut = (packet[7]*256 + packet[8]) / 1000.0
		temp = packet[9] / 2
		gui.Trackers.set_channel(state,voltageIn,currentIn,
                    currentOut,temp,channel)
                gui.Dashboard.set_array(channel,currentOut)
        return True

    def stop(self):
	self.socket.close()
