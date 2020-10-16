#!/usr/bin/env python
import time
import threading 
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(21, GPIO.OUT)

GPIO.output(21, GPIO.LOW)

'''GPIO.setmode(GPIO.BCM)

GPIO.setup(13, GPIO.OUT)

    
print ("Start LED blinks")
led = GPIO.PWM(13,1)
count = 0
while count < 4:
    #led = GPIO.PWM(ledGPIO,1)
    led.start(0)
    led.ChangeDutyCycle(10)
    time.sleep(1)
    count += 1
led.stop()
GPIO.cleanup()'''

'''led = GPIO.PWM(16,1)
count = 0
# done sampling blinks
while count < 4: 
    led.start(0)

    led.ChangeDutyCycle(10)
    time.sleep(1)
    count += 1
led.stop()
GPIO.cleanup()'''