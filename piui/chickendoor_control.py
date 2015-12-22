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

#Web Server Config

current_dir = os.path.dirname(os.path.abspath(__file__))

class DoorControl(object):

    def __init__(self):
        self.title = self.page.add_textbox("Control Chicken Coop Doors!", "h1")
        self.txt = None
        self.img = None
        #self.ui = DoorControl(img_dir=os.path.join(current_dir, 'imgs'))
        #self.src = "chickencoop.png"
    
    def page_buttons(self):    
        self.page = self.ui.new_ui_page(title="Control Door")
        self.ui = DoorControl()
        self.title = self.page.add_textbox("Open Or Close Chicken Coop Doors", "h1")
        self.page.add_textbox("Current Status of Door:", "p")
        self.page.add_button("Open", self.onopenclick)
        self.page.add_button("Close", self.oncloseclick)
        self.page.add_button("Shutdown Door & Server", self.onkillclick)

    def main_menu(self)
        self.page = self.ui.new_ui_page(title="Control Door")
        self.list = self.page.add_list()
        self.list.add_item("Control Door", chevron=True, onclick=self.page_buttons)
        self.list.add_item("Console", chevron=True, onclick=self.page_console)
        self.ui.done()
        
    def onopenclick(self):
	DoorAction = up

    def oncloseclick(self):
	DoorAction = down
	
    def onkillclick(self):
	killSystem = '1'
        
    def main(self):
        self.main_menu()
        self.ui.done()

def main():
    piui = DoorControl()
    piui.main()

if __name__ == '__main__':
    main()

#GPIO Config

#Setting up Board GPIO Pins
GPIO.setmode(GPIO.BCM)
GPIO.setup(17,GPIO.IN) #Open (From Hall Effect)
GPIO.setup(18,GPIO.IN) #Locked (From Hall Effect)
GPIO.setup(22,GPIO.OUT) #Up
GPIO.setup(23,GPIO.OUT) #Down
GPIO.setup(24,GPIO.OUT) #Buzzer
GPIO.setup(25,GPIO.OUT) #LED
GPIO.setup(27,GPIO.IN) #MakeyMakey

#Clean kill of script function (Stops Motor, cleans GPIO)
if killSystem == '1': #Shutdown is queued
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

#Argument controller (Not Needed for Online, so commented out)

#if len(sys.argv)>3: #Tests if you've entered too many arguments
 #   print "You've entered too many arguments!"
  #  print "Exiting program..."
   # sys.exit(0)

#if len(sys.argv)>2: #Argument for door action time
 #   try:
  #      float(sys.argv[2])
   # except:
    #    print 'Error: ',str(sys.argv[2]),' is not a number!'
     #   print "Exiting program..."
      #  sys.exit(0)
    #if int(sys.argv[2])>45: #Checks that a time longer than 45s isn't entered
     #       print 'Please choose a time less than 45s'
      #      print "Exiting program..."
       #     sys.exit(0)

#if len(sys.argv)>1: #Argument for door action
 #   if sys.argv[1]!='close' and sys.argv[1]!='open':
  #          print 'Please choose "open" or "close"'
   #         print "Exiting program..."
    #        sys.exit(0)

#if len(sys.argv)==3:
 #   print 'Forcing door to',str(sys.argv[1]),'for',str(sys.argv[2]),'seconds'
    #Door_Action=sys.argv[1]
   # Door_Time=int(sys.argv[2])
#if len(sys.argv)==2:
   # print 'Forcing door to ',str(sys.argv[1])
    #Door_Action=sys.argv[1]
   # Door_Time=45 #This is a safety time
#if len(sys.argv)==1:
 #   Door_Action='default' #Will reverse door state
  #  Door_Time=45 #This is a safety time
 
#Start door!

#def DoorControl():
TimeStart=time.clock()
runTime=0
#Check door status from Magnets
BottomHall=GPIO.input(31)
TopHall=GPIO.input(33)
if BottomHall==0:print 'Door is locked'
if TopHall==0:print 'Door is open'
if BottomHall==1:print 'No magnet sensed on lock'
if TopHall==1:print 'No magnet sensed top'
if Door_Action=='up' and BottomHall==0: #Door is locked
		print 'The door is locked!'
		print 'The door is going up!'
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
elif Door_Action=='down' and TopHall==0: #Door is open
		print 'The door is open!'
		print 'The door is going down!'
		while BottomHall==1 and runTime<Door_Time:
				GPIO.output(35,False)
				GPIO.output(37,True)
				BottomHall=GPIO.input(31)
				runTime=time.clock()-TimeStart
		if 45==runTime:
				print 'Something went wrong, go check the door!'
				message = "Coop close FAILED!"
				PushOver(message)
		if BottomHall==0:
				time.sleep(1)
				print 'Door is locked!'
				message = "Coop closed successfully!"
				PushOver(message)
