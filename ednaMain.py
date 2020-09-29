#!/usr/bin/env python3
#####################################################################
#This app runs process for programming hardware to collect 3 samples
#of environmental data on a filter. X amount of water is filtered 
#by turning motors on and flipping valves open. X amount of ethanol
#is then added to the sample.
#All variables are configurable via Config file under utilities folder
#####################################################################

#my imports
import time, sys, os, smbus
import RPi.GPIO as GPIO
import logging
from logging import FileHandler
from logging import Formatter
import logging

#third party imports
import Adafruit_ADS1x15 #ADC for pressure

# my imports
from utils import *
from config3 import Config
from ednaClass import *
import logging

# initialize GPIO
GPIO.setwarnings(False) #no GPIO warning
GPIO.setmode(GPIO.BCM)  #pin number
#--------------------------------------------------------------------
#Load config file 
configDat =  sys.argv[1]
configFilename = configDat #Load config file/parameters needed
config = Config() # Create object and load file
ok = config.loadFile( configFilename )
if( not ok ):
	sys.exit(0)

#Initialize parameters 
#PARAMS
logDir = config.getString('System', 'LogDir')
adcAddr = config.getString('Params', 'ADCAddr')
adcBus = config.getString('Params', 'ADCBus')

#FLOW
flowGPIO = config.getInt('FlowSensor', 'Flow')

#LED
ledGPIO = config.getInt('LED', 'ledGPIO')
# start blink initialization 
ledStartdc = config.getInt('LED', 'StartDC') 
ledStartNumBlinks = config.getInt('LED', 'StartNumBlinks')
count = config.getInt('LED', 'count')
successStatusdc = config.getInt('LED', 'SuccessStatusDC')
unsuccessStatusdc = config.getInt('LED', 'UnsuccessStatusDC')
ledDepthdc = config.getInt('LED', 'DepthDC')

#VALVES
valve1En = config.getInt('Valves', 'Valve1En')
valve1 = config.getInt('Valves', 'Valve1')
valve1Gnd = config.getInt('Valves', 'Valve1Gnd')
valve2En = config.getInt('Valves', 'Valve2En')
valve2 = config.getInt('Valves', 'Valve2')
valve2Gnd = config.getInt('Valves', 'Valve2Gnd')
valve3En = config.getInt('Valves', 'Valve3En')
valve3 = config.getInt('Valves', 'Valve3')
valve3Gnd = config.getInt('Valves', 'Valve3Gnd')
valve4En = config.getInt('Valves', 'Valve4En')
valve4 = config.getInt('Valves', 'Valve4')
valve4Gnd = config.getInt('Valves', 'Valve4Gnd')

#MOTOR
waterMotorGPIO = config.getInt('Motor', 'sampleMotor')
ethaMotorGPIO = config.getInt('Motor', 'ethanolMotor')

#PRESSURE
targetDepth1 = config.getInt('PressureSensor', 'TargetDepth1')
targetDepth2 = config.getInt('PressureSensor', 'TargetDepth2')
targetDepth3 = config.getInt('PressureSensor', 'TargetDepth3')
recordRate = config.getInt('PressureSensor', 'recordRate')

depthErr = config.getInt('PressureSensor', 'DepthError')
devParam = config.getInt('PressureSensor', 'DevParam')
checkAvgSamples = config.getInt('PressureSensor', 'CheckAvgSamples')

depthCh = config.getInt('PressureSensor', 'DepthCh')
diffCh = config.getInt('PressureSensor', 'DiffCh') 
gain = config.getFloat('PressureSensor', 'gain')

adc = Adafruit_ADS1x15.ADS1115(address=0x48,busnum=adcBus)

#PROGRAM PARAMETERS
#Number of samples to collect
#Note: This is not the only area this needs to change in, more
#samples will need to be added in for loop below 
totalSamples = config.getInt('Params', 'TotalSamples')
totalSamples = (totalSamples + 1)
startSample = config.getInt('Params', 'StartSample')

#BATTERY
bus0= smbus.SMBus(0)
bus1= smbus.SMBus(1)
battAddr = 0x0B
battVolt= 0x09
battCurrent = 0x0A
battSOC = 0x0e
currentPeak = config.getFloat('Battery', 'CurrentPeak')

recordingInterval = 1./recordRate

#GPIO output
initializeGPIO(ledGPIO,flowGPIO,
                waterMotorGPIO,ethaMotorGPIO,
                valve1En,valve1,valve1Gnd,
                valve2En,valve2,valve2Gnd,
                valve3En,valve3,valve3Gnd,
                valve4En,valve4,valve4Gnd)

#Log files 
eventLog, eDNAData = logParams(recordingInterval,
                               logDir,'eDNAEvent')
# initialize led with PWM 
led = GPIO.PWM(ledGPIO,1)

#create edna object to call once depth is reached 
ednaObj = ednaClass(config,eventLog,eDNAData,adc)

#initialized variables 
tLastRecord = 0
tStart = time.time()

sampleStatus1 = False
sampleStatus2 = False
sampleStatus3 = False
getSamples = True

#------------------------------------------------------------------------
# Initial LED blinks to indicate program is running
#------------------------------------------------------------------------
eventLog.info("[%s] - Start LED blinks" % (str(currentTimeString())))
startEndLed(ledStartNumBlinks,ledGPIO,ledStartdc,led)

#GPIO was cleaned up, reinitialize again 
initializeGPIO(ledGPIO,flowGPIO,
                waterMotorGPIO,ethaMotorGPIO,
                valve1En,valve1,valve1Gnd,
                valve2En,valve2,valve2Gnd,
                valve3En,valve3,valve3Gnd,
                valve4En,valve4,valve4Gnd)

#Initialize led with PWM 
ledDepth = GPIO.PWM(ledGPIO,1)

#Close all valves to initialize
closeValve(valve1En,valve1,valve1Gnd)
closeValve(valve2En,valve2,valve2Gnd)
closeValve(valve3En,valve3,valve3Gnd)
closeValve(valve4En,valve4,valve4Gnd)

#-----------------------------------------------------------------------
#Loop through a total of 3 samples
#This will have to change when more samples are introduced 
#-----------------------------------------------------------------------
for increment in range(startSample,totalSamples):
    tHere = time.time()
    elapsedTime = tHere - tStart
    
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
        valveEn = valve1En
        valve = valve1
        valveGnd = valve1Gnd
    if valve == 'valve2':
        valveEn = valve2En
        valve = valve2
        valveGnd = valve2Gnd
    if valve == 'valve3':
        valveEn = valve3En
        valve = valve3
        valveGnd = valve3Gnd
        
    print ("[%.3f] - Target depth: %d" % (elapsedTime,tDepth))
    eventLog.info("[%s] - Target depth: %d" % (elapsedTime,tDepth))
    print ("[%.3f] - Valve being used: %d" % (elapsedTime,valve))
    eventLog.info("[%s] - Valve being used: %d" % (elapsedTime,valve))
    
    #Initialize sample status for each sample
    #Indicate if sample was successfully collected or not 
    sampleStatus = ("sampleStatus" + strInc)
    
    timeHere = time.time()
    #----------------------------------------------------------------------
    #Loop Begins
    #----------------------------------------------------------------------
    while (getSamples == True):
        #time management 
        time.sleep(recordingInterval)
        tNow = time.time()
        elapsedTime = tNow-timeHere
        tSinceLastRecorded = tNow - tLastRecord
        
        if (tSinceLastRecorded >= recordingInterval):
            
            #LED pattern to indicate depth is being checked
            ledBlink(ledGPIO,ledDepthdc,ledDepth)  
            eventLog.info("[%.3f] - Start checking depth" % elapsedTime)
            
            #Check battery volt and current 
            volt0,volt1 = getVolt(bus0,bus1,battAddr,battVolt)
            print ("[%.3f] - Volt0: %f, Volt1: %f" % (elapsedTime,volt0,volt1))
            eventLog.info("[%.3f] - Volt0: %f, Volt1: %f" % (elapsedTime,volt0,volt1))
            current0,current1 = getCurrent(bus0,bus1,battAddr,battCurrent)
            print ("[%.3f] - Current0: %f, Current1: %f" % (elapsedTime,current0,current1))
            eventLog.info("[%.3f] - Current0: %f, Current1: %f" % (elapsedTime,current0,current1))
    
            #Check depth
            currentDepth = recPressure(checkAvgSamples,depthCh,elapsedTime,eventLog,
                                        gain,adc,devParam,eDNAData)
        
        #Target depth is reached 
        if (tDepth - depthErr) <= currentDepth <= (tDepth + depthErr):
            
            #turn off search LED blink pattern 
            led.stop()
            eventLog.info("[%.3f] - Stop check depth LED blinks" % elapsedTime)
            
            print ("[%.3f] - Target depth reached" % elapsedTime)
            eventLog.info("[%.3f] - Target depth reached: %f" % (elapsedTime,currentDepth))
            
            #Start collecting sample 
            runEdna, elapsedTime = ednaObj.run(elapsedTime,
                                               valveEn,valve,valveGnd,
                                               valve4En,valve4,valve4Gnd,
                                               increment,
                                               tDepth,
                                               depthErr,
                                               bus0,bus1,
                                               battAddr,battCurrent) #call edna object to run
            tStart = time.time()
            
            #returned from running sample, was it successfull?
            #Success = full volume of sea water was collected and full ethanol quantity was
            #added to sample 
            if (runEdna == None or runEdna == False):
                print ("[%.3f] - ERROR: Sample lost" % elapsedTime)
                eventLog.info("[%.3f] - ERROR: Sample lost: %s" % (elapsedTime,runEdna))

                sampleStatus = False
                break
                
            else:
                print ("[%.3f] - Entire sample successfully collected: %s" % (elapsedTime,strInc))
                eventLog.info("[%.3f] - Entire sample successfully collected: %s" % (elapsedTime,runEdna))
                
                sampleStatus = True
                break
            
        #Check current while rosette is being lowered 
        if (current0 > currentPeak or current1 > currentPeak):
            print ("[%.3f] - ERROR: Current too high! current0: %f, current1: %f" % (elapsedTime,current0,current1))
            eventLog.error("[%.3f] - ERROR: Current way too high! current0: %f, current1: %f" % (elapsedTime,current0,current1))
            
        else:
            eventLog.info("[%s] - Rosette being lowered" % (str(currentTimeString())))

    #-----------------------------------------------------
    #Loop Ends
    #-----------------------------------------------------
            
#GPIO was cleaned up, reinitialize again 
initializeGPIO(ledGPIO,flowGPIO,
                waterMotorGPIO,ethaMotorGPIO,
                valve1En,valve1,valve1Gnd,
                valve2En,valve2,valve2Gnd,
                valve3En,valve3,valve3Gnd,
                valve4En,valve4,valve4Gnd)

# initialize led with PWM again 
led0 = GPIO.PWM(ledGPIO,1)
getSamples = False
print ("[%.3f] - Done Sampling" % (elapsedTime))
eventLog.info("[%s] - Done sampling" % (str(currentTimeString())))

#LED blink pattern to indicate sampling is finished  
startEndLed(ledStartNumBlinks,ledGPIO,ledStartdc,led0)

#GPIO was cleaned up, reinitialize again 
initializeGPIO(ledGPIO,flowGPIO,
                waterMotorGPIO,ethaMotorGPIO,
                valve1En,valve1,valve1Gnd,
                valve2En,valve2,valve2Gnd,
                valve3En,valve3,valve3Gnd,
                valve4En,valve4,valve4Gnd)

# report status blinks 
while (getSamples == False):
    for numBlinks in range(1,4):
        time.sleep(2)
        sampleStatusRep(successStatusdc,
                        unsuccessStatusdc,
                        numBlinks,
                        sampleStatus,
                        ledGPIO,
                        eventLog)
