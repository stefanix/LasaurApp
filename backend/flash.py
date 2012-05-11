# Super Awesome LasaurGrbl python flash script.
# 
# Copyright (c) 2011 Nortd Labs
# Open Source by the terms of the Gnu Public License (GPL3) or higher.

import os, sys


def flash_upload(serial_port, resources_dir):
    DEVICE = "atmega328p"
    CLOCK = "16000000"
    PROGRAMMER = "avrisp"
    BITRATE = "115200"
    FIRMWARE = os.path.join(resources_dir, "firmware/LasaurGrbl.hex")
 
    if sys.platform == "darwin":  # OSX
        AVRDUDEAPP    = os.path.join(resources_dir, "firmware/tools_osx/avrdude")
        AVRDUDECONFIG = os.path.join(resources_dir, "firmware/tools_osx/avrdude.conf")
    
    elif sys.platform == "win32": # Windows
        AVRDUDEAPP    = os.path.join(resources_dir, "firmware/tools_win/avrdude")
        AVRDUDECONFIG = os.path.join(resources_dir, "firmware/tools_win/avrdude.conf")
    
    elif sys.platform == "linux" or sys.platform == "linux2":  #Linux
        AVRDUDEAPP    = os.path.join(resources_dir, "firmware/tools_linux/avrdude")
        AVRDUDECONFIG = os.path.join(resources_dir, "firmware/tools_linux/avrdude.conf")
              
    os.system('%(dude)s -c %(programmer)s -b %(bps)s -P %(port)s -p %(device)s -C %(dudeconf)s -B 10 -F -U flash:w:%(firmware)s:i' 
        % {'dude':AVRDUDEAPP, 'programmer':PROGRAMMER, 'bps':BITRATE, 'port':serial_port, 'device':DEVICE, 'dudeconf':AVRDUDECONFIG, 'firmware':FIRMWARE})

    # fuse setting taken over from Makefile for reference
    #os.system('%(dude)s -U hfuse:w:0xd2:m -U lfuse:w:0xff:m' % {'dude':AVRDUDEAPP})
        

