#!/usr/bin/python
import functools
import os
import random
from piui import PiUi
import RPi.GPIO as GPIO
import time
import signal
import sys
import httplib, urllib #for PushOver

#GPIO Config

#Setting up Board GPIO Pins
GPIO.setmode(GPIO.BCM)
GPIO.setup(22,GPIO.OUT) #Up
GPIO.setup(23,GPIO.OUT) #Down

#Clean kill of script function (Stops Motor, cleans GPIO)
def killSystem(): #Shutdown is queued
        print 'Performing safe shutoff of Door & Server!'
        GPIO.output(22,False)
        GPIO.output(23,False)
        GPIO.cleanup()
        sys.exit('Motors shutdown, GPIO cleaned, server killed')

#Motor Config

def openDoor():
	TimeStart=time.clock()
	runTime=0
	runTime=time.clock()-TimeStart
	GPIO.output(23,False)
	if GPIO.output(23,False):
		while 1:
			GPIO.output(22,True)
			if 45==runTime:
				GPIO.output(22,False)
				print 'Something went wrong, go check the door!'

def closeDoor():
	TimeStart=time.clock()
	runTime=0
	runTime=time.clock()-TimeStart
	GPIO.output(22,False)
	if GPIO.output(22,False):
		while 1:
			GPIO.output(23,True)
			if 45==runTime:
				GPIO.output(23,False)
				print 'Something went wrong, go check the door!'

#Web Server Config

current_dir = os.path.dirname(os.path.abspath(__file__))


class DoorControl(object):

    def __init__(self):
        self.title = None
        self.txt = None
        self.img = None
        self.ui = PiUi(img_dir=os.path.join(current_dir, 'imgs'))
        self.src = "chickens.png"

    def page_buttons(self):
        self.page = self.ui.new_ui_page(title="Control", prev_text="Back", onprevclick=self.main_menu)
        self.title = self.page.add_textbox("Open Or Close Chicken Coop Door!", "h1")
        up = self.page.add_button("Open &uarr;", self.onupclick)
        down = self.page.add_button("Close &darr;", self.ondownclick)
        kill = self.page.add_button("Kill Server", self.onkillclick)
        self.img = self.page.add_image("chickens.png")

    def main_menu(self):
        self.page = self.ui.new_ui_page(title="Chicken Control Center")
        self.list = self.page.add_list()
        self.list.add_item("Control", chevron=True, onclick=self.page_buttons)
        self.ui.done()

    def main(self):
        self.main_menu()
        self.ui.done()

    def onupclick(self):
        openDoor()
        self.title.set_text("Opening")
        print "Open"

    def ondownclick(self):
        closeDoor()
        self.title.set_text("Closing")
        print "Close"
    
    def onkillclick(self):
        killSystem()
        self.title.set_text("Killing Server")
        print "Killing"

def main():
  piui = DoorControl()
  piui.main()

if __name__ == '__main__':
    main()
