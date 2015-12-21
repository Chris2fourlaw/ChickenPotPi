#!/usr/bin/python
import functools
import os
import random
import RPi.GPIO as GPIO
import time
import signal
import sys
import httplib, urllib #for PushOver

GPIO.setmode(GPIO.BCM)
GPIO.setup(22,GPIO.OUT)
GPIO.setup(23,GPIO.OUT)
GPIO.setup(21,GPIO.IN) #Locked (From Hall Effect)
GPIO.setup(17,GPIO.IN) #Open (From Hall Effect)

TimeStart=time.clock()
runTime=0

while TopHall==1 and runTime<Door_Time:
				GPIO.output(35,True)
				GPIO.output(37,False)
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
