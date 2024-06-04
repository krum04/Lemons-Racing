'''
   Raspberry Pi Pico GPIO Pinout
       _______
  GP0  | 1  40 | VBUS
  GP1  | 2  39 | VSYS
  GND  | 3  38 | GND
  GP2  | 4  37 | 3V3_EN
  GP3  | 5  36 | 3V3(OUT)
  GP4  | 6  35 | ADC_VREF
  GP5  | 7  34 | GP28
  GND  | 8  33 | GND
  GP6  | 9  32 | GP27
  GP7  | 10 31 | GP26
  GP8  | 11 30 | RUN
  GP9  | 12 29 | GP22
  GND  | 13 28 | GND
  GP10 | 14 27 | GP21
  GP11 | 15 26 | GP20
  GP12 | 16 25 | GP19
  GP13 | 17 24 | GP18
  GND  | 18 23 | GND
  GP14 | 19 22 | GP17
  GP15 | 20 21 | GP16
       -------
'''

import tm1637
from machine import Pin
import utime
import uos

# Pin Assignments
# myDisplay (TM1637 Display)
# CLK: Pin 26
# DIO: Pin 27

# flowMeter: Pin 4
# fillButton: Pin 5
# lowLevel: Pin 3
# fullLevel: Pin 2

# pumpRelayA: Pin 14 (output, initialized as off)
# pumpRelayB: Pin 15 (output, initialized as off)
# lowIndicator: Pin 13 (output, initialized as off)
# underHoodFull: Pin 6 (output, initialized as off)

# LED outputs for indicating pump status
# ledA: Pin 9 (output, initialized as off)
# ledB: Pin 8 (output, initialized as off)

# Functions to read and write oilVolume to a file
def write_oil_volume_to_file(volume):
    with open('oil_volume.txt', 'w') as f:
        f.write(str(volume))

def read_oil_volume_from_file():
    try:
        with open('oil_volume.txt', 'r') as f:
            volume = int(f.read().strip())
            return volume
    except OSError:
        # File not found or other error. Return default volume.
        return 0

def flash_zeros():
    for _ in range(3):  # Flash 3 times
        myDisplay.write([0, 0, 0, 0])  # Display all zeros
        utime.sleep(0.5)  # Wait for half a second
        myDisplay.write([0x7F, 0x7F, 0x7F, 0x7F])  # Turn off the display (assuming 0x7F is the blank character)
        utime.sleep(0.5)  # Wait for half a second

myDisplay = tm1637.TM1637(clk=Pin(26), dio=Pin(27))
flowMeter = Pin(4, Pin.IN)
fillButton = Pin(5, Pin.IN)
lowLevel = Pin(3, Pin.IN)
fullLevel = Pin(2, Pin.IN)

# Updated pin assignments
pumpRelayA = Pin(14, Pin.OUT, value=1)  # Initialize as off
pumpRelayB = Pin(15, Pin.OUT, value=1)  # Initialize as off
lowIndicator = Pin(13, Pin.OUT, value=0)
underHoodFull = Pin(6, Pin.OUT, value=0)

# LED outputs for indicating pump status
ledA = Pin(9, Pin.OUT, value=0)  # Initialize as off
ledB = Pin(8, Pin.OUT, value=0)  # Initialize as off

# Read oilVolume from the file at the start
oilVolume = read_oil_volume_from_file()
myDisplay.number(oilVolume)

# Add a global variable to track the last state of the flow meter
lastFlowMeterState = 0 

# Define debounce time (e.g., 50ms)
DEBOUNCE_TIME = 200

def engagePump():
    global oilVolume
    global lastFlowMeterState  # Use the global variable inside the function
    
    # Use Pump A by default
    pumpRelayA.value(0)  # Turn ON Pump A
    pumpRelayB.value(1)  # Ensure Pump B is OFF
    ledA.value(1)
    ledB.value(0)
    last_flow_time = utime.ticks_ms()  # Initialize with current time

    while fullLevel.value() == 1:

        # Pump switching logic based on flow timeout
        if utime.ticks_diff(utime.ticks_ms(), last_flow_time) > 60000:
            if pumpRelayA.value() == 0:  # If Pump A is currently ON
                pumpRelayA.value(1)  # Turn OFF Pump A
                ledA.value(0)  # Turn OFF LED A
                ledB.value(1)
                pumpRelayB.value(0)  # Turn ON Pump B
            else:
                pumpRelayB.value(1)  # Turn OFF Pump B
                ledA.value(1)  # Turn ON LED A
                ledB.value(0)
                pumpRelayA.value(0)  # Turn ON Pump A
            last_flow_time = utime.ticks_ms()  # Reset the last flow time

        # Flow meter logic for incrementing oil volume
        if flowMeter.value() == 1 and lastFlowMeterState == 0:
            utime.sleep_ms(DEBOUNCE_TIME)  # Wait for debounce time
            if flowMeter.value() == 1:  # Check again to confirm it's a valid transition
                oilVolume += 1
                myDisplay.number(oilVolume)
                # Write the updated oilVolume to the file
                write_oil_volume_to_file(oilVolume)
                last_flow_time = utime.ticks_ms()  # Update last flow time

        # Update the last state of the flow meter
        lastFlowMeterState = flowMeter.value()

    print("Oil Full")
    pumpRelayA.value(1)  # Turn OFF Pump A
    ledA.value(0)  # Turn OFF LED A
    pumpRelayB.value(1)  # Turn OFF Pump B
    ledB.value(0)  # Turn OFF LED B

# New variable to track the countdown start
countdown_start = 0

while True:
    pumpRelayA.value(1)  # Ensure Pump A is OFF
    pumpRelayB.value(1)  # Ensure Pump B is OFF
    utime.sleep(.1)
    
    # Check full stutus sensor and light up underhood light acordingly
    if fullLevel.value() == 1:
        underHoodFull.off()
    else:
        underHoodFull.on()
    
    if lowLevel.value() == 1:
        print("Low Oil")
        lowIndicator.on()
    else:
        lowIndicator.off()

    if fillButton.value() == 1 and lowLevel.value() == 0:
        if countdown_start == 0:
            countdown_start = utime.ticks_ms()

        elapsed_time = utime.ticks_diff(utime.ticks_ms(), countdown_start) / 1000  # Convert to seconds
        remaining_time = 5 - int(elapsed_time)

        # Display the countdown
        myDisplay.number(remaining_time)

        if remaining_time <= 0:
            print("Button held for 5 seconds. Resetting oil volume.")
            oilVolume = 0
            myDisplay.number(oilVolume)
            write_oil_volume_to_file(oilVolume)
            countdown_start = 0

            # Flash zeros to indicate reset completion
            flash_zeros()

            # Display the reset value after flashing
            myDisplay.number(oilVolume)

    else:
        # If the button is not pressed or lowLevel is not 0
        # Reset the countdown_start and display the current oilVolume
        if countdown_start != 0:
            myDisplay.number(oilVolume)
            countdown_start = 0

    if lowLevel.value() == 1 and fillButton.value() == 1:
        print("Pump Engaged")
        engagePump()
