#!/usr/bin/python

# @author: Viviana Castillo, APL UW
##############################################################################################
#This class runs all appropriate hardware to collect one full sample of eDNA plus ethanol
#Appropriate valves are opened, motors are ran and then valves close. 
#If harware runs into problems, sample will be lost after a specific duration identified in 
#testing. If time elapses, ethanol is still added to sample. 
##############################################################################################
#standard imports
from utils import *
import RPi.GPIO as GPIO
import logging
import threading

#-------------------------------------------------------------------
class ednaClass :
    ##############################################################################################
    #constructor for class ednaClass 
    #
    #arguments are found in the Config.dat file:
    #    flowSensor - GPIO location
    #    waterPump - GPIO location
    #    soluPump - GPIO location (ethanol)
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
    def __init__(self,config,eventLog,dataFile,sensor):
        
        self.flowSensor = config.getInt('Track', 'Flow')
        self.waterPump = config.getInt('Track', 'WaterPump')
        self.soluPump = config.getInt('Track', 'SoluPump')
        self.rateCnt = config.getFloat('FlowSensor', 'RateCnt')
        self.totalCnt = config.getFloat('FlowSensor', 'TotCnt')
        self.timeStart = config.getFloat('FlowSensor', 'TimeStart')
        self.constant = config.getFloat('FlowSensor', 'Constant')
        self.lastGpio = config.getInt('FlowSensor', 'LastGpio')
        self.tWLiters = config.getFloat('FlowSensor', 'TargetWaterLiters')
        self.tSLiters = config.getFloat('FlowSensor', 'TargetSoluLiters')
        self.pumpWTime = config.getFloat('FlowSensor', 'PumpWTime')
        self.pumpSTime = config.getFloat('FlowSensor', 'PumpSTime')
        self.eventLog = eventLog
        self.dataFile = dataFile
        self.sensor = sensor
        
    def run(self,elapsedTime,valve1,valve2):
        GPIO.output(valve1, GPIO.HIGH)
        print ("[%.3f] - Flipping valve open, Valve GPIO: %d" % (elapsedTime,valve1))
        self.eventLog.info("[%.3f] - Flipping valve open. Valve GPIO: %d" % (elapsedTime,valve1))
        
        GPIO.output(self.waterPump, GPIO.HIGH)
        print ("[%.3f] - Turning water pump on. Water pump GPIO: %d" % (elapsedTime,self.waterPump))
        self.eventLog.info("[%.3f] - Turning water pump on. Water pump GPIO: %d" % (elapsedTime,self.waterPump))
        
        (totalWaterL,elapsedTime) = recordFlow(self.flowSensor,
                                self.rateCnt,
                                self.totalCnt,
                                self.timeStart,
                                self.constant,
                                self.lastGpio,
                                self.tWLiters,
                                self.eventLog,
                                self.dataFile,
                                elapsedTime,
                                self.pumpWTime,
                                self.sensor)
        elapsedTime = elapsedTime
        if totalWaterL == None:
            self.eventLog.info("[%.3f] - No water flow detected, flipping valve/motor off" % (elapsedTime))
            print ("[%.3f] - ERROR: Solution lost. Faking successfull intake in order to add ethanol and try to salvage sample")
            totalWaterL = self.tWLiters
            self.eventLog.info("[%.3f] - ERROR: Solution lost. Faking successfull water intake to intake ethanol. totalWaterL: %f," % (elapsedTime,totalWaterL))
             
        
        if totalWaterL >= self.tWLiters:
            print ("[%.3f] - Prepping for ethanol" % elapsedTime)
            self.eventLog.info("[%.3f] - Prepping for ethanol" % elapsedTime)
            
            GPIO.output(valve1, GPIO.LOW)
            print ("[%.3f] - Flipping valve closed. Valve GPIO: %d" % (elapsedTime, valve1))
            self.eventLog.info("[%.3f] - Flipping valve closed. Valve GPIO: %d" % (elapsedTime,valve1))
            
            GPIO.output(self.waterPump, GPIO.LOW)
            print ("[%.3f] - Turning water pump off. Water pump GPIO: %d" % (elapsedTime,self.waterPump))
            self.eventLog.info("[%.3f] - Turning water pump off. Water pump GPIO: %d" % (elapsedTime,self.waterPump))
            
            GPIO.output(valve2, GPIO.HIGH)
            print ("[%.3f] - Flipping valve open. Valve GPIO: %d" % (elapsedTime,valve2))
            self.eventLog.info("[%.3f] - Flipping valve open. Valve GPIO: %d" % (elapsedTime,valve2))
            
            GPIO.output(self.soluPump, GPIO.HIGH)
            print ("[%.3f] - Turning solution pump on. Solution pump GPIO: %d" % (elapsedTime, self.soluPump))
            self.eventLog.info("[%.3f] - Turning solution pump on. Solution pump GPIO: %d" % (elapsedTime, self.soluPump))

            
            (totalSoluL,elapsedTime) = recordFlow(self.flowSensor,
                         self.rateCnt,
                         self.totalCnt,
                         self.timeStart,
                         self.constant,
                         self.lastGpio,
                         self.tSLiters,
                         self.eventLog,
                         self.dataFile,
                         elapsedTime,
                         self.pumpSTime,
                         self.sensor)
            
            if totalSoluL == None:
                print ("[%.3f] - ERROR: No ethanol flow detected" % (elapsedTime))
                self.eventLog.info("[%.3f] - ERROR: No ethanol flow detected" % (elapsedTime))
                totalSoluL = self.tSLiters
                self.eventLog.info("[%.3f] - Faking successfull solution intake to close all valves/motors. totalWaterL:%f," % (elapsedTime,totalSoluL))
               
            if totalSoluL >= self.tSLiters:
                print ("[%.3f] - Prepping for system shutdown" % (elapsedTime))
                self.eventLog.info("[%.3f] - Prepping for system shutdown" % (elapsedTime))
                
                GPIO.output(valve2, GPIO.LOW)
                print ("[%.3f] - Flipping valve closed. Valve GPIO: %d" % (elapsedTime,valve2))
                self.eventLog.info("[%.3f] - Flipping valve closed. Valve GPIO: %d" % (elapsedTime,valve2))
                
                GPIO.output(self.soluPump, GPIO.LOW)
                print ("[%.3f] - Turning solution pump off. Solution pump GPIO: %d" % (elapsedTime, self.soluPump))
                self.eventLog.info("[%.3f] - Turning solution pump off, Solution pump GPIO: %d" % (elapsedTime, self.soluPump))
                
    