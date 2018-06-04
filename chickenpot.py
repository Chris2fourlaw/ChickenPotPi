#!/usr/bin/python
import functools
import os
import random
from piui import PiUi
import RPi.GPIO as GPIO
import time
import datetime
import signal
import sys


class DoorControl(object):
    # Constants for GPIO Pins
    ENDSTOP_TOP = 17
    ENDSTOP_BOTTOM = 18
    MOTOR_UP = 22
    MOTOR_DOWN = 23
    BUZZER = 24
    BUTTON = 25
    ENDSTOP_ON = 0  # Active Low
    ENDSTOP_OFF = 1  # Active Low

    # Other Constants
    MAX_DOOR_TIME = 45
    BEEP_TIME = 0.5
    OPEN = 1
    CLOSE = 2
    BUTTON_HOLD_TIME = 0.4
    OPEN_TIME = "10:00"
    CLOSE_TIME = "19:00"

    # Global Variables
    cancel = False
    doorMoving = False
    timerRunning = False
    stopTimer = False

    def __init__(self):
        # Setting up Board GPIO Pins
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.ENDSTOP_TOP, GPIO.IN)  # Open
        GPIO.setup(self.ENDSTOP_BOTTOM, GPIO.IN)  # Closed
        GPIO.setup(self.MOTOR_UP, GPIO.OUT)
        GPIO.setup(self.MOTOR_DOWN, GPIO.OUT)
        GPIO.setup(self.BUZZER, GPIO.OUT)
        GPIO.setup(self.BUTTON, GPIO.IN)

        # False all output pins
        GPIO.output(self.MOTOR_UP, False)
        GPIO.output(self.MOTOR_DOWN, False)
        GPIO.output(self.BUZZER, False)

        # Web Server Config
        self.currentDir = os.path.dirname(os.path.abspath(__file__))

        self.title = None
        self.txt = None
        self.ui = PiUi()

    # Clean kill of script function (Stops Motor, cleans GPIO)
    def killSystem(self):  # Shutdown is queued
        print 'Performing safe shutoff of Door & Server!'
        self.stopTimer = True
        GPIO.output(self.MOTOR_UP, False)
        GPIO.output(self.MOTOR_DOWN, False)
        GPIO.output(self.BUZZER, False)
        GPIO.remove_event_detect(self.BUTTON)
        GPIO.cleanup()
        sys.exit('Motors shutdown, GPIO cleaned, server killed')

    # GPIO Config

    def stopDoor(self):
        self.cancel = True
        GPIO.output(self.MOTOR_UP, False)
        GPIO.output(self.MOTOR_DOWN, False)
        GPIO.output(self.BUZZER, False)
        print 'Door stopped!'

    def buttonCallback(self, channel):
        timeStart = time.clock()
        pressTime = 0
        while GPIO.input(self.BUTTON) and pressTime < BUTTON_HOLD_TIME:
            pressTime = time.clock() - timeStart
        if pressTime >= self.BUTTON_HOLD_TIME:
            print 'Button Pushed'
            self.cancel = True
            if doorMoving:
                print 'Stopping Door'
                return
            self.cancel = False
            if GPIO.input(self.ENDSTOP_BOTTOM) == self.ENDSTOP_ON:
                moveDoor(direction=OPEN)
            elif GPIO.input(self.ENDSTOP_TOP) == self.ENDSTOP_ON:
                moveDoor(direction=CLOSE)
            else:
                moveDoor(force=True, direction=OPEN)
        else:
            print 'Button not pressed long enough!'

    def moveDoor(self, force=False, direction=OPEN):
        self.doorMoving = True
        if not direction == OPEN and not direction == CLOSE:
            print 'Direction is not valid!'
            sys.exit(-1)
        # Print direction of action
        if direction == OPEN and (GPIO.input(self.ENDSTOP_BOTTOM) ==
                                  self.ENDSTOP_ON or force):
            if force:
                print 'Forcing door up!'
            else:
                print 'The door is closed!'
                print 'The door is going up!'
        elif direction == CLOSE and (GPIO.input(self.ENDSTOP_TOP) ==
                                     self.ENDSTOP_ON or force):
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
            GPIO.output(self.MOTOR_DOWN, False)
            GPIO.output(self.MOTOR_UP, True)
        else:
            GPIO.output(self.MOTOR_UP, False)
            GPIO.output(self.MOTOR_DOWN, True)
        # Initialize Timeout
        timeStart = time.clock()
        runTime = 0
        # Wait for door to complete movement
        while ((direction == OPEN and GPIO.input(self.ENDSTOP_TOP) ==
                self.ENDSTOP_OFF or direction == CLOSE and
                GPIO.input(self.ENDSTOP_BOTTOM) == self.ENDSTOP_OFF) and
               runTime < MAX_DOOR_TIME and not cancel):
            time.sleep(self.BEEP_TIME)
            GPIO.output(self.BUZZER, True)
            time.sleep(self.BEEP_TIME)
            GPIO.output(self.BUZZER, False)
            if not force:
                runTime = time.clock() - timeStart
        # Turn off motor
        GPIO.output(self.MOTOR_UP, False)
        GPIO.output(self.MOTOR_DOWN, False)
        # Check if we timed out and print message
        if runTime >= MAX_DOOR_TIME:
            if direction == OPEN:
                print 'Something went wrong while opening! Go check the door!'
            else:
                print 'Something went wrong while closing! Go check the door!'
        elif not cancel:
            if direction == OPEN:
                if force:
                    print 'Door forced open'
                else:
                    print 'Door is open!'
            else:
                if force:
                    print 'Door forced down'
                else:
                    print 'Door is closed!'
        else:
            print 'Door Stopped!'
        self.cancel = False
        self.doorMoving = False

    def updateTimes(self, openTime, closeTime):
        print "Updating times..."
        self.OPEN_TIME = openTime
        self.CLOSE_TIME = closeTime
        if self.timerRunning:
            self.stopTimer()
            self.startTimer()

    def loadMainPage(self):
        print "Loading main page..."
        self.mainPage = self.ui.new_ui_page(title="Control",
                                            prev_text="Back",
                                            onprevclick=self.loadMainMenu)
        self.title = self.mainPage.add_textbox(
            "Open Or Close Chicken Coop Door!",
            "h1")
        self.mainPage.add_button("Enable Automation",
                                 self.startTimer)
        self.mainPage.add_button("Disable Automation",
                                 self.stopTimer)
        self.mainPage.add_button("Set Automation Times", self.loadTimePage)
        self.mainPage.add_button("Open &uarr;", self.onUpClick)
        self.mainPage.add_button("Close &darr;", self.onDownClick)
        self.mainPage.add_button("Force Open &uarr;", self.onUpforceClick)
        self.mainPage.add_button("Force Close &darr;",
                                 self.onDownForceClick)
        self.mainPage.add_button("Stop Door", self.onStopClick)
        self.mainPage.add_button("Kill Server", self.onKillClick)

    def loadTimePage(self):
        print "Loading time page..."
        self.timePage = self.ui.new_ui_page(title="Set Automation Times",
                                            prev_text="Back",
                                            onprevclick=self.mainMenu)

        self.openLabel = self.timePage.add_textbox("Time to open:")
        self.openTimeInput = self.timePage.add_input("text", "xx:xx 24hr time")
        self.closeLabel = self.timePage.add_textbox("Time to close:")
        self.closeTimeInput = self.timePage.add_input(
            "text", "xx:xx 24hr time")
        self.mainPage.add_button("Submit", self.updateTimes(
            self.openTimeInput.get_text(), self.closeTimeInput.get_text()))

    def loadConsolePage(self):
        print "Loading console page..."
        self.consolePage = self.ui.console()

    def loadMainMenu(self):
        print "Loading main menu..."
        self.mainMenu = self.ui.new_ui_page(title="Chicken Control Center")
        self.menuList = self.menu.add_list()
        self.menuList.add_item("Control", chevron=True, onclick=self.loadMainPage)
        self.menuList.add_item("Console", chevron=True,
                               onclick=self.loadConsolePage)
        self.ui.done()

    def main(self):
        self.loadMainMenu()
        self.ui.done()

    def onUpClick(self):
        self.title.set_text("Opening")
        print "Open"
        moveDoor(direction=OPEN)

    def onDownClick(self):
        self.title.set_text("Closing")
        print "Close"
        moveDoor(direction=CLOSE)

    def onUpForceClick(self):
        self.title.set_text("Force Open")
        print "Force Open"
        moveDoor(direction=OPEN, force=True)

    def onDownForceClick(self):
        self.title.set_text("Force Close")
        print "Force Close"
        moveDoor(direction=CLOSE, force=True)

    def onStopClick(self):
        self.title.set_text("Stopping Door")
        print "Stopping"
        stopDoor()

    def onKillClick(self):
        self.title.set_text("Killing Server")
        print "Killing"
        time.sleep(0.5)
        killSystem()

    def controlTimer(self, start=True):
        if start and self.timerRunning or not start and not self.timerRunning:
            return
        if start:
            self.timerRunning = True
            self.stopTimer = False
        else:
            self.stopTimer = True
            return
        secondsSinceLastAction = 999
        [openHour, openMinute] = OPEN_TIME.split(":")
        [closeHour, closeMinute] = CLOSE_TIME.split(":")
        while True and not self.stopTimer:

            # Wait until the specified time and then open or close the
            # door depending on the specified direction

            # Get current time
            now = datetime.datetime.now()

            # Make sure at least two minutes have passed since the last action
            if secondsSinceLastAction > 120:
                print("(%d)  now.hour:%s  now.minute:%s  openHour:%s  "
                      "openMinute:%s  closeHour:%s  closeMinute:%s" %
                      (secondsSinceLastAction, str(now.hour),
                       str(now.minute), openHour, openMinute,
                       closeHour, closeMinute))
                # If it's time, perform the action and reset the timer
                if (now.hour == int(open_hour) and
                        now.minute == int(openMinute)):
                    print "Opening at %s:%s" % (str(now.hour), str(now.minute))
                    moveDoor(direction=OPEN)
                    secondsSinceLastAction = 0
                    # Reset timer
                if (now.hour == int(closeHour) and
                        now.minute == int(closeMinute)):
                    print "Closing at %s:%s" % (str(now.hour), str(now.minute))
                    moveDoor(direction=CLOSE)
                    secondsSinceLastAction = 0

            # Sleep for 1 second before checking again
            time.sleep(1)
            secondsSinceLastAction += 1
        self.timerRunning = False

    def startTimer(self):
        self.controlTimer(start=True)

    def stopTimer(self):
        self.controlTimer(start=False)

    GPIO.add_event_detect(self.BUTTON, GPIO.RISING,
                          callback=self.buttonCallback, bouncetime=300)


def main():
    piui = DoorControl()
    piui.main()


if __name__ == '__main__':
    main()
