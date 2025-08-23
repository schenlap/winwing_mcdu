**This project is no longer maintained.** The successor https://github.com/schenlap/XSchenFly combines all devices into one script.

# winwing_mcdu
Use winwing mcdu on Linuc and Mac for X-Plane Toliss Airbus.

## Status
The scripts fetsches all necessery data from mcdu and displays a mcdu unit in the console and prints all text on winwing mcdu. 
From V1.4 on, the scripts polls for new versions from github and displays it after startup if a new version is available.

For Discussions use https://forums.x-plane.org/forums/topic/324814-winwing-mcdu-on-x-plane-for-mac-studio-and-linux/


![mcdu demo image](./documentation/A319MCDU1.jpg)


## Installation

#### Debian based system
1. clone the repo where you want
2. copy `udev/71-winwing.rules` to `/etc/udev/rules.d`  
`sudo cp udev/71-winwing.rules /etc/udev/rules.d/`
3. install dependencies (on debian based systems)  
`sudo aptitide install python3-hid libhidapi-hidraw0`
5. start script (with udev rule no sudo needed): `python3 ./winwing_mcdu.py` when X-Plane with Toliss aircraft is loaded.


#### MAC-OS

1. clone the repo where you want
2. change into the directory `cd winwing_mcdu`
3. install homebrew
4. install dependencies
`python3 -m pip install hid`
`python3 -m pip install requests`
5. brew install hidapi
6. let hid find hidapi: `ln -s /opt/homebrew/lib/libhidapi.dylib .`
7. start script with sudo: `sudo python3 ./winwing_mcdu.py` when X-Plane with Toliss aircraft is loaded.


## Use MCDU
1. start X-Plane
2. enable incoming traffic in settings / network (at the very bottom of the page)
3. load Toliss A319
4. start script as written above
5. enjoy flying (and report bugs :-)  )


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
