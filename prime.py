#!/usr/bin/env python
#my imports
import time, sys, os
import RPi.GPIO as GPIO
import cv2

# my imports
utilsDir= "/home/pi/eDNA/utilities"
sys.path.insert(0, utilsDir)
from config import Config
from utils import *
#==============================================================================
#Load config file 
configDat = '/home/pi/eDNA/utilities/Config.dat'
configFilename = configDat #Load config file/parameters needed
config = Config() # Create object and load file
ok = config.loadFile( configFilename )
if( not ok ):
	sys.exit(0)

runTime = int(sys.argv[1])

waterPump = config.getInt('Track', 'WaterPump')
valve = config.getInt('Track', 'Valve1')

GPIO.setwarnings(False) #no GPIO warning
GPIO.setmode(GPIO.BCM)  #pin number
GPIO.setup(waterPump,GPIO.OUT)
GPIO.setup(valve,GPIO.OUT)

tStart = time.time()
    
GPIO.output(valve, GPIO.HIGH)
print ("Flipping valve open")
        
GPIO.output(waterPump, GPIO.HIGH)
print ("Turning water pump on")

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
        
print ("Done. Run as many times as necessary until system is ready")
    