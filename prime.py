#!/usr/bin/env python
##############################################################################
#This app primes the eDNA system. A command line argument is issued with the 
#duration to prime in seconds.
##############################################################################
#my imports
import time, sys, os
import RPi.GPIO as GPIO
import cv2

# my imports
from config import Config
from utils import *
#=============================================================================
#Load config file 
configDat = sys.argv[1]
configFilename = configDat #Load config file/parameters needed
config = Config() # Create object and load file
ok = config.loadFile( configFilename )
if( not ok ):
	sys.exit(0)

runTime = int(sys.argv[2])

waterPump = config.getInt('Track', 'WaterPump')
valve = config.getInt('Track', 'Valve1')

GPIO.setwarnings(False) #no GPIO warning
GPIO.setmode(GPIO.BCM)  #pin number
GPIO.setup(waterPump,GPIO.OUT)
GPIO.setup(valve,GPIO.OUT)

tStart = time.time() #initialize time
    
GPIO.output(valve, GPIO.HIGH)
print ("Flipping valve open")
        
GPIO.output(waterPump, GPIO.HIGH)
print ("Turning water pump on")

#----------------------------------------------------------------------
#Loop Begins
#----------------------------------------------------------------------
while True:
    tNow = time.time()
    elapsedTime = int(tNow -tStart)

    if runTime < elapsedTime:
        GPIO.output(valve, GPIO.LOW)
        print ("Flipping valve closed")
            
        GPIO.output(waterPump, GPIO.LOW)
        print ("Turning water pump off")
        break
    if cv2.waitKey(1) & 0xFF == ord('q'):
        sys.exit(0)
#----------------------------------------------------------------------
#Loop Begins
#----------------------------------------------------------------------

print ("Done. Run as many times as necessary until system is ready")
    
