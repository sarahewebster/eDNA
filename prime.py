#!/usr/bin/env python3
##############################################################################
#This app primes entire eDNA system at once 
##############################################################################
#my imports
import time, sys, os
import RPi.GPIO as GPIO
import Adafruit_ADS1x15
from logging import FileHandler
from logging import Formatter
import logging

# my imports
from config3 import Config
from utils import *

GPIO.setwarnings(False) #no GPIO warning
#=============================================================================
#Load config file 
configDat = sys.argv[1]

#sample to prime in command line when ran 
primeValve = int(sys.argv[2])

configFilename = configDat #Load config file/parameters needed
config = Config() # Create object and load file
ok = config.loadFile( configFilename )
if( not ok ):
    sys.exit(0)

#PRIME
runTime = config.getInt('Prime', 'RunTime')

#MOTOR
waterPump = config.getInt('Motor', 'sampleMotor')
soluPump = config.getInt('Motor', 'ethanolMotor')
sampleMotorHz = config.getInt('Motor', 'sampleMotorHz')

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

#PRESSURE
recordRate = config.getInt('PressureSensor', 'recordRate')
recordingInterval = 1./recordRate
diffPressCh = config.getInt('PressureSensor', 'DiffCh') 
diffGain = config.getFloat('PressureSensor', 'gain')
adcBus = config.getString('Params', 'ADCBus')
adc = Adafruit_ADS1x15.ADS1115(address=0x48,busnum=adcBus)
    
#FLOW
flowGPIO = config.getInt('FlowSensor', 'Flow')

#LED
ledGPIO = config.getInt('LED', 'ledGPIO')
    
#GPIO output
initializeGPIO(ledGPIO,flowGPIO,
                waterPump,soluPump,
                valve1En,valve1,valve1Gnd,
                valve2En,valve2,valve2Gnd,
                valve3En,valve3,valve3Gnd,
                valve4En,valve4,valve4Gnd)
GPIO.setup(primeValve,GPIO.OUT)

#LOG FILES
logDir = config.getString('System', 'LogDir')
eventLog, eDNAData = logParams(recordingInterval,
                               logDir,'primeEvent')

if primeValve == 1:
    primeValve = valve1
    valveEn=valve1En
    valveGnd=valve1Gnd
if primeValve == 2:
    primeValve = valve2
    valveEn=valve2En
    valveGnd=valve2Gnd
if primeValve == 3:
    primeValve = valve3
    valveEn=valve3En
    valveGnd=valve3Gnd
    
eventLog.info("[%s] - Valve to prime: %d" % (str(currentTimeString()),primeValve))

sampleMotorP=GPIO.PWM(soluPump,sampleMotorHz) 

#---------------------------------------------------------------   
#Check pumps and valves before priming 
#---------------------------------------------------------------
try: 
    checkValve(valveEn,primeValve,valveGnd,soluPump,sampleMotorP)
    sys.exit(0)
except:
    print ("ERROR: Something went wront with valve: %d" % primeValve)
    eventLog.error("[%s] - ERROR: Something went wrong with valve: %d" % (str(currentTimeString()),primeValve))
    
time.sleep(2)

try: 
    checkPump(waterPump,sampleMotorP)
    sys.exit(0)
except:
    print ("ERROR: Something went wront with pump: %d" % waterPump)
    eventLog.error("[%s] - ERROR: Something went wrong with water pump: %d" % (str(currentTimeString()),waterPump))

time.sleep(2)
try: 
    checkPump(soluPump,sampleMotorP)
    sys.exit(0)
except:
    print ("ERROR: Something went wront with pump: %d" % soluPump)
    eventLog.error("[%s] - ERROR: Something went wrong with ethanol pump: %d" % (str(currentTimeString()),soluPump))

time.sleep(5)

#------------------------------------------------------------
#start priming
#------------------------------------------------------------
try: 
    GPIO.output(valve4, GPIO.HIGH)
    print ("\nFlipping ethanol valve open: %d" % valve4)
    eventLog.error("[%s] - ERROR: Something went wrong with ethanol pump: %d" % (str(currentTimeString()),soluPump))

    time.sleep(2)
    GPIO.output(primeValve, GPIO.HIGH)
    print ("\nFlipping valve to prime open: %d" % valve4)
    time.sleep(2)
    GPIO.output(waterPump, GPIO.HIGH)
    print ("\nTurning water pump on: %d" % waterPump)
except:
    print ("ERROR: something went wrong, please try again")
    sys.exit(0)
                       
tStart = time.time() #initialize time
#------------------------------------------------------------
# Loop Begins
# continue priming for 30 sec
#------------------------------------------------------------
while True:
    tNow = time.time()
    elapsedTime = tNow -tStart
    psi = checkPressure(adc,diffGain,diffPressCh)
    if (psi > 12):
        print ("ERROR: Flow too strong!")
    if runTime < elapsedTime:
        try: 
            GPIO.output(valve4, GPIO.LOW)
            print ("\nFlipping valve closed: %d" % valve4)
            time.sleep(2)
        except:
            print ("ERROR: Valve could not be closed")
            sys.exit(0)
        try:
            GPIO.output(waterPump, GPIO.LOW)
            print ("\nTurning water pump off: %d" % waterPump)
            break
        except:
            print ("ERROR: Pump could not be closed")
            sys.exit(0)
#-------------------------------------------------------------
#Loop Ends
#-------------------------------------------------------------

print ("Done!")
sys.exit(0)