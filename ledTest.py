#!/usr/bin/env python
#############################################################################
#This scipt is a brief intro on how to turn LED's on and off on the Pi
#This will be used as a visual on turning valves to open and close
#WIRING
#330ohm resistor to ground
#ground to pin 3 on pi 
#+ to pin 12 on pi (GPIO18)
#############################################################################
#standard imports
import RPi.GPIO as GPIO
import time
#----------------------------------------------------------------------------
'''#set naming to GPIO on pi 
GPIO.setmode(GPIO.BCM)
#do not print GPIO warning message to screen 
GPIO.setwarnings(False)
#set pin 12 (GPIO18) to output message 
GPIO.setup(18,GPIO.OUT)
#turns GPIO pin on
GPIO.output(18,GPIO.HIGH)
#led should be on 
print ("led on")
#slee of a second 
time.sleep(10)
#turns GPIO pin off 
GPIO.output(18, GPIO.LOW)
#led should be off
print ("led off")'''

#turn the valve on and off in 10sec intervals
def valve_onOff(Pin):
    while True:
        GPIO.output(18,GPIO.HIGH)
        print ("GPIO HIGH (on), valve should be off")
        time.sleep(10)
        GPIO.output(18, GPIO.LOW)
        print ("GPIO LOW (off), valve should be on")
        time.sleep(10)
