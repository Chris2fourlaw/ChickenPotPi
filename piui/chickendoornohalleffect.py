#!/usr/bin/python
import functools
import os
import random
from piui import PiUi
import RPi.GPIO as GPIO
import time
import signal
import sys
import httplib, urllib

GPIO.setmode(GPIO.BCM)
GPIO.setup(22,GPIO.OUT)
GPIO.setup(23,GPIO.OUT)
GPIO.output(22,GPIO.LOW)
GPIO.output(23,GPIO.LOW)

def killSystem():
        print 'Performing safe shutoff of Door & Server!'
        GPIO.output(22,GPIO.LOW)
        GPIO.output(23,GPIO.LOW)
        GPIO.cleanup()
        sys.exit('Motors shutdown, GPIO cleaned, server killed')

def openDoor():
	TimeStart=time.clock()
	runTime=0
	runTime=time.clock()-TimeStart
	GPIO.output(22,GPIO.LOW)
	GPIO.output(23,GPIO.LOW)
	GPIO.output(22,GPIO.HIGH)
	if 45==runTime:
		GPIO.output(22,GPIO.LOW)
		print 'Something went wrong, go check the door!'

def closeDoor():
	TimeStart=time.clock()
	runTime=0
	runTime=time.clock()-TimeStart
	GPIO.output(22,GPIO.LOW)
	GPIO.output(23,GPIO.LOW)
	GPIO.output(23,GPIO.HIGH)
	if 45==runTime:
		GPIO.output(23,GPIO.LOW)
		print 'Something went wrong, go check the door!'

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

class DoorControl(object):
    def __init__(self):
        self.title = None
        self.txt = None
        self.ui = PiUi()
    def page_buttons(self):
        self.page = self.ui.new_ui_page(title="Control", prev_text="Back", onprevclick=self.main_menu)
        self.title = self.page.add_textbox("Open Or Close Chicken Coop Door!", "h1")
        up = self.page.add_button("Open &uarr;", self.onupclick)
        down = self.page.add_button("Close &darr;", self.ondownclick)
        kill = self.page.add_button("Kill Server", self.onkillclick)
    def main_menu(self):
        self.page = self.ui.new_ui_page(title="Chicken Control Center")
        self.list = self.page.add_list()
        self.list.add_item("Control", chevron=True, onclick=self.page_buttons)
        self.ui.done()
    def main(self):
        self.main_menu()
        self.ui.done()

def main():
  piui = DoorControl()
  piui.main()

if __name__ == '__main__':
    main()
