"""
Original utility functions
"""
import RPi.GPIO as GPIO


####################### LED METHODS ###########################
#-----------------------------------------------------------------
# Set led blink pattern with PWM by changing the dudy cycle
#-----------------------------------------------------------------
def ledBlink(ledGPIO, dudyCycle, led):
    led.start(0)
    led.ChangeDutyCycle(dudyCycle)
    time.sleep(1)

#----------------------------------------------------------------------------------------
# give sample status after all samples have been collected indicating if
# the sample was successfully collected or not
#----------------------------------------------------------------------------------------
def sampleStatusRep(successStatusdc, unsuccessStatusdc, numBlinks, entireSample, ledGPIO):
    GPIO.setup(ledGPIO, GPIO.OUT)
    led = GPIO.PWM(ledGPIO,1)
    count = 0
    if entireSample:
        while (count < numBlinks):
            ledBlink(ledGPIO,successStatusdc,led)
            count += 1
        led.stop()
    else:
        while count < numBlinks:
            ledBlink(ledGPIO, unsuccessStatusdc, led)
            count += 1
        led.stop()

#----------------------------------------------------------------------------------------
# one, two or three quick set of blinks, 3 times depending on the number of the sample
# just finished adding ethanol, successfull or not.
#----------------------------------------------------------------------------------------
def getEthanolDone(ledGPIO, sampleNum):
    GPIO.setup(ledGPIO, GPIO.OUT)

    for sets in range(3):
        for blinks in range(sampleNum):
            GPIO.output(ledGPIO, GPIO.HIGH)
            time.sleep(.25)
            GPIO.output(ledGPIO, GPIO.LOW)
            time.sleep(.25)
        time.sleep(1)

#----------------------------------------------------------------------------------------
# one long blink then 1,2 or 3 quick blinks indicating the number of sample that
# just finished, successfull or not.
#----------------------------------------------------------------------------------------
def getSampleDone(ledGPIO, sampleNum):
    GPIO.setup(ledGPIO, GPIO.OUT)

    for sets in range(1):
        GPIO.output(ledGPIO, GPIO.HIGH)
        time.sleep(1)
        for blinks in range(sampleNum+1):
            GPIO.output(ledGPIO, GPIO.HIGH)
            time.sleep(0.25)
            GPIO.output(ledGPIO, GPIO.LOW)

#----------------------------------------------------------------------------------------
#Blink LED patters when program has begin running as well as when samples are
#done being collected (all 3 samples are collected)
#----------------------------------------------------------------------------------------
def startEndLed(ledStartNumBlinks, ledGPIO, ledStartdc, led):
    count = 0
    while count < ledStartNumBlinks:
        ledBlink(ledGPIO, ledStartdc, led)
        count += 1
    led.stop()
