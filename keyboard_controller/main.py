# import time
# from evdev import UInput, ecodes

# # Define the precise capabilities of a PlayStation controller
# cap = {
#     # Digital Buttons
#     ecodes.EV_KEY: [
#         ecodes.BTN_SOUTH,   # Cross (X)
#         ecodes.BTN_EAST,    # Circle
#         ecodes.BTN_NORTH,   # Triangle
#         ecodes.BTN_WEST,    # Square
#         ecodes.BTN_TL,      # L1 Shoulder
#         ecodes.BTN_TR,      # R1 Shoulder
#         ecodes.BTN_SELECT,  # Share / Create
#         ecodes.BTN_START,   # Options
#         ecodes.BTN_MODE,    # PS Button
#         ecodes.BTN_THUMBL,  # L3 (Left Stick Click)
#         ecodes.BTN_THUMBR,  # R3 (Right Stick Click)
#     ],
#     # Analog Sticks, Triggers, and D-Pad
#     ecodes.EV_ABS: [
#         # (code, AbsInfo(value, min, max, fuzz, flat, resolution))
#         (ecodes.ABS_X, (128, 0, 255, 0, 0, 0)),      # Left Stick X (Center 128)
#         (ecodes.ABS_Y, (128, 0, 255, 0, 0, 0)),      # Left Stick Y (Center 128)
#         (ecodes.ABS_Z, (128, 0, 255, 0, 0, 0)),      # Right Stick X (Center 128)
#         (ecodes.ABS_RZ, (128, 0, 255, 0, 0, 0)),     # Right Stick Y (Center 128)
#         (ecodes.ABS_GAS, (0, 0, 255, 0, 0, 0)),      # R2 Trigger (Range 0-255)
#         (ecodes.ABS_BRAKE, (0, 0, 255, 0, 0, 0)),    # L2 Trigger (Range 0-255)
#         (ecodes.ABS_HAT0X, (0, -1, 1, 0, 0, 0)),     # D-Pad Left (-1) / Right (1)
#         (ecodes.ABS_HAT0Y, (0, -1, 1, 0, 0, 0)),     # D-Pad Up (-1) / Down (1)
#     ]
# }

# # Create the virtual PlayStation gamepad device
# with UInput(cap, name="Sony Interactive Entertainment Wireless Controller", vendor=0x054c, product=0x0ce6, version=0x111) as ui:
#     print(f"Virtual controller created: {ui}")
#     time.sleep(1) # Allow system to register device

#     while True:
#     #     print("Simulating pressing start then select (back) button...")
#     #     ui.write(ecodes.EV_KEY, ecodes.BTN_START, 1)  # 1 = Press
#     #     ui.syn()                                      # Sync event
#     #     time.sleep(0.1)
#     #     ui.write(ecodes.EV_KEY, ecodes.BTN_SELECT, 0)  # 0 = Release
#     #     ui.syn()

#         time.sleep(5)
#         print("Simulating moving Left Stick fully right...")
#         ui.write(ecodes.EV_ABS, ecodes.ABS_X, 255)    # 255 = Full right
#         ui.syn()
#         time.sleep(0.5)
#         ui.write(ecodes.EV_ABS, ecodes.ABS_Y, 255)    # 128 = Centered
#         ui.syn()



#!/usr/bin/env python3

from evdev import UInput, ecodes as e
from evdev import ecodes

import sys
import tty
import termios

# Create a virtual gamepad
# capabilities = {
#     e.EV_KEY: [
#         e.BTN_SOUTH,   # A
#         e.BTN_EAST,    # B
#         e.BTN_NORTH,   # X
#         e.BTN_WEST,    # Y
#         e.BTN_TL,
#         e.BTN_TR,
#         e.BTN_SELECT,
#         e.BTN_START,
#     ],
#     e.EV_ABS: [
#         (e.ABS_X, (-32768, 32767, 0, 0)),
#         (e.ABS_Y, (-32768, 32767, 0, 0)),
#     ],
# }
cap = {
    # Digital Buttons
    ecodes.EV_KEY: [
        ecodes.BTN_SOUTH,   # Cross (X)
        ecodes.BTN_EAST,    # Circle
        ecodes.BTN_NORTH,   # Triangle
        ecodes.BTN_WEST,    # Square
        ecodes.BTN_TL,      # L1 Shoulder
        ecodes.BTN_TR,      # R1 Shoulder
        ecodes.BTN_SELECT,  # Share / Create
        ecodes.BTN_START,   # Options
        ecodes.BTN_MODE,    # PS Button
        ecodes.BTN_THUMBL,  # L3 (Left Stick Click)
        ecodes.BTN_THUMBR,  # R3 (Right Stick Click)
    ],
    # Analog Sticks, Triggers, and D-Pad
    ecodes.EV_ABS: [
        # (code, AbsInfo(value, min, max, fuzz, flat, resolution))
        (ecodes.ABS_X, (128, 0, 255, 0, 0, 0)),      # Left Stick X (Center 128)
        (ecodes.ABS_Y, (128, 0, 255, 0, 0, 0)),      # Left Stick Y (Center 128)
        (ecodes.ABS_Z, (128, 0, 255, 0, 0, 0)),      # Right Stick X (Center 128)
        (ecodes.ABS_RZ, (128, 0, 255, 0, 0, 0)),     # Right Stick Y (Center 128)
        (ecodes.ABS_GAS, (0, 0, 255, 0, 0, 0)),      # R2 Trigger (Range 0-255)
        (ecodes.ABS_BRAKE, (0, 0, 255, 0, 0, 0)),    # L2 Trigger (Range 0-255)
        (ecodes.ABS_HAT0X, (0, -1, 1, 0, 0, 0)),     # D-Pad Left (-1) / Right (1)
        (ecodes.ABS_HAT0Y, (0, -1, 1, 0, 0, 0)),     # D-Pad Up (-1) / Down (1)
    ]
}

ui = UInput(cap, name="Virtual Gamepad", vendor=0x054c, product=0x0ce6, version=0x111)

fd = sys.stdin.fileno()
old = termios.tcgetattr(fd)
tty.setcbreak(fd)

print("Virtual gamepad created.")
print("Controls:")
print("  WASD = Left Stick")
print("  J = A")
print("  K = B")
print("  U = X")
print("  I = Y")
print("  Q = Quit")

# Current stick position
x = 0
y = 0

KEYMAP = {
    "j": e.BTN_SOUTH,
    "k": e.BTN_EAST,
    "u": e.BTN_NORTH,
    "i": e.BTN_WEST,
}

try:
    while True:
        c = sys.stdin.read(1)

        if c == "q":
            break

        # Reset stick
        x = 0
        y = 0

        if c == "a":
            x = -32768
        elif c == "d":
            x = 32767
        elif c == "w":
            y = -32768
        elif c == "s":
            y = 32767

        ui.write(e.EV_ABS, e.ABS_X, x)
        ui.write(e.EV_ABS, e.ABS_Y, y)

        if c in KEYMAP:
            button = KEYMAP[c]
            ui.write(e.EV_KEY, button, 1)
            ui.syn()
            ui.write(e.EV_KEY, button, 0)

        ui.syn()

finally:
    termios.tcsetattr(fd, termios.TCSADRAIN, old)
    ui.close()