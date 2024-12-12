#!/usr/bin/env python3

import os
import time
import subprocess
from evdev import InputDevice, ecodes
import RPi.GPIO as GPIO  # Add this import at the top

# Global configuration
SCREEN_TIMEOUT = 60  # Time in seconds before screen turns off

# Find touchscreen device
def find_touchscreen():
    for dev_path in os.listdir('/dev/input'):
        if dev_path.startswith('event'):
            try:
                device = InputDevice(os.path.join('/dev/input', dev_path))
                caps = device.capabilities()
                
                print(f"Checking device: {device.name}")
                print(f"Path: {device.path}")
                print(f"Capabilities: {caps}")
                
                # Check for common touchscreen characteristics
                has_abs_touch = (
                    ecodes.EV_ABS in caps and  # Has absolute positioning events
                    any(code in caps.get(ecodes.EV_ABS, []) 
                        for code in [
                            ecodes.ABS_X,  # Basic touch
                            ecodes.ABS_Y,
                            ecodes.ABS_MT_POSITION_X,  # Multi-touch
                            ecodes.ABS_MT_POSITION_Y,
                            ecodes.ABS_PRESSURE,  # Pressure sensitivity
                            53,  # Alternative X position
                            54   # Alternative Y position
                        ])
                )
                
                has_touch_name = any(keyword in device.name.lower() 
                    for keyword in ['touch', 'ts', 'touchscreen', 'qdtech'])
                
                if has_abs_touch or has_touch_name:
                    print(f"Found touchscreen device: {device.name}")
                    return device
                
            except Exception as e:
                print(f"Error checking device {dev_path}: {str(e)}")
                continue
    
    print("No touchscreen devices found after checking all input devices")
    return None

# Set GPIO pin state using RPi.GPIO
def set_gpio(state):
    # Convert 'h'/'l' to True/False
    gpio_state = True if state == 'h' else False
    GPIO.output(24, gpio_state)

def main():
    # Find touchscreen device
    device = find_touchscreen()
    if not device:
        print("No touchscreen device found")
        return

    # Setup GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(24, GPIO.OUT)
    GPIO.output(24, GPIO.LOW)  # Initialize as off
    
    try:
        last_touch_time = time.time()
        last_print_time = 0  # Add tracking for last print time
        set_gpio('h')  # Turn on initially

        while True:
            current_time = time.time()
            
            # Check for touch events without blocking
            try:
                # Read all pending events without processing them multiple times
                events = []
                while True:
                    event = device.read_one()
                    if event is None:
                        break
                    events.append(event)

                # Only process the most recent touch event
                if any(event.type == ecodes.EV_ABS for event in events):
                    # Only print message if it's been at least 1 second since last print
                    if current_time - last_print_time >= 1:
                        print("Touch detected! Screen will turn off in 60 seconds if no further input.")
                        last_print_time = current_time
                    set_gpio('h')
                    last_touch_time = current_time

            except BlockingIOError:
                pass

            # Check timeout regardless of events
            if last_touch_time > 0:
                time_remaining = SCREEN_TIMEOUT - (current_time - last_touch_time)
                if time_remaining <= 0:
                    print("Turning screen off")
                    set_gpio('l')
                    last_touch_time = 0
                elif int(time_remaining) % 10 == 0 and current_time - last_print_time >= 1:
                    print(f"Screen will turn off in {int(time_remaining)} seconds")
                    last_print_time = current_time
            
            time.sleep(0.1)  # Prevent CPU hogging

    finally:
        # Cleanup GPIO on exit
        GPIO.cleanup()

if __name__ == "__main__":
    main()
