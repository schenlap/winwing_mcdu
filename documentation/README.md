# Documentation for developers

## usb device information ##
### kernel messages on connect ###
```
TODO
```

### usb decriptor MCDU ###
lsusb -d 4098:bb36 -v
```
Bus 001 Device 007: ID 4098:bb36 Winwing WINWING MCDU-32-CAPTAIN
Negotiated speed: Full Speed (12Mbps)
Device Descriptor:
  bLength                18
  bDescriptorType         1
  bcdUSB               2.00
  bDeviceClass            0 [unknown]
  bDeviceSubClass         0 [unknown]
  bDeviceProtocol         0
  bMaxPacketSize0        64
  idVendor           0x4098 Winwing
  idProduct          0xbb36 WINWING MCDU-32-CAPTAIN
  bcdDevice            1.01
  iManufacturer           1 Winwing
  iProduct                2 WINWING MCDU-32-CAPTAIN
  iSerial                 3 E465E021F66050A482666023
  bNumConfigurations      1
  Configuration Descriptor:
    bLength                 9
    bDescriptorType         2
    wTotalLength       0x0029
    bNumInterfaces          1
    bConfigurationValue     1
    iConfiguration          0
    bmAttributes         0x80
      (Bus Powered)
    MaxPower              100mA
    Interface Descriptor:
      bLength                 9
      bDescriptorType         4
      bInterfaceNumber        0
      bAlternateSetting       0
      bNumEndpoints           2
      bInterfaceClass         3 Human Interface Device
      bInterfaceSubClass      0 [unknown]
      bInterfaceProtocol      0
      iInterface              0
        HID Device Descriptor:
          bLength                 9
          bDescriptorType        33
          bcdHID               1.11
          bCountryCode            0 Not supported
          bNumDescriptors         1
          bDescriptorType        34 (null)
          wDescriptorLength     160
          Report Descriptor: (length is 160)
            Item(Global): Usage Page, data= [ 0x01 ] 1
                            (null)
            Item(Local ): (null), data= [ 0x04 ] 4
                            (null)
            Item(Main  ): (null), data= [ 0x01 ] 1
                            Application
            Item(Global): (null), data= [ 0x01 ] 1
            Item(Global): Usage Page, data= [ 0x09 ] 9
                            (null)
            Item(Local ): (null), data= [ 0x01 ] 1
                            (null)
            Item(Local ): (null), data= [ 0x80 ] 128
                            (null)
            Item(Global): (null), data= [ 0x00 ] 0
            Item(Global): (null), data= [ 0x01 ] 1
            Item(Global): (null), data= [ 0x00 ] 0
            Item(Global): (null), data= [ 0x01 ] 1
            Item(Global): (null), data= [ 0x01 ] 1
            Item(Global): (null), data= [ 0x80 ] 128
            Item(Main  ): (null), data= [ 0x02 ] 2
                            Data Variable Absolute No_Wrap Linear
                            Preferred_State No_Null_Position Non_Volatile Bitfield
            Item(Global): Usage Page, data= [ 0x01 ] 1
                            (null)
            Item(Local ): (null), data= [ 0x33 ] 51
                            (null)
            Item(Global): (null), data= [ 0x00 ] 0
            Item(Global): (null), data= [ 0xff 0x0f 0x00 0x00 ] 4095
            Item(Global): (null), data= [ 0x00 ] 0
            Item(Global): (null), data= [ 0xff 0x0f 0x00 0x00 ] 4095
            Item(Global): (null), data= [ 0x10 ] 16
            Item(Global): (null), data= [ 0x01 ] 1
            Item(Main  ): (null), data= [ 0x02 ] 2
                            Data Variable Absolute No_Wrap Linear
                            Preferred_State No_Null_Position Non_Volatile Bitfield
            Item(Global): Usage Page, data= [ 0x01 ] 1
                            (null)
            Item(Local ): (null), data= [ 0x34 ] 52
                            (null)
            Item(Global): (null), data= [ 0x00 ] 0
            Item(Global): (null), data= [ 0xff 0x0f 0x00 0x00 ] 4095
            Item(Global): (null), data= [ 0x00 ] 0
            Item(Global): (null), data= [ 0xff 0x0f 0x00 0x00 ] 4095
            Item(Global): (null), data= [ 0x10 ] 16
            Item(Global): (null), data= [ 0x01 ] 1
            Item(Main  ): (null), data= [ 0x02 ] 2
                            Data Variable Absolute No_Wrap Linear
                            Preferred_State No_Null_Position Non_Volatile Bitfield
            Item(Global): Usage Page, data= [ 0x01 ] 1
                            (null)
            Item(Global): (null), data= [ 0x00 ] 0
            Item(Global): (null), data= [ 0xff 0xff 0x00 0x00 ] 65535
            Item(Global): (null), data= [ 0x00 ] 0
            Item(Global): (null), data= [ 0xff 0xff 0x00 0x00 ] 65535
            Item(Local ): (null), data= [ 0xd0 ] 208
                            (null)
            Item(Local ): (null), data= [ 0xd1 ] 209
                            (null)
            Item(Global): (null), data= [ 0x10 ] 16
            Item(Global): (null), data= [ 0x02 ] 2
            Item(Main  ): (null), data= [ 0x01 ] 1
                            Constant Array Absolute No_Wrap Linear
                            Preferred_State No_Null_Position Non_Volatile Bitfield
            Item(Global): (null), data= [ 0x02 ] 2
            Item(Global): Usage Page, data= [ 0xff 0x00 ] 255
                            (null)
            Item(Local ): (null), data= [ 0x01 ] 1
                            (null)
            Item(Global): (null), data= [ 0x00 ] 0
            Item(Global): (null), data= [ 0xff 0x00 ] 255
            Item(Global): (null), data= [ 0x00 ] 0
            Item(Global): (null), data= [ 0xff 0x00 ] 255
            Item(Global): (null), data= [ 0x08 ] 8
            Item(Global): (null), data= [ 0x0d ] 13
            Item(Main  ): (null), data= [ 0x02 ] 2
                            Data Variable Absolute No_Wrap Linear
                            Preferred_State No_Null_Position Non_Volatile Bitfield
            Item(Local ): (null), data= [ 0x02 ] 2
                            (null)
            Item(Main  ): (null), data= [ 0x02 ] 2
                            Data Variable Absolute No_Wrap Linear
                            Preferred_State No_Null_Position Non_Volatile Bitfield
            Item(Global): (null), data= [ 0xf0 ] 240
            Item(Global): Usage Page, data= [ 0xff 0x00 ] 255
                            (null)
            Item(Local ): (null), data= [ 0x03 ] 3
                            (null)
            Item(Global): (null), data= [ 0x3f ] 63
            Item(Main  ): (null), data= [ 0x02 ] 2
                            Data Variable Absolute No_Wrap Linear
                            Preferred_State No_Null_Position Non_Volatile Bitfield
            Item(Local ): (null), data= [ 0x04 ] 4
                            (null)
            Item(Main  ): (null), data= [ 0x02 ] 2
                            Data Variable Absolute No_Wrap Linear
                            Preferred_State No_Null_Position Non_Volatile Bitfield
            Item(Global): (null), data= [ 0xf2 ] 242
            Item(Global): Usage Page, data= [ 0xff 0x00 ] 255
                            (null)
            Item(Local ): (null), data= [ 0x05 ] 5
                            (null)
            Item(Global): (null), data= [ 0x3f ] 63
            Item(Main  ): (null), data= [ 0x02 ] 2
                            Data Variable Absolute No_Wrap Linear
                            Preferred_State No_Null_Position Non_Volatile Bitfield
            Item(Local ): (null), data= [ 0x06 ] 6
                            (null)
            Item(Main  ): (null), data= [ 0x02 ] 2
                            Data Variable Absolute No_Wrap Linear
                            Preferred_State No_Null_Position Non_Volatile Bitfield
            Item(Main  ): (null), data=none
      Endpoint Descriptor:
        bLength                 7
        bDescriptorType         5
        bEndpointAddress     0x81  EP 1 IN
        bmAttributes            3
          Transfer Type            Interrupt
          Synch Type               None
          Usage Type               Data
        wMaxPacketSize     0x0040  1x 64 bytes
        bInterval               1
      Endpoint Descriptor:
        bLength                 7
        bDescriptorType         5
        bEndpointAddress     0x02  EP 2 OUT
        bmAttributes            3
          Transfer Type            Interrupt
          Synch Type               None
          Usage Type               Data
        wMaxPacketSize     0x0040  1x 64 bytes
        bInterval               1
Device Status:     0x0001
  Self Powered

```
hid descriptor read `od -t x1 -Anone  /sys/bus/usb/devices/usb1/1-7/descriptors`

```
0x12, 0x01, 0x00,  // Unknown (bTag: 0x01, bType: 0x00)
0x02, 0x00, 0x00,  // Unknown (bTag: 0x00, bType: 0x00)
0x00,              // Unknown (bTag: 0x00, bType: 0x00)
0x40,              // Unknown (bTag: 0x04, bType: 0x00)
0x05, 0x0B,        // Usage Page (Telephony)
0xAF, 0x19, 0x00, 0x01, 0x01,  // Unknown (bTag: 0x0A, bType: 0x03)
0x02, 0x03, 0x01,  // Unknown (bTag: 0x00, bType: 0x00)
0x09, 0x02,        // Usage (Answering Machine)
0x2B, 0x00, 0x02, 0x01, 0x00,  // Usage Maximum (0x010200)
0xA0,              // Collection
0x08,              //   Usage
0x09, 0x04,        //   Usage (Handset)
0x00,              //   Unknown (bTag: 0x00, bType: 0x00)
0x00,              //   Unknown (bTag: 0x00, bType: 0x00)
0x00,              //   Unknown (bTag: 0x00, bType: 0x00)
0xFF, 0xFF, 0xFF, 0x00, 0x09,  //   Unknown (bTag: 0x0F, bType: 0x03)
0x04,              //   Usage Page
0x02, 0x00, 0x01,  //   Unknown (bTag: 0x00, bType: 0x00)
0x03, 0x00, 0x00, 0x00, 0x09,  //   Unknown (bTag: 0x00, bType: 0x00)
0x21, 0x11,        //   Unknown (bTag: 0x02, bType: 0x00)
0x01, 0x00,        //   Unknown (bTag: 0x00, bType: 0x00)
0x01, 0x22,        //   Unknown (bTag: 0x00, bType: 0x00)
0x24,              //   Logical Maximum
0x00,              //   Unknown (bTag: 0x00, bType: 0x00)
0x07, 0x05, 0x82, 0x03, 0x20,  //   Usage Page (0x20038205)
0x00,              //   Unknown (bTag: 0x00, bType: 0x00)
0x04,              //   Usage Page

// 61 bytes

```


## sniff winwing usb protocol

I use Linux as host system and Windows in virt-manager that runs SimApp pro. Wirshark runs in Linux to sniff usb transfer.


## wireshark

to start sniffing:
1. sudo mount -t debugfs none /sys/kernel/debug
2. sudo modprobe usbmon
3. sudo setfacl -m u:$USER:r /dev/usbmon*
4. wireshark


