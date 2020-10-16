#!/user/bin/python
#Kevin Zack
#BB-2590/U Battery read code using two busses on a RasPi
#For RasPi4 added line dtparam=i2c_vc=0n in /boot/config.txt
#BUS1 Pin3,5
#BUS0 Pin27,28
#WARNING: this will not allow camera or EPROM to be used

import smbus
import time
#bus0= smbus.SMBus(0)
bus1= smbus.SMBus(1)

DEVICE_ADDRESS = 0x0b

BatteryReg = 0x2f #propriatary SMBUS reg not sure whats its for

VOLTAGE= 0x00
CURRENT = 0x0A
SOC = 0x0e

###############GET VOLTAGE ###############
#bus.write_byte(DEVICE_ADDRESS, VOLTAGE)
#voltage0 = bus0.read_i2c_block_data(DEVICE_ADDRESS,VOLTAGE,2)
#voltage0 = (voltage0[1]*256+voltage0[0])/1000 #change from mV to Voltage
while True:
    voltage1 = bus1.read_i2c_block_data(DEVICE_ADDRESS,VOLTAGE,2)
    #print (voltage1)
    #voltage1 = (voltage1[1]*256+voltage1[0])/1000 #change from mV to Voltage

    print("Voltage (V) is {" , voltage1 , "}")
    time.sleep(.5)

###############GET CURRENT ###############

'''#bus0.write_byte(DEVICE_ADDRESS, CURRENT)
current0 = bus0.read_i2c_block_data(DEVICE_ADDRESS,CURRENT,2)

current0= (current0[1]*256+current0[0]) 
if(current0 & 0x8000): #figure out if charge or discharge and place signs
    current0 = -0x10000 + current0

current1 = bus1.read_i2c_block_data(DEVICE_ADDRESS,CURRENT,2)

current1= (current1[1]*256+current1[0]) 
if(current1 & 0x8000): #figure out if charge or discharge and place signs
    current1 = -0x10000 + current1
    
print("Current (mA) is {", current0 , "," , current1 , "}")

###############GET CAPACITY ###############
charge0 = bus0.read_i2c_block_data(DEVICE_ADDRESS,SOC,2)
charge0= (charge0[1]*256+charge0[0])

charge1 = bus1.read_i2c_block_data(DEVICE_ADDRESS,SOC,2)
charge1= (charge1[1]*256+charge1[0])

print("Charge is (%) is {" , charge0 , "," , charge1 , "}")'''
