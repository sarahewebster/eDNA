#!/usr/bin/env python3
import time
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
#top 
#GPIO.setup(26, GPIO.OUT)

#bottom
GPIO.setup(13, GPIO.OUT) #enable 

#GPIO.output(12, GPIO.HIGH)

#START
bottom=GPIO.PWM(13,800) #configure for pwm
bottom.start(100)

#time.sleep(10)
#bottom.ChangeDutyCycle(100)
#bottom.ChangeFrequency(1200)
#STOP
time.sleep(60)
bottom.stop()

#time.sleep(3)
GPIO.cleanup()

'''valve1 = 6
valve2 = 5
valve3 = 16
valve4 =12

GPIO.setup(valve1, GPIO.OUT)
GPIO.setup(valve2, GPIO.OUT)
GPIO.setup(valve3, GPIO.OUT)
GPIO.setup(valve4, GPIO.OUT)

GPIO.output(valve2, 1)
#time.sleep(5)
#GPIO.output(valve2, 1)'''