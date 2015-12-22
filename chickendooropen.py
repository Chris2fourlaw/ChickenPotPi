#!/usr/bin/python
import functools
import os
import random
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

#Clean kill of script function (Stops Motor, cleans GPIO)
if killSystem == '1': #Shutdown is queued
        print 'Performing safe shutoff of Door & Server!'
        GPIO.output(22,False)
        GPIO.output(23,False)
        GPIO.output(25,False)
        GPIO.cleanup()
        sys.exit('Motors shutdown, GPIO cleaned, server killed')

#PushOver Config

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
 
#Start door!

TimeStart=time.clock()
runTime=0
#Check door status from Magnets
BottomHall=GPIO.input(17)
TopHall=GPIO.input(18)
if BottomHall==0:print 'Door is locked'
if TopHall==0:print 'Door is open'
if BottomHall==1:print 'No magnet sensed on lock'
if TopHall==1:print 'No magnet sensed top'
if Door_Action=='up' and BottomHall==0: #Door is locked
		print 'The door is locked!'
		print 'The door is going up!'
		while TopHall==1 and runTime<45:
				GPIO.output(22,True)
				GPIO.output(23,False)
				TopHall=GPIO.input(33)
				runTime=time.clock()-TimeStart
		if 45==runTime:
				print 'Something went wrong, go check the door!'
				message = 'Coop open FAILED!'
				PushOver(message)
		if TopHall==0:
				print 'Door is open!'
				message = 'Coop opened successfully!'
				PushOver(message)
