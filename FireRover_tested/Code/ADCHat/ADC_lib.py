from smbus2 import SMBus
import logging
from time import sleep

logger = logging.getLogger(__name__)
#logger.basicConfig(filename="ADC_Lib.log", filemode="w", level=logger.DEBUG)



"""
---------------------------------------------------------------------
INA219 CONFIG CONSTANTS
---------------------------------------------------------------------
"""
class BusVoltageRange:
    """Constants for ``bus_voltage_range``"""

    RANGE_16V = 0x00  # set bus voltage range to 16V
    RANGE_32V = 0x01  # set bus voltage range to 32V  (DEFAULT)


class Gain:
    """Constants for ``gain``"""

    DIV_1_40MV  = 0x00  # shunt prog. gain set to  1, 40 mV range
    DIV_2_80MV  = 0x01  # shunt prog. gain set to /2, 80 mV range
    DIV_4_160MV = 0x02  # shunt prog. gain set to /4, 160 mV range
    DIV_8_320MV = 0x03  # shunt prog. gain set to /8, 320 mV range (DEFAULT)


class ADCResolution:
    """Constants for ``bus_adc_resolution`` or ``shunt_adc_resolution``"""

    ADCRES_9BIT_1S      = 0x00  #  9bit,   1 sample,     84us
    ADCRES_10BIT_1S     = 0x01  # 10bit,   1 sample,    148us
    ADCRES_11BIT_1S     = 0x02  # 11 bit,  1 sample,    276us
    ADCRES_12BIT_1S     = 0x03  # 12 bit,  1 sample,    532us   (DEFAULT)
    ADCRES_12BIT_2S     = 0x09  # 12 bit,  2 samples,  1.06ms
    ADCRES_12BIT_4S     = 0x0A  # 12 bit,  4 samples,  2.13ms
    ADCRES_12BIT_8S     = 0x0B  # 12bit,   8 samples,  4.26ms
    ADCRES_12BIT_16S    = 0x0C  # 12bit,  16 samples,  8.51ms
    ADCRES_12BIT_32S    = 0x0D  # 12bit,  32 samples, 17.02ms
    ADCRES_12BIT_64S    = 0x0E  # 12bit,  64 samples, 34.05ms
    ADCRES_12BIT_128S   = 0x0F  # 12bit, 128 samples, 68.10ms


class Mode:
    """Constants for ``mode``"""

    POWERDOWN               = 0x00  # power down
    SVOLT_TRIGGERED         = 0x01  # shunt voltage triggered
    BVOLT_TRIGGERED         = 0x02  # bus voltage triggered
    SANDBVOLT_TRIGGERED     = 0x03  # shunt and bus voltage triggered
    ADCOFF                  = 0x04  # ADC off
    SVOLT_CONTINUOUS        = 0x05  # shunt voltage continuous
    BVOLT_CONTINUOUS        = 0x06  # bus voltage continuous
    SANDBVOLT_CONTINUOUS    = 0x07  # shunt and bus voltage continuous (DEFAULT)

"""
---------------------------------------------------------------------
INA219 REGISTER CONSTANTS
---------------------------------------------------------------------
"""

class Reg():
    CONFIG          = 0x00
    SHUNT_VOLTAGE   = 0x01
    BUS_VOLTAGE     = 0x02
    POWER           = 0x03
    CURRENT         = 0x04
    CALIBRATION     = 0x05

"""
---------------------------------------------------------------------
INA219 POWER/CURRENT SENSOR
---------------------------------------------------------------------
"""

class INA219():
    """
    INA219 API Functions:
    """   

    def __init__(self, BUS:int=1,address:int=0x40):
        self.address = address
        self.bus = SMBus(BUS)
        sleep(1)

        """
        ---------------------------------------------------------------------
        INA219 Config Variables
        ---------------------------------------------------------------------
        """
        self.bus_voltage_range  = BusVoltageRange.RANGE_32V
        self.gain               = Gain.DIV_8_320MV
        self.badc_resolution    = ADCResolution.ADCRES_12BIT_1S
        self.sadc_resolution    = ADCResolution.ADCRES_12BIT_1S
        self.mode               = Mode.SANDBVOLT_CONTINUOUS



        logging.debug(f"INA219 instance established at address {hex(self.address)}, connected to RPI I2C bus {BUS}")

    def set_config(self,    bus_voltage_range = None,\
                            gain = None,\
                            badc_resolution = None, \
                            sadc_resolution = None, \
                            mode = None):
        
        """
        Updates the INA configuration with new values. If a value is not selected, the value will be unchanged
        """

        if bus_voltage_range == None:
            self.bus_voltage_range = self.bus_voltage_range
        else:   
            self.bus_voltage_range = bus_voltage_range

        if gain == None:
            self.gain = self.gain
        else:   
            self.gain = gain
        
        if badc_resolution == None:
            self.badc_resolution = self.badc_resolution
        else:   
            self.badc_resolution = badc_resolution

        if sadc_resolution == None:
            self.sadc_resolution = self.sadc_resolution
        else:   
            self.sadc_resolution = sadc_resolution

        if mode == None:
            self.mode = self.mode
        else:   
            self.mode = mode

        self.w_conf()

    def r_conf(self):
        """
        Read and return the config data from the INA219
        """
        return self.read_word(Reg.CONFIG)

    def w_conf(self):
        """
        Convert INA219 config data to a 16bit word and write the data to the sensor
        """

        config_word=(self.bus_voltage_range << 13) + \
                    (self.gain              << 11) + \
                    (self.badc_resolution   << 7) + \
                    (self.sadc_resolution   << 3) + \
                    (self.mode              << 0) + \
        self.write_word(Reg.CONFIG, config_word)
        #log.debug(f"writing {conf} to  config register")

    def reset(self):
        """
        Write a logical '1' to the INA219 reset pin. 
        """

        #Set the internal config variables to DEFAULT values
        self.bus_voltage_range  = BusVoltageRange.RANGE_32V
        self.gain               = Gain.DIV_8_320MV
        self.badc_resolution     = ADCResolution.ADCRES_12BIT_1S
        self.sadc_resolution     = ADCResolution.ADCRES_12BIT_1S
        self.mode               = Mode.SANDBVOLT_CONTINUOUS

        #Set the RESET bit in INA219
        self.write_word(Reg.CONFIG, 0xFFFF)

    def r_shunt_voltage(self):
        """
        Measure voltage between Vin+ and Vin-. The voltage is measured over the shunt voltage.
        Used to calculate current. Can be used to calculate Vin by adding the shunt voltage to the bus voltage.
        """
        return self.read_word(self.address, Reg.SHUNT_VOLTAGE) 

    def r_voltage(self):
        """
        Measure voltage between Vin- and GND. 
        Voltage is calculated by shifting the measured value by 3 bits to filter out the status
        indicators.

        Multiply raw value by the LSBvalue of 4mV
        """
        raw_bus_voltage = self.read_word(Reg.BUS_VOLTAGE)
        voltage = (raw_bus_voltage >> 3) * 0.004
        return round(voltage, 3)

    def r_power(self):
        """
        Calculate power in watts with power_raw*20*current_LSB
        """

        power_raw = self.read_word(Reg.POWER)
        return power_raw

    def r_current(self):
        """
        Calculate current in amps with current_raw * current_LSB
        """

        current_raw =  self.read_word(Reg.CURRENT)
        return current_raw

    def r_cal(self):
        """
        Read Sensor calibration value from INA219
        """

        return self.read_word(Reg.CALIBRATION)

    def w_cal(self, cal_data):
        """
        Write calibration value to INA219
        """

        return self.write_word(Reg.CALIBRATION, cal_data)

    def write_word(self, reg:int, data:int):
        """
        Uses the SMBus library to write 16-bits to the INA219. Shuffels the order of the bytes 
        being writtent to make it compatible with a INT input
        """

        data_string = "{:016b}".format(data)
        MSByte = data_string[8:16]
        LSByte = data_string[0:8]
        data = int(MSByte+LSByte, 2)
        self.bus.write_word_data(self.address, reg, data)

    def read_word(self, reg) -> int:
        """
        Uses the SMBus library to read 16-bits from the INA219. Shuffels the order of the bytes 
        being read and reurn the values as a MSB - LSB format.
        """

        raw = self.bus.read_word_data(self.address, reg)
        data_string = "{:016b}".format(raw)
        MSByte = data_string[8:16]
        LSByte = data_string[0:8]

        data = MSByte + LSByte
        return(int(data, 2))

class ADC_Hat():
    """
    Uses the SMBus library to read 16-bits from the INA219. Shuffels the order of the bytes 
    being read and returns the values as a MSB - LSB format.
    """

    def __init__(self):
        self.shunt_r = 0.1
        self.i_max = 0
        self.current_LSB = 0
        self.cal = 0


        self.Sensor0 = INA219(1, 0x40)
        self.Sensor1 = INA219(1, 0x41)
        self.Sensor2 = INA219(1, 0x42)
        self.Sensor3 = INA219(1, 0x43)

    def read_voltage_all(self):
        """
        Reads the voltage on all INA219 rails
        """
        v0 = round(self.Sensor0.r_voltage(), 2)
        v1 = round(self.Sensor1.r_voltage(), 2)
        v2 = round(self.Sensor2.r_voltage(), 2)
        v3 = round(self.Sensor3.r_voltage(), 2)

        return(v0, v1, v2, v3)
    
    def read_current_all(self):
        """
        Reads the current on all INA219 rails

        Current in Amps is given by:
        current = measured_value * current_LSB
        """

        i0 = round(self.Sensor0.r_current() * self.current_LSB*self.current_LSB, 2)
        i1 = round(self.Sensor1.r_current() * self.current_LSB*self.current_LSB, 2)
        i2 = round(self.Sensor2.r_current() * self.current_LSB*self.current_LSB, 2)
        i3 = round(self.Sensor3.r_current() * self.current_LSB*self.current_LSB, 2)
        return(i0, i1, i2, i3)

    def read_power_all(self):
        """
        Reads the power on all INA219 rails

        Power in Watts is given by:
        power = measured_value * current_LSB * 20
        """

        p0 = round(self.Sensor0.r_power() * self.current_LSB * 20, 2)
        p1 = round(self.Sensor1.r_power() * self.current_LSB * 20, 2)
        p2 = round(self.Sensor2.r_power() * self.current_LSB * 20, 2)
        p3 = round(self.Sensor3.r_power() * self.current_LSB * 20, 2)
        return(p0, p1, p2, p3)
    
    def read_shunt_voltage_all(self):
        """
        Reads the shunt voltage on all INA219 rails
        """

        vs0 = round(self.Sensor0.r_shunt_voltage(), 2)
        vs1 = round(self.Sensor1.r_shunt_voltage(), 2)
        vs2 = round(self.Sensor2.r_shunt_voltage(), 2)
        vs3 = round(self.Sensor3.r_shunt_voltage(), 2)

    def calibrate_all(self, i_max=3.2):
        """
        Calibrate all sensors with the given max current value.

        Current_LSB is the resolution of the measured current. It is calculated with the equation:
        current_LSB = Max_current/2**15

        Calibration value is ised by the INA219 to calculate the measured currentn and power.
        it is calculated with the equation 
        calibration_value = 0.04096 / (current_LSB * shunt_resistor)

        Shunt resistor is decided with hardware and is hardcoded to be equal to 0.1R
        """


        self.current_LSB = int(i_max / 2**15)
        if self.current_LSB == 0:
            self.cal = 0
        else:
            self.cal = int(0.04096/(self.current_LSB * self.shunt_r))

        self.Sensor0.w_cal(self.cal)
        self.Sensor1.w_cal(self.cal)
        self.Sensor2.w_cal(self.cal)
        self.Sensor3.w_cal(self.cal)

    def read_voltage(self, channel):
        """
        Returns the voltage on the selected channel.
        """

        if channel == 0:
            return round(self.Sensor0.r_voltage(), 2)
        
        elif channel == 1:
            return round(self.Sensor1.r_voltage(), 2)

        elif channel == 2:
            return round(self.Sensor2.r_voltage(), 2)

        elif channel == 3:
            return round(self.Sensor3.r_voltage(), 2)
        
        else:
            return 0
    
    def battery_gauge(self, channel):
        """
        Calculates battery capacity based on the equation
        
        battery_charge = 123 - 123 / (( 1 + (battery_voltage/3.7)**80)**0.165)
        """

        battery_voltage = self.read_voltage(channel)
        charge = 123 - 123 / (( 1 + ((battery_voltage/3)/3.7)**80)**0.165)
        if charge > 100:
            charge = 100

        elif charge < 0:
            charge = 0

        return round(charge, 1)

    def calibrate_sensor(self):
        self.Sensor0.w_cal(self.cal)
        self.Sensor1.w_cal(self.cal)
        self.Sensor2.w_cal(self.cal)
        self.Sensor3.w_cal(self.cal)

if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)
    logging.debug(f"{__name__}: Debug Mode")

    Sensor = INA219(address=0x40)
    Sensor.reset()
    conf = Sensor.r_conf()
    ADC = ADC_Hat()
    ADC.calibrate_all()

    print("Conf: {:n} \t {:04X} \t {:016b}".format(conf, conf, conf))

    while True:
        print("-"*10)
        v = ADC.read_voltage_all()
        i = ADC.read_current_all()
        p = ADC.read_power_all()
        c = ADC.battery_gauge(0)
        #print(f"Voltage: {v}V, I = {i}A, P={p}")

        print(c)
        sleep(1)
