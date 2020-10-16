#!/usr/bin/env python
import time
import threading 
import RPi.GPIO as GPIO
from multiprocessing import Process
from threading import Thread 

GPIO.setmode(GPIO.BCM)

GPIO.setup(14, GPIO.OUT)
#GPIO.output(14, GPIO.LOW)

#PWM
'''
0-off
The higher the dudy cycle the longer its on
100-solid on 

'''
#setup GPIO pins and import GPIO module
led = GPIO.PWM(14,1)
led.start(0)
doneBlinking = False 

def flashLED():
    for dc in xrange(0,100,30):
        led.ChangeDutyCycle(50)
        print (dc)
        time.sleep(0.60)
        doneBlinking = True
        
def printHello():
    for num in xrange(10):
        print "hello"
        time.sleep(1)
        
while True:
    if (doneBlinking == False):
        ledBlink.run()
        hello.run()
        ledBlink.join()
        hello.join()  
        
    if (doneBlinking == True):
        led.stop()
        GPIO.cleanup()
        
    print "what"
    
def ledBlink(ledGPIO,
             blinkGTimes,
             blinkRedTimes,
             howBlink):
    
    if (howBlink.lower() == ("green").lower()):    
        for blink in blinkGTimes: 
            GPIO.output(ledGPIO, GPIO.HIGH)
        
    elif (howBlink.lower() == ("red").lower()):
        for blink in blinkGTimes: 
            GPIO.output(ledGPIO, GPIO.LOW)
        
    elif (howBlink.lower() == ("alternate").lower()):
        for blink in blinkGTimes: 
            GPIO.output(ledGPIO, GPIO.HIGH)
