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
OPEN = 1
CLOSE = 2
BUTTON_HOLD_TIME = 0.5

# Global Variables
cancel = False
door_moving = False

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
    GPIO.remove_event_detect(BUTTON)
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


def stopDoor():
    global cancel
    cancel = True
    GPIO.output(MOTOR_UP, False)
    GPIO.output(MOTOR_DOWN, False)
    GPIO.output(BUZZER, False)
    print 'Door stopped!'


def buttonCallback(channel):
    global door_moving
    TimeStart = time.clock()
    pressTime = 0
    while GPIO.input(BUTTON) and pressTime < BUTTON_HOLD_TIME:
        pressTime = time.clock() - TimeStart
    if pressTime >= BUTTON_HOLD_TIME:
        print 'Button Pushed'
        cancel = True
        GPIO.output(BUZZER, True)
        time.sleep(0.2)
        GPIO.output(BUZZER, False)
        while door_moving:
            time.sleep(0.1)
        cancel = False
        if GPIO.input(HALL_BOTTOM) == HALL_ON:
            moveDoor(direction=OPEN)
        elif GPIO.input(HALL_TOP) == HALL_ON:
            moveDoor(direction=CLOSE)
        else:
            moveDoor(force=True, direction=OPEN)
    else:
        print 'Button not pressed long enough!'


def moveDoor(force=False, direction=OPEN):
    global cancel
    global door_moving
    door_moving = True
    if direction != OPEN and direction != CLOSE:
        print 'Direction is not valid!'
        sys.exit(-1)
    # Print direction of action
    if direction == OPEN and (GPIO.input(HALL_BOTTOM) == HALL_ON or force):
        if force:
            print 'Forcing door up!'
        else:
            print 'The door is closed!'
            print 'The door is going up!'
    elif direction == CLOSE and (GPIO.input(HALL_TOP) == HALL_ON or force):
        if force:
            print 'Forcing door down!'
        else:
            print 'The door is open!'
            print 'The door is going down!'
    else:
        print 'Door is stuck or moving!'
        return
    # Activate Motor
    if direction == OPEN:
        GPIO.output(MOTOR_DOWN, False)
        GPIO.output(MOTOR_UP, True)
    else:
        GPIO.output(MOTOR_UP, False)
        GPIO.output(MOTOR_DOWN, True)
    # Initialize Timeout
    TimeStart = time.clock()
    runTime = 0
    # Wait for door to complete movement
    while ((direction == OPEN and GPIO.input(HALL_TOP) == HALL_OFF or
            direction == CLOSE and GPIO.input(HALL_BOTTOM) == HALL_OFF) and
           runTime < MAX_DOOR_TIME and not cancel):
        time.sleep(BEEP_TIME)
        GPIO.output(BUZZER, True)
        time.sleep(BEEP_TIME)
        GPIO.output(BUZZER, False)
        if not force:
            runTime = time.clock() - TimeStart
    # Turn off motor
    GPIO.output(MOTOR_UP, False)
    GPIO.output(MOTOR_DOWN, False)
    # Check if we timed out and print message
    if runTime >= MAX_DOOR_TIME:
        if direction == OPEN:
            print 'Something went wrong while opening! Go check the door!'
            message = 'Coop open FAILED!'
        else:
            print 'Something went wrong while closing! Go check the door!'
            message = 'Coop close FAILED!'
    elif not cancel:
        if direction == OPEN:
            if force:
                print 'Door forced open'
                message = 'Coop forced open successfully!'
            else:
                print 'Door is open!'
                message = 'Coop opened successfully!'
        else:
            if force:
                print 'Door forced down'
                message = 'Coop forced down successfully!'
            else:
                print 'Door is closed!'
                message = 'Coop closed successfully!'
    else:
        print 'Door Stopped!'
        message = 'Door Stopped!'
    PushOver(message)
    cancel = False
    door_moving = False


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
        moveDoor(direction=OPEN)

    def ondownclick(self):
        self.title.set_text("Closing")
        print "Close"
        moveDoor(direction=CLOSE)

    def onupforceclick(self):
        self.title.set_text("Force Open")
        print "Force Open"
        moveDoor(direction=OPEN, force=True)

    def ondownforceclick(self):
        self.title.set_text("Force Close")
        print "Force Close"
        moveDoor(direction=CLOSE, force=True)

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
