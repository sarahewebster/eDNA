#!/usr/bin/python3

# @author: Viviana Castillo, APL UW
##############################################################################################
#This class runs all appropriate hardware to collect one full sample of eDNA plus ethanol
#Appropriate valves are opened, motors are ran and then valves close.
#If harware runs into problems, sample will be lost after a specific duration identified in
#testing. If time elapses, ethanol is still added to sample.
##############################################################################################
#standard imports
from . import utils
import RPi.GPIO as GPIO
import logging


GPIO.setwarnings(False) #no GPIO warning
GPIO.setmode(GPIO.BCM)  #pin number

#-------------------------------------------------------------------
class ednaClass :
    ##############################################################################################
    #constructor for class ednaClass
    #
    #arguments are found in the Config.dat file:
    #    flowSensor - GPIO location
    #    sampleMotor - GPIO location
    #    ethanolMotor - GPIO location (ethanol)
    #    rateCnt - rate at which water is flowing
    #    totalCnt - total water meas
    #    timeStart - initialize time to 0
    #    constant - calc constant for water flow
    #    lastGpio - initialize the Gpio state
    #    tWLiters - target amount of L for water
    #    tWLiters - target amount of L for solution (ethanol)
    #    pumpWTime - Total amout of time pumping water should take
    #    pumpSTime - Total amount of time pumping ethanol should take
    #    eventLog - Log to event log
    #    dataFile - Log to data file
    #
    ##############################################################################################
    def __init__(self,config,eventLog,dataFile,adc):

        self.flowSensor = config.getInt('FlowSensor', 'Flow')

        #Motor
        self.sampleMotor = config.getInt('Motor', 'SampleMotor')
        self.sampleMotorHz = config.getInt('Motor', 'SampleMotorHz')
        self.ethanolMotor = config.getInt('Motor', 'EthanolMotor')
        self.ethanolMotorHz = config.getInt('Motor', 'EthanolMotorHz')

        #flow
        self.tWLiters = config.getFloat('FlowSensor', 'TargetWaterLiters')
        self.tSLiters = config.getFloat('FlowSensor', 'TargetSoluLiters')
        self.pumpWTime = config.getFloat('FlowSensor', 'PumpWTime')
        self.pumpSTime = config.getFloat('FlowSensor', 'PumpSTime')
        self.recordRate = config.getFloat('FlowSensor', 'RecordRate')
        self.constant = config.getFloat('FlowSensor', 'Constant')
        self.rateCnt = config.getInt('FlowSensor', 'RateCnt')
        self.totalCnt = config.getInt('FlowSensor', 'TotCnt')
        self.startTime = config.getInt('FlowSensor', 'TimeStart')
        self.lastGPIO = config.getInt('FlowSensor', 'LastGPIO')

        #Valve (only to initialize)
        self.valve1En = config.getInt('Valves', 'Valve1En')
        self.valve1 = config.getInt('Valves', 'Valve1')
        self.valve1Gnd = config.getInt('Valves', 'Valve1Gnd')
        self.valve2En = config.getInt('Valves', 'Valve2En')
        self.valve2 = config.getInt('Valves', 'Valve2')
        self.valve2Gnd = config.getInt('Valves', 'Valve2Gnd')
        self.valve3En = config.getInt('Valves', 'Valve3En')
        self.valve3 = config.getInt('Valves', 'Valve3')
        self.valve3Gnd = config.getInt('Valves', 'Valve3Gnd')
        self.valve4En = config.getInt('Valves', 'Valve4En')
        self.valve4 = config.getInt('Valves', 'Valve4')
        self.valve4Gnd = config.getInt('Valves', 'Valve4Gnd')

        #pressure
        self.depthCh = config.getInt('PressureSensor', 'DepthCh')
        self.diffCh = config.getInt('PressureSensor', 'DiffCh')
        self.gain = config.getFloat('PressureSensor', 'gain')
        self.maxDiffPress = config.getFloat('PressureSensor', 'MaxDiffPress')
        self.adc = adc
        self.checkAvgSamples = config.getInt('PressureSensor', 'CheckAvgSamples')

        #system check
        self.checkAvgSampels = config.getInt('SystemCheck', 'CheckAvgSamples')
        self.devParam = config.getInt('SystemCheck', 'StDevParam')

        #logging
        self.eventLog = eventLog
        self.dataFile = dataFile

        self.ledGPIO = config.getInt('LED', 'ledGPIO')

    ##############################################################################################
    # begin collecting individual sample from a set of 3
    # flow is recorded and colected, then ethanol is ran through the system
    ##############################################################################################
    def run(self,
            elapsedTime,
            valveEn,
            valve,
            valveGnd,
            valveEthaEn,
            valveEtha,
            valveEthaGnd,
            sampleNum,
            tDepth,
            depthErr,
            bus0,
            bus1,
            battAddr,
            battCurrent):

        #GPIO was cleaned up, reinitialize again
        utils.initializeGPIO(self.ledGPIO,self.flowSensor,
                             self.sampleMotor,self.ethanolMotor,
                             self.valve1En,self.valve1,self.valve1Gnd,
                             self.valve2En,self.valve2,self.valve2Gnd,
                             self.valve3En,self.valve3,self.valve3Gnd,
                             self.valve4En,self.valve4,self.valve4Gnd)

        successfull = True

        sampleMotorP=GPIO.PWM(self.sampleMotor,self.sampleMotorHz)

        current0,current1 = utils.getCurrent(bus0,bus1,battAddr,battCurrent)
        print ("[%.3f] - Current0: %f, Current1: %f" % (elapsedTime,current0,current1))
        self.eventLog.info("[%.3f] - Current0 before flipping valve open: %f, Current1 before flipping valve open: %f" % (elapsedTime,current0,current1))

        utils.openValve(valveEn,valve,valveGnd)
        print ("[%.3f] - Flipping valve open, Valve GPIO: %d" % (elapsedTime,valve))
        self.eventLog.info("[%s] - Flipping valve open. Valve GPIO: %d" % (str(utils.currentTimeString()),valve))

        current0,current1 = utils.getCurrent(bus0,bus1,battAddr,battCurrent)
        print ("[%.3f] - Current0: %f, Current1: %f" % (elapsedTime,current0,current1))
        self.eventLog.info("[%.3f] - Current0 after flipping valve open: %f, Current1 after flipping valve open: %f" % (elapsedTime,current0,current1))

        sampleMotorP.start(100)

        print ("[%.3f] - Turning water pump on. Water pump GPIO: %d" % (elapsedTime,self.sampleMotor))
        self.eventLog.info("[%s] - Turning water pump on. Water pump GPIO: %d" % (str(utils.currentTimeString()),self.sampleMotor))

        #WATER PUMPING
        (totalWaterL,elapsedTime,pressure) = utils.recordFlow(self.flowSensor,self.maxDiffPress,self.tWLiters,
                                                              self.eventLog,self.dataFile,elapsedTime,
                                                              self.pumpWTime,self.recordRate,self.rateCnt,
                                                              self.totalCnt,self.startTime,self.constant,
                                                              self.lastGPIO,self.depthCh,self.diffCh,
                                                              self.gain,self.adc,self.checkAvgSamples,
                                                              self.devParam,tDepth,depthErr,
                                                              self.ledGPIO,bus0,bus1,
                                                              battAddr,battCurrent)

        print ("[%.3f] -  TOTAL WATER L: %f" % (elapsedTime, totalWaterL))

        utils.getSampleDone(self.ledGPIO, sampleNum) #LED

        elapsedTime = elapsedTime
        if (totalWaterL < self.tWLiters):
            sampleMotorP.stop()
            self.eventLog.info("[%s] - No water flow detected,flipping valve/motor off" % (str(utils.currentTimeString())))
            print ("[%.3f] - ERROR: Solution lost. Faking successfull intake in order to add ethanol and try to salvage sample" % elapsedTime)
            totalWaterL = self.tWLiters
            self.eventLog.info("[%s] - ERROR: Solution lost. Faking successfull water intake to intake ethanol. totalWaterL: %f," % (str(utils.currentTimeString()),totalWaterL))
            successfull = False

        if (pressure == False):
            self.eventLog.info("[%s] - Pressure too high" % (str(utils.currentTimeString())))
            print ("[%.3f] - ERROR: Solution lost. Water pressure too high" % elapsedTime)
            totalWaterL = self.tWLiters
            self.eventLog.info("[%s] - ERROR: Solution lost. Water pressure too high" % (str(utils.currentTimeString())))
            successfull = False

        if (totalWaterL >= self.tWLiters):
            print ("[%.3f] - Prepping for ethanol" % elapsedTime)
            self.eventLog.info("[%s] - Prepping for ethanol" % str(utils.currentTimeString()))


            current0,current1 = utils.getCurrent(bus0,bus1,battAddr,battCurrent)
            print ("[%.3f] - Current0: %f, Current1: %f" % (elapsedTime,current0,current1))
            self.eventLog.info("[%.3f] - Current0 before flipping valve closed: %f, Current1 before flipping valve closed: %f" % (elapsedTime,current0,current1))

            utils.closeValve(valveEn,valve,valveGnd)
            print ("[%.3f] - Flipping valve closed. Valve GPIO: %d" % (elapsedTime, valve))
            self.eventLog.info("[%s] - Flipping valve closed. Valve GPIO: %d" % (str(utils.currentTimeString()),valve))

            current0,current1 = utils.getCurrent(bus0,bus1,battAddr,battCurrent)
            print ("[%.3f] - Current0: %f, Current1: %f" % (elapsedTime,current0,current1))
            self.eventLog.info("[%.3f] - Current0 after flipping valve closed: %f, Current1 after flipping valve closed: %f" % (elapsedTime,current0,current1))

            sampleMotorP.stop()
            GPIO.cleanup()
            print ("[%.3f] - Turning water pump off. Water pump GPIO: %d" % (elapsedTime,self.sampleMotor))
            self.eventLog.info("[%s] - Turning water pump off. Water pump GPIO: %d" % (str(utils.currentTimeString()),self.sampleMotor))
            GPIO.setmode(GPIO.BCM)  #pin number

            #GPIO was cleaned up, reinitialize again
            utils.initializeGPIO(self.ledGPIO,self.flowSensor,
                                 self.sampleMotor,self.ethanolMotor,
                                 self.valve1En,self.valve1,self.valve1Gnd,
                                 self.valve2En,self.valve2,self.valve2Gnd,
                                 self.valve3En,self.valve3,self.valve3Gnd,
                                 self.valve4En,self.valve4,self.valve4Gnd)

            current0,current1 = utils.getCurrent(bus0,bus1,battAddr,battCurrent)
            print ("[%.3f] - Current0: %f, Current1: %f" % (elapsedTime,current0,current1))
            self.eventLog.info("[%.3f] - Current0 before flipping valve open: %f, Current1 before flipping valve open: %f" % (elapsedTime,current0,current1))

            utils.openValve(valveEthaEn,valveEtha,valveEthaGnd)
            print ("[%.3f] - Flipping valve open. Valve GPIO: %d" % (elapsedTime,valveEtha))
            self.eventLog.info("[%s] - Flipping valve open. Valve GPIO: %d" % (str(utils.currentTimeString()),valveEtha))

            current0,current1 = utils.getCurrent(bus0,bus1,battAddr,battCurrent)
            print ("[%.3f] - Current0: %f, Current1: %f" % (elapsedTime,current0,current1))
            self.eventLog.info("[%.3f] - Current0 after flipping valve open: %f, Current1 after flipping valve open: %f" % (elapsedTime,current0,current1))

            ethanolMotorP=GPIO.PWM(self.ethanolMotor,self.ethanolMotorHz)

            ethanolMotorP.start(100)
            print ("[%.3f] - Turning solution pump on. Solution pump GPIO: %d" % (elapsedTime, self.ethanolMotor))
            self.eventLog.info("[%s] - Turning solution pump on. Solution pump GPIO: %d" % (str(utils.currentTimeString()), self.ethanolMotor))

            #ETHANOL PUMPING
            (totalSoluL,elapsedTime,pressure) = utils.recordFlow(self.flowSensor,self.maxDiffPress,self.tSLiters,
                                                                 self.eventLog,self.dataFile,elapsedTime,
                                                                 self.pumpSTime,self.recordRate,self.rateCnt,
                                                                 self.totalCnt,self.startTime,self.constant,
                                                                 self.lastGPIO,self.depthCh,self.diffCh,
                                                                 self.gain,self.adc,self.checkAvgSamples,
                                                                 self.devParam,tDepth,depthErr,
                                                                 self.ledGPIO,bus0,bus1,
                                                                 battAddr,battCurrent)

            utils.getEthanolDone(self.ledGPIO, sampleNum) #LED

            if (totalSoluL < self.tSLiters):
                ethanolMotorP.stop()
                print ("[%.3f] - ERROR: No ethanol flow detected" % (elapsedTime))
                self.eventLog.info("[%s] - ERROR: No ethanol flow detected" % (str(utils.currentTimeString())))
                totalSoluL = self.tSLiters
                self.eventLog.info("[%s] - Faking successfull solution intake to close all valves/motors. totalWaterL:%f," % (str(utils.currentTimeString()),totalSoluL))
                successfull = False

            if (pressure == False):
                self.eventLog.info("[%s] - Pressure too high" % (str(utils.currentTimeString())))
                print ("[%.3f] - ERROR: Solution lost. Water pressure too high" % elapsedTime)
                totalWaterL = self.tWLiters
                self.eventLog.info("[%s] - ERROR: Solution lost. Water pressure too high" % (str(utils.currentTimeString())))
                successfull = False

            if (totalSoluL >= self.tSLiters):
                print ("[%.3f] - Prepping for system shutdown" % (elapsedTime))
                self.eventLog.info("[%s] - Prepping for system shutdown" % (str(utils.currentTimeString())))


                current0,current1 = utils.getCurrent(bus0,bus1,battAddr,battCurrent)
                print ("[%.3f] - Current0: %f, Current1: %f" % (elapsedTime,current0,current1))
                self.eventLog.info("[%.3f] - Current0 before flipping valve closed: %f, Current1 before flipping valve closed: %f" % (elapsedTime,current0,current1))

                utils.closeValve(valveEthaEn,valveEtha,valveEthaGnd)
                print ("[%.3f] - Flipping valve closed. Valve GPIO: %d" % (elapsedTime,valveEtha))
                self.eventLog.info("[%s] - Flipping valve closed. Valve GPIO: %d" % (str(utils.currentTimeString()),valveEtha))

                current0,current1 = utils.getCurrent(bus0,bus1,battAddr,battCurrent)
                print ("[%.3f] - Current0: %f, Current1: %f" % (elapsedTime,current0,current1))
                self.eventLog.info("[%.3f] - Current0 after flipping valve closed: %f, Current1 after flipping valve closed: %f" % (elapsedTime,current0,current1))

                ethanolMotorP.stop()
                GPIO.cleanup()
                print ("[%.3f] - Turning solution pump off. Solution pump GPIO: %d" % (elapsedTime, self.ethanolMotor))
                self.eventLog.info("[%s] - Turning solution pump off, Solution pump GPIO: %d" % (str(utils.currentTimeString()), self.ethanolMotor))

        return (successfull, elapsedTime)
