#!/usr/bin/env python
##############################################################################
#This app monitors power, voltage and current from all electronics #powered on a raspberry pi 
##############################################################################
#standard imports
import time
import sys

#third party imports 
from ina219 import INA219, DeviceRangeError

#my imports
from config3 import Config
from utils import *
#=============================================================================
#Load config file 
configDat = sys.argv[1]
configFilename = configDat #Load config file/parameters needed
config = Config() # Create object and load file
ok = config.loadFile( configFilename )
if( not ok ):
	sys.exit(0)
#i2c = config.getStr('currentSensor','i2c')
sleepTime = config.getFloat('CurrentSensor','SleepTime')
runTime = config.getInt('CurrentSensor','runTime')

#Current sensor parameters
SHUNT_OHMS = config.getFloat('CurrentSensor','shuntOhms')
MAX_EXPECTED_AMPS = config.getFloat('CurrentSensor','maxCurrentExpected')
ina = INA219(SHUNT_OHMS, MAX_EXPECTED_AMPS)
ina.configure(ina.RANGE_16V)

#logging
recRate=config.getInt('CurrentSensor','recordRate')
logDir = config.getString('System', 'LogDir')
recordingInterval=1./recRate
print ("Interval: %.3f" % recordingInterval)
dataFile = str(currentTimeString()) #file name


logPower = open(logDir + '/' + 'powerData-' + dataFile + '.txt', 'a')
tStart = time.time()
tLastRecord = 0 # initialize last record

def read_ina219():
    try:
        print('Bus Voltage: {0:0.2f}V'.format(ina.voltage()))
        print('Bus Current: {0:0.2f}mA'.format(ina.current()))
        print('Power: {0:0.2f}mW'.format(ina.power()))
        print('Shunt Voltage: {0:0.2f}mV\n'.format(ina.shunt_voltage()))
    except DeviceRangeError as e:
        # Current out of device range with specified shunt resister
        print(e)
#--------------------------------------------------------------------------
#Loop begins
while True:
    tNow = time.time()
    elapsedTime = tNow - tStart 
    tSinceLastRecorded = tNow - tLastRecord
    time.sleep(recordingInterval)
    if (tSinceLastRecorded) >= recordingInterval:
        read_ina219()
        logPower.write("%f,%f,%f,%f,%f\n" % (elapsedTime,ina.voltage(),ina.current(),ina.power(),ina.shunt_voltage()))
        logPower.flush()
    if elapsedTime > runTime: 
        break
print ('Done!')
