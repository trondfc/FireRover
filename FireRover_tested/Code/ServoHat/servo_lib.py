import smbus2
import time
import multiprocessing as mp
import logging

#logging = logging
#logger = logging.getLogger(__name__)
#logging.basicConfig(filename="servo_Lib.log", filemode="w", level=logging.DEBUG)

def map(x, in_min, in_max, out_min, out_max):
            mapped_value = (x - (in_min)) * (out_max - out_min) // (in_max - (in_min)) + out_min
            return mapped_value

class PCA9685:
    def __init__(self, address, BUS:int=1):
        """
        Initializes the PCA9685 at the specified I2C address.
        """
        self.address = address
        self.BUS = BUS
        self.bus = smbus2.SMBus(self.BUS)
        addr_hex = "{:02x}".format(self.address)
        logging.debug(f"PCA9685 instance established at address {self.address} / 0x{addr_hex}, connected to RPI I2C bus {self.BUS}")
        logging.debug(f"")
        time.sleep(0.5)

        self.reset()
        time.sleep(0.5)
        
        self.pwm_frequency = 50
        self.set_frequency(self.pwm_frequency)  # Set the PWM frequency to 100Hz
        self.set_all_pwm(0, 0)  # Initialize all PWM channels to off

    def write_byte(self, reg, value):
        """
        Writes a single byte to the specified register address.
        """
        self.bus.write_byte_data(self.address, reg, value)

    def read_byte(self, reg):
        """
        Reads a single byte from the specified register address.
        """
        return self.bus.read_byte_data(self.address, reg)

    def set_frequency(self, frequency):
        """
        Sets the PWM frequency to the specified value in Hz.
        """
        prescale_value = int(25000000 / (4096 * frequency)) - 1
        old_mode = self.bus.read_byte_data(self.address, 0x00)
        self.write_byte(0x00, (old_mode & 0x7F) | 0x10 )  # sleep
        self.write_byte(0xFE, prescale_value)
        self.write_byte(0x00, old_mode)
        time.sleep(0.005)
        #self.write_byte(0x00, old_mode | 0x80)  # restart
        self.pwm_frequency = frequency

    def set_pwm(self, channel, on_value, off_value, inv=False):
        """
        Sets the PWM value for the specified channel.
        """
        if not(inv):
            self.write_byte(0x06 + 4 * channel, on_value & 0xFF)
            self.write_byte(0x07 + 4 * channel, on_value >> 8)
            self.write_byte(0x08 + 4 * channel, off_value & 0xFF)
            self.write_byte(0x09 + 4 * channel, off_value >> 8)
        else:
            self.write_byte(0x06 + 4 * channel, off_value & 0xFF)
            self.write_byte(0x07 + 4 * channel, off_value >> 8)
            self.write_byte(0x08 + 4 * channel, on_value & 0xFF)
            self.write_byte(0x09 + 4 * channel, on_value >> 8) 

    def read_pwm_on(self, channel):
        ledn_on_l_reg = self.read_byte(0x06 + 4 * channel)
        ledn_on_h_reg = self.read_byte(0x07 + 4 * channel)
        on_value = ( ledn_on_h_reg << 8 ) + (ledn_on_l_reg)
        return on_value

    def read_pwm_off(self, channel):
        ledn_off_l_reg = self.read_byte(0x08 + 4 * channel)
        ledn_off_h_reg = self.read_byte(0x09 + 4 * channel)
        off_value = (ledn_off_h_reg << 8 ) + (ledn_off_l_reg)
        return off_value

    def reset(self):
        logging.debug(f"Resetting PCA9685")
        #Set the reset bit in register 0
        self.write_byte(0x00, 0x80)
        time.sleep(0.5)
        logging.debug("Reset Complete")           


    def set_all_pwm(self, on_value, off_value):
        """
        Sets the PWM value for all channels.
        """
        self.write_byte(0xFA, on_value & 0xFF)
        self.write_byte(0xFB, on_value >> 8)
        self.write_byte(0xFC, off_value & 0xFF)
        self.write_byte(0xFD, off_value >> 8)


class Servo:
    def __init__(self, pca9685, channel, inv=False, min_pulse_us=1000, max_pulse_us=2000, min_angle=0, max_angle=180):
        """
        Initializes a servo connected to the specified PCA9685 channel.
        """
        

        self.pca9685 = pca9685
        self.channel = channel
        self.inv = inv
        self.min_pulse = min_pulse_us
        self.max_pulse = max_pulse_us
        
        self.min_angle = min_angle
        self.max_angle = max_angle
        self.angle_range = abs(max_angle - min_angle)
        self.frequency = self.pca9685.pwm_frequency

        self.pwm_width_min = (self.min_pulse * self.frequency * 4095) / 1e6
        self.pwm_width_max = (self.max_pulse * self.frequency * 4095) / 1e6
        
        self.frequency = self.pca9685.pwm_frequency 
        self.periode_time_us = 1e6 / self.frequency #T[us] = 1_000_000us / freq[Hz]

        logging.debug(f"")
        logging.debug(f"-"*30)
        logging.debug(f"Servo instance established with {self.pca9685}, connected to PCA channel: {self.channel}")
        logging.debug(f"Frequency = {self.frequency}")
        logging.debug(f"Inv = {self.inv}")
        logging.debug(f"min_pulse = {self.min_pulse}")
        logging.debug(f"max_pulse = {self.max_pulse}")
        logging.debug(f"angle range = {self.angle_range}")

    def set_angle(self, angle):
        """
        Sets the servo angle in degrees.
        """
        # Calculate the PWM value corresponding to the specified angle
        pulse_range = self.max_pulse - self.min_pulse
        pulse_width = self.min_pulse + (pulse_range * angle / self.angle_range)
        #pwm_value = int(pulse_width * 4096 / (1000000 / self.pca9685.read_byte(0xFE)))
        pwm_frequency = self.pca9685.pwm_frequency
        periode_time = 1e6 / pwm_frequency
        pwm_value = int (pulse_width/periode_time * 4095 )

        logging.debug(f"Servo {self.channel}: pwm output: {pwm_value} / ({pulse_width}ns)")
        #print(pwm_value)

        # Set the PWM value for the servo channel
        self.pca9685.set_pwm(self.channel, 0, pwm_value, self.inv)

    def read_angle(self) -> int:
        pwm_on_value = self.pca9685.read_pwm_on(self.channel)
        pwm_off_value = self.pca9685.read_pwm_off(self.channel)
        logging.debug(f"PWM_on: {pwm_on_value} /t PWM_off: {pwm_off_value}")

        angle = map(pwm_off_value, self.pwm_width_min, self.pwm_width_max, self.min_angle, self.max_angle)
        return int(angle)

    def set_servo_want_angle(self, want_angle):
        self.want_angle = want_angle

    def step_towards_angle_want(self, want_angle, step_length=5, step_frequency=10):
        step_time = 1 / step_frequency
        current_angle = self.read_angle()

        if current_angle < self.min_angle:
            self.set_angle(self.min_angle)

        elif current_angle > self.max_angle:
            self.set_angle(self.max_angle)

        angle_diff = want_angle - current_angle
        if want_angle > current_angle:
            if angle_diff > 5:
                self.set_angle(current_angle + step_length)
            else:
                self.set_angle(current_angle + angle_diff)
        elif want_angle < current_angle:
            if abs(angle_diff) > 5:
                self.set_angle(current_angle - step_length)
            else:
                self.set_angle(current_angle - angle_diff)



class Servo_Switch:
    def __init__(self, pca9685, channel, min_pulse=1000, max_pulse=2000):
        # Create a Servo object with the given parameters
        self.servo = Servo(pca9685, channel, min_pulse, max_pulse)

        # Set the servo angle to 0 degrees (off)
        self.servo.set_angle(0)
    
    def on(self):
        # Set the servo angle to 180 degrees (on)
        #logging.info("Switching Servo {channel} ON")
        self.servo.set_angle(180)
    
    def off(self):
        # Set the servo angle to 0 degrees (off)
        #self.servo.set_angle(0)
        logging.info("Switching Servo {channel} OFF")

class PWM_Motor:
    def __init__(self, pca9685, channel, inv=False) -> None:
        self.motor = Servo(pca9685, channel, inv=inv)
        
    def set_speed(self, speed):
        if (speed < 10) and (speed > -10):
            speed = 0

        #Convert -100 to 100 into 0 to 180
        angle = (speed - (-100)) * (180 - 0) // (100 - (-100)) + 0
        self.motor.set_angle(angle)


    def set_angle(self, angle):
        if (angle < 85) and (angle > 95):
            angle = 90

        self.motor.set_angle(angle)  

class Camera_Tilt:
    def __init__(self, pca9685, tilt_channel, pan_channel):
        # Initialize the tilt and pan servos with default center positions
        self.pca9685 = pca9685
        self.tilt_channel = tilt_channel
        self.pan_channel = pan_channel


        self.tilt_servo = Servo(self.pca9685, self.tilt_channel)
        self.pan_servo = Servo(self.pca9685, self.pan_channel)

        # Set the initial tilt and pan angles to the center positions
        self.center_tilt_angle = 90
        self.center_pan_angle = 90
        self.tilt_angle = self.center_tilt_angle
        self.pan_angle = self.center_pan_angle
        self.MIN_TILT_ANGLE = 0
        self.MAX_TILT_ANGLE = 180

    def tilt(self, angle):
        # Set the tilt angle
        self.tilt_angle = angle
        self.tilt_servo.set_angle(angle)

    def pan(self, angle):
        # Set the pan angle
        self.pan_servo.set_angle(angle)

    def center(self):
        # Set the tilt and pan angles to the center positions
        self.tilt(self.center_tilt_angle)
        self.pan(self.center_pan_angle)


class ServoWatchdog:
    def __init__(self, servo, channel, timeout, default_angle=90):
        """
        Initializes the ServoWatchdog with the specified Servo object, channel number,
        and timeout (in seconds).
        """
        self.servo = servo
        self.channel = channel
        self.timeout = timeout
        self.default_angle = default_angle
        self.reset_event = mp.Event()
        self.process = mp.Process(target=self.watchdog_process)

    def start(self):
        """
        Starts the servo watchdog process.
        """
        logging.debug("WD Start")
        self.process.start()

    def stop(self):
        """
        Stops the servo watchdog process.
        """
        self.process.terminate()

    def reset(self):
        """
        Resets the servo watchdog timer.
        """
        logging.debug("WD Reset")
        self.reset_event.set()

    def watchdog_process(self):
        """
        The main process for the servo watchdog.
        """
        self.last_reset_time = time.time()
        while True:
            # Wait for the timeout duration
            time.sleep(self.timeout)
            # Check if the reset event has been set since the last timeout
            if self.reset_event.is_set():
                # Reset the timer and clear the reset event
                self.last_reset_time = time.time()
                self.reset_event.clear()
            else:
                # The timer has expired without being reset, so turn off the servo channel
                self.servo.set_angle(self.default_angle)
                logging.ERROR("WD Timeout")
                # Reset the timer for the next cycle
                self.last_reset_time = time.time()

class FireRover:
    def __init__(self, address:int=0x48, esc_channel:int=0, steering_channel:int=1, \
                 shift_channel:int=2, tilt_channel:int=3, pan_channel:int=4) -> None:
        self.address            = address
        self.esc_channel        = esc_channel
        self.steering_channel   = steering_channel
        self.shift_channel      = shift_channel
        self.tilt_channel       = tilt_channel
        self.pan_channel        = pan_channel

        self.pca9685 = PCA9685(self.address)
        self.ESC_init()

        self.steering_servo = Servo(self.pca9685, self.steering_channel)
        self.shift_servo = Servo(self.pca9685, self.shift_channel)
        self.camera = Camera_Tilt(self.pca9685, self.tilt_channel, self.pan_channel)

    def ESC_init(self):
        #Create a PWM_motor instance
        self.ESC = PWM_Motor(self.pca9685, self.esc_channel, inv=False)

        #Initialize the ESC watchdog and configure it with a timeout value of 1 second
        self.watchdog_timeout = 1 #second
        #self.ESC_watchdog = ServoWatchdog(self.ESC, self.esc_channel, self.watchdog_timeout)
        #self.ESC_watchdog.start()
        
        #Initialize the ESC by setting the speed to 0% (or 50% DS) for 1 second. While resetting 
        #WD every watchdog_timeout/timeout_segments seconds (default=0.2s)
        logging.debug("ESC INIT: Start...")
        timeout_segments = 5
        for i in range(timeout_segments):
            self.speed(0)
            time.sleep(self.watchdog_timeout/timeout_segments)

        time.sleep(1)
        logging.debug("ESC INIT: Done!")

    def speed(self, speed):
        #self.ESC_watchdog.reset()
        self.ESC.set_speed(speed)


    def steering(self, angle):
        self.steering_servo.set_angle(angle)

    def camera_tilt(self, angle):
        self.camera.tilt(angle)

    def camera_pan(self, angle):
        self.camera.pan(angle)



if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.debug(f"{__name__}: Debug Mode")

    rover = FireRover(address=0x48)

    while True:
        logging.debug(f"---OFF---")
        print(f"ON")
        rover.speed(0)
        rover.steering(0)
        rover.camera_pan(0)
        rover.camera_tilt(0)
        time.sleep(2)

        logging.debug(f"---ON---")
        print(f"OFF")
        rover.speed(100)
        rover.steering(180)
        rover.camera_pan(180)
        rover.camera_tilt(180)
        time.sleep(2)




    """
    pca9685 = PCA9685(0x40)
    servo = Servo(pca9685, 12)
    servo_switch = Servo_Switch(pca9685, 13)
    camera = Camera_Tilt(pca9685, 14, 15)
    servo_watchdog = ServoWatchdog(servo, 12, 1)
    servo_watchdog.start()

    while True:
        print("---ON---")   
        servo.set_angle(180)
        servo_watchdog.reset()
        servo_switch.on()
        camera.pan(180)
        camera.tilt(180)
        time.sleep(2)

        print("---OFF---")
        servo.set_angle(0)
        servo_switch.off()
        camera.pan(0)
        camera.tilt(0)
        time.sleep(2)"""
    
