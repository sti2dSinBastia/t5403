import smbus
import time


"""
Class for T5403 - Barometric Sensor Breakout (SparkFun)
Website : https://www.sparkfun.com/products/retired/12039
Datasheet : https://cdn.sparkfun.com/datasheets/Sensors/Weather/T5400.pdf
Application note : https://en.tdk.eu/download/531174/a6c0bd6a9bbc43ad1439cf9ff6e7b1c1/t5403-applicationnote.pdf
"""

#Addresses
T5403_I2C_ADDR = 0x77
T5403_DATA_REG = 0xF5
T5403_COMMAND_REG = 0xF1
#Calibration registers addresses
T5403_C1 = 0x8E
T5403_C2 = 0x90
T5403_C3 = 0x92
T5403_C4 = 0x94
T5403_C5 = 0x96
T5403_C6 = 0x98
T5403_C7 = 0x9A
T5403_C8 = 0x9C
T5403_C9 = 0x9E
T5403_C10 = 0xA0
#definitions for pressure reading commands with accuracy modes
MODE_LOW = 0x00
MODE_STANDARD = 0x01
MODE_HIGH = 0x10
MODE_ULTRA = 0x11
COMMAND_GET_TEMP = 0x03


class T5403(object):
    
    def __init__(self):
        """Read calibration registers"""
        self.c1 = self.getUnsignedData(T5403_C1) #uint
        self.c2 = self.getUnsignedData(T5403_C2)
        self.c3 = self.getUnsignedData(T5403_C3)
        self.c4 = self.getUnsignedData(T5403_C4)
        self.c5 = self.getSignedData(T5403_C5) #int
        self.c6 = self.getSignedData(T5403_C6)
        self.c7 = self.getSignedData(T5403_C7)
        self.c8 = self.getSignedData(T5403_C8)
        self.c9 = self.getSignedData(T5403_C9)
        self.c10 = self.getSignedData(T5403_C10)
        
        
    def getUnsignedData(self, location):
        """Read 2 bytes lsb first, return unsigned int"""
        bus = smbus.SMBus(1)
        datas = bus.read_i2c_block_data(T5403_I2C_ADDR, location, 2)
        bus.close()
        return (datas[1] << 8) + datas[0]


    def getSignedData(self, location):
        """Read 2 bytes lsb first, return signed int"""
        bus = smbus.SMBus(1)
        datas = bus.read_i2c_block_data(T5403_I2C_ADDR, location, 2)
        bus.close()
        data = (datas[1] << 8) + datas[0]
        if data > 32767:
            return (65536 - data) * (-1)
        else:
            return data


    def sendCommand(self, location, command):
        """Write command byte in location"""
        bus = smbus.SMBus(1)
        bus.write_i2c_block_data(T5403_I2C_ADDR, location, [command])
        bus.close()
        

    def getRawTemp(self):
        """Read raw temperature from sensor"""
        self.sendCommand(T5403_COMMAND_REG, COMMAND_GET_TEMP)
        time.sleep(0.005)
        tr = self.getSignedData(T5403_DATA_REG)
        temp = ((((self.c1 * tr) >> 8) + (self.c2 << 6)) * 100) >> 16
        return temp


    def getTemperature(self):
        """Return temperature in Celsius"""
        temp = self.getRawTemp()
        return temp / 100.0


    def getPressure(self, mesurement_mode=MODE_STANDARD):
        """Return pressure in hPa"""
        tr = self.getRawTemp()
        
        self.sendCommand(T5403_COMMAND_REG, mesurement_mode)
        if mesurement_mode is MODE_LOW:
            time.sleep(0.005)
        elif mesurement_mode is MODE_STANDARD:
            time.sleep(0.02)
        elif mesurement_mode is MODE_HIGH:
            time.sleep(0.019)
        elif mesurement_mode is MODE_ULTRA:
            time.sleep(0.067)

        pressure_raw = self.getUnsignedData(T5403_DATA_REG)
        """
        s_old = ((((self.c5 * tr) >> 15) * tr) >> 19) + self.c3 + ((self.c4 * tr) >> 17)
        o_old = ((((self.c8 * tr) >> 15) * tr) >> 4) + ((self.c7 * tr) >> 3) + (self.c6 * 0x4000)
        pa_old = (s_old * pressure_raw + o_old) >> 14
        """
        s = self.c3 + (self.c4 * tr / 2**17) + (self.c5 * tr / 2**15 * tr) / 2**19 + (((self.c9 * tr / 2**15 * tr)/2**15) * tr) / 2**16
        o = self.c6 * 2**14 + self.c7 * tr / 2**3 + (self.c8 * tr / 2**15 * tr) / 2**4 + ((self.c9 * tr / 2**15 * tr) / 2**16) * tr
        x = (s * pressure_raw + o) / 2**14

        pa = x + ((x-75000)**2/2**16 - 9537) * self.c10 / 2**16
        pa = round(pa / 100.0, 2)
        return pa


if __name__ == '__main__':
    sensor = T5403()
    print('Temp:', sensor.getTemperature(), '°C')
    print('Press:', sensor.getPressure(MODE_STANDARD), 'hPa')


