import logging
import os
import time
import smbus
from smbus2 import SMBusWrapper
from threading import Thread
from typing import Union

import serial

import submodules.command_ingest as ci
from core import config
# Initalize global variables
from submodules import command_ingest
from submodules.command_ingest import logger, dispatch

logger = logging.getLogger("EPS")
pause_sending = False
send_buffer = []
beacon_seen = False
last_telem_time = time.time()
last_message_time = time.time()

user = False
bperiod = 60
ser: Union[serial.Serial, None] = None

address = 43
bus = smbus.SMBus(1)

epsdict = {'gps':0, 'magnetorquer':1, 'aprs':2, \
'iridium':3, 'antenna':4}

def listen():
    while True:
        # Read in a full message from serial
        line = ser.readline()
        # Dispatch command
        parse_aprs_packet(line)
def pin_on(device_name):
    with SMBusWrapper(1) as bus:
        PDM_val = [epsdict[device_name]]
        bus.write_i2c_block_data(address, 0x12, PDM_val)
        #Logging function to say if pin was already on or successful
def pin_off(device_name):
    with SMBusWrapper(1) as bus:
        PDM_val = [epsdict[device_name]]
        bus.write_i2c_block_data(address, 0x13, PDM_val)
def get_board_status():
    with SMBusWrapper(1) as bus:
        return bus.read_i2c_block_data(address, 0x01)
def set_system_watchdog_timeout(timeout):
    with SMBusWrapper(1) as bus:
        timeout = [timeout]
        bus.write_i2c_block_data(address, 0x06, timeout)
def get_BCR1_volts():
    with SMBusWrapper(1) as bus:
        bus.write_i2c_block_data(address, 0x10, 0x00)
        return bus.read_byte(address)
def get_BCR1_amps_A():
    with SMBusWrapper(1) as bus:
        bus.write_i2c_block_data(address, 0x10, 0x01)
        return bus.read_byte(address)
def get_BCR1_amps_B():
    with SMBusWrapper(1) as bus:
        bus.write_i2c_block_data(address, 0x10, 0x02)
        return bus.read_byte(address)
def led_on_off():
    while true:
        pin_on('aprs')
        time.sleep(1)
        pin_off('aprs')
        time.sleep(1)

# Method that is called upon application startup.
def on_startup():
    global ser, logfile
    global address, bus

    # Opens the serial port for all methods to use with 19200 baud
    #ser = serial.Serial(config['eps']['serial_port'], 19200)


    # Create all the background threads
    t1 = Thread(target=led_on_off, args=(), daemon=True)

    # Open the log file
    log_dir = os.path.join(config['core']['log_dir'], 'eps')
    filename = 'eps' + '-'.join([str(x) for x in time.localtime()[0:3]])
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)
    logfile = open(os.path.join(log_dir, filename + '.txt'), 'a+')

    # Mark the start of the log
    log_message('RUN@' + '-'.join([str(x) for x in time.localtime()[3:5]]))


    # Start the background threads
    t1.start()
    t1.daemon = True


# Have the 3 below methods. Say pass if you dont know what to put there yet
# these are in reference to power levels. Shut stuff down if we need to go to
# emergency mode or low power. Entering normal mode should turn them back on
def enter_normal_mode():
    global bperiod
    bperiod = 60


def enter_low_power_mode():
    global bperiod
    bperiod = 120


def enter_emergency_mode():
    pass


def log_message(msg):
    global logfile
    # Write to file
    logfile.write(msg + '\n')
    logfile.flush()
