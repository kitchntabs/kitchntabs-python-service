# helpers.py

from datetime import datetime
import usb.core
import usb.backend.libusb1
from escpos.printer import Usb
from pinoywok.config import config
from pinoywok.logging import log
import psutil
import logging
import platform

import json
import asyncio

def get_timestamp():
    now = datetime.now()
    return now.strftime('%Y%m%d-%H%M%S')

def read_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        text = f.read()
    return text

def usb_busses():
    # FIND AVAILABLKE USB DEVICES, requires 1.0.20+ libusb windows x64
    busses = usb.busses()
    for bus in busses:
        devices = bus.devices
        for dev in devices:
            #print (repr(dev))
            print ("Device:", dev.filename)
            print ("  idVendor: %d (0x%04x)" % (dev.idVendor, dev.idVendor))
            print ("  idProduct: %d (0x%04x)" % (dev.idProduct, dev.idProduct))
            print ("Manufacturer:", dev.iManufacturer)
            print ("Serial:", dev.iSerialNumber)
            print ("Product:", dev.iProduct)
      
def enumerate_devices(): 
    LIBUSB_PATH = get_libusbdll_path()
    backend = usb.backend.libusb1.get_backend(
    find_library=lambda x: LIBUSB_PATH)
    usb_devices = usb.core.find(backend=backend, find_all=True)
    for i, d in enumerate(usb_devices):
        try:
            print(f"USB Device number {i}:\n")
            print(d._get_full_descriptor_str() + "\n")
            # print(d.get_active_configuration() + "\n")
            print("\n")
        except NotImplementedError:
            print(f"Device number {i} is busy.\n\n")
        except usb.core.USBError:
            print(f"Device number {i} is either disconnected or not found.\n\n")
def check_devcice_message():
    PRINTER_VENDOR = config.get_printer_vendor()
    PRINTER_PRODUCT = config.get_printer_product()
    print(f"Check for device ID: {PRINTER_VENDOR}, PRODUCT: {PRINTER_PRODUCT}")       
def check_devcice():
    PRINTER_VENDOR = config.get_printer_vendor()
    PRINTER_PRODUCT = config.get_printer_product()
    #LIBUSB_PATH = get_libusbdll_path()
    #backend = usb.backend.libusb1.get_backend(
    #find_library=lambda x: LIBUSB_PATH)
    print(f"Check for device ID: {PRINTER_VENDOR}, PRODUCT: {PRINTER_PRODUCT}")
    printer = Usb(PRINTER_VENDOR, PRINTER_PRODUCT, 0, 0x81, 0x02)
    print(printer.is_online())
    print(printer.is_usable())
    
    #printer.open()
    #printer.close()
def close_printer():
    PRINTER_VENDOR = config.get_printer_vendor()
    PRINTER_PRODUCT = config.get_printer_product()
    print(f"Close for device ID: {PRINTER_VENDOR}, PRODUCT: {PRINTER_PRODUCT}")
    printer = Usb(PRINTER_VENDOR, PRINTER_PRODUCT, 0, 0x81, 0x02)
    printer.close()


def get_json_value(json_data, json_path):
    try:
        value = json_data
        for key in json_path.split('.'):
            value = value[key]
        return value
    except (KeyError, TypeError):
        return "-"

def get_json_str_value(json_data, json_path):
    try:
        value = json_data
        for key in json_path.split('.'):
            value = value[key]
        return str(value)
    except (KeyError, TypeError):
        return "-"


def to_json(input_str):
    """
    Converts input string to a JSON string.

    Args:
        input_str: str

    Returns:
        str: JSON string
    """
    try:
        # Try to parse the input string as JSON
        json_data = json.loads(input_str)
        return json.dumps(json_data)
    except json.JSONDecodeError:
        # If parsing fails, return the original input string
        return input_str
    
def validJsonString(input_data):
    """
    Converts input data to a JSON string.

    Args:
        input_data: str, bytes, or bytearray

    Returns:
        str: JSON string
    """
    if isinstance(input_data, str):
        # If input is a string, try to parse it as JSON
        try:
            json_data = json.loads(input_data)
            return json.dumps(json_data)
        except json.JSONDecodeError:
            # If parsing fails, assume it's an escaped string and unescape it
            unescaped_input = input_data.encode('utf-8').decode('unicode_escape')
            return to_json(unescaped_input)
    elif isinstance(input_data, (bytes, bytearray)):
        # If input is bytes or bytearray, decode it to a string first
        input_str = input_data.decode('utf-8')
        return to_json(input_str)
    else:
        raise ValueError("Invalid input type. Expected str, bytes, or bytearray.")
    

#SYSTEM SUSPENSION HANDLERS
async def prevent_system_sleep():
    log("Preventing system sleep")
    if platform.system() == 'Windows':
        import ctypes
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001 | 0x00000002)
    elif platform.system() == 'Darwin':  # Mac
        import subprocess
        subprocess.call(['caffeinate', '-i'])
    else:  # Linux
        import subprocess
        subprocess.call(['systemd-inhibit', 'sleep'])

async def allow_system_sleep():
   
    if platform.system() == 'Windows':
        import ctypes
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
    elif platform.system() == 'Darwin':  # Mac
        import subprocess
        subprocess.call(['caffeinate', '-d'])
    else:  # Linux
        import subprocess
        subprocess.call(['systemd-inhibit', '--release'])
        
        

async def handle_system_hibernation():
    log("System hibernation/suspension detected")
    # Perform any necessary actions before hibernation/suspension
    # ...
    await allow_system_sleep()

async def handle_system_wake_up():
    log("System wake-up detected")
    # Perform any necessary actions after wake-up
    # ...
    await prevent_system_sleep()

async def monitor_system_events():
    log("Monitoring system events")
    while True:
        # Check for system hibernation/suspension
        if psutil.sensors_battery() is not None and psutil.sensors_battery().power_plugged is False:
            if psutil.sensors_battery() and psutil.sensors_battery().percent < 3:
                await handle_system_hibernation()
        # Check for system wake-up
        elif psutil.sensors_battery() is not None and psutil.sensors_battery().power_plugged is True:
            await handle_system_wake_up()
        # Wait for next event
        await asyncio.sleep(1)

