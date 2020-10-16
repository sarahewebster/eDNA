#!/usr/bin/env python3
import time
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

flow = 20
GPIO.setup(flow, GPIO.IN)
#flow sensor parameters/variables
rateCnt = 0.0           #rate of counts (L/min)
totCnt = 0.0            #total counts (total liters)
minutes = 0.0            #total minutes  
constant = 0.0001323   #pulses to liters constant
                       #based on testing
tStart = 0.0           #initialize time
lastGPIO = 2          #last state 0 or 1 or other?
#------------------------------------------------------

inFlow = True
tS = time.time()
topTime = 60

while (inFlow):
    time.sleep(.25)
    tNow = time.time()
    elapsedTime = tNow - tS
    current = GPIO.input(flow)
    print (current)
   #while (time.time() <= tStart):

    if current != lastGPIO:
        rateCnt += 1
        totCnt += 1
    else:
        rateCnt = rateCnt
        totCnt = totCnt
      
    lastGPIO = current
    lPerMin = (rateCnt * constant)
    totalL = (totCnt * constant)

    print('[%.3f] - Total liters %f' % (elapsedTime,totalL))
    print('[%.3f] - Liters/min %f'% (elapsedTime,lPerMin))
        
    if (elapsedTime > topTime):
        inFlow = False
