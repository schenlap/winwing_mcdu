#!/usr/bin/env python3

# IP Address of machine running X-Plane. 
UDP_IP = "127.0.0.1"
UDP_PORT = 49000

import binascii
from dataclasses import dataclass
from enum import Enum, IntEnum
import os
import socket
import struct
from termcolor import colored, cprint

#for raw usb
import re
import subprocess

from threading import Thread, Event, Lock
from time import sleep

import usb.core
import usb.backend.libusb1
import usb.util

import XPlaneUdp

# TODOLIST
#  * show vertslew_key

BUTTONS_CNT = 99 # TODO
PAGE_LINES = 14 # Header + 6 * label + 6 * cont + textbox
PAGE_CHARS_PER_LINE = 24
PAGE_BYTES_PER_CHAR = 3
PAGE_BYTES_PER_LINE = PAGE_CHARS_PER_LINE * PAGE_BYTES_PER_CHAR
PAGE_BYTES_PER_PAGE = PAGE_BYTES_PER_LINE * PAGE_LINES

#@unique
class DEVICEMASK(IntEnum):
    NONE =  0
    MCDU =  0x01
    PFP3N = 0x02
    PFP4 =  0x04
    PFP7 =  0x08
    CAP =   0x10
    FO =    0x20
    OBS =   0x40


class ButtonType(Enum):
    SWITCH = 0
    TOGGLE = 1
    SEND_0 = 2
    SEND_1 = 3
    SEND_2 = 4
    SEND_3 = 5
    SEND_4 = 6
    SEND_5 = 7
    NONE = 5 # for testing


class Leds(Enum):
    BACKLIGHT = 0 # 0 .. 255
    SCREEN_BACKLIGHT = 1 # 0 .. 255


class DrefType(Enum):
    DATA = 0
    CMD = 1
    NONE = 2 # for testing


@dataclass
class Button:
    id: int
    label: str
    dataref: str = None
    dreftype: DrefType = DrefType.DATA
    type: ButtonType = ButtonType.NONE
    led: Leds = None

values_processed = Event()
xplane_connected = False
buttonlist = []
values = []

led_brightness = 180

device_config = DEVICEMASK.NONE


class Byte(Enum):
    H0 = 0


@dataclass
class Flag:
    name : str
    byte : Byte
    mask : int
    value : bool = False


#flags = dict([("spd", Flag('spd-mach_spd', Byte.H0, 0x01)),
#              ])


def winwing_mcdu_set_leds(ep, leds, brightness):
    if isinstance(leds, list):
        for i in range(len(leds)):
            winwing_mcdu_set_led(ep, leds[i], brightness)
    else:
        winwing_mcdu_set_led(ep, leds, brightness)

def winwing_mcdu_set_led(ep, led, brightness):
    data = [0x02, 0x32, 0xbb, 0, 0, 3, 0x49, led.value, brightness, 0,0,0,0,0]
    if 'data' in locals():
      cmd = bytes(data)
      ep.write(cmd)



class DisplayManager:
    col_map = {
            'L' : 0x0000, # black with grey background
            'A' : 0x0021, # amber
            'W' : 0x0042, # white
            'B' : 0x0063, # cyan
            'G' : 0x0084, # green
            'M' : 0x00A5, # magenta
            'R' : 0x00C6, # red
            'Y' : 0x00E7, # yellow
            'E' : 0x0108  # grey
    }

    def __init__(self, ep_out):
        self.ep_out = ep_out
        self.page = [[' ' for _ in range(PAGE_BYTES_PER_LINE)] for _ in range(PAGE_LINES)]
        ep_out.write(bytes([0xf0, 0x0, 0x1, 0x38, 0x32, 0xbb, 0x0, 0x0, 0x1e, 0x1, 0x0, 0x0, 0xc4, 0x24, 0xa, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x32, 0xbb, 0x0, 0x0, 0x18, 0x1, 0x0, 0x0, 0xc4, 0x24, 0xa, 0x0, 0x0, 0x8, 0x0, 0x0, 0x0, 0x34, 0x0, 0x18, 0x0, 0xe, 0x0, 0x18, 0x0, 0x32, 0xbb, 0x0, 0x0, 0x19, 0x1, 0x0, 0x0, 0xc4, 0x24, 0xa, 0x0, 0x0, 0xe, 0x0, 0x0, 0x0, 0x0]))
        ep_out.write(bytes([0xf0, 0x0, 0x2, 0x38, 0x0, 0x0, 0x0, 0x1, 0x0, 0x5, 0x0, 0x0, 0x0, 0x2, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x32, 0xbb, 0x0, 0x0, 0x19, 0x1, 0x0, 0x0, 0xc4, 0x24, 0xa, 0x0, 0x0, 0xe, 0x0, 0x0, 0x0, 0x1, 0x0, 0x6, 0x0, 0x0, 0x0, 0x3, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x32, 0xbb, 0x0, 0x0, 0x19, 0x1, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]))
        ep_out.write(bytes([0xf0, 0x0, 0x3, 0x38, 0x76, 0x72, 0x19, 0x0, 0x0, 0xe, 0x0, 0x0, 0x0, 0x2, 0x0, 0x0, 0x0, 0x0, 0xff, 0x4, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x32, 0xbb, 0x0, 0x0, 0x19, 0x1, 0x0, 0x0, 0x76, 0x72, 0x19, 0x0, 0x0, 0xe, 0x0, 0x0, 0x0, 0x2, 0x0, 0x0, 0xa5, 0xff, 0xff, 0x5, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x32, 0xbb, 0x0, 0x0, 0x0, 0x0]))
        ep_out.write(bytes([0xf0, 0x0, 0x4, 0x38, 0x0, 0x0, 0x19, 0x1, 0x0, 0x0, 0x76, 0x72, 0x19, 0x0, 0x0, 0xe, 0x0, 0x0, 0x0, 0x2, 0x0, 0xff, 0xff, 0xff, 0xff, 0x6, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x32, 0xbb, 0x0, 0x0, 0x19, 0x1, 0x0, 0x0, 0x76, 0x72, 0x19, 0x0, 0x0, 0xe, 0x0, 0x0, 0x0, 0x2, 0x0, 0xff, 0xff, 0x0, 0xff, 0x7, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]))
        ep_out.write(bytes([0xf0, 0x0, 0x5, 0x38, 0x0, 0x0, 0x0, 0x0, 0x32, 0xbb, 0x0, 0x0, 0x19, 0x1, 0x0, 0x0, 0x76, 0x72, 0x19, 0x0, 0x0, 0xe, 0x0, 0x0, 0x0, 0x2, 0x0, 0x3d, 0xff, 0x0, 0xff, 0x8, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x32, 0xbb, 0x0, 0x0, 0x19, 0x1, 0x0, 0x0, 0x76, 0x72, 0x19, 0x0, 0x0, 0xe, 0x0, 0x0, 0x0, 0x2, 0x0, 0xff, 0x63, 0x0, 0x0, 0x0, 0x0]))
        ep_out.write(bytes([0xf0, 0x0, 0x6, 0x38, 0xff, 0xff, 0x9, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x32, 0xbb, 0x0, 0x0, 0x19, 0x1, 0x0, 0x0, 0x76, 0x72, 0x19, 0x0, 0x0, 0xe, 0x0, 0x0, 0x0, 0x2, 0x0, 0x0, 0x0, 0xff, 0xff, 0xa, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x32, 0xbb, 0x0, 0x0, 0x19, 0x1, 0x0, 0x0, 0x76, 0x72, 0x19, 0x0, 0x0, 0xe, 0x0, 0x0, 0x0, 0x0, 0x0]))
        ep_out.write(bytes([0xf0, 0x0, 0x7, 0x38, 0x0, 0x0, 0x2, 0x0, 0x0, 0xff, 0xff, 0xff, 0xb, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x32, 0xbb, 0x0, 0x0, 0x19, 0x1, 0x0, 0x0, 0x76, 0x72, 0x19, 0x0, 0x0, 0xe, 0x0, 0x0, 0x0, 0x2, 0x0, 0x42, 0x5c, 0x61, 0xff, 0xc, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x32, 0xbb, 0x0, 0x0, 0x19, 0x1, 0x0, 0x0, 0x76, 0x0, 0x0, 0x0, 0x0]))
        ep_out.write(bytes([0xf0, 0x0, 0x8, 0x38, 0x72, 0x19, 0x0, 0x0, 0xe, 0x0, 0x0, 0x0, 0x2, 0x0, 0x77, 0x77, 0x77, 0xff, 0xd, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x32, 0xbb, 0x0, 0x0, 0x19, 0x1, 0x0, 0x0, 0x76, 0x72, 0x19, 0x0, 0x0, 0xe, 0x0, 0x0, 0x0, 0x2, 0x0, 0x5e, 0x73, 0x79, 0xff, 0xe, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x32, 0xbb, 0x0, 0x0, 0x0, 0x0, 0x0]))
        ep_out.write(bytes([0xf0, 0x0, 0x9, 0x38, 0x0, 0x19, 0x1, 0x0, 0x0, 0x76, 0x72, 0x19, 0x0, 0x0, 0xe, 0x0, 0x0, 0x0, 0x3, 0x0, 0x20, 0x20, 0x20, 0xff, 0xf, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x32, 0xbb, 0x0, 0x0, 0x19, 0x1, 0x0, 0x0, 0x76, 0x72, 0x19, 0x0, 0x0, 0xe, 0x0, 0x0, 0x0, 0x3, 0x0, 0x0, 0xa5, 0xff, 0xff, 0x10, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]))
        ep_out.write(bytes([0xf0, 0x0, 0xa, 0x38, 0x0, 0x0, 0x0, 0x32, 0xbb, 0x0, 0x0, 0x19, 0x1, 0x0, 0x0, 0x76, 0x72, 0x19, 0x0, 0x0, 0xe, 0x0, 0x0, 0x0, 0x3, 0x0, 0xff, 0xff, 0xff, 0xff, 0x11, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x32, 0xbb, 0x0, 0x0, 0x19, 0x1, 0x0, 0x0, 0x76, 0x72, 0x19, 0x0, 0x0, 0xe, 0x0, 0x0, 0x0, 0x3, 0x0, 0xff, 0xff, 0x0, 0x0, 0x0, 0x0, 0x0]))
        ep_out.write(bytes([0xf0, 0x0, 0xb, 0x38, 0xff, 0x12, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x32, 0xbb, 0x0, 0x0, 0x19, 0x1, 0x0, 0x0, 0x76, 0x72, 0x19, 0x0, 0x0, 0xe, 0x0, 0x0, 0x0, 0x3, 0x0, 0x3d, 0xff, 0x0, 0xff, 0x13, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x32, 0xbb, 0x0, 0x0, 0x19, 0x1, 0x0, 0x0, 0x76, 0x72, 0x19, 0x0, 0x0, 0xe, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]))
        ep_out.write(bytes([0xf0, 0x0, 0xc, 0x38, 0x0, 0x3, 0x0, 0xff, 0x63, 0xff, 0xff, 0x14, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x32, 0xbb, 0x0, 0x0, 0x19, 0x1, 0x0, 0x0, 0x76, 0x72, 0x19, 0x0, 0x0, 0xe, 0x0, 0x0, 0x0, 0x3, 0x0, 0x0, 0x0, 0xff, 0xff, 0x15, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x32, 0xbb, 0x0, 0x0, 0x19, 0x1, 0x0, 0x0, 0x76, 0x72, 0x0, 0x0, 0x0, 0x0]))
        ep_out.write(bytes([0xf0, 0x0, 0xd, 0x38, 0x19, 0x0, 0x0, 0xe, 0x0, 0x0, 0x0, 0x3, 0x0, 0x0, 0xff, 0xff, 0xff, 0x16, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x32, 0xbb, 0x0, 0x0, 0x19, 0x1, 0x0, 0x0, 0x76, 0x72, 0x19, 0x0, 0x0, 0xe, 0x0, 0x0, 0x0, 0x3, 0x0, 0x42, 0x5c, 0x61, 0xff, 0x17, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x32, 0xbb, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]))
        ep_out.write(bytes([0xf0, 0x0, 0xe, 0x38, 0x19, 0x1, 0x0, 0x0, 0x76, 0x72, 0x19, 0x0, 0x0, 0xe, 0x0, 0x0, 0x0, 0x3, 0x0, 0x77, 0x77, 0x77, 0xff, 0x18, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x32, 0xbb, 0x0, 0x0, 0x19, 0x1, 0x0, 0x0, 0x76, 0x72, 0x19, 0x0, 0x0, 0xe, 0x0, 0x0, 0x0, 0x3, 0x0, 0x5e, 0x73, 0x79, 0xff, 0x19, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]))
        ep_out.write(bytes([0xf0, 0x0, 0xf, 0x38, 0x0, 0x0, 0x32, 0xbb, 0x0, 0x0, 0x19, 0x1, 0x0, 0x0, 0x76, 0x72, 0x19, 0x0, 0x0, 0xe, 0x0, 0x0, 0x0, 0x4, 0x0, 0x0, 0x0, 0x0, 0x0, 0x1a, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x32, 0xbb, 0x0, 0x0, 0x19, 0x1, 0x0, 0x0, 0x76, 0x72, 0x19, 0x0, 0x0, 0xe, 0x0, 0x0, 0x0, 0x4, 0x0, 0x1, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]))
        ep_out.write(bytes([0xf0, 0x0, 0x10, 0x38, 0x1b, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x32, 0xbb, 0x0, 0x0, 0x19, 0x1, 0x0, 0x0, 0x76, 0x72, 0x19, 0x0, 0x0, 0xe, 0x0, 0x0, 0x0, 0x4, 0x0, 0x2, 0x0, 0x0, 0x0, 0x1c, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x32, 0xbb, 0x0, 0x0, 0x1a, 0x1, 0x0, 0x0, 0x76, 0x72, 0x19, 0x0, 0x0, 0x1, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]))
        ep_out.write(bytes([0xf0, 0x0, 0x11, 0x12, 0x2, 0x32, 0xbb, 0x0, 0x0, 0x1c, 0x1, 0x0, 0x0, 0x76, 0x72, 0x19, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]))

    def clear(self):
        blank_line = [0xf2] + [0x42, 0x00, ord(' ')] * PAGE_CHARS_PER_LINE
        for _ in range(16):
            self.ep_out.write(bytes(blank_line))
        print("LCD cleared")

    def write_line_repeated(self, text: str, repeat: int = 16):
        encoded = [ord(c) for c in text]
        c = 0
        for _ in range(repeat):
            buf = [0xf2]
            for _ in range(21):
                buf.extend([0x42, 0x00, encoded[c]])
                c = (c + 1) % len(encoded)
            self.ep_out.write(bytes(buf))

    def set_from_page(self, page, vertslew_key):
        buf = []
        for i in range(PAGE_LINES):
            for j in range(PAGE_CHARS_PER_LINE):
                color = page[i][j * PAGE_BYTES_PER_CHAR]
                font_small = page[i][j * PAGE_BYTES_PER_CHAR + 1]
                col_winwing = self.col_map.get(color.upper())
                if col_winwing == None:
                    col_winwing = 0x0042
                if font_small == 1:
                    col_winwing = col_winwing + 0x016b
                buf.append(col_winwing & 0x0ff)
                buf.append((col_winwing >> 8) & 0xff)
                val = ord(page[i][j * PAGE_BYTES_PER_CHAR + PAGE_BYTES_PER_CHAR - 1])
                if val == 35: # #
                    buf.extend([0xe2, 0x98, 0x90])
                elif val == 60: # <
                    buf.extend([0xe2, 0x86, 0x90])
                elif val == 62: # >
                    buf.extend([0xe2, 0x86, 0x92])
                elif val == 96: # °
                    buf.extend([0xc2, 0xb0])
                #elif val == "A": # down arrow
                #    buf.extend([0xe2, 0x86, 0x93])
                #elif val == "ö": # up arrow
                #    buf.extend([0xe2, 0x86, 0x91])
                else:
                    if i == PAGE_LINES - 1 and j == PAGE_CHARS_PER_LINE - 2:
                        print(f"vsk: {vertslew_key}")
                    if i == PAGE_LINES - 1 and j == PAGE_CHARS_PER_LINE - 2 and (vertslew_key == 1 or vertslew_key == 2):
                        buf.extend([0xe2, 0x86, 0x91])
                    elif i == PAGE_LINES - 1 and j == PAGE_CHARS_PER_LINE - 1 and (vertslew_key == 1 or vertslew_key == 3):
                        buf.extend([0xe2, 0x86, 0x93])
                    else:
                        buf.append(val)

        while len(buf):
            max_len = min(63, len(buf))
            usb_buf = buf[:max_len]
            usb_buf.insert(0, 0xf2)
            if max_len < 63:
                usb_buf.extend([0] * (63 - max_len))
            self.ep_out.write(bytes(usb_buf))
            del buf[:max_len]

    def write_test(self):
        c = 80
        for j in range(16):
            buf = [0xf2]
            for i in range(3):
                buf.append(0x42)
                buf.append(0x0)
                buf.append(c)

                buf.append(0x42)
                buf.append(0x0)
                buf.append(ord(':'))

                s = '{0:03}'.format(c)
                print(f"c: {c}, s: {s}")
                buf.append(0x42)
                buf.append(0x0)
                buf.append(ord(str(s[0])))
                buf.append(0x42)
                buf.append(0x0)
                buf.append(ord(str(s[1])))
                buf.append(0x42)
                buf.append(0x0)
                buf.append(ord(str(s[2])))
                buf.append(0x42)
                buf.append(0x0)
                buf.append(ord(' '))
                buf.append(0x42)
                buf.append(0x0)
                buf.append(ord(' '))
                c = c + 1
                if c == 255:
                    c = 1
            self.ep_out.write(bytes(buf))


mcdu_device = None # usb /dev/inputx device

datacache = {}

# List of datarefs without led connection to request.
# Text Dataref format:  <MCDU[1,2]><Line[title/label/cont/etc]><Linenumber[1...6]><Color[a,b,m,s,w,y]>.
# We must read all 25 Bytes per dataref!
array_datarefs = [
    #("AirbusFBW/MCDU1titleb", None),
    ("AirbusFBW/MCDU1titleg", None),
    ("AirbusFBW/MCDU1titles", None),
    ("AirbusFBW/MCDU1titlew", None),
    #("AirbusFBW/MCDU1titley", None),
    ("AirbusFBW/MCDU1stitley", None),
    ("AirbusFBW/MCDU1stitlew", None),
    ("AirbusFBW/MCDU1label1w", None),
    ("AirbusFBW/MCDU1label2w", None),
    ("AirbusFBW/MCDU1label3w", None),
    ("AirbusFBW/MCDU1label4w", None),
    ("AirbusFBW/MCDU1label5w", None),
    ("AirbusFBW/MCDU1label6w", None),
    #("AirbusFBW/MCDU1label1a", None),
    ("AirbusFBW/MCDU1label2a", None),
    ("AirbusFBW/MCDU1label3a", None),
    #("AirbusFBW/MCDU1label4a", None),
    #("AirbusFBW/MCDU1label5a", None),
    ("AirbusFBW/MCDU1label6a", None),
    #("AirbusFBW/MCDU1label1g", None),
    ("AirbusFBW/MCDU1label2g", None),
    ("AirbusFBW/MCDU1label3g", None),
    ("AirbusFBW/MCDU1label4g", None),
    ("AirbusFBW/MCDU1label5g", None),
    #("AirbusFBW/MCDU1label6g", None),
    #("AirbusFBW/MCDU1label1b", None),
    #("AirbusFBW/MCDU1label2b", None),
    ("AirbusFBW/MCDU1label3b", None),
    ("AirbusFBW/MCDU1label4b", None),
    ("AirbusFBW/MCDU1label5b", None),
    ("AirbusFBW/MCDU1label6b", None),
    #("AirbusFBW/MCDU1label1y", None),
    #("AirbusFBW/MCDU1label2y", None),
    #("AirbusFBW/MCDU1label3y", None),
    #("AirbusFBW/MCDU1label4y", None),
    #("AirbusFBW/MCDU1label5y", None),
    ("AirbusFBW/MCDU1label6y", None),
    ("AirbusFBW/MCDU1cont1b", None),
    ("AirbusFBW/MCDU1cont2b", None),
    ("AirbusFBW/MCDU1cont3b", None),
    ("AirbusFBW/MCDU1cont4b", None),
    ("AirbusFBW/MCDU1cont5b", None),
    ("AirbusFBW/MCDU1cont6b", None),
    ("AirbusFBW/MCDU1cont1m", None),
    ("AirbusFBW/MCDU1cont2m", None),
    ("AirbusFBW/MCDU1cont3m", None),
    #("AirbusFBW/MCDU1cont4m", None),
    #("AirbusFBW/MCDU1cont5m", None),
    #("AirbusFBW/MCDU1cont6m", None),
    ("AirbusFBW/MCDU1scont1m", None),
    ("AirbusFBW/MCDU1scont2m", None),
    ("AirbusFBW/MCDU1scont3m", None),
    ("AirbusFBW/MCDU1scont4m", None),
    ("AirbusFBW/MCDU1scont5m", None),
    ("AirbusFBW/MCDU1scont6m", None),
    ("AirbusFBW/MCDU1cont1a", None),
    ("AirbusFBW/MCDU1cont2a", None),
    ("AirbusFBW/MCDU1cont3a", None),
    ("AirbusFBW/MCDU1cont4a", None),
    ("AirbusFBW/MCDU1cont5a", None),
    ("AirbusFBW/MCDU1cont6a", None),
    ("AirbusFBW/MCDU1scont1a", None),
    ("AirbusFBW/MCDU1scont2a", None),
    ("AirbusFBW/MCDU1scont3a", None),
    ("AirbusFBW/MCDU1scont4a", None),
    ("AirbusFBW/MCDU1scont5a", None),
    ("AirbusFBW/MCDU1scont6a", None),
    ("AirbusFBW/MCDU1cont1w", None),
    ("AirbusFBW/MCDU1cont2w", None),
    ("AirbusFBW/MCDU1cont3w", None),
    ("AirbusFBW/MCDU1cont4w", None),
    ("AirbusFBW/MCDU1cont5w", None),
    ("AirbusFBW/MCDU1cont6w", None),
    ("AirbusFBW/MCDU1cont1g", None),
    ("AirbusFBW/MCDU1cont2g", None),
    ("AirbusFBW/MCDU1cont3g", None),
    ("AirbusFBW/MCDU1cont4g", None),
    ("AirbusFBW/MCDU1cont5g", None),
    ("AirbusFBW/MCDU1cont6g", None),
    ("AirbusFBW/MCDU1scont1g", None),
    ("AirbusFBW/MCDU1scont2g", None),
    ("AirbusFBW/MCDU1scont3g", None),
    #("AirbusFBW/MCDU1scont4g", None),
    ("AirbusFBW/MCDU1scont5g", None),
    ("AirbusFBW/MCDU1scont6g", None),
    ("AirbusFBW/MCDU1cont1s", None),
    ("AirbusFBW/MCDU1cont2s", None),
    ("AirbusFBW/MCDU1cont3s", None),
    ("AirbusFBW/MCDU1cont4s", None),
    ("AirbusFBW/MCDU1cont5s", None),
    ("AirbusFBW/MCDU1cont6s", None),
    ("AirbusFBW/MCDU1scont1b", None),
    ("AirbusFBW/MCDU1scont2b", None),
    ("AirbusFBW/MCDU1scont3b", None),
    ("AirbusFBW/MCDU1scont4b", None),
    ("AirbusFBW/MCDU1scont5b", None),
    ("AirbusFBW/MCDU1scont6b", None),
    ("AirbusFBW/MCDU1cont1y", None),
    ("AirbusFBW/MCDU1cont2y", None),
    ("AirbusFBW/MCDU1cont3y", None),
    ("AirbusFBW/MCDU1cont4y", None),
    ("AirbusFBW/MCDU1cont5y", None),
    ("AirbusFBW/MCDU1cont6y", None),
    ("AirbusFBW/MCDU1scont1w", None),
    ("AirbusFBW/MCDU1scont2w", None),
    ("AirbusFBW/MCDU1scont3w", None),
    ("AirbusFBW/MCDU1scont4w", None),
    ("AirbusFBW/MCDU1scont5w", None),
    ("AirbusFBW/MCDU1scont6w", None),
    ("AirbusFBW/MCDU1scont1y", None),
    ("AirbusFBW/MCDU1scont2y", None),
    ("AirbusFBW/MCDU1scont3y", None),
    ("AirbusFBW/MCDU1scont4y", None),
    #("AirbusFBW/MCDU1scont5y", None),
    #("AirbusFBW/MCDU1scont6y", None),
    ("AirbusFBW/MCDU1spw", 4) # textbox
  ]

datarefs = [
    ("AirbusFBW/MCDU1VertSlewKeys", None)
  ]

buttons_press_event = [0] * BUTTONS_CNT
buttons_release_event = [0] * BUTTONS_CNT

usb_retry = False

xp = None


def create_button_list_mcdu():
    buttonlist.append(Button(0, "LSK1L", "AirbusFBW/MCDU1LSK1L", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(1, "LSK2L", "AirbusFBW/MCDU1LSK2L", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(2, "LSK3L", "AirbusFBW/MCDU1LSK3L", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(3, "LSK4L", "AirbusFBW/MCDU1LSK4L", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(4, "LSK5L", "AirbusFBW/MCDU1LSK5L", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(5, "LSK6L", "AirbusFBW/MCDU1LSK6L", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(6, "LSK1R", "AirbusFBW/MCDU1LSK1R", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(7, "LSK2R", "AirbusFBW/MCDU1LSK2R", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(8, "LSK3R", "AirbusFBW/MCDU1LSK3R", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(9, "LSK4R", "AirbusFBW/MCDU1LSK4R", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(10, "LSK5R", "AirbusFBW/MCDU1LSK5R", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(11, "LSK6R", "AirbusFBW/MCDU1LSK6R", DrefType.CMD, ButtonType.TOGGLE)) # 0x800
    buttonlist.append(Button(12, "DIRTO", "AirbusFBW/MCDU1DirTo", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(13, "PROG", "AirbusFBW/MCDU1Prog", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(14, "PERF", "AirbusFBW/MCDU1Perf", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(15, "INIT", "AirbusFBW/MCDU1Init", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(16, "DATA", "AirbusFBW/MCDU1Data", DrefType.CMD, ButtonType.TOGGLE))
    #17 empty
    buttonlist.append(Button(18, "BRT", "AirbusFBW/MCDU1KeyBright", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(19, "FPLN", "AirbusFBW/MCDU1Fpln", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(20, "RADNAV", "AirbusFBW/MCDU1RadNav", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(21, "FUEL", "AirbusFBW/MCDU1FuelPred", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(22, "SEC-FPLN", "AirbusFBW/MCDU1SecFpln", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(23, "ATC", "AirbusFBW/MCDU1ATC", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(24, "MENU", "AirbusFBW/MCDU1Menu", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(25, "DIM", "AirbusFBW/MCDU1KeyDim", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(26, "AIRPORT", "AirbusFBW/MCDU1Airport", DrefType.CMD, ButtonType.TOGGLE))
    #27 empty
    buttonlist.append(Button(28, "SLEW_LEFT", "AirbusFBW/MCDU1SlewLeft", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(29, "SLEW_UP", "AirbusFBW/MCDU1SlewUp", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(30, "SLEW_RIGHT", "AirbusFBW/MCDU1SlewRight", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(31, "SLEW_DOWN", "AirbusFBW/MCDU1SlewDown", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(32, "KEY1", "AirbusFBW/MCDU1Key1", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(33, "KEY2", "AirbusFBW/MCDU1Key2", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(34, "KEY3", "AirbusFBW/MCDU1Key3", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(35, "KEY4", "AirbusFBW/MCDU1Key4", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(36, "KEY5", "AirbusFBW/MCDU1Key5", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(37, "KEY6", "AirbusFBW/MCDU1Key6", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(38, "KEY7", "AirbusFBW/MCDU1Key7", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(39, "KEY8", "AirbusFBW/MCDU1Key8", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(40, "KEY9", "AirbusFBW/MCDU1Key9", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(41, "DOT", "AirbusFBW/MCDU1KeyDecimal", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(42, "KEY0", "AirbusFBW/MCDU1Key0", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(43, "PLUSMINUS", "AirbusFBW/MCDU1KeyPM", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(44, "KEYA", "AirbusFBW/MCDU1KeyA", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(45, "KEYB", "AirbusFBW/MCDU1KeyB", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(46, "KEYC", "AirbusFBW/MCDU1KeyC", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(47, "KEYD", "AirbusFBW/MCDU1KeyD", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(48, "KEYE", "AirbusFBW/MCDU1KeyE", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(49, "KEYF", "AirbusFBW/MCDU1KeyF", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(50, "KEYG", "AirbusFBW/MCDU1KeyG", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(51, "KEYH", "AirbusFBW/MCDU1KeyH", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(52, "KEYI", "AirbusFBW/MCDU1KeyI", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(53, "KEYJ", "AirbusFBW/MCDU1KeyJ", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(54, "KEYK", "AirbusFBW/MCDU1KeyK", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(55, "KEYL", "AirbusFBW/MCDU1KeyL", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(56, "KEYM", "AirbusFBW/MCDU1KeyM", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(57, "KEYN", "AirbusFBW/MCDU1KeyN", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(58, "KEYO", "AirbusFBW/MCDU1KeyO", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(59, "KEYP", "AirbusFBW/MCDU1KeyP", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(60, "KEYQ", "AirbusFBW/MCDU1KeyQ", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(61, "KEYR", "AirbusFBW/MCDU1KeyR", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(62, "KEYS", "AirbusFBW/MCDU1KeyS", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(63, "KEYT", "AirbusFBW/MCDU1KeyT", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(64, "KEYU", "AirbusFBW/MCDU1KeyU", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(65, "KEYV", "AirbusFBW/MCDU1KeyV", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(66, "KEYW", "AirbusFBW/MCDU1KeyW", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(67, "KEYX", "AirbusFBW/MCDU1KeyX", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(68, "KEYY", "AirbusFBW/MCDU1KeyY", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(69, "KEYZ", "AirbusFBW/MCDU1KeyZ", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(70, "SLASH", "AirbusFBW/MCDU1KeySlash", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(71, "SPACE", "AirbusFBW/MCDU1KeySpace", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(72, "OVERFLY", "AirbusFBW/MCDU1KeyOverfly", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(73, "Clear", "AirbusFBW/MCDU1KeyClear", DrefType.CMD, ButtonType.TOGGLE))
    buttonlist.append(Button(75, "LCDBright", "AirbusFBW/DUBrightness[6]", DrefType.DATA, ButtonType.NONE, Leds.SCREEN_BACKLIGHT))
    buttonlist.append(Button(75, "Backlight", "ckpt/fped/lights/mainPedLeft/anim", DrefType.DATA, ButtonType.NONE, Leds.BACKLIGHT))


def RequestDataRefs(xp):
    dataref_cnt = 0
    for idx,b in enumerate(buttonlist):
        datacache[b.dataref] = None
        if b.dreftype != DrefType.CMD and b.led != None:
            print(f"register dataref {b.dataref}")
            xp.AddDataRef(b.dataref, 3)
            dataref_cnt += 1
    for d in array_datarefs:
        print(f"register dataref {d[0]}[0..{PAGE_CHARS_PER_LINE-1}]")
        for i in range(PAGE_CHARS_PER_LINE):
            freq = d[1]
            if freq == None:
                freq = 2
            xp.AddDataRef(d[0]+'['+str(i)+']', freq)
            dataref_cnt += 1
    for d in datarefs:
        print(f"register dataref {d[0]}")
        freq = d[1]
        if freq == None:
            freq = 2
        xp.AddDataRef(d[0], freq)
        dataref_cnt += 1
    print(f"registered {dataref_cnt} datarefs")


def xor_bitmask(a, b, bitmask):
    return (a & bitmask) != (b & bitmask)


def mcdu_button_event():
    #print(f'events: press: {buttons_press_event}, release: {buttons_release_event}')
    for b in buttonlist:
        if not any(buttons_press_event) and not any(buttons_release_event):
            break
        if b.id == None:
            continue
        if buttons_press_event[b.id]:
            buttons_press_event[b.id] = 0
            #print(f'button {b.label} pressed')
            if b.type == ButtonType.TOGGLE:
                val = datacache[b.dataref]
                if b.dreftype== DrefType.DATA:
                    print(f'set dataref {b.dataref} from {bool(val)} to {not bool(val)}')
                    xp.WriteDataRef(b.dataref, not bool(val))
                elif b.dreftype== DrefType.CMD:
                    print(f'send command {b.dataref}')
                    xp.SendCommand(b.dataref)
            elif b.type == ButtonType.SWITCH:
                val = datacache[b.dataref]
                if b.dreftype== DrefType.DATA:
                    print(f'set dataref {b.dataref} to 1')
                    xp.WriteDataRef(b.dataref, 1)
                elif b.dreftype== DrefType.CMD:
                    print(f'send command {b.dataref}')
                    xp.SendCommand(b.dataref)
            elif b.type == ButtonType.SEND_0:
                if b.dreftype== DrefType.DATA:
                    print(f'set dataref {b.dataref} to 0')
                    xp.WriteDataRef(b.dataref, 0)
            elif b.type == ButtonType.SEND_1:
                if b.dreftype== DrefType.DATA:
                    print(f'set dataref {b.dataref} to 1')
                    xp.WriteDataRef(b.dataref, 1)
            elif b.type == ButtonType.SEND_2:
                if b.dreftype== DrefType.DATA:
                    print(f'set dataref {b.dataref} to 2')
                    xp.WriteDataRef(b.dataref, 2)
            elif b.type == ButtonType.SEND_3:
                if b.dreftype== DrefType.DATA:
                    print(f'set dataref {b.dataref} to 3')
                    xp.WriteDataRef(b.dataref, 3)
            elif b.type == ButtonType.SEND_4:
                if b.dreftype== DrefType.DATA:
                    print(f'set dataref {b.dataref} to 4')
                    xp.WriteDataRef(b.dataref, 4)
            elif b.type == ButtonType.SEND_5:
                if b.dreftype== DrefType.DATA:
                    print(f'set dataref {b.dataref} to 5')
                    xp.WriteDataRef(b.dataref, 5)
            else:
                print(f'no known button type for button {b.label}')
        if buttons_release_event[b.id]:
            buttons_release_event[b.id] = 0
            print(f'button {b.label} released')
            if b.type == ButtonType.SWITCH:
                xp.WriteDataRef(b.dataref, 0)


def mcdu_create_events(usb_mgr, display_mgr):
        global values
        sleep(2) # wait for values to be available
        buttons_last = 0
        while True:
            if not xplane_connected: # wait for x-plane
                sleep(1)
                continue

            set_datacache(usb_mgr, display_mgr, values.copy())
            values_processed.set()
            sleep(0.005)
            try:
                data_in = usb_mgr.ep_in.read(0x81, 105)
            except Exception as error:
                # print(f' *** continue after usb-in error: {error} ***') # TODO
                sleep(0.5) # TODO remove
                continue
            if len(data_in) != 25:
                print(f'rx data count {len(data_in)} not valid')
                continue
            #print(f"data_in: {data_in}")

            #create button bit-pattern
            buttons = 0
            for i in range(12):
                buttons |= data_in[i + 1] << (8 * i)
            #print(hex(buttons))
            for i in range (BUTTONS_CNT):
                mask = 0x01 << i
                if xor_bitmask(buttons, buttons_last, mask):
                    #print(f"buttons: {format(buttons, "#04x"):^14}")
                    if buttons & mask:
                        buttons_press_event[i] = 1
                    else:
                        buttons_release_event[i] = 1
                    mcdu_button_event()
            buttons_last = buttons


def set_button_led_lcd(ep, dataref, v):
    global led_brightness
    for b in buttonlist:
        if b.dataref == dataref:
            if b.led == None:
                break
            if v >= 255:
                v = 255
            print(f'led: {b.led}, value: {v}')

            winwing_mcdu_set_leds(ep, b.led, int(v))
            break

page = [[' ' for i in range(0, PAGE_BYTES_PER_LINE)] for j in range(0, PAGE_LINES)]

def set_datacache(usb_mgr, display_mgr, values):
    global datacache
    global page
    new = False
    spw_line_ended = False
    vertslew_key = None
    page_tmp = [[' ' for i in range(0, PAGE_BYTES_PER_LINE)] for j in range(0, PAGE_LINES)]
    for v in values:
        pos = 0
        val = int(values[v])
        data_valid = False

        if "DUBrightness" in v and values[v] <= 1:
            # brightness is in 0..1, we need 0..255
            values[v] = int(values[v] * 255)
        if "/anim" in v and values[v] > 255:
            # brightness is in 0..270, we need 0..255
            values[v] = 255

        #write leds ob buttons (also NONE Buttons)
        if "DUBrightness" in v or "/anim" in v:
            if datacache[v] != int(values[v]):
                print(f'cache: v:{v} val:{int(values[v])}')
                datacache[v] = int(values[v])
                set_button_led_lcd(usb_mgr.ep_out, v, int(values[v]))


        color = v.split('[')[0][-1]
        font_small = 1 # 0 .. normal, 1 .. small
        if ('cont' in v and not 'scont' in v) or 'spw' in v:
            font_small = 0 # normal
        #print(f"page: v:{v} val:{val},'{chr(val)}', col:{color}")
        if val == 0x20 or (val == 0 and not 'MCDU1spw' in v):
            continue
        if color == 's':
            if chr(val) == 'A':
                val = 91 # '[', should be blue
                color = 'b'
            if chr(val) == 'B':
                val = 93 # ']', should be blue
                color = 'b'
            if chr(val) == '0':
                val = 60 # '<', should be a small blue arrow
                color = 'b'
            if chr(val) == '1':
                val = 62 # '>', should be a small bluearrow
                color = 'b'
            if chr(val) == '2':
                val = 60 # '<', should be a small white arrow in title
                color = 'w'
            if chr(val) == '3':
                val = 62 # '>', should be a small white arrow in title
                color = 'w'
            if chr(val) == '4':
                val = 60 # '<', should be a small orange arrow in cont
                color = 'a'
            if chr(val) == 'E':
                val = 35 # '#', should be an orange box
                color = 'a'
            #print(f"page: v:{v} val:{val},'{chr(val)}', col:{color}")
        if "MCDU1title" in v or "MCDU1stitle" in v:
            pos = int(v.split('[')[1].split(']')[0])
            line = 0
            data_valid = True
        if "MCDU1label" in v:
            line = int(v.split('label')[1][0]) * 2 - 1
            pos = int(v.split('[')[1].split(']')[0])
            data_valid = True
        if "MCDU1cont" in v or "MCDU1scont" in v: # and color == 'w':
            line = int(v.split('cont')[1][0]) * 2
            pos = int(v.split('[')[1].split(']')[0])
            data_valid = True
        if "MCDU1spw" in v: # and color == 'w':
            line = 13
            pos = int(v.split('[')[1].split(']')[0])
            if val == 0:
                spw_line_ended = True
            if spw_line_ended:
                val = 0x20
            data_valid = True
        else:
            if color == 's':
                color = None
            if "MCDU1s" not in v and color != None:
                color = chr(ord(color) - 32) # convert y in Y, a in A, ... if not small font
            if color == None:
                color = 'm' # symbol
        if "VertSlewKeys" in v:
            vertslew_key = val # 1: up/down, 2: up, 3: down

        pos = pos * PAGE_BYTES_PER_CHAR # we decode color and font (2 bytes) and char(1 byte) = sum 3 bytes per char

        if data_valid: # we received mcdu data
            #if page_tmp[line][pos] == ' ' or page_tmp[line][pos] == 0: # do not overwrite text, page_tmp always start with empty text
                newline = page_tmp[line]
                newline[pos] = str(color)
                if PAGE_BYTES_PER_CHAR == 3:
                    newline[pos + 1] = font_small
                newline[pos + PAGE_BYTES_PER_CHAR - 1] = chr(val)
                page_tmp[line] = newline

                # reset vertslew_key to not trigger an continous redraw
                #page[PAGE_LINES - 1][(PAGE_CHARS_PER_LINE - 2) * PAGE_BYTES_PER_CHAR + PAGE_BYTES_PER_CHAR - 1] = ' '
                #page[PAGE_LINES - 1][(PAGE_CHARS_PER_LINE - 1) * PAGE_BYTES_PER_CHAR + PAGE_BYTES_PER_CHAR - 1] = ' '

                if page[line][pos + PAGE_BYTES_PER_CHAR - 1] != newline[pos + PAGE_BYTES_PER_CHAR - 1]:
                    new = True
            #else:
            #    print(f"do not overwrite line:{line}, pos:{pos}, buf_char:{page_tmp[line][pos]} with char:{val}:'{chr(val)}'")

    #display MCDU in Console
    if new:
        page = page_tmp.copy()
        up = ' '
        down = ' '
        if vertslew_key == 1:
            up = '🠉'
            down = '🠋'
        elif vertslew_key == 2:
            up = '🠉'
        elif vertslew_key == 3:
            down = '🠋'

        # TODO reenable vert slew keys, they make an error in usb write also we do this on a copy only
        #page[PAGE_LINES - 1][(PAGE_CHARS_PER_LINE - 2) * PAGE_BYTES_PER_CHAR + PAGE_BYTES_PER_CHAR - 1] = up
        #page[PAGE_LINES - 1][(PAGE_CHARS_PER_LINE - 1) * PAGE_BYTES_PER_CHAR + PAGE_BYTES_PER_CHAR - 1] = down
        print("|------ MCDU SCREEN -----|")
        for i in range(PAGE_LINES):
            cprint('|', 'white', end='')
            for j in range(PAGE_CHARS_PER_LINE):
                val = page[i][j * PAGE_BYTES_PER_CHAR + PAGE_BYTES_PER_CHAR - 1]
                if val == '#':
                    #val = '▯'
                    val = '☐'
                if val == '`':
                    val = '°'
                if val == '>':
                    val = '🠊'
                if val == '<':
                    val = '🠈'
                cprint(val, colorname_from_char(page[i][j * PAGE_BYTES_PER_CHAR]), end='')
            print('|')
        print("|------- COLORS ---------|")
        for i in range(PAGE_LINES):
            cprint('|', 'white', end='')
            for j in range(PAGE_CHARS_PER_LINE):
                print(page[i][j * PAGE_BYTES_PER_CHAR], end='') # TODO font and color, not just color
            print('|')
        print("|------------------------|")
        print("|-------  FONT  ---------|")
        for i in range(PAGE_LINES):
            cprint('|', 'white', end='')
            for j in range(PAGE_CHARS_PER_LINE):
                print(page[i][j * PAGE_BYTES_PER_CHAR + 1], end='') # TODO font and color, not just color
            print('|')
        print("|------------------------|")
        print("")


    #display mcdu on winwing
    if new == True or usb_retry == True:

        if True:
            #try: # dataref may not be received already, even when connected
            #    exped_led_state_desired = datacache['AirbusFBW/APVerticalMode'] >= 112
            #except:
            #    exped_led_state_desired = False
            display_mgr.set_from_page(page_tmp, vertslew_key)
        sleep(0.05)

        # TODO EFISL

def colorname_from_char(c):
    c = c.lower()
    if c == 'w': return 'white'
    if c == 'b': return 'blue'
    if c == 'c': return 'cyan'
    if c == 'g': return 'green'
    if c == 'a': return 'yellow'
    if c == 'y': return 'light_yellow'
    if c == 'm': return 'magenta'
    if c == 's': return 'white'
    if c == None: return 'white'
    if c == ' ': return 'white'
    print(f"color-code {c} not known")
    return 'white'


def kb_wait_quit_event():
    print(f"*** Press ENTER to quit this script ***\n")
    while True:
        c = input() # wait for ENTER (not worth to implement kbhit for differnt plattforms, so make it very simple)
        print(f"Exit")
        os._exit(0)


def find_usblib():
    path = ['/opt/homebrew/lib/libusb-1.0.0.dylib',
            '/usr/lib/x86_64-linux-gnu/libusb-1.0.so.0',
            '/usr/lib/libusb-1.0.so.0']
    pathlist = list(enumerate(path))
    for p in range(len(pathlist)):
        backend = usb.backend.libusb1.get_backend(find_library=lambda x: pathlist[p][1])
        if backend:
            print(f"using {pathlist[p][1]}")
            return backend

    print(f"*** No usblib found. Install it with:")
    print(f"***   debian: apt install libusb1")
    print(f"***   mac: brew install libusb")
    print(f"***   If you get this warning and mcdu is working, please open an issue at")
    print(f"***   https://github.com/schenlap/winwing_mcdu")
    return None


class UsbManager:
    def __init__(self):
        self.backend = self.find_usb_backend()
        self.device = None
        self.ep_in = None
        self.ep_out = None

    def find_usb_backend(self):
        paths = [
            '/opt/homebrew/lib/libusb-1.0.0.dylib',
            '/usr/lib/x86_64-linux-gnu/libusb-1.0.so.0',
            '/usr/lib/libusb-1.0.so.0'
        ]
        for path in paths:
            backend = usb.backend.libusb1.get_backend(find_library=lambda x: path)
            if backend:
                print(f"Using USB backend: {path}")
                return backend
        raise RuntimeError("No compatible USB backend found")

    def connect_device(self, vid: int, pid: int):
        self.device = usb.core.find(idVendor=vid, idProduct=pid, backend=self.backend)
        if self.device is None:
            raise RuntimeError("Device not found")

        interface = self.device[0].interfaces()[0]
        if self.device.is_kernel_driver_active(interface.bInterfaceNumber):
            self.device.detach_kernel_driver(interface.bInterfaceNumber)
        self.device.set_configuration()

        endpoints = interface.endpoints()
        self.ep_out = endpoints[1]
        self.ep_in = endpoints[0]
        print("Device connected and endpoints assigned.")

    def find_device(self):
        device_config = 0
        devlist = [{'vid':0x4098, 'pid':0xbb10, 'name':'MCDU', 'mask':DEVICEMASK.MCDU},
                   {'vid':0x4098, 'pid':0xbb36, 'name':'MCDU - Captain', 'mask':DEVICEMASK.MCDU | DEVICEMASK.CAP},
                   {'vid':0x4098, 'pid':0xbb36, 'name':'MCDU - First Offizer', 'mask':DEVICEMASK.MCDU | DEVICEMASK.FO},
                   {'vid':0x4098, 'pid':0xbb36, 'name':'MCDU - Observer', 'mask':DEVICEMASK.MCDU | DEVICEMASK.OBS},
                   {'vid':0x4098, 'pid':0xbc1e, 'name':'PFP 3N (not tested)', 'mask':DEVICEMASK.PFP3N},
                   {'vid':0x4098, 'pid':0xbc1d, 'name':'PFP 4 (not tested)', 'mask':DEVICEMASK.PFP4},
                   {'vid':0x4098, 'pid':0xba01, 'name':'PFP 7 (not tested)', 'mask':DEVICEMASK.PFP7}]
        for d in devlist:
            print(f"now searching for winwing {d['name']} ... ", end='')
            device = usb.core.find(idVendor=d['vid'], idProduct=d['pid'], backend=self.backend)
            if device is not None:
                print(f"found")
                device_config |= d['mask']
                return device, d['pid'], device_config
                break
            else:
                print(f"not found")


def main():
    global xp
    global values, xplane_connected
    global device_config

    usb_mgr = UsbManager()
    device, pid, device_config = usb_mgr.find_device()

    if device is None:
        exit(f"No compatible winwing device found, quit")
    else:
        usb_mgr.connect_device(vid=0x4098, pid=pid)

    print('compatible with X-Plane 11/12 and all Toliss Airbus')

    display_mgr = DisplayManager(usb_mgr.ep_out)
    #display_mgr.clear() # triggers pipe error on mac
    #display_mgr.write_line_repeated('www.github.com/schenlap ', 16)

    create_button_list_mcdu()

    #leds = [Leds.SCREEN_BACKLIGHT]
    #winwing_mcdu_set_leds(usb_mgr.ep_out, leds, 100)

    usb_event_thread = Thread(target=mcdu_create_events, args=[usb_mgr, display_mgr])
    usb_event_thread.start()

    kb_quit_event_thread = Thread(target=kb_wait_quit_event)
    kb_quit_event_thread.start()

    xp = XPlaneUdp.XPlaneUdp()
    xp.BeaconData["IP"] = UDP_IP # workaround to set IP and port
    xp.BeaconData["Port"] = UDP_PORT
    xp.UDP_PORT = xp.BeaconData["Port"]
    print(f'wait for X-Plane to connect on port {xp.BeaconData["Port"]}')

    while True:
        if not xplane_connected:
            try:
                xp.AddDataRef("sim/aircraft/view/acf_tailnum")
                values = xp.GetValues()
                xplane_connected = True
                print(f"X-Plane connected")
                RequestDataRefs(xp)
                xp.AddDataRef("sim/aircraft/view/acf_tailnum", 0)
            except XPlaneUdp.XPlaneTimeout:
                xplane_connected = False
                sleep(2)
                print(f"wait for X-Plane")
            continue

        try:
            values = xp.GetValues()
            values_processed.wait()
            #print(values)
            #values will be handled in mcdu_create_events to write to usb only in one thread.
            # see function set_datacache(values)
        except XPlaneUdp.XPlaneTimeout:
            print(f'X-Plane timeout, could not connect on port {xp.BeaconData["Port"]}')
            xplane_connected = False
            sleep(2)

if __name__ == '__main__':
  main() 
