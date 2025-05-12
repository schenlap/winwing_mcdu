# winwing_mcdu
Use winwing mcdu on Linuc and Mac for X-Plane Toliss Airbus.

## Status
The scripts fetsches all necessery data from mcdu and displays a mcdu unit in the console and prints all text on winwing mcdu. 
It is only useable as pilot-mcdu now.


![mcdu demo image](./documentation/A319MCDU1.jpg)
```
|------ MCDU SCREEN -----|
|          INIT        <>|
| CO RTE        FROM/TO  |
|##########     #### ####|
|ALTN/CO RTE             |
|----/----------         |
|FLT NBR                 |
|########                |
|LAT                 LONG|
|----.-          -----.--|
|COST INDEX              |
|---                WIND>|
|CRZ FL/TEMP       TROPO |
|-----/---`         36090|
|                        |
|------- COLORS ---------|
|          WWWW        SS|
| WW WWW        WWWWWWW  |
|SSSSSSSSSS     SSSS SSSS|
|WWWWWWW WWW             |
|WWWWWWWWWWWWWWW         |
|WWW WWW                 |
|SSSSSSSS                |
|WWW                 WWWW|
|WWWWWW          WWWWWWWW|
|WWWW WWWWW              |
|WWW                WWWWW|
|WWW WWWWWWW       WWWWW |
|WWWWWWWWWW         bbbbb|
|                        |
|------------------------|
```

## Installation

#### Debian based system
1. clone the repo where you want
2. copy `udev/71-winwing.rules` to `/etc/udev/rules.d`  
`sudo cp udev/71-winwing.rules /etc/udev/rules.d/`
3. install dependencies (on debian based systems)  
`sudo aptitude install python3-usb`
4. start script (with udev rule no sudo needed): `python3 ./winwing_mcdu.py` when X-Plane with Toliss aircraft is loaded.


#### MAC-OS

1. clone the repo where you want
2. install homebrew
3. install dependencies
`python3 -m pip install pyusb`
4. brew install libusb
5. let pyusb find libusb: `ln -s /opt/homebrew/lib ~/lib` 
6. start script with sudo: `sudo python3 ./winwing_mcdu.py` when X-Plane with Toliss aircraft is loaded.
7. A detailed installation instruction can be found on [x-plane forum](https://forums.x-plane.org/index.php?/forums/topic/310045-winwing-fcu-on-plane-12-on-a-mac-studio/&do=findComment&comment=2798635).

## Use FCU
1. start X-Plane
2. load Toliss A319
3. start script as written above
4. enjoy flying (and report bugs :-)  )


## developer documentation
See [documention](./documentation/README.md) for developers. TODO

## Notes
Use at your own risk. Updates to the MCDU can make the script incompatible.
TODO: The data sent in the USB protocol by SimApp Pro has not yet been fully implemented, only to the extent that it currently works.

## Next steps
 * TODO 

## Contact
<memo_5_@gmx.at> (without the two underscores!) or as pm in https://forums.x-plane.org, user memo5.

## Sponsoring
To sponsor you can ![buy_me_a_coffee](https://github.com/user-attachments/assets/d0a94d75-9ad3-41e4-8b89-876c0a2fdf36)
[http://buymeacoffee.com/schenlap](http://buymeacoffee.com/schenlap)
