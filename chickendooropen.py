#!/usr/bin/python
import functools
import os
import random
import RPi.GPIO as GPIO
import time
import signal
import sys
import httplib, urllib #for PushOver

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

GPIO.setmode(GPIO.BCM)
GPIO.setup(22,GPIO.OUT) #Up
GPIO.setup(23,GPIO.OUT) #Down
GPIO.setup(21,GPIO.IN) #Locked (From Hall Effect)
GPIO.setup(17,GPIO.IN) #Open (From Hall Effect)

TimeStart=time.clock()
runTime=0

while TopHall==1 and runTime<45:
				GPIO.output(22,True)
				GPIO.output(23,False)
				TopHall=GPIO.input(17)
				runTime=time.clock()-TimeStart
				
if 45==runTime:
				print 'Something went wrong, go check the door!'
				message = 'Coop open FAILED!'
				PushOver(message)
				
if TopHall==0:
				print 'Door is open!'
				message = 'Coop opened successfully!'
				PushOver(message)
