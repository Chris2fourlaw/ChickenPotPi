#!/usr/bin/python
import functools
import os
import random
from piui import PiUi
import RPi.GPIO as GPIO
import time
import signal
import sys
import httplib, urllib # for PushOver

# RPi.GPIO Config

# Constants for GPIO Pins
HALL_TOP = 17
HALL_BOTTOM = 18
MOTOR_UP = 22
MOTOR_DOWN = 23
BUZZER = 24
BUTTON = 25
HALL_ON = 0 # Active Low
HALL_OFF = 1 # Active Low

# Other Constants
MAX_DOOR_TIME = 45

# Setting up Board GPIO Pins
GPIO.setmode(GPIO.BCM)
GPIO.setup(HALL_TOP,GPIO.IN) # Open
GPIO.setup(HALL_BOTTOM,GPIO.IN) # Closed
GPIO.setup(MOTOR_UP,GPIO.OUT)
GPIO.setup(MOTOR_DOWN,GPIO.OUT)
GPIO.setup(BUZZER,GPIO.OUT)
GPIO.setup(BUTTON,GPIO.IN) # Button

# False all output pins
GPIO.output(MOTOR_UP,False)
GPIO.output(MOTOR_DOWN,False)
GPIO.output(BUZZER,False)

# Clean kill of script function (Stops Motor, cleans GPIO)
def killSystem(): # Shutdown is queued
        print 'Performing safe shutoff of Door & Server!'
        GPIO.output(MOTOR_UP,False)
        GPIO.output(MOTOR_DOWN,False)
        GPIO.output(BUZZER,False)
        GPIO.cleanup()
        sys.exit('Motors shutdown, GPIO cleaned, server killed')

# PushOver Config

# config.txt first line is the token, the second line is the key
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
def openDoor():
	TimeStart = time.clock()
	runTime = 0
	if GPIO.input(HALL_BOTTOM) == HALL_ON: # Door is closed
		print 'The door is closed!'
		print 'The door is going up!'
		GPIO.output(MOTOR_DOWN, False)
		GPIO.output(MOTOR_UP, True)
		while GPIO.input(HALL_TOP) == HALL_OFF and runTime < MAX_DOOR_TIME:
			runTime = time.clock() - TimeStart
		GPIO.output(MOTOR_UP, False)
		time.sleep(1) # Wait for bounce to settle
		if GPIO.input(HALL_TOP) == HALL_ON:
#			up = '0'
			print 'Door is open!'
			message = 'Coop opened successfully!'
			PushOver(message)
		else:
#			up = '0'
			print 'Something went wrong while opening! Go check the door!'
			message = 'Coop open FAILED!'
			PushOver(message)

def closeDoor():
	TimeStart = time.clock()
	runTime = 0
	if GPIO.input(HALL_TOP) == HALL_ON: # Door is open
		print 'The door is open!'
		print 'The door is going down!'
		GPIO.output(MOTOR_UP, False)
		GPIO.output(MOTOR_DOWN, True)
		while GPIO.input(HALL_BOTTOM) == HALL_OFF and runTime < MAX_DOOR_TIME:
			runTime = time.clock() - TimeStart
		GPIO.output(MOTOR_DOWN, False)
		time.sleep(1) # Wait for bounce to settle
		if GPIO.input(HALL_BOTTOM) == HALL_ON:
#			down = '0'
			print 'Door is closed!'
			message = 'Coop closed successfully!'
			PushOver(message)
		else:
#			down = '0'
			print 'Something went wrong while closing! Go check the door!'
			message = 'Coop close FAILED!'
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
        self.page = self.ui.new_ui_page(title = "Control", prev_text = "Back", onprevclick = self.main_menu)
        self.title = self.page.add_textbox("Open Or Close Chicken Coop Door!", "h1")
        up = self.page.add_button("Open &uarr;", self.onupclick)
        down = self.page.add_button("Close &darr;", self.ondownclick)
        kill = self.page.add_button("Kill Server", self.onkillclick)
        self.img = self.page.add_image("chickens.png")

    def main_menu(self):
        self.page = self.ui.new_ui_page(title = "Chicken Control Center")
        self.list = self.page.add_list()
        self.list.add_item("Control", chevron = True, onclick = self.page_buttons)
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
