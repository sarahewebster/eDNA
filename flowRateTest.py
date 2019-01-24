#!/usr/bin/env python
##############################################################################
#This script tests a flow sensor on GPIO17 on raspbrry pi (YF-S402 sensor)
#
#WIRING
#red (power) --> pin 2 or pin 4 
#black (ground) -->  pin6
#yellow (sensor) --> pin 11 (GPIO17) 10kohm resistor to power 
#
#############################################################################

#my imports
import time, sys, os
import RPi.GPIO as GPIO

# my imports
utilsDir= "/home/pi/dev/utilities"
sys.path.insert(0, utilsDir)
from utils import currentTimeString
#----------------------------------------------------------------------------
# specify what directory to save the written file in 
directory = sys.argv[1]

# get the file name from currentTimeString functino
dataFile = str(currentTimeString())

# joing the directory path to save with file name 
path = os.path.join(directory, dataFile)

# open the file to write 
f = open(path + '.txt', 'w')

#flow sensor parameters/variables

FLOW_SENSOR = 17
rate_cnt = 0           #rate of counts (L/min)
tot_cnt = 0            #total counts (total liters)
minutes = 0            #total minutes  
constant = 0.0001323     #pulses to liters constant based on testing
tStart = 0.0           #initialize time
gpio_last = 2          #was last state 0 or 1 or other?

print('Water Flow - Approximate')
print('Control c to exit')

#BCM indicates the GPIO#, BOARD would indicate the pin number
#from that GPIO 
GPIO.setmode(GPIO.BCM)
#set up gpio with gpio pin being used 
GPIO.setup(FLOW_SENSOR, GPIO.IN)


global count
count = 0

def countPulse(FlOW_SENSOR):
   global count
   count = count+1
   #print count

GPIO.add_event_detect(FLOW_SENSOR, GPIO.FALLING, callback=countPulse)

while True:
    tNow = time.time()
    # get the elapsed time since the beginning of the app
    elapsedTime = tNow-tStart
    #print "Elapsed time: %.3f" % elapsedTime
    for sec_mult in range(0,1):
        tStart = time.time() + 1
        rate_cnt = 0
        while time.time() <= tStart:
            gpio_cur = GPIO.input(FLOW_SENSOR)
            if gpio_cur != gpio_last:
                rate_cnt += 1
                tot_cnt += 1
            else:
                rate_cnt = rate_cnt
                tot_cnt = tot_cnt
            try:
                None

            except KeyboardInterrupt:
                print('\nCTRL C - Exiting nicely')
                GPIO.cleanup()
                print ('Done')
                sys.exit()
            gpio_last = gpio_cur
    print (rate_cnt)
    print (tot_cnt)
    print('Liters/min',(rate_cnt * constant), 'approximate')
    print('Total liters',(tot_cnt * constant))

    f.write("%f %f \n" % ((rate_cnt * constant),
                        (tot_cnt * constant)))
    f.flush()
   
