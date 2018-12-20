#!/usr/bin/python

# @author: Viviana Castillo, APL UW 
##################################################################################
#print pressure sensor output  
##################################################################################
#standard imports
import time

#third party imports
import ms5837

#-------------------------------------------------------------------------------------------------
#pressure sensor 
#-------------------------------------------------------------------------------------------------
sensor=ms5837.MS5837_30BA() #default i2c bus is 1

#initialize sensor before reading it 
#Pressure sensor checked if iniitialized
if not sensor.init():
    print ("Sensor could not be initialized")
    exit(1)
    
#================================================================================
#Loop Begins
#================================================================================
while True:
    #read sensor
    if sensor.read():
	print("P: %0.1f mbar %0.3f psi\tT: %0.2f C %0.2f F") % (sensor.pressure(),
	sensor.pressure(ms5837.UNITS_psi),
	sensor.temperature(),
	sensor.temperature(ms5837.UNITS_Farenheit))
    else:
	print ("Sensor failed")
	exit(1)
    #------------------------------------------------------------
    #calculate current depth from pressure sensor
    #------------------------------------------------------------
    #set variable to pressure sensors current psiS readings 
    psi = sensor.pressure(ms5837.UNITS_psi)
    #standard psi for water 
    water=1/1.4233
    #pressure at sea level 
    p = 14.7
    #calculate the current depth 
    currentDepth = (psi-p)*water
    print ("Current Depth: %s" % currentDepth)
    
    time.sleep(0.5)
#================================================================================
#Loop Begins
#================================================================================SS