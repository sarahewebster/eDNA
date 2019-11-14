#!/usr/bin/python

# standard imports 
import numpy as np
import datetime 
import time 
from datetime import datetime
import RPi.GPIO as GPIO
import logging
#import ms5837

###############################################################
# This function names files created with current date and time 
###############################################################
def currentTimeString(): 	
    # Name the file according to the current time and date  
    dataFile = datetime.strftime(datetime.now(), "%Y%m%d%H%M%S")
    print (dataFile)
    return dataFile

###############################################################
#run flow meter to record water/ethanol flow 
###############################################################
def recordFlow(flow,
                rateCnt,
                totalCnt,
                timeStart,
                constant,
                lastGpio,
                targetLiters,
                eventLog,
                dataFile,
                elapsedTime,
                soluTime,
                sensor):
    tStart = time.time()
    
    while True:
        tNow = time.time()
        elapsed = tNow - tStart
        elapseTime = (elapsedTime + elapsed)
        time.sleep(.25)
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
        print ("[%.3f] - Current Depth: %.4f" % (elapseTime, currentDepth))
        
        flowSensor = GPIO.input(flow)
        
        if flowSensor != lastGpio:
            rateCnt += 1
            totalCnt += 1
        else:
            rateCnt = rateCnt
            totalCnt = totalCnt
            
        lastGpio = flowSensor
        lPerMin =(rateCnt*constant)
        totalLiters = (totalCnt*constant)
        eventLog.info("[%.3f] - Measuring Flow. Total liters: %f" % (elapseTime,totalLiters))
        dataFile.write("%f,%f,%f,%s\n" % (elapseTime,lPerMin,totalLiters,'999'))
        dataFile.write("%f,%f,%f,%f \n" % (elapseTime,currentDepth,sensor.pressure(ms5837.UNITS_psi),sensor.temperature()))
        print('[%.3f] - Total liters %f' % (elapseTime,totalLiters))

        dataFile.flush()
        if totalLiters >= targetLiters:
            return (totalLiters,elapseTime)
        if elapsed > soluTime:
            return None
            break 
    
    
