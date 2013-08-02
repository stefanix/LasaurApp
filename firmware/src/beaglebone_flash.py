# Super Awesome LasaurGrbl python flash script.
# 
# Copyright (c) 2011 Nortd Labs
# Open Source by the terms of the Gnu Public License (GPL3) or higher.

import os, sys


# Make sure you have avrdude installed on the beaglebone
# opkg install libreadline5_5.2-r8.9_armv4.ipk
# opkg install avrdude_5.10-r1.9_armv7a.ipk
# get the packages from http://www.angstrom-distribution.org/repo/

AVRDUDEAPP    = "avrdude"
AVRDUDECONFIG = "/etc/avrdude.conf"
SERIAL_PORT = "/dev/ttyO1"
DEVICE = "atmega328p"
PROGRAMMER = "arduino"    # use this for bootloader
SERIAL_OPTION = '-P %(port)s' % {'port':SERIAL_PORT}
BITRATE = "115200"
BUILDNAME = "LasaurGrbl"

# use beaglebone gpio2_7 to reset the atmege here

os.system('%(dude)s -c %(programmer)s -b %(bps)s %(serial_option)s -p %(device)s -C %(dudeconf)s -Uflash:w:%(product)s.hex:i' % {'dude':AVRDUDEAPP, 'programmer':PROGRAMMER, 'bps':BITRATE, 'serial_option':SERIAL_OPTION, 'device':DEVICE, 'dudeconf':AVRDUDECONFIG, 'product':BUILDNAME})
# os.system('%(dude)s -c %(programmer)s -b %(bps)s -P %(port)s -p %(device)s -C %(dudeconf)s -B 10 -F -U flash:w:%(product)s.hex:i' % {'dude':AVRDUDEAPP, 'programmer':PROGRAMMER, 'bps':BITRATE, 'port':SERIAL_PORT, 'device':DEVICE, 'dudeconf':AVRDUDECONFIG, 'product':BUILDNAME})


