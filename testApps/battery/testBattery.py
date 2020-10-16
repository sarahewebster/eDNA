#!/usr/bin/env python
import time
import smbus 
from smbus import SMBus
'''import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)

GPIO.setup(2, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(3, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(26, GPIO.OUT)

#GPIO.output(2,GPIO.HIGH)
#GPIO.output(3,GPIO.HIGH)
GPIO.output(26,GPIO.HIGH)'''

bus = smbus.SMBus(1)
addr = 0x0b
addr2 = 0x0d

#battVolt = ((bus.read_word_data(addr, 0x09))) #/1000.0)/4.45
#print (battVolt)

current = ((bus.read_word_data(0x0b, 0x0a))) #/1000.0)/4.45
#current = ((bus.read_word_data(addr2, 0x0a))) #/1000.0)/4.45
print (current)

'''def getBattStatus(bus, addr):
    try:
        battVolt = ((bus.read_word_data(addr, 0x09))) #/1000.0)/4.45
        current = ((bus.read_word_data(addr, 0x0a))) #/1000.0)/4.45
        #return battVolt, current

    except IOError:
        return 0, 0
    
    return (battVolt, current)

(battVolt, current) = getBattStatus(bus, addr)
print (battVolt, current)'''
'''def setCharger():


def getInternalTemp():'''
    
