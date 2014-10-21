
import sys
import os
import time
import argparse

import web
from config import conf

__author__  = 'Stefan Hechenberger <stefan@nortd.com>'



### Setup Argument Parser
argparser = argparse.ArgumentParser(description='Run LasaurApp.', prog='lasaurapp')
argparser.add_argument('port', metavar='serial_port', nargs='?', default=False,
                    help='serial port to the Lasersaur')
argparser.add_argument('-v', '--version', action='version', version='%(prog)s ' + conf['version'],
                    default=False, help='bind to all network devices (default: bind to 127.0.0.1)')
# argparser.add_argument('-l', '--list', dest='list_serial_devices', action='store_true',
#                     default=False, help='list all serial devices currently connected')
argparser.add_argument('-t', '--threaded', dest='threaded', action='store_true',
                    default=False, help='run web server in thread')
argparser.add_argument('-d', '--debug', dest='debug', action='store_true',
                    default=False, help='print more verbose for debugging')
argparser.add_argument('-u', '--usbhack', dest='usbhack', action='store_true',
                    default=False, help='use usb reset hack (advanced)')
argparser.add_argument('-b', '--browser', dest='browser', action='store_true',
                    default=False, help='launch interface in browser')
# for backwards compatibility
argparser.add_argument('-p', '--public', dest='host_on_all_interfaces', action='store_true',
                       default=False, help='dummy, for backwards compatibility')
argparser.add_argument('--beaglebone', dest='beaglebone', action='store_true',
                       default=False, help='dummy, for backwards compatibility')
args = argparser.parse_args()



print "LasaurApp " + conf['version']
conf['usb_reset_hack'] = args.usbhack

if args.debug:
    if hasattr(sys, "_MEIPASS"):
        print "Data root is: " + sys._MEIPASS

# run
web.start(threaded=args.threaded, browser=args.browser, debug=args.debug)
if args.threaded:
    while 1:
        try:
            time.sleep(0.1)
        except KeyboardInterrupt:
            break
    web.stop()
print "END of LasaurApp"



