import multiprocessing as mp
import subprocess
import logging
import time
import os
import json
import atexit
import math
from time import sleep 
import RPi.GPIO as GPIO
import datetime
import csv

from ServoHat.servo_lib import FireRover
from ADCHat.ADC_lib import ADC_Hat

"""
Main Program to be run on the RPi FireRover
"""

BuzzerPin = 18

#GPIO.setmode(GPIO.BCM)
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup(BuzzerPin, GPIO.OUT)


recv_data_queue = mp.Queue()
send_data_queue = mp.Queue()
firerover_data_template = {
    "battery_gauge":0,
    "battery_voltage":0,
    "motor_speed":0,
    "steering_angle":0,
    "rover_gear_angle":0,
    "SYS_RESET":False,
    "Server_RESET":False
    }

def BuzzerStartup():
    for i in range(3):
        GPIO.output(BuzzerPin, GPIO.HIGH)
        sleep(0.08)
        GPIO.output(BuzzerPin, GPIO.LOW)
        sleep(0.08)

def BuzzerShutdown():
    for i in range(3):
        GPIO.output(BuzzerPin, GPIO.HIGH)
        sleep(0.5)
        GPIO.output(BuzzerPin, GPIO.LOW)
        sleep(0.1)

def start_tunnel(logging_level = logging.ERROR):
    logging.basicConfig(level=logging_level)
    logging.info(f"Starting Pagekite Tunnel")

    #Setting Correct Working Dir
    full_path = os.path.realpath(__file__)
    path, filename = os.path.split(full_path)
    os.chdir(path + "/WebRTC/aiortc_oneway")

    #Shell Command to start pagekite
    cmd = ["python", "pagekite.py", "5000", "firerover.pagekite.me"]
    try:
        subprocess.run(cmd, capture_output=True, shell=False)

    except KeyError:
        logging.error(f"Wrong working dir selected")

def start_WebRTC_server(recv_data_queue, send_data_queue, data_manager, logging_level = logging.ERROR):
    logging.basicConfig(level=logging_level)
    logging.info(f"Starting WebRTC Server")

    full_path = os.path.realpath(__file__)
    path, filename = os.path.split(full_path)
    os.chdir(path + "/WebRTC/aiortc_oneway")

    try:
        import WebRTC.aiortc_oneway.server as server
        server.start_queues(recv_data_queue, send_data_queue, data_manager)
        server.start_server()

    except OSError as error:
        logging.error("File Not Found")
        logging.error(f"{error}")

    except KeyError:
        logging.error(f"Wrong working dir selected")
    
    except KeyboardInterrupt:
        logging.error(f"KeyBoardInterrupt Detected")

    except FileNotFoundError:
        logging.error("Wrong Camera Selected")
    
    """
    except Exception as error:
        logging.error(f"Error Detected: \t {type(error).__name__} -, {error}")"""



def print_queue_data(recv_data_queue, logging_level = logging.ERROR):
    logging.basicConfig(level=logging_level)
    logging.info(f"Print Recv_Data")

    while True:
        try:
            if recv_data_queue.qsize() != 0:
                recv_data_str = recv_data_queue.get()
                recv_data = json.loads(recv_data_str)
                logging.info(f"Data From Queue: {recv_data_str}")

        except:
            pass

        time.sleep(0.001)

def servo_control(firerover_data, recv_data_queue, logging_level=logging.ERROR):
    logging.basicConfig(level=logging_level)
    logging.debug("Starting servo control")

    try:
        led_pin = 35 #GPIO 19
        process_active_indicator = 36 #GPIO 16
        #GPIO.setmode(GPIO.BOARD)
        GPIO.setup(led_pin, GPIO.OUT, initial=0)
        GPIO.setup(process_active_indicator, GPIO.OUT, initial=0)
        GPIO.output(process_active_indicator, 1)
        rover = FireRover()

        @atexit.register
        def exit_handler():
            # Sets motorspeed to zero if process exits
            print("Servo Control Exit Handler")
            GPIO.output(process_active_indicator, 0)
            rover.speed(0)


        queue_last_write_time = time.time()
        camera_hold = False
        camera_lock = False
        while True:
            if recv_data_queue.qsize() != 0:

                try:
                    commands_str = recv_data_queue.get() # Get data from queue
                    commands = json.loads(commands_str)["values"]
                    queue_last_write_time = time.time() #Reset Watchdog Timer

                    if type(commands) is dict:
                        logging.debug(f"Servo Commands: {commands}")

                        #Motor Control
                        speed_int = int(map(commands["right_trigger"], 0, 1, 0, 100)) 
                        rev_int = int(map(commands["left_trigger"], 0, 1, 0, -100))
                        speed_factor = float(commands["speed_multiplier"])/100
                        motor_speed = (speed_int+rev_int) * speed_factor                      
                        rover.speed(motor_speed)
                        firerover_data["motor_speed"] = motor_speed
                        logging.debug(f"Motor Speed: {motor_speed}")

                        #Steering factor
                        steering_factor = 2 - math.exp(0.4*speed_factor)

                        #Steering Control
                        steering_int = int(map(commands["l_thumb_x"]*steering_factor, -1, 1, 10, 170)) #Steering angle limited to prevent stress on servo amd motor
                        steering_offset = int(commands["steering_offset"])
                        steering_angle = steering_int + steering_offset
                        rover.steering(steering_angle)
                        firerover_data["steering_angle"] = steering_angle
                        logging.debug(f"Steering Angle: {steering_angle}")

                        #Camera Lock
                        if commands["buttons"]["RB"]:
                            
                            if not(camera_hold):
                                logging.debug("Camera Lock Toggle")
                                camera_lock = not(camera_lock)
                                camera_hold = True
                        else:
                            camera_hold = False

                        #Camera Control
                        if not(camera_lock):
                            tilt_angle = int(map(commands["r_thumb_y"], -1, 1, 0, 180))
                            rover.camera_tilt(tilt_angle)

                            pan_angle = int(map(commands["r_thumb_x"], -1, 1, 180, 0))
                            rover.camera_pan(pan_angle)
                        

                        #Gear Control
                        if commands['buttons']["D_PAD_UP"]:
                            rover.shift_servo.set_angle(0) #Shift to HIGH gear
                            firerover_data["rover_gear_angle"] = "HIGH"
                            
                        
                        elif commands['buttons']["D_PAD_DOWN"]: 
                            rover.shift_servo.set_angle(110) # Shift to LOW gear
                            firerover_data["rover_gear_angle"] = "LOW"

                        #LED Control
                        if commands['buttons']["A"]:
                            GPIO.output(led_pin, 1)
                            #logging.debug("LED ON")
                        else:
                            GPIO.output(led_pin, 0)

                        if  firerover_data["SYS_RESET"]:
                            logging.info("Resetting System")
                            GPIO.output(process_active_indicator, 0)
                            rover.speed(0)
                            rover.pca9685.reset()
                            BuzzerShutdown()
                            GPIO.cleanup()
                            time.sleep(2)
                            os.system("sudo reboot")
                            break

                except Exception as error:
                    logging.error(f"ServoLib Error: {error}")
                    rover.speed(0)
            else:
                #Speed watchdog: If recv_data_queue is empy for >= 1 second then set motor speed to 0
                if (time.time() - queue_last_write_time) > 1:
                    rover.speed(0)
                    queue_last_write_time = time.time()
                
            time.sleep(0.001)

    except IOError:
        logging.error("PWM HAT not connected to I2C")

def batt_gauge(manager_dict, sample_frequency=1 ,logging_level=logging.ERROR):
    logging.basicConfig(level=logging_level)
    logging.info(f"Start Battery Gauge")
    try:
        ADC = ADC_Hat()
        ADC.calibrate_all()
        while True:
            gauge = ADC.battery_gauge(0)
            voltage = ADC.read_voltage(0)
            manager_dict["battery_gauge"] = gauge
            manager_dict["battery_voltage"] = voltage
            logging.debug(f"Battery Gauge: \t {gauge}%")
            logging.debug(f"Battery Gauge: \t {voltage}%")
            time.sleep(1/sample_frequency)
    except IOError:
        logging.error("ADC Hat not connected to I2C")

def logging_file(firerover_data, logging_level=logging.ERROR):
    logging.basicConfig(level=logging_level)
    logging.info(f"Starting Logging File")

    frequency = 1

    file_dirname = os.path.dirname(__file__)
    os.chdir(file_dirname)

    dirname = "csv_log"
    try:
        os.mkdir(dirname)
    except FileExistsError:
        logging.debug(f"Directory {dirname} already exists")
    os.chdir(dirname)

    filename = "firerover_log"+str(datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))+".csv"
    columns = ["timestamp", "motor_speed", "steering_angle","rover_gear_angle", "battery_gauge", "battery_voltage"]
    with open(filename, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(columns)
        logging.debug("Writing column names to log file")

    while True:
        timestamp = datetime.datetime.now()
        datarow = [timestamp, firerover_data["motor_speed"], firerover_data["steering_angle"], firerover_data["rover_gear_angle"], firerover_data["battery_gauge"], firerover_data["battery_voltage"]]
        with open(filename, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(datarow)
            logging.debug("Writing row to log file")
        
        time.sleep(1/frequency)
    

def map(x, in_min, in_max, out_min, out_max):
    mapped_value = (x - (in_min)) * (out_max - out_min) // (in_max - (in_min)) + out_min
    #Bounds the output to be withing the configured min and max output values
    if out_max > out_min:
        if mapped_value < out_min: mapped_value = out_min
        elif mapped_value > out_max: mapped_value = out_max

    else:
        if mapped_value < out_max: mapped_value = out_max
        elif mapped_value > out_min: mapped_value = out_min

    return mapped_value

file = __file__ # File defines as a variable becaise exit handler can't use the __file__ variable. 
@atexit.register
def exit_handler():
    # Closes all Processes That has been started by this program
    print("Exit Handler")
    cmd = ["pkill", "-f", file]
    subprocess.call(cmd)

if __name__ == "__main__":

    logging_level = logging.INFO
    print_queue = False #Debug function for printing queue data to stdout
    log_file = True #Debug function for logging data to csv file

    with mp.Manager() as manager:

        firerover_data = manager.dict(firerover_data_template)
        
        #Starts the pagekite tunnel. The tunnel is used to initiate etablish the WebRTC connection
        tunnel_process = mp.Process(target=start_tunnel, args=(logging_level, ))

        #Starts the WebRTC server. 
        server_process = mp.Process(target=start_WebRTC_server, args=(recv_data_queue, send_data_queue, firerover_data, logging_level))

        #Reads controll data from the WebRTC server and uses it to control the FireRover Servoes.
        servo_process = mp.Process(target=servo_control, args=(firerover_data, recv_data_queue, logging_level))

        #Reads battery gauge and write data to manager
        battery_gauge_process = mp.Process(target=batt_gauge, args=(firerover_data, ))

        #DEBUG: prints date in queue to stdout if print_queue==true
        if print_queue: print_process = mp.Process(target=print_queue_data, args=(recv_data_queue, logging_level))

        if log_file: logging_file_process = mp.Process(target=logging_file, args=(firerover_data, logging_level))

        #Start all the processes
        tunnel_process.start()
        server_process.start()
        servo_process.start()
        battery_gauge_process.start()
        if print_queue: print_process.start()
        if log_file: logging_file_process.start()
        BuzzerStartup()

        while True:
            if firerover_data["Server_RESET"]:
                logging.info("Restarting Server...")
                time.sleep(3)
                server_process.kill()
                time.sleep(1)
                server_process = mp.Process(target=start_WebRTC_server, args=(recv_data_queue, send_data_queue, firerover_data, logging_level))
                server_process.start()
                firerover_data["Server_RESET"] = False
            time.sleep(0.1)

        #Merge when all the processes are finished. 
        tunnel_process.join()
        server_process.join()
        servo_process.join()
        battery_gauge_process.join()
        if print_queue: print_process.join()
        if log_file: logging_file_process.join()

    print("Done!")


