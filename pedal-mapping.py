#!/usr/bin/env python3

# Dependencies
# pip3 install evdev
# User needs to be in "input" group
# usermod -a -G input <user>

import re
import time
import evdev
from evdev import InputDevice, UInput, ecodes

print("Started")

def find_device(vendor,product):
    devices = [InputDevice(path) for path in evdev.list_devices()]
    #print(devices)
    device_found = False
    for device in devices:
        if device.info.vendor==vendor and device.info.product==product:
            print(f"{device.name} found")
            device.grab()
            return device
    return None

device = None
ui = UInput()
while True:
    if device is None:
        device = find_device(vendor=0x05f3,product=0x00ff)
        continue
    try:
        for event in device.read_loop():
            if event.type == ecodes.EV_KEY:
                if event.value == 0x01:
                    print("LEFT")
                    ui.write(ecodes.EV_KEY, ecodes.KEY_PAGEUP, 1)  # KEY_A down
                    ui.write(ecodes.EV_KEY, ecodes.KEY_PAGEUP, 0)  # KEY_A up
                    ui.syn()
                if event.value == 0x02:
                    print("MIDDLE")
                    ui.write(ecodes.EV_KEY, ecodes.KEY_ENTER, 1)  # KEY_A down
                    ui.write(ecodes.EV_KEY, ecodes.KEY_ENTER, 0)  # KEY_A up
                    ui.syn()
                if event.value == 0x04:
                    print("RIGHT")
                    ui.write(ecodes.EV_KEY, ecodes.KEY_PAGEDOWN, 1)  # KEY_A down
                    ui.write(ecodes.EV_KEY, ecodes.KEY_PAGEDOWN, 0)  # KEY_A up
                    ui.syn()
    except OSError as ex:
        print("Pedal disappeared")
        device = None
