#!/usr/bin/env python

import pygtk
pygtk.require('2.0')
import gtk
import gobject
import Pages
import netTelemClient
import sys

class MainWindow:
    def __init__(self,client):
        self.client = client

        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.frames = gtk.VBox(False,0)
        self.tabs = gtk.VBox(False,0)

        self.window.add(self.frames)
        self.frames.show()

        self.frames.add(self.tabs)
        self.tabs.show()

        self.status = gtk.Statusbar()
        self.frames.pack_start(self.status,False,True,0)
        self.status.show()

        #Fill up the tabs
        self.Battery = Pages.BatteryPage(self.tabs,30)
        #self.tabs.set_tab_label_text(self.Battery.container,"Battery")

	self.Trackers = Pages.TrackerPage(self.tabs)

	self.Dashboard = Pages.DashboardPage(self.tabs)
	#self.tabs.set_tab_label_text(self.Dashboard.container,"Dashboard")

        #Setup base window stuff
        self.window.connect("delete_event", self.delete_event)
        self.window.connect("destroy", self.destroy)
        xid = self.status.get_context_id("Test")
        self.status.push(xid,"Testing")
        gobject.timeout_add(200,self.client.ProcessPacket,self)

        #Show the window last
        self.window.show()
    
    def delete_event(self, widget, event, data=None):
        #Evenutally kill other threads here
        self.client.stop()
        return False

    def destroy(self, widget, data=None):
        gtk.main_quit()
    
    def main(self):
        gtk.main()

if __name__ == '__main__':
    if len(sys.argv) > 1:
	client = netTelemClient.TelemClient(sys.argv[1],8192)
    else:
	client = netTelemClient.TelemClient('localhost',8192)
    client.start()
    win = MainWindow(client)
    win.main()
