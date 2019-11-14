#!/usr/bin/env python
#####################################################################
#This app runs process for programming hardware to collect 3 samples
#of environmental data on a filter. X amount of water is filtered 
#by turning motors on and flipping valves open. X amount of ethanol
#is then added to the sample.
#All variables are configurable via Config file under utilities folder
#####################################################################
#my imports
import time, sys, os
import RPi.GPIO as GPIO
import logging
from logging import FileHandler
from logging import Formatter

#third party imports
import ms5837 #pressure

# my imports
from config2 import Config
from utils import *
from ednaClass import *
import logging
#--------------------------------------------------------------------
#Load config file 
configDat =  sys.argv[1]
configFilename = configDat #Load config file/parameters needed
config = Config() # Create object and load file
ok = config.loadFile( configFilename )
if( not ok ):
	sys.exit(0)

#PARAMS
logDir = config.getString('System', 'LogDir')
recRate = config.getInt('Track', 'RecordRate')

flowSensor = config.getInt('Track', 'Flow')
waterPump = config.getInt('Track', 'WaterPump')
soluPump = config.getInt('Track', 'SoluPump')
valve1 = config.getInt('Track', 'Valve1')
valve2 = config.getInt('Track', 'Valve2')
valve3 = config.getInt('Track', 'Valve3')
valve4 = config.getInt('Track', 'Valve4')

#pressure
targetDepth1 = config.getInt('PressureSensor', 'TargetDepth1')
targetDepth2 = config.getInt('PressureSensor', 'TargetDepth2')
targetDepth3 = config.getInt('PressureSensor', 'TargetDepth3')
sleepTime = config.getFloat('PressureSensor', 'Sleep')
depthErr = config.getInt('PressureSensor', 'DepthError')

#logging
recordingInterval=1./recRate
print ("Interval: %.3f" % recordingInterval)
dataFile = str(currentTimeString()) #file name

f = open(logDir + '/' + 'eDNAData-' + dataFile + '.txt', 'a')
#EVENT Log
LOG_FORMAT = ('[%(levelname)s] %(message)s')
LOG_LEVEL = logging.INFO 
EVENT_LOG_FILE = (logDir + '/' + 'eDNAEvent' + dataFile + '.log')
eventLog = logging.getLogger("Event")
eventLog.setLevel(LOG_LEVEL)
eventLogFileHandler = FileHandler(EVENT_LOG_FILE)
eventLogFileHandler.setLevel(LOG_LEVEL)
eventLogFileHandler.setFormatter(Formatter(LOG_FORMAT))
eventLog.addHandler(eventLogFileHandler)


GPIO.setwarnings(False) #no GPIO warning
GPIO.setmode(GPIO.BCM)  #pin number

#hardware GPIO location 
GPIO.setup(flowSensor, GPIO.IN)
GPIO.setup(waterPump,GPIO.OUT)
GPIO.setup(soluPump,GPIO.OUT)
GPIO.setup(valve1,GPIO.OUT)
GPIO.setup(valve2,GPIO.OUT)
GPIO.setup(valve3,GPIO.OUT)
GPIO.setup(valve4,GPIO.OUT)
#--------------------------------------------------------------------------
#pressure sensor 
sensor=ms5837.MS5837_02BA() #sensor type
if not sensor.init(): #initialize sensort
    print ("Sensor could not be initialized")
    exit(1)
#---------------------------------------------------------------------------
    
#create edna object to run once depth is reached 
ednaObj = ednaClass(config,eventLog,f,sensor)
#initialized variables 
tLastRecord = 0
tStart = time.time()

for increment in range(1,4):
    tHere = time.time()
    elaTime = tHere - tStart 
    strInc = str(increment)
    valve = ('valve' + strInc)
    tDepth = ('tDepth' + strInc)
    if tDepth == 'tDepth1':
        tDepth = targetDepth1
    if tDepth == 'tDepth2':
        tDepth = targetDepth2
    if tDepth == 'tDepth3':
        tDepth = targetDepth3
    if valve == 'valve1':
        valve = valve1
    if valve == 'valve2':
        valve = valve2
    if valve == 'valve3':
        valve = valve3
    print ("[%.3f] - Target depth: %d" % (elaTime,tDepth))
    eventLog.info("[%.3f] - Target depth: %d" % (elaTime,tDepth))
    print ("[%.3f] - Valve being used: %d" % (elaTime,valve))
    eventLog.info("[%.3f] - Valve being used: %d" % (elaTime,valve))
    #----------------------------------------------------------------------
    #Loop Begins
    #----------------------------------------------------------------------
    while True:
        #time management 
        time.sleep(sleepTime)
        tNow = time.time()
        elapsedTime = tNow-tStart
        tSinceLastRecorded = tNow - tLastRecord
        
        if (tSinceLastRecorded) >= recordingInterval:
            if sensor.read():
                print("[%.3f] - Pressure: %0.3f psi") % (elapsedTime,
                                                         sensor.pressure(ms5837.UNITS_psi))
                print("[%.3f] - Temperature: %0.2f C") % (elapsedTime,
                                                         sensor.temperature())
            else:
                print ("[%.3f] - Pressure sensor failed" % elapsedTime)
                eventLog.info("[%.3f] - ERROR: Pressure Sensor Failed %f" % (elapsedTime))
                exit(1)
   
            psi = sensor.pressure(ms5837.UNITS_psi)
            water=1/1.4233 #standard psi for water 
            p = 14.7 #pressure at sea level 
            currentDepth = (psi-p)*water #calculate the current depth 
            print ("[%.3f] - Current Depth: %.4f" % (elapsedTime, currentDepth))
            
            if (tDepth - depthErr) <= currentDepth <= (tDepth + depthErr):
                print ("[%.3f] - Target depth reached" % elapsedTime)
                eventLog.info("[%.3f] - Target depth reached: %f" % (elapsedTime,currentDepth))
                runEdna = ednaObj.run(elapsedTime,valve,valve4) #call edna object to run
                break
            
                if runEdna == None:
                    print ("[%.3f] - ERROR: Sample lost" % elapsedTime)
                    eventLog.info("[%.3f] - ERROR: Sample lost: %s" % (elapsedTime,runEdna))

            else:
                #print ("[%.3f] - Rosette being lowered" % elapsedTime)
                eventLog.info("[%.3f] - Rosette being lowered" % (elapsedTime))
        
                    
        f.write("%f,%f,%f,%f \n" % (elapsedTime,currentDepth,sensor.pressure(ms5837.UNITS_psi),sensor.temperature()))
        f.flush()
    #-----------------------------------------------------
    #Loop Ends
    #----------------------------------------------------- 
        
print ("DONE!")

