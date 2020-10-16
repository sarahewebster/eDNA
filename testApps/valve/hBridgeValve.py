#!/usr/bin/env python3

#Flip solenoid valves open and closed  
import time
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
#----------------------------------------------------

#valve1
enValve1=27
valve1 = 24
valve1GND = 25
#valve2
enValve2=23
valve2 = 18
valve2GND = 22
#valve3
enValve3=17
valve3 = 16
valve3GND =19
#valve4
enValve4=6
valve4 = 5
valve4GND = 4

GPIO.setup(valve1, GPIO.OUT)
GPIO.setup(valve1GND, GPIO.OUT)
GPIO.setup(enValve1, GPIO.OUT)
GPIO.setup(valve2, GPIO.OUT)
GPIO.setup(valve2GND, GPIO.OUT)
GPIO.setup(enValve2, GPIO.OUT)
GPIO.setup(valve3, GPIO.OUT)
GPIO.setup(valve3GND, GPIO.OUT)
GPIO.setup(enValve3, GPIO.OUT)
GPIO.setup(valve4, GPIO.OUT)
GPIO.setup(valve4GND, GPIO.OUT)
GPIO.setup(enValve4, GPIO.OUT)

def openValve(enValve, valve, valveGND):
    GPIO.output(enValve, GPIO.HIGH)
    GPIO.output(valve, GPIO.HIGH)
    GPIO.output(valveGND, GPIO.LOW)
    
def closeValve(enValve, valve, valveGND):
    GPIO.output(enValve, GPIO.HIGH)
    GPIO.output(valve, GPIO.LOW)
    GPIO.output(valveGND, GPIO.HIGH)

print ("open valve 1")
openValve(enValve1, valve1, valve1GND)
time.sleep(3)
print ("close valve 1")
closeValve(enValve1, valve1, valve1GND)
time.sleep(3)

print ("open valve 2")
openValve(enValve2, valve2, valve2GND)
time.sleep(3)
print ("close valve 2")
closeValve(enValve2, valve2, valve2GND)
time.sleep(3)

print ("open valve 3")
openValve(enValve3, valve3, valve3GND)
time.sleep(3)
print ("close valve 3")
closeValve(enValve3, valve3, valve3GND)
time.sleep(3)

print ("open valve 4")
openValve(enValve4, valve4, valve4GND)
time.sleep(3)
print ("close valve 4")
closeValve(enValve4, valve4, valve4GND)

print ("Done")


