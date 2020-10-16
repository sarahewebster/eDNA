#!/usr/bin/env python3

#Need to re-calibrate the flow meter - how to make it more sensative? 
import time
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
#----------------------------------------------------

bottomMEn = 13

#topDudy = 50
bottomDudy = 3
bottomTime = 500 #5 min for 1 L?? -goal

flow = 20
led = 21

#VALVES
valve1En = 27
valve1 = 24
valve1Gnd = 25
valve2En = 23
valve2 = 18
valve2Gnd = 22
valve3En = 17
valve3 = 16
valve3Gnd = 19 
valve4En = 6
valve4 = 5 
valve4Gnd = 4

GPIO.setup(valve1En, GPIO.OUT)
GPIO.setup(valve1, GPIO.OUT)
GPIO.setup(valve1Gnd, GPIO.OUT)
GPIO.setup(valve2En, GPIO.OUT)
GPIO.setup(valve2, GPIO.OUT)
GPIO.setup(valve2Gnd, GPIO.OUT)
GPIO.setup(valve3En, GPIO.OUT)
GPIO.setup(valve3, GPIO.OUT)
GPIO.setup(valve3Gnd, GPIO.OUT)
GPIO.setup(valve4En, GPIO.OUT)
GPIO.setup(valve4, GPIO.OUT)
GPIO.setup(valve4Gnd, GPIO.OUT)
GPIO.setup(bottomMEn, GPIO.OUT)
GPIO.setup(flow, GPIO.IN)
GPIO.setup(led, GPIO.OUT)

#flow sensor parameters/variables
rate_cnt = 0.0           #rate of counts (L/min)
tot_cnt = 0.0            #total counts (total liters)
minutes = 0.0            #total minutes  
constant = 0.007075   #pulses to liters constant
#0.001323                       #based on testing
tStart = 0.0           #initialize time
lastGPIO = 2          #last state 0 or 1 or other?
#------------------------------------------------------
GPIO.output(led, GPIO.HIGH)
GPIO.output(bottomMEn, GPIO.HIGH)

p=GPIO.PWM(bottomMEn,600) #configure for pwm
inFlow = True
tS = time.time()

#--------------------------------------------------------------------------------
def openValve(valveEn,valve,valveGND):
    GPIO.setmode(GPIO.BCM)
    
    GPIO.setup(valve, GPIO.OUT)
    GPIO.setup(valveGND, GPIO.OUT)
    GPIO.setup(valveEn, GPIO.OUT)


    GPIO.output(valveEn, GPIO.HIGH)
    GPIO.output(valve, GPIO.HIGH)
    GPIO.output(valveGND, GPIO.LOW)
#--------------------------------------------------------------------------------
#Close solenoid valves. Given valve enable pin, valve pin, and valve ground pin.
#valve is opened by enabling valve power pin to high and valve gnd pin to low.
#--------------------------------------------------------------------------------
def closeValve(valveEn,valve,valveGND):
    GPIO.setmode(GPIO.BCM)
    
    GPIO.setup(valve, GPIO.OUT)
    GPIO.setup(valveGND, GPIO.OUT)
    GPIO.setup(valveEn, GPIO.OUT)

    GPIO.output(valveEn, GPIO.HIGH)
    GPIO.output(valve, GPIO.LOW)
    GPIO.output(valveGND, GPIO.HIGH)
#--------------------------------------------------------------------------------
openValve(valve1En, valve1, valve1Gnd) #correct
closeValve(valve3En, valve3, valve3Gnd) #correct
openValve(valve4En, valve4, valve4Gnd) #backwards

closeValve(valve2En, valve2, valve2Gnd) #backwards

while (inFlow):
    time.sleep(0.25)
    tNow = time.time()
    elapsedTime = tNow - tS
    
    p.start(bottomDudy) #dudycycle
    #time.sleep(3)
    p.ChangeDutyCycle(100)
    current = GPIO.input(flow)

    if current != lastGPIO:
        rate_cnt += 1
        tot_cnt += 1
    else:
        rate_cnt = rate_cnt
        tot_cnt = tot_cnt
    lastGPIO = current
    lPerMin = (rate_cnt * constant)
    totalL = (tot_cnt * constant)
        
    print('[%.3f] - Total liters %f' % (elapsedTime,totalL))
    print('[%.3f] - Liters/min %f'% (elapsedTime,lPerMin))
    
    if (elapsedTime > bottomTime):
        inFlow = False
    
p.stop()
GPIO.cleanup()
