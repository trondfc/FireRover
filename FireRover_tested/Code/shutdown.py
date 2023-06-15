#!/usr/bin/env python3

# Import the modules to send commands to the system and access GPIO pins
from subprocess import call
import RPi.GPIO as GPIO
from time import sleep
import logging
import atexit


# Map pin seven and eight on the Pi Switch PCB to chosen pins on the Raspberry Pi header
# The PCB numbering is a legacy with the original design of the board
Shutdown_Input_pin = 37 #GPIO26 is connected to switch_pin 7
LED_Indicator_Pin = 13 #GPIO27 is connected to switch_pin 8

GPIO.setmode(GPIO.BOARD) # Set pin numbering to board numbering
GPIO.setup(Shutdown_Input_pin, GPIO.IN) # Set up PinSeven as an input
GPIO.setup(LED_Indicator_Pin, GPIO.OUT, initial=1) # Setup PinEight as output

def wait_for_shutdown(bounce_filter_ms:int=100, test_mode=False):
    logging.info(f"Starting Shutdown Watchdog")
    logging.info(f"Test Mode: {test_mode}")
    #If test_mode == True then the shutdown and reset commands will not be executed
    bounce_filter_timer = 0

    while (bounce_filter_timer <= bounce_filter_ms): # While button not pressed
        logging.debug(f"Shutdown Input Pin: {read_inputs(Shutdown_Input_pin)}")
        logging.debug(f"Bounce Filter: {bounce_filter_timer}")
        if (GPIO.input(Shutdown_Input_pin) == True):
            bounce_filter_timer += 10

        else:
            bounce_filter_timer = 0
        
        sleep(0.01)
    
    sleep(2); # Sleep 2s to distinguish a long press from a short press

    if (GPIO.input(Shutdown_Input_pin) == False):
        GPIO.output(LED_Indicator_Pin,0) # Bring down PinEight so that the capacitor can discharge and remove power to the Pi
        
        logging.info("Shutdown started...")
        shutdown_cmd = ["sudo", "shutdown", "now"]
        if test_mode == False:
            call(shutdown_cmd, shell=False) # Initiate OS Poweroff

    else:
        logging.info("Reboot started...")
        reboot_cmd = ["sudo", "reboot"]
        if test_mode == False:
            call(reboot_cmd, shell=False) # Initiate OS Reboot

@atexit.register
def exit_handler():
    # Turns output off when program is closed  
    GPIO.output(LED_Indicator_Pin,0)
    logging.info("Exit Handler")



def read_inputs(pin):
    return(GPIO.input(pin))

if __name__ == "__main__":
    logging_level = logging.INFO
    logging.basicConfig(level=logging_level)
    wait_for_shutdown(test_mode=False)   
      