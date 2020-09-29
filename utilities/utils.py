#!/usr/bin/python3
#--------------------------------------------------------------
# contains functions used in ednaClass and ednaMain
#--------------------------------------------------------------
# standard imports 
import numpy as np
import datetime 
import time
import smbus
from datetime import datetime
import RPi.GPIO as GPIO
from logging import FileHandler
from logging import Formatter
import logging

#--------------------------------------------------------------

################### TIME METHODS ################
#--------------------------------------------------------------
# this function names files created with current date and time 
#--------------------------------------------------------------
def currentTimeString(): 	
    # Name the file according to the current time and date  
    dataFile = datetime.strftime(datetime.now(), "%Y%m%d%H%M%S")
    return dataFile

############## PRIME METHODS ###################
#------------------------------------------------------------
# To prime one valve at a time
#------------------------------------------------------------
def primeValve(valveEn,
               valve,
               valveGnd,
               pump,
               sampleMotorP):
    
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(valve, GPIO.OUT)
    GPIO.setup(pump, GPIO.OUT)

    try: 
        openValve(valveEn,valve,valveGnd)
        print ("\nFlipping valve open: %d" % valve)
        time.sleep(2)
        
        sampleMotorP.start(100)
        print ("\nTurning water pump on: %d" % pump)
    except:
        print ("ERROR: something went wrong, please try again")
        sys.exit(0)

#------------------------------------------------------------
# check motors by turning on and off
#------------------------------------------------------------
def checkPump(pump,
              blinkNum,
              blinkDuration,
              ledGPIO,
              sampleMotorP):
    GPIO.setmode(GPIO.BCM)
    
    GPIO.setup(pump, GPIO.OUT)
    GPIO.setup(ledGPIO, GPIO.OUT)

    try:
        blink = 0
        GPIO.output(pump, GPIO.LOW)
        print ("\n")
        print ("Turning off motor to initialize: %d" % pump)
        print ("Turning ethanol pump on: %d" % pump)
        GPIO.output(pump, GPIO.HIGH)
        while (blink < blinkNum):
            GPIO.output(ledGPIO, GPIO.HIGH)
            time.sleep(blinkDuration) #how long LED is on
            GPIO.output(ledGPIO, GPIO.LOW)
            blink += 1
            time.sleep(2) #how long LED is off
        print ("Turning ethanol pump off: %d" % pump)
        GPIO.output(pump, GPIO.LOW)
    except:
        print ("ERROR: Something went wrong with pump: %d" % pump)

#-----------------------------------------------------------
# Check valve by flippin open and closed 
#-----------------------------------------------------------
def checkValve(valve,
               blinkNum,
               blinkDuration,
               ledGPIO):
    GPIO.setmode(GPIO.BCM)
    
    GPIO.setup(valve, GPIO.OUT)
    GPIO.setup(ledGPIO, GPIO.OUT)

    blink = 0
    try:
        GPIO.output(valve, GPIO.HIGH)
        print ("\nFlipping valve open: %d" % valve)
        while (blink < blinkNum):
            GPIO.output(ledGPIO, GPIO.HIGH)
            time.sleep(blinkDuration) #how long led is on 
            GPIO.output(ledGPIO, GPIO.LOW)
            blink += 1
            time.sleep(2) #How long LED is off
        GPIO.output(valve, GPIO.LOW)
        print ("\nFlipping valve closed: %d" % valve)
    except:
        print ("ERROR: something went wrong, please try again")
        sys.exit(0)
        

################ FLOW AND PRESSURE METHODS #####################
#--------------------------------------------------------------
# run flow meter to record water/ethanol flow
# contineu checking depth and differential pressure sensor
# pressure for psi across each filer sample
#--------------------------------------------------------------
def recordFlow(flowGPIO,maxDiffPressure,targetLiters,
                eventLog,dataFile,elapsedTime,
                soluTime,recordRate,rateCnt,
                totCnt,tStart,constant,
                lastGPIO,depthCh,diffCh,
                gain,adc,checkAvgSamples,
                devParam,tDepth,depthErr,
                ledGPIO,bus0,bus1,
                battAddr,battCurrent):
    
    GPIO.setmode(GPIO.BCM)
    
    GPIO.setup(flowGPIO, GPIO.IN)
    GPIO.setup(ledGPIO, GPIO.OUT)

    tStart = time.time()
    sleepTime = 1/recordRate

    goodPressure = True
    inFlow = True
    while (inFlow):
        GPIO.output(ledGPIO, GPIO.HIGH)
        tNow = time.time()
        elapsed = tNow - tStart
        elapseTime = (elapsedTime + elapsed)
        print ("[%.3f] - Measuing flow" % elapseTime)
        time.sleep(sleepTime)
        
        currentDepth = recPressure(checkAvgSamples,
                                   depthCh,
                                   elapseTime,
                                   eventLog,
                                   gain,
                                   adc,
                                   devParam,
                                   dataFile) 
                                             
        #Check current while sample is being collected 
        current0,current1 = getCurrent(bus0,bus1,battAddr,battCurrent)
        print ("[%.3f] - Current0: %f, Current1: %f" % (elapseTime,current0,current1))
        eventLog.info("[%.3f] - Current0 during flow: %f, Current1 during flow: %f" % (elapseTime,current0,current1))

        # retun none if depth moves while processing data 
        if (tDepth - depthErr) >= currentDepth >= (tDepth + depthErr):
            return none
            
        psi = checkPressure(adc,gain,diffCh) #check diff pressure psi
        
        if (psi > maxDiffPressure):
            print ("[%.3f] - ERROR: Flow too strong!")
            eventLog.info("[%s] - ERROR: Flow too strong!" % (str(currentTimeString())))
            goodPressure = False
        
        current = GPIO.input(flowGPIO)
       
        if current != lastGPIO:
            rateCnt += 1
            totCnt += 1
        else:
            rateCnt = rateCnt
            totCnt = totCnt
        lastGPIO = current
        lPerMin = (rateCnt * constant)
        totalL = (totCnt * constant)
        
        dataFile.write("%s,%f,%f,%f\n" % (str(currentTimeString()),elapseTime,flowGPIO,totalL))
        print('[%.3f] - Total liters %f' % (elapseTime,totalL))
        print('[%.3f] - Liters/min %f'% (elapseTime,lPerMin))
        dataFile.flush()
        
        print ('[%.3f] - Elapsed Time: %f' % (elapseTime, elapsed))
        
        if (totalL >= targetLiters):
            GPIO.output(ledGPIO, GPIO.LOW)
            time.sleep(1)
            GPIO.output(ledGPIO, GPIO.HIGH)
            time.sleep(1)
            GPIO.output(ledGPIO, GPIO.LOW)
            
            return (totalL,elapseTime,goodPressure)
        
        elif (elapsed > soluTime):
            print ("[%.3f] - Time to collect sample has exceeded maximum time needed" % elapseTime)
            GPIO.output(ledGPIO, GPIO.LOW)
            time.sleep(1)
            GPIO.output(ledGPIO, GPIO.HIGH)
            time.sleep(1)
            GPIO.output(ledGPIO, GPIO.LOW)
            inFlow = False
            
            return (totalL,elapseTime,goodPressure)
            break
        
        
#----------------------------------------------------------------------------------------
# calculate and return rcurrent depth from given pressure 
#---------------------------------------------------------------------------------------- 
def getDepth(pressureSenCh,
                elapsedTime,
                eventLog,
                GAIN,
                adc):
    GPIO.setmode(GPIO.BCM)
    
    value = [0]
    value[0] = adc.read_adc(pressureSenCh, gain=2/3)
        
    volts = value[0]/32767.0*6.144
    psi= 50.0*volts-10.0
    water=1/1.4233 #standard psi for water 
    p = 14.7 #pressure at sea level 
    currentDepth = (psi-p)*water #calculate the current depth 
    
    return currentDepth

#----------------------------------------------------------------------------------------
# record pressure to determine depth eDNA samples is at. If average sample from 
# cehckAvgSamples is within the standerd dev of the previous avg sample then, get 
# current depth for that pressure and return current depth 
#----------------------------------------------------------------------------------------
def recPressure(checkAvgSamples,
                depthSens,
                elapsedTime,
                eventLog,
                gain,
                adc,
                devParam,
                dataFile):
    
    GPIO.setmode(GPIO.BCM)
    
    #avg every 10 data points
    depthArray = []
    time.sleep(1)
    for x in range(0,checkAvgSamples):
        currentDepth = getDepth(depthSens,elapsedTime,eventLog,gain,adc)
                    
        eventLog.info("[%s] - Appending las 10 depth reading" % str(currentTimeString()))
        depthArray.append(currentDepth)
        eventLog.info("[%s] - This is the data array: %s" % (str(currentTimeString()),depthArray))
                
    avg = np.mean(depthArray)
    lastAndRecent = [currentDepth,avg]
    stDev = abs(np.std(lastAndRecent))
                
    if (stDev > devParam):
        print ("[%.3f] - Avg of numbers is not within the stdev of the most recent depth" %
                                                                                    elapsedTime)
        print ("[%.3f] - Throwing out last avg" % elapsedTime)
        eventLog.info("[%s] - Avg of numbers is not within the stdev of the most recent depth" % str(currentTimeString() ))
        
        eventLog.info("[%s] - Throwing out last avg" % str(currentTimeString()))
        pass
    else:     
        #set depth to the average  
        currentDepth = avg
        print ("[%.3f] - Setting the current depth to the average of the last 10 samples: %f " % (elapsedTime,currentDepth))
        eventLog.info("[%s] - Setting the current depth to the average of the last 10 samples: %f" % (str(currentTimeString()),currentDepth))
                    
    #print ("[%.3f] - Current Depth: %f" % (elapsedTime,currentDepth))
    dataFile.write("%s,%f,%f,%s \n" % (str(currentTimeString()),elapsedTime,currentDepth,depthArray))
    dataFile.flush()
    
    return currentDepth

#----------------------------------------------------------------------------------------
# check the pressure in psi and return psi 
#----------------------------------------------------------------------------------------
def checkPressure(adc,GAIN,channel):
    value = [0]
    value[0] = adc.read_adc(channel, gain=2/3)
    volts = value[0]/32767.0*6.144
    psi= 50.0*volts-25.0
    return psi


####################### LED METHODS ###########################
#-----------------------------------------------------------------
# Set led blink pattern with PWM by changing the dudy cycle 
#-----------------------------------------------------------------
def ledBlink(ledGPIO,dudyCycle,led):

    led.start(0)
    led.ChangeDutyCycle(dudyCycle)
    time.sleep(1)

#----------------------------------------------------------------------------------------
# give sample status after all samples have been collected indicating if
# the sample was successfully collected or not 
#----------------------------------------------------------------------------------------
def sampleStatusRep(successStatusdc,unsuccessStatusdc,numBlinks,entireSample,ledGPIO,eventLog):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(ledGPIO, GPIO.OUT)
    led = GPIO.PWM(ledGPIO,1)
    count = 0
    if (entireSample == True):
        while (count < numBlinks):
            ledBlink(ledGPIO,successStatusdc,led)
            eventLog.info("[%s] - Sample successfull: %d" % (str(currentTimeString()), numBlinks))
            print ("[%s] - Sample successfull: %d" % (str(currentTimeString()), numBlinks))
            count += 1
        led.stop()
        GPIO.cleanup()
            
    elif (entireSample == False):
        while count < numBlinks:
            ledBlink(ledGPIO,unsuccessStatusdc,led)
            eventLog.info("[%s] - Sample unsuccessfull: %d" % (str(currentTimeString()), numBlinks))
            print ("[%s] - Sample unsuccessfull: %d" % (str(currentTimeString()), numBlinks))
            count += 1
        led.stop()
        GPIO.cleanup()
            
#----------------------------------------------------------------------------------------
# one, two or three quick set of blinks, 3 times depending on the number of the sample
# just finished adding ethanol, successfull or not. 
#----------------------------------------------------------------------------------------
def getEthanolDone(ledGPIO,sampleNum):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(ledGPIO, GPIO.OUT)

    for sets in range(3):
        for blinks in range(sampleNum):
            GPIO.output(ledGPIO, GPIO.HIGH)
            time.sleep(.25)
            GPIO.output(ledGPIO, GPIO.LOW)
            time.sleep(.25)
        time.sleep(1)
        
#----------------------------------------------------------------------------------------
# one long blink then 1,2 or 3 quick blinks indicating the number of sample that
# just finished, successfull or not. 
#----------------------------------------------------------------------------------------
def getSampleDone(ledGPIO,sampleNum):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(ledGPIO, GPIO.OUT)

    for sets in range(1):
        GPIO.output(ledGPIO, GPIO.HIGH)
        time.sleep(1)
        for blinks in range(sampleNum+1):
            GPIO.output(ledGPIO, GPIO.HIGH)
            time.sleep(0.25)
            GPIO.output(ledGPIO, GPIO.LOW)

#----------------------------------------------------------------------------------------
#Return the voltage from both the batteries 
#----------------------------------------------------------------------------------------
def getVolt(bus0,bus1,
            deviceAddr,
            voltAddr):

    voltage0 = bus0.read_i2c_block_data(deviceAddr,voltAddr,2)
    voltage0 = (voltage0[1]*256+voltage0[0])/1000 #change from mV to Voltage

    voltage1 = bus1.read_i2c_block_data(deviceAddr,voltAddr,2)
    voltage1 = (voltage1[1]*256+voltage1[0])/1000 #change from mV to Voltage
    
    return (voltage0,voltage1) 
    
#----------------------------------------------------------------------------------------
#Return the current from both batteries 
#----------------------------------------------------------------------------------------
def getCurrent(bus0,bus1,
               deviceAddr,
               currentAddr):
    
    current0 = bus0.read_i2c_block_data(deviceAddr,currentAddr,2)

    current0= (current0[1]*256+current0[0]) 
    if(current0 & 0x8000): #figure out if charge or discharge and place signs
        current0 = -0x10000 + current0

    current1 = bus1.read_i2c_block_data(deviceAddr,currentAddr,2)

    current1= (current1[1]*256+current1[0]) 
    if(current1 & 0x8000): #figure out if charge or discharge and place signs
        current1 = -0x10000 + current1
            
    return (current0, current1) 
    
def getCharge(bus0,bus1,
              deviceAddr,
              SOC):
    charge0 = bus0.read_i2c_block_data(deviceAddr,SOC,2)
    charge0= (charge0[1]*256+charge0[0])

    charge1 = bus1.read_i2c_block_data(deviceAddr,SOC,2)
    charge1= (charge1[1]*256+charge1[0])
    
    return (charge0, charge1)

#----------------------------------------------------------------------------------------
#Open solenoid valves. Given valve enable pin, valve pin, and valve ground pin.
#valve is opened by enabling valve power pin to low and valve gnd pin to high 
#----------------------------------------------------------------------------------------
def openValve(valveEn,valve,valveGND):
    GPIO.setmode(GPIO.BCM)
    
    GPIO.setup(valve, GPIO.OUT)
    GPIO.setup(valveGND, GPIO.OUT)
    GPIO.setup(valveEn, GPIO.OUT)


    GPIO.output(valveEn, GPIO.HIGH)
    GPIO.output(valve, GPIO.HIGH)
    GPIO.output(valveGND, GPIO.LOW)

#----------------------------------------------------------------------------------------
#Close solenoid valves. Given valve enable pin, valve pin, and valve ground pin.
#valve is opened by enabling valve power pin to high and valve gnd pin to low.
#----------------------------------------------------------------------------------------
def closeValve(valveEn,valve,valveGND):
    GPIO.setmode(GPIO.BCM)
    
    GPIO.setup(valve, GPIO.OUT)
    GPIO.setup(valveGND, GPIO.OUT)
    GPIO.setup(valveEn, GPIO.OUT)

    GPIO.output(valveEn, GPIO.HIGH)
    GPIO.output(valve, GPIO.LOW)
    GPIO.output(valveGND, GPIO.HIGH)
    
#----------------------------------------------------------------------------------------
#Initialize all GPIO pins
#This is done to initialize GPIO after GPIO.cleanup() 
#----------------------------------------------------------------------------------------
def initializeGPIO(ledGPIO,flowGPIO,
                   waterMotorGPIO,ethaMotorGPIO,
                   valve1En,valve1,valve1Gnd,
                   valve2En,valve2,valve2Gnd,
                   valve3En,valve3,valve3Gnd,
                   valve4En,valve4,valve4Gnd):
    GPIO.setmode(GPIO.BCM)  #pin number
    
    GPIO.setup(ledGPIO, GPIO.OUT)
    GPIO.setup(flowGPIO, GPIO.IN)
    GPIO.setup(waterMotorGPIO, GPIO.OUT)
    GPIO.setup(ethaMotorGPIO, GPIO.OUT)
    GPIO.setup(valve1En, GPIO.OUT)
    GPIO.setup(valve1, GPIO.OUT)
    GPIO.setup(valve1Gnd, GPIO.OUT)
    GPIO.setup(valve2En, GPIO.OUT)
    GPIO.setup(valve2, GPIO.OUT)
    GPIO.setup(valve2Gnd, GPIO.OUT)
    GPIO.setup(valve3En, GPIO.OUT)
    GPIO.setup(valve3, GPIO.OUT)
    GPIO.setup(valve3Gnd, GPIO.OUT)
    GPIO.setup(valve4En, GPIO.OUT)
    GPIO.setup(valve4, GPIO.OUT)
    GPIO.setup(valve4Gnd, GPIO.OUT)

#----------------------------------------------------------------------------------------
#Create log files to log eDNA data as well as a log file to log info and error events
#----------------------------------------------------------------------------------------
def logParams(recordingInterval,
              logDir, eventLogName):
    # logging
    dataFile = str(currentTimeString()) #file name

    # log data
    eDNAData = open(logDir + '/' + 'eDNAData-' + dataFile + '.txt', 'a')

    # event log
    LOG_FORMAT = ('[%(levelname)s] %(message)s')
    LOG_LEVEL = logging.INFO 
    EVENT_LOG_FILE = (logDir + '/' + eventLogName + dataFile + '.log')
    eventLog = logging.getLogger("Event")
    eventLog.setLevel(LOG_LEVEL)
    eventLogFileHandler = FileHandler(EVENT_LOG_FILE)
    eventLogFileHandler.setLevel(LOG_LEVEL)
    eventLogFileHandler.setFormatter(Formatter(LOG_FORMAT))
    eventLog.addHandler(eventLogFileHandler)
    
    return (eventLog, eDNAData)

#----------------------------------------------------------------------------------------
#Blink LED patters when program has begin running as well as when samples are
#done being collected (all 3 samples are collected) 
#----------------------------------------------------------------------------------------
def startEndLed(ledStartNumBlinks,ledGPIO,ledStartdc,led):
    count = 0
    while count < ledStartNumBlinks: 
        ledBlink(ledGPIO,ledStartdc,led)
        count += 1
    led.stop()
    GPIO.cleanup()

    