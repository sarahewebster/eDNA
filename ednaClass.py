#!/usr/bin/python

# @author: Viviana Castillo, APL UW
####################################################################

####################################################################
#standard imports
from utils import *
import RPi.GPIO as GPIO
import logging

#-------------------------------------------------------------------

class ednaClass :
    ##############################################################################################
    #constructor for class ednaStuff
    #
    #arguments are:
    #   
    #   
    #   
    ##############################################################################################
    def __init__(self,config,eventLog,dataFile):
        
        self.flowSensor = config.getInt('Track', 'Flow')
        self.waterPump = config.getInt('Track', 'WaterPump')
        self.soluPump = config.getInt('Track', 'SoluPump')
        self.rateCnt = config.getFloat('FlowSensor', 'RateCnt')
        self.totalCnt = config.getFloat('FlowSensor', 'TotCnt')
        self.timeStart = config.getFloat('FlowSensor', 'TimeStart')
        self.constant = config.getFloat('FlowSensor', 'Constant')
        self.lastGpio = config.getInt('FlowSensor', 'LastGpio')
        self.targetWLiters = config.getFloat('FlowSensor', 'TargetWaterLiters')
        self.targetSLiters = config.getFloat('FlowSensor', 'TargetSoluLiters')
        self.pumpWTime = config.getFloat('FlowSensor', 'PumpWTime')
        self.pumpSTime = config.getFloat('FlowSensor', 'PumpSTime')
        self.eventLog = eventLog
        self.dataFile = dataFile
        
    def run(self,elapsedTime,valve1,valve2):
        GPIO.output(valve1, GPIO.HIGH)
        print ("GPIO HIGH (on), valve one should be flipped open")
        self.eventLog.info("[%.3f] - Flipping valve open. Valve GPIO: %d" % (elapsedTime,valve1))
        
        GPIO.output(self.waterPump, GPIO.HIGH)
        print ("GPIO HIGH (on), water pump should be on")
        self.eventLog.info("[%.3f] - Turning water pump on" % (elapsedTime))
        
        totalWaterL = recordFlow(self.flowSensor,
                         self.rateCnt,
                         self.totalCnt,
                         self.timeStart,
                         self.constant,
                         self.lastGpio,
                         self.targetWLiters,
                         self.eventLog,
                         self.dataFile,
                         elapsedTime,
                         self.pumpWTime)
        
        if totalWaterL == None:
            self.eventLog.info("[%.3f] - No water flow detected, flipping valve/motor off" % (elapsedTime))
            
            totalWaterL = self.targetWLiters
            self.eventLog.info("[%.3f] - Faking successfull water intake to intake ethanol. totalWaterL:%f," % (elapsedTime,totalWaterL))
             
        
        if totalWaterL >= self.targetWLiters:
            print ("TARGET LITERS OF WATER REACHED")
            self.eventLog.info("[%.3f] - Target Liters of water reached: %f" % (elapsedTime,totalWaterL))
            
            GPIO.output(valve1, GPIO.LOW)
            print ("Flip valve closed")
            self.eventLog.info("[%.3f] - Flipping valve closed. Valve GPIO: %d" % (elapsedTime,valve1))
            
            GPIO.output(self.waterPump, GPIO.LOW)
            print ("GPIO HIGH (off), water pump should be off")
            self.eventLog.info("[%.3f] - Turning water pump off" % (elapsedTime))
            
            GPIO.output(valve2, GPIO.HIGH)
            print ("GPIO HIGH (on), valve two should be flipped open")
            self.eventLog.info("[%.3f] - Flipping valve open. Valve GPIO: %d" % (elapsedTime,valve2))
            
            GPIO.output(self.soluPump, GPIO.HIGH)
            print ("GPIO HIGH (on), solution pump should be on")
            self.eventLog.info("[%.3f] - Turning solution pump on" % (elapsedTime))

            
            totalSoluL = recordFlow(self.flowSensor,
                         self.rateCnt,
                         self.totalCnt,
                         self.timeStart,
                         self.constant,
                         self.lastGpio,
                         self.targetSLiters,
                         self.eventLog,
                         self.dataFile,
                         elapsedTime,
                         self.pumpSTime)
            if totalSoluL == None:
                self.eventLog.info("[%.3f] - No ethanol flow detected, flipping valve/motor off" % (elapsedTime))
                totalSoluL = self.targetSLiters
                self.eventLog.info("[%.3f] - Faking successfull solution intake to close all valves/motors. totalWaterL:%f," % (elapsedTime,totalSoluL))
               
            if totalSoluL >= self.targetSLiters:
                print ("TARGET LITERS OF SOLUTION REACHED")
                self.eventLog.info("[%.3f] - Target Liters of solution reached: %f" % (elapsedTime,totalSoluL))
                
                GPIO.output(valve2, GPIO.LOW)
                print ("Flip valve two closed")
                self.eventLog.info("[%.3f] - Flipping valve closed. Valve GPIO: %d" % (elapsedTime,valve2))
                
                GPIO.output(self.soluPump, GPIO.LOW)
                print ("GPIO LOW (off), solution pump should be off")
                self.eventLog.info("[%.3f] - Turning solution pump off" % (elapsedTime))
                
            return (totalWaterL, totalSoluL)
    
 