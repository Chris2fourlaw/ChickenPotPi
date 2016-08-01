#!/usr/bin/python
import functools
import os
import random
from piui import PiUi
import RPi.GPIO as GPIO
import time
import signal
import sys
import httplib  # for PushOver
import urllib  # for PushOver

# RPi.GPIO Config

# Constants for GPIO Pins
HALL_TOP = 17
HALL_BOTTOM = 18
MOTOR_UP = 22
MOTOR_DOWN = 23
BUZZER = 24
BUTTON = 25
HALL_ON = 0  # Active Low
HALL_OFF = 1  # Active Low
# HALL_ON = 1  # FIX ME
# HALL_OFF = 0  # FIX ME

# Other Constants
MAX_DOOR_TIME = 45
BEEP_TIME = 0.35

# Global Variables
cancel = False

# Setting up Board GPIO Pins
GPIO.setmode(GPIO.BCM)
GPIO.setup(HALL_TOP, GPIO.IN)  # Open
GPIO.setup(HALL_BOTTOM, GPIO.IN)  # Closed
GPIO.setup(MOTOR_UP, GPIO.OUT)
GPIO.setup(MOTOR_DOWN, GPIO.OUT)
GPIO.setup(BUZZER, GPIO.OUT)
GPIO.setup(BUTTON, GPIO.IN)  # Button

# False all output pins
GPIO.output(MOTOR_UP, False)
GPIO.output(MOTOR_DOWN, False)
GPIO.output(BUZZER, False)


# Clean kill of script function (Stops Motor, cleans GPIO)
def killSystem():  # Shutdown is queued
    print 'Performing safe shutoff of Door & Server!'
    GPIO.output(MOTOR_UP, False)
    GPIO.output(MOTOR_DOWN, False)
    GPIO.output(BUZZER, False)
    GPIO.cleanup()
    sys.exit('Motors shutdown, GPIO cleaned, server killed')

# PushOver Config

# config.txt first line is the token, the second line is the key
config = open('config.txt').readlines()
pushover_token = config[0].rstrip()
pushover_user = config[1]


def PushOver(message):
    conn = httplib.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
                 urllib.urlencode({"token": pushover_token,
                                   "user": pushover_user,
                                   "message": message,
                                   }),
                 {"Content-type": "application/x-www-form-urlencoded"})
    conn.getresponse()


# GPIO Config


def buttonCallback(channel):
    if GPIO.input(HALL_BOTTOM) == HALL_ON:
        openDoor()
    elif GPIO.input(HALL_TOP) == HALL_ON:
        closeDoor()
    else:
        openDoor(force=True)


def stopDoor():
    global cancel
    GPIO.output(MOTOR_UP, False)
    GPIO.output(MOTOR_DOWN, False)
    GPIO.output(BUZZER, False)
    cancel = True
    print 'Door stopped!'


def openDoor(force=False):
    global cancel
    TimeStart = time.clock()
    runTime = 0
    if GPIO.input(HALL_BOTTOM) == HALL_ON or force:  # Door is closed
        print 'The door is closed!'
        print 'The door is going up!'
        GPIO.output(MOTOR_DOWN, False)
        GPIO.output(MOTOR_UP, True)
        while (GPIO.input(HALL_TOP) == HALL_OFF and
               runTime < MAX_DOOR_TIME and not cancel):
            time.sleep(BEEP_TIME)
            GPIO.output(BUZZER, True)
            time.sleep(BEEP_TIME)
            GPIO.output(BUZZER, False)
            if not force:
                runTime = time.clock() - TimeStart
        cancel = False
        GPIO.output(MOTOR_UP, False)
        time.sleep(1)  # Wait for bounce to settle
        if GPIO.input(HALL_TOP) == HALL_ON:
            # up = '0'
            print 'Door is open!'
            message = 'Coop opened successfully!'
            PushOver(message)
        else:
            # up = '0'
            print 'Something went wrong while opening! Go check the door!'
            message = 'Coop open FAILED!'
            PushOver(message)


def closeDoor(force=False):
    global cancel
    TimeStart = time.clock()
    runTime = 0
    if GPIO.input(HALL_TOP) == HALL_ON or force:  # Door is open
        print 'The door is open!'
        print 'The door is going down!'
        GPIO.output(MOTOR_UP, False)
        GPIO.output(MOTOR_DOWN, True)
        while (GPIO.input(HALL_BOTTOM) == HALL_OFF and
               runTime < MAX_DOOR_TIME and not cancel):
            time.sleep(BEEP_TIME)
            GPIO.output(BUZZER, True)
            time.sleep(BEEP_TIME)
            GPIO.output(BUZZER, False)
            if not force:
                runTime = time.clock() - TimeStart
        cancel = False
        GPIO.output(MOTOR_DOWN, False)
        time.sleep(1)  # Wait for bounce to settle
        if GPIO.input(HALL_BOTTOM) == HALL_ON:
            # down = '0'
            print 'Door is closed!'
            message = 'Coop closed successfully!'
            PushOver(message)
        else:
            # down = '0'
            print 'Something went wrong while closing! Go check the door!'
            message = 'Coop close FAILED!'
            PushOver(message)

# Web Server Config

current_dir = os.path.dirname(os.path.abspath(__file__))


class DoorControl(object):

    def __init__(self):
        self.title = None
        self.txt = None
        self.img = None
        self.ui = PiUi(img_dir=os.path.join(current_dir, 'imgs'))
        self.src = "chickens.png"

    def page_buttons(self):
        self.page = self.ui.new_ui_page(title="Control",
                                        prev_text="Back",
                                        onprevclick=self.main_menu)
        self.title = self.page.add_textbox("Open Or Close Chicken Coop Door!",
                                           "h1")
        up = self.page.add_button("Open &uarr;", self.onupclick)
        down = self.page.add_button("Close &darr;", self.ondownclick)
        fup = self.page.add_button("Force Open &uarr;", self.onupforceclick)
        fdown = self.page.add_button("Force Close &darr;",
                                     self.ondownforceclick)
        stop = self.page.add_button("Stop Door", self.onstopclick)
        kill = self.page.add_button("Kill Server", self.onkillclick)
        self.img = self.page.add_image("chickens.png")

    def main_menu(self):
        self.page = self.ui.new_ui_page(title="Chicken Control Center")
        self.list = self.page.add_list()
        self.list.add_item("Control", chevron=True,
                           onclick=self.page_buttons)
        self.ui.done()

    def main(self):
        self.main_menu()
        self.ui.done()

    def onupclick(self):
        self.title.set_text("Opening")
        print "Open"
        openDoor()

    def ondownclick(self):
        self.title.set_text("Closing")
        print "Close"
        closeDoor()

    def onupforceclick(self):
        self.title.set_text("Force Open")
        print "Force Open"
        openDoor(force=True)

    def ondownforceclick(self):
        self.title.set_text("Force Close")
        print "Force Close"
        closeDoor(force=True)

    def onstopclick(self):
        self.title.set_text("Stopping Door")
        print "Stopping"
        stopDoor()

    def onkillclick(self):
        self.title.set_text("Killing Server")
        print "Killing"
        time.sleep(0.5)
        killSystem()

    GPIO.add_event_detect(BUTTON, GPIO.RISING, callback=buttonCallback,
                          bouncetime=300)


def main():
    piui = DoorControl()
    piui.main()

if __name__ == '__main__':
    main()
