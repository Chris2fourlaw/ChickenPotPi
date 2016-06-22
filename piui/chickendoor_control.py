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
GPIO.setup(17,GPIO.IN) #Open (From Hall Effect)
GPIO.setup(18,GPIO.IN) #Locked (From Hall Effect)
GPIO.setup(22,GPIO.OUT) #Up
GPIO.setup(23,GPIO.OUT) #Down
GPIO.setup(24,GPIO.OUT) #Buzzer
GPIO.setup(25,GPIO.OUT) #LED
GPIO.setup(27,GPIO.IN) #Button (Outdoor Door Toggle)

#Clean kill of script function (Stops Motor, cleans GPIO)
def killSystem(): #Shutdown is queued
        print 'Performing safe shutoff of Door & Server!'
        GPIO.output(22,False)
        GPIO.output(23,False)
        GPIO.output(24,False)
        GPIO.output(25,False)
        GPIO.cleanup()
        sys.exit('Motors shutdown, GPIO cleaned, server killed')

#PushOver Config

#config.txt included in .gitignore first line is the token, the second line is the key
config = open('config.txt').readlines()
pushover_token=config[0].rstrip()
pushover_user=config[1]

def PushOver(message):
    conn = httplib.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
      urllib.urlencode({
        "token": pushover_token,
        "user": pushover_user,
        "message": message,
      }), { "Content-type": "application/x-www-form-urlencoded" })
    conn.getresponse()

#Motor Config

BottomHall=GPIO.input(18)
TopHall=GPIO.input(17)
if BottomHall==0:print 'Door is locked'
if TopHall==0:print 'Door is open'
if BottomHall==1:print 'No magnet sensed on lock'
if TopHall==1:print 'No magnet sensed top'
def openDoor():
	TimeStart=time.clock()
	runTime=0
	if BottomHall==0: #Door is locked
		print 'The door is locked!'
		print 'The door is going up!'
		while TopHall==1 and runTime<Door_Time:
				GPIO.output(35,True)
				GPIO.output(37,False)
				TopHall=GPIO.input(33)
				runTime=time.clock()-TimeStart
		if 45==runTime:
				up = '0'
				print 'Something went wrong, go check the door!'
				message = 'Coop open FAILED!'
				PushOver(message)
		if TopHall==0:
				up = '0'
				print 'Door is open!'
				message = 'Coop opened successfully!'
				PushOver(message)
def closeDoor():
	TimeStart=time.clock()
	runTime=0
	if TopHall==0: #Door is open
		print 'The door is open!'
		print 'The door is going down!'
		while BottomHall==1 and runTime<Door_Time:
				GPIO.output(35,False)
				GPIO.output(37,True)
				BottomHall=GPIO.input(31)
				runTime=time.clock()-TimeStart
		if 45==runTime:
				down = '0'
				print 'Something went wrong, go check the door!'
				message = "Coop close FAILED!"
				PushOver(message)
		if BottomHall==0:
				down = '0'
				time.sleep(1)
				print 'Door is locked!'
				message = "Coop closed successfully!"
				PushOver(message)

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
