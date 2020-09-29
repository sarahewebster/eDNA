#!/usr/bin/env python3
##############################################################################
#This app primes entire eDNA system at once 
##############################################################################
#my imports
import time, sys, os
import RPi.GPIO as GPIO

# my imports
from config3 import Config
from utils import *

GPIO.setwarnings(False) #no GPIO warning
#=============================================================================
#Load config file 
configDat = sys.argv[1]

configFilename = configDat #Load config file/parameters needed
config = Config() # Create object and load file
ok = config.loadFile( configFilename )
if( not ok ):
	sys.exit(0)

#MOTOR
waterPump = config.getInt('Motor', 'sampleMotor')
soluPump = config.getInt('Motor', 'ethanolMotor')

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

#------------------------------------------------------------  
#Check all before priming
#------------------------------------------------------------
try: 
    checkValve(valve1)
    sys.exit(0)
except:
    print ("ERROR: Something went wront with valve: %d" % valve1)
time.sleep(2)
try:
    checkValve(valve2)
    sys.exit(0)
except:
    print ("ERROR: Something went wront with valve: %d" % valve2)                 
time.sleep(2)
try: 
    checkValve(valve3)
    sys.exit(0)
except:
    print ("ERROR: Something went wront with valve: %d" % valve3)      
time.sleep(2)
try: 
    checkValve(valve4)
    sys.exit(0)
except:
    print ("ERROR: Something went wront with valve: %d" % valve4)    
time.sleep(2)
try: 
    checkPump(waterPump)
    sys.exit(0)
except:
    print ("ERROR: Something went wront with pump: %d" % waterPump)   
time.sleep(2)
try: 
    checkPump(soluPump)
    sys.exit(0)
except:
    print ("ERROR: Something went wront with pump: %d" % soluPump)           
time.sleep(5)
        
#------------------------------------------------------------
#time to prime   
#Loop through one valve at a time
#------------------------------------------------------------
for increment in range(1,4):
    strInc = str(increment)
    valve = ('valve' + strInc)
    if valve == 'valve1':
        valve = valve1
    if valve == 'valve2':
        valve = valve2
    if valve == 'valve3':
        valve = valve3
                           
    tStart = time.time() #initialize time
    #----------------------------------------------------------------------
    #Loop Begins
    #----------------------------------------------------------------------
    primeValve(valve, waterPump)

    while True:
        tNow = time.time()
        elapsedTime = tNow -tStart
        psi = getPressure(adc,diffGain,diffPressGain)
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
    #----------------------------------------------------------------------
    #Loop Ends
    #----------------------------------------------------------------------

print ("Done!")
sys.exit(0)

