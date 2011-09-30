import pygtk
pygtk.require('2.0')
import gtk

class BatteryPage:
    def __init__(self,parent,nCells):
        self.container = gtk.Table(4,15,False)
        self.tooltips = gtk.Tooltips()
        self.cells = []
    	self.labels = []
        for i in xrange(nCells):
            cell = gtk.ProgressBar()
            if i < (nCells / 2):
                cell.set_orientation(gtk.PROGRESS_TOP_TO_BOTTOM)
            else:
                cell.set_orientation(gtk.PROGRESS_BOTTOM_TO_TOP)
            label = gtk.Label('%2d' % i)
            if i < (nCells / 2):
                self.container.attach(label,i,i+1,0,1,
                    gtk.FILL|gtk.EXPAND,gtk.FILL)
                self.container.attach(cell,i,i+1,1,2,
                    gtk.FILL|gtk.EXPAND,gtk.FILL|gtk.EXPAND)
            else:
                self.container.attach(cell,29 - i,30 - i,2,3,
                    gtk.FILL|gtk.EXPAND,gtk.FILL|gtk.EXPAND)
                self.container.attach(label,29 - i,30 - i,3,4,
                    gtk.FILL|gtk.EXPAND,gtk.FILL)
            label.show()
            self.cells.append(cell)
            self.labels.append(label)
            self.set_cell(i,0.0)
            cell.show()
        parent.add(self.container)
        self.container.show()

    def set_cell(self,id,voltage):
        if id >= len(self.cells):
            return
        if voltage < 3.0:
            self.cells[id].set_fraction(0)
        elif voltage > 4.2:
            self.cells[id].set_fraction(1)
        else:
            self.cells[id].set_fraction((voltage - 3.0) / 1.2)
        self.tooltips.set_tip(self.cells[id], '%.3f V' % voltage)
        self.cells[id].set_text('%.3f V' % voltage)

    def set_temp(self,id,temp):
        if id >= len(self.labels):
            return
        self.labels[id].set_text('%2d: %2dC' % (id,temp))

class DashboardPage:
    def __init__(self, parent):
        self.VData = 0
        self.ArrayCurrents = []
        self.ArrayIndex = []        

        self.container = gtk.Table(5,2,False)
        self.speed = gtk.ProgressBar()
        self.container.attach(self.speed,0,1,0,1)
        self.speed.show()
        
        self.throttle = gtk.ProgressBar()
        self.container.attach(self.throttle,0,1,1,2)
        self.throttle.show()

        self.regen = gtk.ProgressBar()
        self.container.attach(self.regen,0,1,2,3)
        self.regen.show()

        self.status = gtk.ProgressBar()
        self.container.attach(self.status,0,1,3,4)
        self.status.set_fraction(0)
        self.status.show()

        self.currentout = gtk.ProgressBar()
        self.container.attach(self.currentout,1,2,0,1)
        self.currentout.show()

        self.arrayin = gtk.ProgressBar()
        self.container.attach(self.arrayin,1,2,1,2)
        self.arrayin.show()

        self.voltage = gtk.ProgressBar()
        self.container.attach(self.voltage,1,2,2,3)
        self.voltage.show()

        self.batStats = gtk.ProgressBar()
        self.container.attach(self.batStats,1,2,3,4)
        self.batStats.show()

        self.batCalc = gtk.Label()
        self.container.attach(self.batCalc,1,2,4,5)
        self.batCalc.show()
        
        self.scrutineering = gtk.Label()
        self.container.attach(self.scrutineering,0,1,4,5)
        self.scrutineering.show()
        self.scrut_V = 0.0
        self.scrut_T = 0.0

        parent.add(self.container)
        #parent.pack_start(self.container,False,True,0)
        self.container.show()
    
    def set_scrutineering_voltage(self, voltage):
        self.scrut_V = voltage
        self.scrutineering.set_text('Scrutineering: %.3fV %dC' % (self.scrut_V, self.scrut_T))

    def set_scrutineering_temp(self, temp):
        self.scrut_T = temp
        self.scrutineering.set_text('Scrutineering: %.3fV %dC' % (self.scrut_V, self.scrut_T))

    def set_array(self,id,current):
        if id in self.ArrayIndex:
            offset = self.ArrayIndex.index(id)
            self.ArrayCurrents[offset] = current
        else:
            self.ArrayIndex.append(id)
            self.ArrayIndex.sort()
            offset = self.ArrayIndex.index(id)
            self.ArrayCurrents.insert(offset,current)
        power = sum(self.ArrayCurrents) * self.VData
        self.arrayin.set_fraction(min(1,power / 2000.0))
        self.arrayin.set_text('%.1fW' % power)

    def set_speed(self,speed):
        if speed > 80 or speed < 0:
            self.speed.set_fraction(0)
        else:
            self.speed.set_fraction(speed / 80.0)
        self.speed.set_text('%.1f MPH   %.1f KPH' % (speed,speed * 1.609))

    def set_throttle(self, throttle):
        self.throttle.set_fraction(throttle / 255.0)
        self.throttle.set_text('%d%%' % (throttle * 100.0 / 255.0))

    def set_regen(self, regen):
        self.regen.set_fraction(regen / 255.0)
        self.regen.set_text('%d%%' % (regen * 100.0 / 255.0))
    
    def set_calc(self, power, Ah, Means):
        text = '%.1fW %.3fAh' % (power, Ah)
        for x in Means:
            text += ' %.3fA' % x
        self.batCalc.set_text(text)

    def set_current(self, current):
        self.currentout.set_fraction(abs(current) / 60.0)
        if current > 0:
            self.currentout.set_orientation(gtk.PROGRESS_RIGHT_TO_LEFT)
        else:
            self.currentout.set_orientation(gtk.PROGRESS_LEFT_TO_RIGHT)
        self.currentout.set_text('%.3fA' % current)

    def set_voltage(self,voltage):
        self.VData = voltage
        if voltage < 90:
            self.voltage.set_fraction(0)
        elif voltage > 126:
            self.voltage.set_fraction(1)
        else:
            self.voltage.set_fraction((voltage - 90) / 36.0)
        self.voltage.set_text('%.2fV (%.3fV)' % (voltage,voltage / 30))

    def set_status(self,status1,status2):
        text = '%.1fV' % (self.status.get_fraction() * 3.6 + 9.0,)
        if not status1 & 0x08:
            text += " Disabled"
        elif (status1 & 0x09) == 0x09:
            text += " Forward"
        elif status1 & 0x08:
            text += " Reverse"
        if status1 & 0x80:
            text += " Headlights"
        if status1 & 0x02:
            text += " Brake"
        if status1 & 0x40:
            text += " Left"
        if status1 & 0x20:
            text += " Right"
        self.status.set_text(text)

    def set_sec_pack(self,voltage):
        if voltage < 9.0:
            self.status.set_fraction(0)
        elif voltage > 12.6:
            self.status.set_fraction(1)
        else:
            self.status.set_fraction((voltage - 9.0) / 3.6)

    def set_battery_stats(self,min,avg,max):
        if max - min > .050:
            self.batStats.set_fraction(1.0)
        elif max < min:
            self.batStats.set_fraction(0.0)
        else:
            self.batStats.set_fraction((max - min) / 0.050)
            self.batStats.set_text('Min: %.3fV Avg:%.3fV Max:%.3fV Split:%.3fV' % 
                (min, avg, max, max-min))

class TrackerPage:
    def __init__(self,parent):
        self.container = gtk.Table(1,5,False)
        self.parent = parent
        self.voltsIn = []
        self.currentsIn = []
        self.currentsOut = []
        self.powersIn = []
        self.states = []
        self.temps = []
        self.voltsOut = 0
        self.headers = []
        self.sdisp = []
        self.vidisp = []
        self.cidisp = []
        self.codisp = []
        self.pidisp = []
        self.tdisp = []
        label = gtk.Label('State')
        self.container.attach(label,0,1,0,1,gtk.FILL|gtk.EXPAND,gtk.FILL)
        label.show()
        label = gtk.Label('Voltage In')
        self.container.attach(label,1,2,0,1,gtk.FILL|gtk.EXPAND,gtk.FILL)
        label.show()
        label = gtk.Label('Current In')
        self.container.attach(label,2,3,0,1,gtk.FILL|gtk.EXPAND,gtk.FILL)
        label.show()
        label = gtk.Label('Current Out')
        self.container.attach(label,3,4,0,1,gtk.FILL|gtk.EXPAND,gtk.FILL)
        label.show()
        label = gtk.Label('Power In')
        self.container.attach(label,4,5,0,1,gtk.FILL|gtk.EXPAND,gtk.FILL)
        label.show()
        label = gtk.Label('Temperature')
        self.container.attach(label,5,6,0,1,gtk.FILL|gtk.EXPAND,gtk.FILL)
        label.show()
        parent.pack_start(self.container,False,True,0)
        #self.container.show()

    def set_bus_voltage(self,voltage):
        self.voltsOut = voltage
        self.update_displays()    

    def set_channel(self, state, voltageIn, 
        currentIn, currentOut, temp, header):

        if header in self.headers:
            offset = self.headers.index(header)
            self.states[offset] = state
            self.voltsIn[offset] = voltageIn
            self.currentsIn[offset] = currentIn
            self.currentsOut[offset] = currentOut
            self.powersIn[offset] = voltageIn * currentIn
            self.temps[offset] = temp
        else:
            self.headers.append(header)
            self.headers.sort()
            offset = self.headers.index(header)
            self.container.set_property('n-rows',
            self.container.get_property('n-rows') + 1)
            self.states.insert(offset, state)
            self.voltsIn.insert(offset, voltageIn)
            self.currentsIn.insert(offset, currentIn)
            self.currentsOut.insert(offset, currentOut)
            self.powersIn.insert(offset, voltageIn * currentIn)
            self.temps.insert(offset, temp)
            self.sdisp.append(gtk.Label(state))
            self.vidisp.append(gtk.ProgressBar())
            self.cidisp.append(gtk.ProgressBar())
            self.codisp.append(gtk.ProgressBar())
            self.pidisp.append(gtk.ProgressBar())
            self.tdisp.append(gtk.ProgressBar())
            self.reattach_displays()
        self.update_displays()

    def reattach_displays(self):
        for i in xrange(len(self.vidisp)):
            if not self.sdisp[i].parent:
                self.container.attach(self.sdisp[i],0,1,i+1,i+2,
                gtk.FILL|gtk.EXPAND,gtk.FILL)
                self.sdisp[i].show()
        for i in xrange(len(self.vidisp)):
            if not self.vidisp[i].parent:
                self.container.attach(self.vidisp[i],1,2,i+1,i+2,
                gtk.FILL|gtk.EXPAND,gtk.FILL)
                self.vidisp[i].show()
        for i in xrange(len(self.cidisp)):
            if not self.cidisp[i].parent:
                self.container.attach(self.cidisp[i],2,3,i+1,i+2,
                gtk.FILL|gtk.EXPAND,gtk.FILL)
                self.cidisp[i].show()
        for i in xrange(len(self.codisp)):
            if not self.codisp[i].parent:
                self.container.attach(self.codisp[i],3,4,i+1,i+2,
                gtk.FILL|gtk.EXPAND,gtk.FILL)
                self.codisp[i].show()
        for i in xrange(len(self.pidisp)):
            if not self.pidisp[i].parent:
                self.container.attach(self.pidisp[i],4,5,i+1,i+2,
                gtk.FILL|gtk.EXPAND,gtk.FILL)
                self.pidisp[i].show()
        for i in xrange(len(self.tdisp)):
            if not self.tdisp[i].parent:
                self.container.attach(self.tdisp[i],5,6,i+1,i+2,
                gtk.FILL|gtk.EXPAND,gtk.FILL)
                self.tdisp[i].show()
            self.container.show()

    def update_displays(self):
        for i in xrange(len(self.states)):
            self.sdisp[i].set_text(self.states[i])
        for i in xrange(len(self.voltsIn)):
            self.vidisp[i].set_fraction(self.voltsIn[i] / 120.0)
            self.vidisp[i].set_text('%.1f V' % self.voltsIn[i])
        for i in xrange(len(self.currentsIn)):
            self.cidisp[i].set_fraction(self.currentsIn[i] / 7.0)
            self.cidisp[i].set_text('%.2f A' % self.currentsIn[i])
        for i in xrange(len(self.currentsOut)):
            self.codisp[i].set_fraction(self.currentsOut[i] / 7.0)
            self.codisp[i].set_text('%.2f A' % self.currentsOut[i])
        for i in xrange(len(self.powersIn)):
            self.pidisp[i].set_fraction(self.powersIn[i] / 1000.0)
            self.pidisp[i].set_text('%.1f W' % self.powersIn[i])
        for i in xrange(len(self.temps)):
            self.tdisp[i].set_fraction(self.temps[i] / 100.0)
            self.tdisp[i].set_text('%.1f C' % self.temps[i])
