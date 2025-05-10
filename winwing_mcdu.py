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
#  * CLR in textbox does not update, special handling necessary
#  * no colors
#  * show vertslew_key

BUTTONS_CNT = 99 # TODO
PAGE_LINES = 14 # Header + 6 * label + 6 * cont + textbox
PAGE_CHARS_PER_LINE = 25
PAGE_BYTES_PER_CHAR = 2
PAGE_BYTEs_PER_LINE = PAGE_CHARS_PER_LINE * PAGE_BYTES_PER_CHAR

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


class BUTTON(Enum):
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


class DREF_TYPE(Enum):
    DATA = 0
    CMD = 1
    NONE = 2 # for testing


class Button:
    def __init__(self, nr, label, dataref = None, dreftype = DREF_TYPE.DATA, button_type = BUTTON.NONE, led = None):
        self.id = nr
        self.label = label
        self.dataref = dataref
        self.dreftype = dreftype
        self.type = button_type
        self.led = led

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


flags = dict([("spd", Flag('spd-mach_spd', Byte.H0, 0x01)),
              ])


def winwing_mcdu_set_leds(ep, leds, brightness):
    if isinstance(leds, list):
        for i in range(len(leds)):
            winwing_mcdu_set_led(ep, leds[i], brightness)
    else:
        winwing_mcdu_set_led(ep, leds, brightness)

def winwing_mcdu_set_led(ep, led, brightness):
    data = [0x02, 0x10, 0xbb, 0, 0, 3, 0x49, led.value, brightness, 0,0,0,0,0]
    if 'data' in locals():
      cmd = bytes(data)
      ep.write(cmd)


def lcd_init(ep):
    return # TODO
    data = [0xf0, 0x2, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0] # init packet
    cmd = bytes(data)
    ep.write(cmd)


def winwing_mcdu_set_lcd(ep, speed, heading, alt, vs):
    global usb_retry
    return # TODO
    #s = data_from_string( 3, string_fix_length(speed, 3))

    #bl = [0] * len(Byte)
    #for f in flags:
    #    bl[flags[f].byte.value] |= (flags[f].mask * flags[f].value)

    #pkg_nr = 1
    #data = [0xf0, 0x0, pkg_nr, 0x31, 0x10, 0xbb, 0x0, 0x0, 0x2, 0x1, 0x0, 0x0, 0xff, 0xff, 0x2, 0x0, 0x0, 0x20, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, s[2], s[1] | bl[Byte.S1.value], s[0], h[3] | bl[Byte.H3.value], h[2], h[1], h[0] | bl[Byte.H0.value], a[5] | bl[Byte.A5.value], a[4] | bl[Byte.A4.value], a[3] | bl[Byte.A3.value], a[2] | bl[Byte.A2.value], a[1] | bl[Byte.A1.value], a[0] | v[4] | bl[Byte.A0.value], v[3] | bl[Byte.V3.value], v[2] | bl[Byte.V2.value], v[1] | bl[Byte.V1.value], v[0] | bl[Byte.V0.value], 0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]
    #cmd = bytes(data)
    try:
        ep.write(cmd)
    except Exception as error:
        usb_retry = True
        print(f"error in write data: {error}")

    data = [0xf0, 0x0, pkg_nr, 0x11, 0x10, 0xbb, 0x0, 0x0, 0x3, 0x1, 0x0, 0x0, 0xff, 0xff, 0x2, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]
    cmd = bytes(data)
    try:
        ep.write(cmd)
        usb_retry = False
    except Exception as error:
        usb_retry = True
        print(f"error in commit data: {error}")


mcdu_device = None # usb /dev/inputx device

datacache = {}

# List of datarefs without led connection to request.
# Text Dataref format:  <MCDU[1,2]><Line[title/label/cont/etc]><Linenumber[1...6]><Color[a,b,m,s,w,y]>.
# We must read all 25 Bytes per dataref!
datarefs = [
    #("AirbusFBW/MCDU1titleb", 2),
    ("AirbusFBW/MCDU1titleg", 2),
    ("AirbusFBW/MCDU1titles", 2),
    ("AirbusFBW/MCDU1titlew", 2),
    #("AirbusFBW/MCDU1titley", 2),
    ("AirbusFBW/MCDU1stitley", 2),
    ("AirbusFBW/MCDU1stitlew", 2),
    ("AirbusFBW/MCDU1label1w", 2), # missing b,m,s
    ("AirbusFBW/MCDU1label2w", 2),
    ("AirbusFBW/MCDU1label3w", 2),
    ("AirbusFBW/MCDU1label4w", 2),
    ("AirbusFBW/MCDU1label5w", 2),
    ("AirbusFBW/MCDU1label6w", 2),
    #("AirbusFBW/MCDU1label1a", 2),
    ("AirbusFBW/MCDU1label2a", 2),
    #("AirbusFBW/MCDU1label3a", 2),
    #("AirbusFBW/MCDU1label4a", 2),
    #("AirbusFBW/MCDU1label5a", 2),
    ("AirbusFBW/MCDU1label6a", 2),
    #("AirbusFBW/MCDU1label1g", 2),
    #("AirbusFBW/MCDU1label2g", 2),
    ("AirbusFBW/MCDU1label3g", 2),
    ("AirbusFBW/MCDU1label4g", 2),
    ("AirbusFBW/MCDU1label5g", 2),
    #("AirbusFBW/MCDU1label6g", 2),
    #("AirbusFBW/MCDU1label1b", 2),
    #("AirbusFBW/MCDU1label2b", 2),
    ("AirbusFBW/MCDU1label3b", 2),
    ("AirbusFBW/MCDU1label4b", 2),
    ("AirbusFBW/MCDU1label5b", 2),
    ("AirbusFBW/MCDU1label6b", 2),
    ("AirbusFBW/MCDU1cont1b", 2), # missing none
    ("AirbusFBW/MCDU1cont2b", 2),
    ("AirbusFBW/MCDU1cont3b", 2),
    ("AirbusFBW/MCDU1cont4b", 2),
    ("AirbusFBW/MCDU1cont5b", 2),
    ("AirbusFBW/MCDU1cont6b", 2),
    ("AirbusFBW/MCDU1cont1m", 2),
    #("AirbusFBW/MCDU1cont2m", 2),
    #("AirbusFBW/MCDU1cont3m", 2),
    #("AirbusFBW/MCDU1cont4m", 2),
    #("AirbusFBW/MCDU1cont5m", 2),
    #("AirbusFBW/MCDU1cont6m", 2),
    ("AirbusFBW/MCDU1scont1m", 2),
    ("AirbusFBW/MCDU1scont2m", 2),
    ("AirbusFBW/MCDU1scont3m", 2),
    ("AirbusFBW/MCDU1scont4m", 2),
    ("AirbusFBW/MCDU1scont5m", 2),
    ("AirbusFBW/MCDU1scont6m", 2),
    #("AirbusFBW/MCDU1cont1a", 2),
    ("AirbusFBW/MCDU1cont2a", 2),
    #("AirbusFBW/MCDU1cont3a", 2),
    ("AirbusFBW/MCDU1cont4a", 2),
    #("AirbusFBW/MCDU1cont5a", 2),
    ("AirbusFBW/MCDU1cont6a", 2),
    #("AirbusFBW/MCDU1scont1a", 2),
    #("AirbusFBW/MCDU1scont2a", 2),
    #("AirbusFBW/MCDU1scont3a", 2),
    #("AirbusFBW/MCDU1scont4a", 2),
    #("AirbusFBW/MCDU1scont5a", 2),
    ("AirbusFBW/MCDU1scont6a", 2),
    ("AirbusFBW/MCDU1cont1w", 2),
    ("AirbusFBW/MCDU1cont2w", 2),
    ("AirbusFBW/MCDU1cont3w", 2),
    ("AirbusFBW/MCDU1cont4w", 2),
    ("AirbusFBW/MCDU1cont5w", 2),
    ("AirbusFBW/MCDU1cont6w", 2),
    ("AirbusFBW/MCDU1cont1g", 2),
    ("AirbusFBW/MCDU1cont2g", 2),
    ("AirbusFBW/MCDU1cont3g", 2),
    ("AirbusFBW/MCDU1cont4g", 2),
    ("AirbusFBW/MCDU1cont5g", 2),
    ("AirbusFBW/MCDU1cont6g", 2),
    ("AirbusFBW/MCDU1scont1g", 2),
    ("AirbusFBW/MCDU1scont2g", 2),
    ("AirbusFBW/MCDU1scont3g", 2),
    #("AirbusFBW/MCDU1scont4g", 2),
    ("AirbusFBW/MCDU1scont5g", 2),
    ("AirbusFBW/MCDU1scont6g", 2),
    ("AirbusFBW/MCDU1cont1s", 2),
    ("AirbusFBW/MCDU1cont2s", 2),
    ("AirbusFBW/MCDU1cont3s", 2),
    ("AirbusFBW/MCDU1cont4s", 2),
    ("AirbusFBW/MCDU1cont5s", 2),
    ("AirbusFBW/MCDU1cont6s", 2),
    ("AirbusFBW/MCDU1scont1b", 2),
    ("AirbusFBW/MCDU1scont2b", 2),
    ("AirbusFBW/MCDU1scont3b", 2),
    ("AirbusFBW/MCDU1scont4b", 2),
    ("AirbusFBW/MCDU1scont5b", 2),
    ("AirbusFBW/MCDU1scont6b", 2),
    ("AirbusFBW/MCDU1cont1y", 2),
    ("AirbusFBW/MCDU1cont2y", 2),
    ("AirbusFBW/MCDU1cont3y", 2),
    ("AirbusFBW/MCDU1cont4y", 2),
    ("AirbusFBW/MCDU1cont5y", 2),
    ("AirbusFBW/MCDU1cont6y", 2),
    ("AirbusFBW/MCDU1scont1w", 2),
    ("AirbusFBW/MCDU1scont2w", 2),
    ("AirbusFBW/MCDU1scont3w", 2),
    ("AirbusFBW/MCDU1scont4w", 2),
    ("AirbusFBW/MCDU1scont5w", 2),
    #("AirbusFBW/MCDU1scont6w", 2),
    ("AirbusFBW/MCDU1scont1y", 2),
    ("AirbusFBW/MCDU1scont2y", 2),
    ("AirbusFBW/MCDU1scont3y", 2),
    #("AirbusFBW/MCDU1scont4y", 2),
    #("AirbusFBW/MCDU1scont5y", 2),
    #("AirbusFBW/MCDU1scont6y", 2),
    ("AirbusFBW/MCDU1spw", 2), # textbox
    ("AirbusFBW/MCDU1VertSlewKeys", 2)
  ]


buttons_press_event = [0] * BUTTONS_CNT
buttons_release_event = [0] * BUTTONS_CNT

mcdu_out_endpoint = None
mcdu_in_endpoint = None

usb_retry = False

xp = None


def create_button_list_mcdu():
    buttonlist.append(Button(0, "LSK1L", "AirbusFBW/MCDU1LSK1L", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(1, "LSK2L", "AirbusFBW/MCDU1LSK2L", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(2, "LSK3L", "AirbusFBW/MCDU1LSK3L", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(3, "LSK4L", "AirbusFBW/MCDU1LSK4L", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(4, "LSK5L", "AirbusFBW/MCDU1LSK5L", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(5, "LSK6L", "AirbusFBW/MCDU1LSK6L", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(6, "LSK1R", "AirbusFBW/MCDU1LSK1R", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(7, "LSK2R", "AirbusFBW/MCDU1LSK2R", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(8, "LSK3R", "AirbusFBW/MCDU1LSK3R", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(9, "LSK4R", "AirbusFBW/MCDU1LSK4R", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(10, "LSK5R", "AirbusFBW/MCDU1LSK5R", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(11, "LSK6R", "AirbusFBW/MCDU1LSK6R", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(12, "INIT", "AirbusFBW/MCDU1Init", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(13, "DATA", "AirbusFBW/MCDU1Data", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(14, "INIT", "AirbusFBW/MCDU1Menu", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(15, "PERF", "AirbusFBW/MCDU1Perf", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(16, "PROG", "AirbusFBW/MCDU1Prog", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(17, "FPLN", "AirbusFBW/MCDU1Fpln", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(18, "DIRTO", "AirbusFBW/MCDU1DirTo", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(19, "RADNAV", "AirbusFBW/MCDU1RadNav", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(20, "AIRPORT", "AirbusFBW/MCDU1Airport", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(21, "FUEL", "AirbusFBW/MCDU1", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(22, "SEC-FPLN", "AirbusFBW/MCDU1", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(23, "SLASH", "AirbusFBW/MCDU1KeySlash", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(24, "SPACE", "AirbusFBW/MCDU1KeySpace", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(25, "OVERFLY", "AirbusFBW/MCDU1KeyOverfly", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(26, "Clear", "AirbusFBW/MCDU1KeyClear", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(26, "PLUSMINUS", "AirbusFBW/MCDU1KeyPM", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(27, "DOT", "AirbusFBW/MCDU1KeyDecimal", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(28, "KEY0", "AirbusFBW/MCDU1Key0", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(29, "KEY1", "AirbusFBW/MCDU1Key1", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(30, "KEY2", "AirbusFBW/MCDU1Key2", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(31, "KEY3", "AirbusFBW/MCDU1Key3", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(32, "KEY4", "AirbusFBW/MCDU1Key4", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(33, "KEY5", "AirbusFBW/MCDU1Key5", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(34, "KEY6", "AirbusFBW/MCDU1Key6", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(35, "KEY7", "AirbusFBW/MCDU1Key7", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(36, "KEY8", "AirbusFBW/MCDU1Key8", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(37, "KEY9", "AirbusFBW/MCDU1Key9", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(38, "KEYA", "AirbusFBW/MCDU1KeyA", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(39, "KEYB", "AirbusFBW/MCDU1KeyB", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(40, "KEYC", "AirbusFBW/MCDU1KeyC", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(41, "KEYD", "AirbusFBW/MCDU1KeyD", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(42, "KEYE", "AirbusFBW/MCDU1KeyE", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(43, "KEYF", "AirbusFBW/MCDU1KeyF", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(44, "KEYG", "AirbusFBW/MCDU1KeyG", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(45, "KEYH", "AirbusFBW/MCDU1KeyH", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(46, "KEYI", "AirbusFBW/MCDU1KeyI", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(47, "KEYJ", "AirbusFBW/MCDU1KeyJ", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(48, "KEYK", "AirbusFBW/MCDU1KeyK", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(49, "KEYL", "AirbusFBW/MCDU1KeyL", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(50, "KEYM", "AirbusFBW/MCDU1KeyM", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(51, "KEYN", "AirbusFBW/MCDU1KeyN", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(52, "KEYO", "AirbusFBW/MCDU1KeyO", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(53, "KEYP", "AirbusFBW/MCDU1KeyP", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(54, "KEYQ", "AirbusFBW/MCDU1KeyQ", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(55, "KEYR", "AirbusFBW/MCDU1KeyR", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(56, "KEYS", "AirbusFBW/MCDU1KeyS", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(57, "KEYT", "AirbusFBW/MCDU1KeyT", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(58, "KEYU", "AirbusFBW/MCDU1KeyU", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(59, "KEYV", "AirbusFBW/MCDU1KeyV", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(60, "KEYW", "AirbusFBW/MCDU1KeyW", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(61, "KEYX", "AirbusFBW/MCDU1KeyX", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(62, "KEYY", "AirbusFBW/MCDU1KeyY", DREF_TYPE.CMD, BUTTON.TOGGLE))
    buttonlist.append(Button(63, "KEYZ", "AirbusFBW/MCDU1KeyZ", DREF_TYPE.CMD, BUTTON.TOGGLE))


def RequestDataRefs(xp):
    dataref_cnt = 0
    for idx,b in enumerate(buttonlist):
        datacache[b.dataref] = None
        if b.dreftype != DREF_TYPE.CMD and b.led != None:
            print(f"register dataref {b.dataref}")
            xp.AddDataRef(b.dataref, 3)
            dataref_cnt += 1
    for d in datarefs:
        print(f"register dataref {d[0]}")
        #for i in range(PAGE_CHARS_PER_LINE - 1, -1, -1): # registering backward gives us better options to detect line ending, it is on the first message
        for i in range(PAGE_CHARS_PER_LINE):
            #datacache[d[0]] = None
            xp.AddDataRef(d[0]+'['+str(i)+']', d[1])
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
            if b.type == BUTTON.TOGGLE:
                val = datacache[b.dataref]
                if b.dreftype== DREF_TYPE.DATA:
                    print(f'set dataref {b.dataref} from {bool(val)} to {not bool(val)}')
                    xp.WriteDataRef(b.dataref, not bool(val))
                elif b.dreftype== DREF_TYPE.CMD:
                    print(f'send command {b.dataref}')
                    xp.SendCommand(b.dataref)
            elif b.type == BUTTON.SWITCH:
                val = datacache[b.dataref]
                if b.dreftype== DREF_TYPE.DATA:
                    print(f'set dataref {b.dataref} to 1')
                    xp.WriteDataRef(b.dataref, 1)
                elif b.dreftype== DREF_TYPE.CMD:
                    print(f'send command {b.dataref}')
                    xp.SendCommand(b.dataref)
            elif b.type == BUTTON.SEND_0:
                if b.dreftype== DREF_TYPE.DATA:
                    print(f'set dataref {b.dataref} to 0')
                    xp.WriteDataRef(b.dataref, 0)
            elif b.type == BUTTON.SEND_1:
                if b.dreftype== DREF_TYPE.DATA:
                    print(f'set dataref {b.dataref} to 1')
                    xp.WriteDataRef(b.dataref, 1)
            elif b.type == BUTTON.SEND_2:
                if b.dreftype== DREF_TYPE.DATA:
                    print(f'set dataref {b.dataref} to 2')
                    xp.WriteDataRef(b.dataref, 2)
            elif b.type == BUTTON.SEND_3:
                if b.dreftype== DREF_TYPE.DATA:
                    print(f'set dataref {b.dataref} to 3')
                    xp.WriteDataRef(b.dataref, 3)
            elif b.type == BUTTON.SEND_4:
                if b.dreftype== DREF_TYPE.DATA:
                    print(f'set dataref {b.dataref} to 4')
                    xp.WriteDataRef(b.dataref, 4)
            elif b.type == BUTTON.SEND_5:
                if b.dreftype== DREF_TYPE.DATA:
                    print(f'set dataref {b.dataref} to 5')
                    xp.WriteDataRef(b.dataref, 5)
            else:
                print(f'no known button type for button {b.label}')
        if buttons_release_event[b.id]:
            buttons_release_event[b.id] = 0
            print(f'button {b.label} released')
            if b.type == BUTTON.SWITCH:
                xp.WriteDataRef(b.dataref, 0)


def mcdu_create_events(ep_in, ep_out):
        global values
        sleep(2) # wait for values to be available
        buttons_last = 0
        while True:
            if not xplane_connected: # wait for x-plane
                sleep(1)
                continue

            set_datacache(values)
            values_processed.set()
            sleep(0.005)
            try:
                data_in = ep_in.read(0x81, 105)
            except Exception as error:
                # print(f' *** continue after usb-in error: {error} ***') # TODO
                sleep(0.5) # TODO remove
                continue
            if len(data_in) != 41:
                print(f'rx data count {len(data_in)} not valid')
                continue
            buttons = data_in[1] | (data_in[2] << 8) | (data_in[3] << 16) | (data_in[4] << 24)
            buttons |= (data_in[5] << 64) | (data_in[6] << 72 ) | (data_in[7] << 80) | (data_in[8] << 88)
            buttons |= (data_in[9] << 32) | (data_in[10] << 40 ) | (data_in[11] << 48)# | (data_in[12] << 56)
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


def set_button_led_lcd(dataref, v):
    global led_brightness
    for b in buttonlist:
        if b.dataref == dataref:
            if b.led == None:
                break
            if v >= 255:
                v = 255
            print(f'led: {b.led}, value: {v}')

            winwing_mcdu_set_leds(mcdu_out_endpoint, b.led, int(v))
            if b.led == Leds.BACKLIGHT:
                winwing_mcdu_set_led(mcdu_out_endpoint, Leds.EXPED_YELLOW, int(v))
                print(f'set led brigthness: {b.led}, value: {v}')
                led_brightness = v
            break

page = [list('                                                  ')] * PAGE_LINES
def set_datacache(values):
    #global datacache
    #global exped_led_state
    global page
    #print(f'###')
    new = False
    spw_line_ended = False
    vertslew_key = None
    page_tmp = [list('                                                  ')] * PAGE_LINES
    for v in values:
        pos = 0
        val = int(values[v])
        data_valid = False
        color = v.split('[')[0][-1]
        #print(f"page: v:{v} val:{val},'{chr(val)}', col:{color}")
        if val == 0x20 or (val == 0 and not 'MCDU1spw' in v):
            continue
        #if val == '`':
        #    val = '°'
        if color == 's':
            if chr(val) == 'A': val = 91 # '['
            if chr(val) == 'B': val = 93 # ']'
            if chr(val) == '0': val = 60 # '<', should be a small blue arrow
            if chr(val) == '1': val = 62 # '>', should be a small arrow
            if chr(val) == '2': val = 60 # '<', should be a small white arrow in title
            if chr(val) == '3': val = 62 # '>', should be a small white arrow in title
            if chr(val) == '4': val = 60 # '<', should be a small orange arrow in cont
            if chr(val) == 'E': val = 35 # '#', should be an orange box
            #print(f"page: v:{v} val:{val},'{chr(val)}', col:{color}")
        if "MCDU1title" in v or "MCDU1stitle" in v:
            pos = int(v.split('[')[1].split(']')[0])
            line = 0
            data_valid = True
            #print(f"pos: {pos}, val: {chr(val)}:{val}")
            #newline = page[0][:pos] + list(chr(val)) + page[0][pos+1:]
            #if page[0] != newline:
            #    page[0] = newline
            #    new = True
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
                color = 'S' # symbol
        if "MCDU1VertSlewKeys" in v:
            vertslew_key = val # 1: up/down, 2: up, 3: down TODO show slew key
        pos = pos * 2 # we decode color, char, so 2 entries per displayed char

        # we write all colors in one buffer for now. Maybe we split it later when we know how winwing mcfu handles colors
        if data_valid: # we received all mcdu data from page
            if page_tmp[line][pos] == ' ' or page_tmp[line][pos] == 0: # do not overwrite text, page_tmp always start with empty text
                newline = page_tmp[line][:pos] + list(''.join(str(color))) +list(chr(val)) + page_tmp[line][pos+2:] # set char # todo set color
                page_tmp[line] = newline
                if page[line][pos] != newline[pos]:
                    new = True
            else:
                print(f"do not overwrite line:{line}, pos:{pos}, buf_char:{page_tmp[line][pos]} with char:{val}:'{chr(val)}'")
    if new:
        page = page_tmp.copy()
        print("|------ MCDU SCREEN -----|")
        for i in range(PAGE_LINES):
            s = f" |{''.join(page[i])}"
            s.ljust(PAGE_CHARS_PER_LINE)
            for i in range(PAGE_CHARS_PER_LINE):
                #print(s[i*2+1], end='')
                cprint(s[i*2+1], colorname_from_char(s[i*2]), end='')
            print('|')
        print("|------- COLORS ---------|")
        for i in range(PAGE_LINES):
            s = f"| {''.join(page[i])}"
            s.ljust(PAGE_CHARS_PER_LINE)
            for i in range(PAGE_CHARS_PER_LINE):
                print(s[i*2], end='')
            print('|')
        print("|------------------------|")
        print("")


        #if values[v] != 0:
        #    print(f'cache: v:{v} val:{int(values[v])}')
        #if v == 'AirbusFBW/SupplLightLevelRehostats[0]' and values[v] <= 1:
            # brightness is in 0..1, we need 0..255
        #    values[v] = int(values[v] * 255)
        #if datacache[v] != int(values[v]):
        #    new = True
            #print(f'cache: v:{v} val:{int(values[v])}')
        #    datacache[v] = int(values[v])
        #    set_button_led_lcd(v, int(values[v]))
    if new == True or usb_retry == True:

        if True:
            try: # dataref may not be received already, even when connected
                exped_led_state_desired = datacache['AirbusFBW/APVerticalMode'] >= 112
            except:
                exped_led_state_desired = False

        #winwing_mcdu_set_lcd(mcdu_out_endpoint, speed, heading, alt, vs)
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


def main():
    global xp
    global mcdu_in_endpoint, mcdu_out_endpoint
    global values, xplane_connected
    global device_config

    backend = find_usblib()

    devlist = [{'vid':0x4098, 'pid':0xbb10, 'name':'MCDU', 'mask':DEVICEMASK.MCDU},
               {'vid':0x4098, 'pid':0xbb36, 'name':'MCDU - Captain', 'mask':DEVICEMASK.MCDU | DEVICEMASK.CAP},
               {'vid':0x4098, 'pid':0xbb36, 'name':'MCDU - First Offizer', 'mask':DEVICEMASK.MCDU | DEVICEMASK.FO},
               {'vid':0x4098, 'pid':0xbb36, 'name':'MCDU - Observer', 'mask':DEVICEMASK.MCDU | DEVICEMASK.OBS},
               {'vid':0x4098, 'pid':0xbc1e, 'name':'PFP 3N (not tested)', 'mask':DEVICEMASK.PFP3N},
               {'vid':0x4098, 'pid':0xbc1d, 'name':'PFP 4 (not tested)', 'mask':DEVICEMASK.PFP4},
               {'vid':0x4098, 'pid':0xba01, 'name':'PFP 7 (not tested)', 'mask':DEVICEMASK.PFP7}]

    for d in devlist:
        print(f"now searching for winwing {d['name']} ... ", end='')
        device = usb.core.find(idVendor=d['vid'], idProduct=d['pid'], backend=backend)
        if device is not None:
            print(f"found")
            device_config |= d['mask']
            break
        else:
            print(f"not found")

    if device is None:
        #exit(f"No compatible winwing device found, quit")
        print(f"No compatible winwing device found, quit") # TODO
        mcdu_out_endpoint = None
        mcdu_in_endpoint = None
    else:
        interface = device[0].interfaces()[0]
        if device.is_kernel_driver_active(interface.bInterfaceNumber):
            device.detach_kernel_driver(interface.bInterfaceNumber)
        device.set_configuration()
        endpoints = device[0].interfaces()[0].endpoints()
        mcdu_out_endpoint = endpoints[1]
        mcdu_in_endpoint = endpoints[0]


    print('compatible with X-Plane 11/12 and all Toliss Airbus')

    create_button_list_mcdu()
    datacache['baro_efisr_last'] = None
    datacache['baro_efisl_last'] = None

    
    leds = [Leds.SCREEN_BACKLIGHT]
    #if device_config & DEVICEMASK.EFISR:
    #  leds.append(Leds.EFISR_BACKLIGHT)
    #if device_config & DEVICEMASK.EFISL:
    #  leds.append(Leds.EFISL_BACKLIGHT)

    #winwing_mcdu_set_leds(mcdu_out_endpoint, leds, 180)
    #winwing_mcdu_set_leds(mcdu_out_endpoint, leds, 80)
    #winwing_mcdu_set_lcd(mcdu_out_endpoint, "   ", "   ", "Schen", " lap")
    #TODO set EFISL

    usb_event_thread = Thread(target=mcdu_create_events, args=[mcdu_in_endpoint, mcdu_out_endpoint])
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
