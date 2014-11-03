# Configuration of LasaurApp
#
# NOTE!
# -----
# To add/change config parameters create a file named
# userconfig.py and write something like this:
#
# conf = {
#     'network_port': 4411,
#     'serial_port': 'COM3'
# }
#

import os
import sys


conf = {
    'appname': 'lasaurapp',
    'version': '15.00-beta1',
    'company_name': 'com.nortd.labs',
    'network_host': '',                    # '' for all nics
    'network_port': 4444,
    'websocket_port': 4411,
    'serial_port': '/dev/ttyACM0',         # set to '' for auto (req. firmware)
    # 'baudrate': 57600,
    'baudrate': 19200,
    'rootdir': None,                       # defined further down (../)
    'stordir': None,                       # defined further down
    'hardware': None,                      # defined further down
    'firmware': 'LasaurGrbl.hex',
    'tolerance': 0.08,
    'workspace': [1220,610,0],
    # 'intensity_minmax': [0,255],
    'seekrate': 6000,
    'feedrate': 2000,
    'intensity': 0,
    'kerf': 0.3,
    'max_raster_size': [3000,3000],
    'max_jobs_in_list': 20,
    'users': {
        'laser': 'laser',
    },

    'usb_reset_hack': False,
    'raster_leadin': 40,
}


### make some 'smart' default setting choices


### serial port
#
if conf['serial_port'] == '':
    import lasersaur
    conf['serial_port'] = lasersaur.find_controller()
    reload(lasersaur)  # so port defaults are correct
#
###


### rootdir
# This is to be used with all relative file access.
# _MEIPASS is a special location for data files when creating
# standalone, single file python apps with pyInstaller.
# Standalone is created by calling from 'other' directory:
# python pyinstaller/pyinstaller.py --onefile app.spec
if hasattr(sys, "_MEIPASS"):
    conf['rootdir'] = sys._MEIPASS
else:
    # root is one up from this file
    conf['rootdir'] = os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '../'))
#
###


### stordir
# This is to be used to store queue files and similar
if sys.platform == 'darwin':
    directory = os.path.join(os.path.expanduser('~'), 
                             'Library', 'Application Support', 
                             conf['company_name'], conf['appname'])
elif sys.platform == 'win32':
    directory = os.path.join(os.path.expandvars('%APPDATA%'), 
                             conf['company_name'], conf['appname'])
else:
    directory = os.path.join(os.path.expanduser('~'), "." + conf['appname'])
if not os.path.exists(directory):
    os.makedirs(directory)
conf['stordir'] = directory
#
###



### auto-check hardware
#
conf['hardware'] = 'standard'
### check if running on BBB
# also works on old Beaglebone if named 'lasersaur'
# os.uname() on BBB:
# ('Linux', 'lasersaur', '3.8.13-bone20', 
#  '#1 SMP Wed May 29 06:14:59 UTC 2013', 'armv7l')
uname = os.uname()
if (sys.platform == "linux2" 
        and (uname[1] == 'lasersaur' or uname[2] == '3.8.13-bone20')):
    conf['hardware'] = 'beaglebone'
### check if running on RaspberryPi
try:
    import RPi.GPIO
    conf['hardware'] = 'raspberrypi'
except ImportError:
    pass
#
###



if conf['hardware'] == 'beaglebone':
    conf['serial_port'] = '/dev/ttyO1'
    # if running as root
    if os.geteuid() == 0:
        conf['network_port'] = 80

    if os.path.exists("/sys/kernel/debug/omap_mux/uart1_txd"):
        # we are not on the beaglebone black, setup uart1
        # echo 0 > /sys/kernel/debug/omap_mux/uart1_txd
        fw = file("/sys/kernel/debug/omap_mux/uart1_txd", "w")
        fw.write("%X" % (0))
        fw.close()
        # echo 20 > /sys/kernel/debug/omap_mux/uart1_rxd
        fw = file("/sys/kernel/debug/omap_mux/uart1_rxd", "w")
        fw.write("%X" % ((1 << 5) | 0))
        fw.close()

    ### Set up atmega328 reset control
    # The reset pin is connected to GPIO2_7 (2*32+7 = 71).
    # Setting it to low triggers a reset.
    # echo 71 > /sys/class/gpio/export
    try:
        fw = file("/sys/class/gpio/export", "w")
        fw.write("%d" % (71))
        fw.close()
    except IOError:
        # probably already exported
        pass
    # set the gpio pin to output
    # echo out > /sys/class/gpio/gpio71/direction
    fw = file("/sys/class/gpio/gpio71/direction", "w")
    fw.write("out")
    fw.close()
    # set the gpio pin high
    # echo 1 > /sys/class/gpio/gpio71/value
    fw = file("/sys/class/gpio/gpio71/value", "w")
    fw.write("1")
    fw.flush()
    fw.close()

    ### Set up atmega328 reset control - BeagleBone Black
    # The reset pin is connected to GPIO2_9 (2*32+9 = 73).
    # Setting it to low triggers a reset.
    # echo 73 > /sys/class/gpio/export
    try:
        fw = file("/sys/class/gpio/export", "w")
        fw.write("%d" % (73))
        fw.close()
    except IOError:
        # probably already exported
        pass
    # set the gpio pin to output
    # echo out > /sys/class/gpio/gpio73/direction
    fw = file("/sys/class/gpio/gpio73/direction", "w")
    fw.write("out")
    fw.close()
    # set the gpio pin high
    # echo 1 > /sys/class/gpio/gpio73/value
    fw = file("/sys/class/gpio/gpio73/value", "w")
    fw.write("1")
    fw.flush()
    fw.close()

    ### read stepper driver configure pin GPIO2_12 (2*32+12 = 76).
    # Low means Geckos, high means SMC11s
    try:
        fw = file("/sys/class/gpio/export", "w")
        fw.write("%d" % (76))
        fw.close()
    except IOError:
        # probably already exported
        pass
    # set the gpio pin to input
    fw = file("/sys/class/gpio/gpio76/direction", "w")
    fw.write("in")
    fw.close()
    # set the gpio pin high
    fw = file("/sys/class/gpio/gpio76/value", "r")
    ret = fw.read()
    fw.close()
    print "Stepper driver configure pin is: " + str(ret)

elif conf['hardware'] == 'raspberrypi':
    conf['serial_port'] = '/dev/ttyAMA0'
    # if running as root
    if os.geteuid() == 0:
        conf['network_port'] = 80
    import RPi.GPIO as GPIO
    # GPIO.setwarnings(False) # surpress warnings
    GPIO.setmode(GPIO.BCM)  # use chip pin number
    pinSense = 7
    pinReset = 2
    pinExt1 = 3
    pinExt2 = 4
    pinExt3 = 17
    pinTX = 14
    pinRX = 15
    # read sens pin
    GPIO.setup(pinSense, GPIO.IN)
    isSMC11 = GPIO.input(pinSense)
    # atmega reset pin
    GPIO.setup(pinReset, GPIO.OUT)
    GPIO.output(pinReset, GPIO.HIGH)
    # no need to setup the serial pins
    # although /boot/cmdline.txt and /etc/inittab needs
    # to be edited to deactivate the serial terminal login
    # (basically anything related to ttyAMA0)



### overwrite conf with parameters from userconfig.py
try:
    import userconfig
    conf.update(userconfig.conf)
    print "Config: using userconfig.py"
except ImportError:
    print "Config: using defaults, no userconfig.py present"