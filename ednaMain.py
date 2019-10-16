#!/usr/bin/env python
#####################################################################
#
#
#
#
#
#turn on the light every .5L,
#wait 5sec and then do it again 
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
from config import Config
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
runTime=config.getInt('Track', 'RunTime')
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
sensor=ms5837.MS5837_30BA() #sensor type
if not sensor.init(): #initialize sensort
    print ("Sensor could not be initialized")
    exit(1)
#---------------------------------------------------------------------------
    
#create edna object to run once depth is reached 
ednaObj = ednaClass(config,eventLog,f)
tLastRecord = 0
tStart = time.time()
var = 0 
#----------------------------------------------------------------------
#Loop Begins
#----------------------------------------------------------------------
while True:
    time.sleep(sleepTime)
    tNow = time.time()
    elapsedTime = tNow-tStart
    tSinceLastRecorded = tNow - tLastRecord
    #time.sleep(recordingInterval)
    if (tSinceLastRecorded) >= recordingInterval:
        if sensor.read():
            print("P: %0.1f mbar %0.3f psi\tT: %0.2f C %0.2f F") % (sensor.pressure(),
            sensor.pressure(ms5837.UNITS_psi),
            sensor.temperature(),
            sensor.temperature(ms5837.UNITS_Farenheit))
        else:
            print ("Sensor failed")
            eventLog.info("[%.3f] - ERROR: Pressure Sensor Failed %f" % (elapsedTime))
            exit(1)
   
        psi = sensor.pressure(ms5837.UNITS_psi)
        #standard psi for water 
        water=1/1.4233
        #pressure at sea level 
        p = 14.7
        #calculate the current depth 
        currentDepth = (psi-p)*water
        print ("Current Depth: %s" % currentDepth)
        if (targetDepth1 - depthErr) <= currentDepth <= (targetDepth1 + depthErr):
            if var == 1 or var == 2:
                print ("first run already ran")
                continue 
            print ("TARGET DEPTH ONE REACHED")
            eventLog.info("[%.3f] - Target depth one reached: %f" % (elapsedTime,currentDepth))
            runEdna1 = ednaObj.run(elapsedTime,valve1,valve4) #call edna object to run
            print (runEdna1)
            var = 1 
            if runEdna1 == None:
                print "Sample lost, flow meter not pumping"
                eventLog.info("[%.3f] - Sample one lost, flow meter not pumping: %s" % (elapsedTime,runEdna1))

        if (targetDepth2 - depthErr) <= currentDepth <= (targetDepth2 + depthErr):
            if var == 2:
                print ("second run already ran")
                print (var)
                continue
            print ("TARGET DEPTH TWO REACHED")
            eventLog.info("[%.3f] - Target depth two reached: %f" % (elapsedTime,currentDepth))
            runEdna2 = ednaObj.run(elapsedTime,valve2,valve4) #call edna object to run
            print (runEdna2)
            var = 2
            if runEdna2 == None:
                print "Sample lost, flow meter not pumping"
                eventLog.info("[%.3f] - Sample two lost, flow meter not pumping: %s" % (elapsedTime,runEdna2))
                
        if (targetDepth3 - depthErr) <= currentDepth <= (targetDepth3 + depthErr):
            print ("TARGET DEPTH THREE REACHED")
            eventLog.info("[%.3f] - Target depth three reached: %f" % (elapsedTime,currentDepth))
            runEdna3 = ednaObj.run(elapsedTime,valve3,valve4) #call edna object to run
            print (runEdna3)
            var = 3 
            if runEdna3 == None:
                print "Sample lost, flow meter not pumping"
                eventLog.info("[%.3f] - Sample three lost, flow meter not pumping: %s" % (elapsedTime,runEdna3))
            if var == 3:
                print ("last run")
                break 
        else:
            print ("Rosette being lowered")
            eventLog.info("[%.3f] - Rosette being lowered" % (elapsedTime))
        
                    
        f.write("%f,pressure sensor:%f,%f \n" % (elapsedTime,currentDepth,sensor.temperature()))
        f.flush()
        
print ("Done!")

#-----------------------------------------------------
#Loop Ends
#----------------------------------------------------- 
