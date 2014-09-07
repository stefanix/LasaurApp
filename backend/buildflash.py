
import sys
import time

import build
import flash
# import lasersaur


# build
ret = build.build_firmware()
if ret != 0:
    print "ERROR: build failed"
    sys.exit()

# flash
ret = flash.flash_upload('/dev/ttyACM0')
if ret != 0:
    print "ERROR: flash failed"
    sys.exit()

