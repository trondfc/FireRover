import multiprocessing as mp
import json
import logging
import os
import time
import webbrowser

import WebRTC.aiortc_oneway.start as start
#import Controller.controller as controller

send_data_queue = mp.Queue()


def run_client(logging_level=logging.ERROR):
    logging.basicConfig(level=logging_level)
    logging.info("Starting client") 

    full_path = os.path.realpath(__file__)
    path, filename = os.path.split(full_path)
    os.chdir(path + "/WebRTC/aiortc_oneway")

    start.start_client()

def run_browser(logging_level=logging.ERROR):
    logging.basicConfig(level=logging_level)
    logging.info("Starting browser")
    time.sleep(2)
    
    webbrowser.open("http://localhost:8000")
"""
def controller_input(send_data_queue, logging_level=logging.ERROR):
    logging.basicConfig(level=logging_level)
    logging.info("Starting controller input")
    controller.sample_joystick(send_data_queue)"""
"""
def queue_to_file(send_data_queue, logging_level=logging.ERROR):
    logging.basicConfig(level=logging_level)
    logging.info("Staring Controller_to_file")

    full_path = os.path.realpath(__file__)
    path, filename = os.path.split(full_path)
    os.chdir(path + "/WebRTC/aiortc_oneway")

    while True:
        if send_data_queue.qsize() > 0:
            data = send_data_queue.get()
            with open('send_data.json', 'w') as f:
                logging.debug(f"Writing data to file: {data}")
                json.dump(data, f)
        time.sleep(0.001)
"""


if __name__ == "__main__":

    logging_level = logging.INFO
    logging.basicConfig(level=logging_level)
    open_browser = True

    client_process = mp.Process(target=run_client, args=(logging_level,))
    #controller_process = mp.Process(target=controller_input, args=(send_data_queue,logging_level))
    #queue_to_file_process = mp.Process(target=queue_to_file, args=(send_data_queue, logging_level))
    if open_browser: browser_process = mp.Process(target=run_browser, args=(logging_level,))

    client_process.start()
    #controller_process.start()
    #queue_to_file_process.start()
    if open_browser: browser_process.start()
    print("Processes started")

    client_process.join()
    #controller_process.join()
    #queue_to_file_process.join()
    if open_browser: browser_process.join()
