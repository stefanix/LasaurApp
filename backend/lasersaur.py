
import os
import sys
import time
import json
import copy
import threading
import collections
from itertools import islice
import serial
import serial.tools.list_ports
from config import conf
import statserver


__author__  = 'Stefan Hechenberger <stefan@nortd.com>'



################ SENDING PROTOCOL
CMD_STOP = '\x01'
CMD_RESUME = '\x02'
CMD_STATUS = "\x03"
CMD_SUPERSTATUS = "\x04"
SERIAL_XON = '\x17'
SERIAL_XOFF = '\x19'
CMD_RASTER_DATA_START = '\x07'
CMD_RASTER_DATA_END = '\x08'
STATUS_END = '\x09'

CMD_NONE = "A"
CMD_LINE = "B"
CMD_DWELL = "C"
CMD_RASTER = "D"

CMD_REF_RELATIVE = "E" 
CMD_REF_ABSOLUTE = "F"

CMD_HOMING = "G"

CMD_SET_OFFSET_TABLE = "H"
CMD_SET_OFFSET_CUSTOM = "I"
CMD_SEL_OFFSET_TABLE = "J"
CMD_SEL_OFFSET_CUSTOM = "K"

CMD_AIR_ENABLE = "L"
CMD_AIR_DISABLE = "M"
CMD_AUX1_ENABLE = "N"
CMD_AUX1_DISABLE = "O"
CMD_AUX2_ENABLE = "P"
CMD_AUX2_DISABLE = "Q"


PARAM_TARGET_X = "x"
PARAM_TARGET_Y = "y" 
PARAM_TARGET_Z = "z" 
PARAM_FEEDRATE = "f"
PARAM_INTENSITY = "s"
PARAM_DURATION = "d"
PARAM_PIXEL_WIDTH = "p"
PARAM_OFFTABLE_X = "h"
PARAM_OFFTABLE_Y = "i"
PARAM_OFFTABLE_Z = "j"
PARAM_OFFCUSTOM_X = "k"
PARAM_OFFCUSTOM_Y = "l"
PARAM_OFFCUSTOM_Z = "m"

################


################ RECEIVING PROTOCOL

# status: error flags
ERROR_SERIAL_STOP_REQUEST = '!'
ERROR_RX_BUFFER_OVERFLOW = '"'

ERROR_LIMIT_HIT_X1 = '$'
ERROR_LIMIT_HIT_X2 = '%'
ERROR_LIMIT_HIT_Y1 = '&'
ERROR_LIMIT_HIT_Y2 = '*'
ERROR_LIMIT_HIT_Z1 = '+'
ERROR_LIMIT_HIT_Z2 = '-'

ERROR_INVALID_MARKER = '#'
ERROR_INVALID_DATA = ':'
ERROR_INVALID_COMMAND = '<'
ERROR_INVALID_PARAMETER ='>'
ERROR_TRANSMISSION_ERROR ='='

# status: info flags
INFO_READY_YES = 'A'
INFO_DOOR_OPEN = 'B'
INFO_CHILLER_OFF = 'C'
INFO_BUFFER_UNDERRUN = 'D'

# status: info params
INFO_POS_X = 'x'
INFO_POS_Y = 'y'
INFO_POS_Z = 'z'
INFO_VERSION = 'v'

INFO_HELLO = '~'

INFO_OFFCUSTOM_X = 'a'
INFO_OFFCUSTOM_Y = 'b'
INFO_OFFCUSTOM_Z = 'c'
# INFO_TARGET_X = 'd'
# INFO_TARGET_Y = 'e'
# INFO_TARGET_Z = 'f'
INFO_FEEDRATE = 'g'
INFO_INTENSITY = 'h'
INFO_DURATION = 'i'
INFO_PIXEL_WIDTH = 'j'
################


SerialLoop = None

class SerialLoopClass(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

        self.device = None
        self.tx_buffer = collections.deque()

        # TX_CHUNK_SIZE - this is the number of bytes to be 
        # written to the device in one go. It needs to match the device.
        self.TX_CHUNK_SIZE = 16
        self.RX_CHUNK_SIZE = 256
        self.xon_active = False
        
        # used for calculating percentage done
        self.job_size = 0

        # status flags
        self._status = {}
        self._s = {}
        self.reset_status()
        self._paused = False
        self._ready = False

        self.request_stop = False
        self.request_resume = False
        self.request_status = 2       # 0: no request, 1: normal request, 2: super request

        self.pdata_count = 0
        self.pdata_chars = [None, None, None, None]

        threading.Thread.__init__(self)
        self.stop_processing = False

        self.deamon = True  # kill thread when main thread exits

        # lock mechanism for chared data
        # see: http://effbot.org/zone/thread-synchronization.htm
        self.lock = threading.Lock()

        self.server_enabled = False



    def reset_status(self):
        self._status = {
            'appver':conf['version'],
            'firmver': None,
            'ready': False,
            'paused': False,
            'serial': False,
            'pos':[0.0, 0.0, 0.0],

            ### stop conditions
            # indicated when key present
            # possible keys are:
            # x1, x2, y1, y2, z1, z2
            # requested
            # buffer
            # marker
            # data
            # command
            # parameter
            # transmission
            'stops': {},

            # door
            # chiller
            'info':{},

            ### super
            'offset': [0.0, 0.0, 0.0],
            # 'pos_target': [0.0, 0.0, 0.0],
            'feedrate': 0.0,
            'intensity': 0.0,
            'duration': 0.0,
            'pixelwidth': 0.0         
        }
        self._s = copy.deepcopy(self._status)


    def send_command(self, command):
        self.tx_buffer.append(command)
        self.job_size += 1


    def send_param(self, param, val):
        # num to be [-134217.728, 134217.727], [-2**27, 2**27-1]
        # three decimals are retained
        num = int(round(((val+134217.728)*1000)))
        char0 = chr((num&127)+128)
        char1 = chr(((num&(127<<7))>>7)+128)
        char2 = chr(((num&(127<<14))>>14)+128)
        char3 = chr(((num&(127<<21))>>21)+128)
        self.tx_buffer.append(char0)
        self.tx_buffer.append(char1)
        self.tx_buffer.append(char2)
        self.tx_buffer.append(char3)
        self.tx_buffer.append(param)
        self.job_size += 5



    def run(self):
        """Main loop of the serial thread."""
        last_status_request = 0
        while True:
            if self.stop_processing:
                break
            with self.lock:
                self._process()
                if time.time()-last_status_request > 0.5:
                    if self._ready:
                        self.request_status = 2  # ready -> super request
                    else:
                        self.request_status = 1  # processing -> normal request
                    last_status_request = time.time()
            time.sleep(0.004)



    def _process(self):
        if self.device:
            if not self._paused:
                try:
                    ### receiving
                    for char in self.device.read(self.RX_CHUNK_SIZE):
                        self._process_char(char)
                   
                    ### sending super commands (handled in serial rx interrupt)
                    if self.request_status == 1:
                        self._send_char(CMD_STATUS)
                        self.request_status = 0
                    elif self.request_status == 2:
                        self._send_char(CMD_SUPERSTATUS)
                        self.request_status = 0

                    if self.request_stop:
                        self._send_char(CMD_STOP)
                        self.request_stop = False

                    if self.request_resume:
                        self._send_char(CMD_RESUME)
                        self.request_resume = False
                        self.reset_status()
                        self.request_status = 2  # super request

                    ### sending from buffer
                    if self.tx_buffer and self.xon_active:
                        try:
                            to_send = ''.join(islice(self.tx_buffer, 0, self.TX_CHUNK_SIZE))
                            t_prewrite = time.time()
                            actuallySent = self.device.write(to_send)
                            # self.device.flush()  # wait until kernel buffer is written
                            if time.time() - t_prewrite > 0.01:
                                print "WARN: write delay 1"
                        except serial.SerialTimeoutException:
                            actuallySent = 0  # assume nothing has been sent
                            print "ERROR: writeTimeoutError 2"
                        for i in range(actuallySent):
                            self.tx_buffer.popleft()
                    else:
                        if self.job_size:  # job finished sending
                            self.job_size = 0
                except OSError:
                    print "ERROR: serial got disconnected 1."
                    self.stop_processing = True
                    self._status['serial'] = False
                    self._status['ready'] = False
                except ValueError:
                    print "ERROR: serial got disconnected 2."
                    self.stop_processing = True
                    self._status['serial'] = False
                    self._status['ready']  = False    
        else:
            print "ERROR: serial got disconnected 3."
            self.stop_processing = True
            self._status['serial'] = False
            self._status['ready']  = False

        # flush stdout, so print shows up timely
        sys.stdout.flush()



    def _send_char(self, char):
        try:
            t_prewrite = time.time()
            self.device.write(char)
            if time.time() - t_prewrite > 0.01:
                print "WARN: write delay 2"
            self.device.flushOutput()
        except serial.SerialTimeoutException:
            print "ERROR: writeTimeoutError 1"



    def _process_char(self, char):
        # sys.stdout.write('('+char+','+str(ord(char))+')')
        if ord(char) < 32:  ### flow
            if char == SERIAL_XON:
                self.xon_active = True
                self.device.flowControlOut(enable=True)
                sys.stdout.write('+')
            elif char == SERIAL_XOFF:
                self.xon_active = False
                self.device.flowControlOut(enable=False)
                sys.stdout.write('-')
            elif char == STATUS_END:
                # status frame complete, compile status
                self._status, self._s = self._s, self._status
                self._status['ready'] = self._ready
                self._status['paused'] = self._paused
                self._status['serial'] = bool(self.device)
                self._s['stops'].clear()
                self._s['info'].clear()
                # send through status server
                if self.server_enabled:
                    statusjson = json.dumps(self._status)
                    statserver.send(statusjson)
                    statserver.on_connected_message(statusjson)
        elif 31 < ord(char) < 65:  ### stop error markers
            # chr is in [!-@], process flag
            if char == ERROR_LIMIT_HIT_X1:
                self._s['stops']['x1'] = True
            elif char == ERROR_LIMIT_HIT_X2:
                self._s['stops']['x2'] = True
            elif char == ERROR_LIMIT_HIT_Y1:
                self._s['stops']['y1'] = True
            elif char == ERROR_LIMIT_HIT_Y2:
                self._s['stops']['y2'] = True
            elif char == ERROR_LIMIT_HIT_Z1:
                self._s['stops']['z1'] = True
            elif char == ERROR_LIMIT_HIT_Z2:
                self._s['stops']['z2'] = True
            elif char == ERROR_SERIAL_STOP_REQUEST:
                self._s['stops']['requested'] = True
            elif char == ERROR_RX_BUFFER_OVERFLOW:
                self._s['stops']['buffer'] = True                                    
            elif char == ERROR_INVALID_MARKER:
                self._s['stops']['marker'] = True
            elif char == ERROR_INVALID_DATA:
                self._s['stops']['data'] = True
            elif char == ERROR_INVALID_COMMAND:
                self._s['stops']['command'] = True
            elif char == ERROR_INVALID_PARAMETER:
                self._s['stops']['parameter'] = True
            elif char == ERROR_TRANSMISSION_ERROR:
                self._s['stops']['transmission'] = True
            else:
                print "ERROR: invalid stop error marker"
            # in stop mode
            self.tx_buffer.clear()
            self.job_size = 0
            self._ready = False

        elif 64 < ord(char) < 91:  # info flags
            # chr is in [A-Z], info flag
            if char == INFO_READY_YES:
                self._ready = True
            elif char == INFO_DOOR_OPEN:
                self._s['info']['door'] = True
            elif char == INFO_CHILLER_OFF:
                self._s['info']['chiller'] = True
            elif char == INFO_BUFFER_UNDERRUN:
                if not self._ready:
                    print "INFO: Firmware rx buffer empty."
            else:
                print "ERROR: invalid info flag"
                sys.stdout.write('('+char+','+str(ord(char))+')')
        elif 96 < ord(char) < 123:  # parameter
            # char is in [a-z], process parameter
            num = ((((ord(self.pdata_chars[3])-128)*2097152
                   + (ord(self.pdata_chars[2])-128)*16384
                   + (ord(self.pdata_chars[1])-128)*128
                   + (ord(self.pdata_chars[0])-128) )- 134217728)/1000.0)
            self.pdata_count = 0
            if char == INFO_POS_X:
                self._s['pos'][0] = num
            elif char == INFO_POS_Y:
                self._s['pos'][1] = num
            elif char == INFO_POS_Z:
                self._s['pos'][2] = num
            elif char == INFO_VERSION:
                num = 'v' + str(int(num)/100.0)
                self._s['firmver'] = num
            # super status
            elif char == INFO_OFFCUSTOM_X:
                self._s['offset'][0] = num
            elif char == INFO_OFFCUSTOM_Y:
                self._s['offset'][1] = num
            elif char == INFO_OFFCUSTOM_Z:
                self._s['offset'][2] = num
            elif char == INFO_FEEDRATE:
                self._s['feedrate'] = num
            elif char == INFO_INTENSITY:
                self._s['intensity'] = num
            elif char == INFO_DURATION:
                self._s['duration'] = num
            elif char == INFO_PIXEL_WIDTH:
                self._s['pixelwidth'] = num
            else:
                print "ERROR: invalid param"
        elif ord(char) > 127:  ### data
            # char is in [128,255]
            if self.pdata_count < 4:
                self.pdata_chars[self.pdata_count] = char
                self.pdata_count += 1
            else:
                print "ERROR: invalid data" 
        else:
            print ord(char)
            print char
            print "ERROR: invalid marker"



###########################################################################
### API ###################################################################
###########################################################################

            
def find_controller(baudrate=conf['baudrate']):
    if os.name == 'posix':
        iterator = sorted(serial.tools.list_ports.grep('tty'))
        for port, desc, hwid in iterator:
            print "Looking for controller on port: " + port
            try:
                s = serial.Serial(port=port, baudrate=baudrate, timeout=2.0)
                lasaur_hello = s.read(8)
                if lasaur_hello.find(INFO_HELLO) > -1:
                    return port
                s.close()
            except serial.SerialException:
                pass
    else:
        # windows hack because pyserial does not enumerate USB-style com ports
        print "Trying to find controller ..."
        for i in range(24):
            try:
                s = serial.Serial(port=i, baudrate=baudrate, timeout=2.0)
                lasaur_hello = s.read(8)
                if lasaur_hello.find(INFO_HELLO) > -1:
                    return s.portstr
                s.close()
            except serial.SerialException:
                pass      
    print "ERROR: No controller found."
    return None

    

def connect(port=conf['serial_port'], baudrate=conf['baudrate'], server=False):
    global SerialLoop
    if not SerialLoop:
        SerialLoop = SerialLoopClass()

        # Create serial device with read timeout set to 100us.
        # This results in the read() being almost non-blocking 
        # without consuming the entire processor.
        # Write on the other hand uses a large timeout but should not be blocking
        # much because we ask it only to write TX_CHUNK_SIZE at a time.
        # BUG WARNING: the pyserial write function does not report how
        # many bytes were actually written if this is different from requested.
        # Work around: use a big enough timeout and a small enough chunk size.
        try:
            if conf['usb_reset_hack']:
                import flash
                flash.usb_reset_hack()
            # connect
            SerialLoop.device = serial.Serial(port, baudrate, timeout=0, writeTimeout=4)
            if conf['hardware'] == 'standard':
                # clear throat
                # Toggle DTR to reset Arduino
                SerialLoop.device.setDTR(False)
                time.sleep(1)
                SerialLoop.device.flushInput()
                SerialLoop.device.setDTR(True)
                # for good measure
                SerialLoop.device.flushOutput()
            else:
                reset()
                # time.sleep(0.5)
                # SerialLoop.device.flushInput()
                # SerialLoop.device.flushOutput()

            start = time.time()
            while True:
                if time.time() - start > 2:
                    print "ERROR: Cannot get 'hello' from controller"
                    raise serial.SerialException
                char = SerialLoop.device.read(1)
                if char == INFO_HELLO:
                    print "Controller says Hello!"
                    break

            SerialLoop.start()  # this calls run() in a thread

            # start up status server
            SerialLoop.server_enabled = server
            if SerialLoop.server_enabled:
                statserver.start()

        except serial.SerialException:
            SerialLoop = None
            print "ERROR: Cannot connect serial on port: %s" % (port)

    else:
        print "ERROR: disconnect first"


def connected():
    global SerialLoop
    return SerialLoop and bool(SerialLoop.device)


def close():
    global SerialLoop
    if SerialLoop:
        if SerialLoop.device:
            SerialLoop.device.flushOutput()
            SerialLoop.device.flushInput()
            ret = True
        else:
            ret = False
        if SerialLoop.is_alive():
            SerialLoop.stop_processing = True
            SerialLoop.join()
        # stop status server
        if SerialLoop.server_enabled:
            statserver.stop()
    else:
        ret = False
    SerialLoop = None
    return ret



def flash(serial_port=conf['serial_port'], firmware_file=conf['firmware']):
    import flash
    reconnect = False
    if connected():
        close()
        reconnect = True
    ret = flash.flash_upload(serial_port=serial_port, firmware_file=firmware_file)
    if reconnect:
        connect()
    if ret != 0:
        print "ERROR: flash failed"
    return ret


def build(firmware_name="LasaurGrbl"):
    import build
    ret = build.build_firmware(firmware_name=firmware_name)
    if ret != 0:
        print "ERROR: build failed"
    return ret


def reset():
    import flash
    flash.reset_atmega()


def percentage():
    """Return the percentage done as an integer between 0-100.
    Return -1 if no job is active."""
    global SerialLoop
    ret = -1
    with SerialLoop.lock:
        if SerialLoop.job_size != 0:
            ret = int(100-100*len(SerialLoop.tx_buffer)/float(SerialLoop.job_size))
    return ret


def status():
    """Get status."""
    global SerialLoop
    with SerialLoop.lock:
        stats = copy.deepcopy(SerialLoop._status)
    return stats


def homing():
    """Run homing cycle."""
    global SerialLoop
    with SerialLoop.lock:
        if SerialLoop._ready or status()['stops']:
            SerialLoop.send_command(CMD_HOMING)
        else:
            print "WARN: ignoring homing command while job running"


def feedrate(val):
    global SerialLoop
    with SerialLoop.lock:
        SerialLoop.send_param(PARAM_FEEDRATE, val)

def intensity(val):
    global SerialLoop
    with SerialLoop.lock:
        SerialLoop.send_param(PARAM_INTENSITY, val)

def duration(val):
    global SerialLoop
    with SerialLoop.lock:
        SerialLoop.send_param(PARAM_DURATION, val)

def pixelwidth(val):
    global SerialLoop
    with SerialLoop.lock:
        SerialLoop.send_param(PARAM_PIXEL_WIDTH, val)

def relative():
    global SerialLoop
    with SerialLoop.lock:
        SerialLoop.send_command(CMD_REF_RELATIVE)

    
def absolute():
    global SerialLoop
    with SerialLoop.lock:
        SerialLoop.send_command(CMD_REF_ABSOLUTE)
    
def move(x, y, z=0.0):
    global SerialLoop
    with SerialLoop.lock:
        SerialLoop.send_param(PARAM_TARGET_X, x)
        SerialLoop.send_param(PARAM_TARGET_Y, y)
        SerialLoop.send_param(PARAM_TARGET_Z, z)
        SerialLoop.send_command(CMD_LINE)

def rastermove(x, y, z=0.0):
    global SerialLoop
    with SerialLoop.lock:
        SerialLoop.send_param(PARAM_TARGET_X, x)
        SerialLoop.send_param(PARAM_TARGET_Y, y)
        SerialLoop.send_param(PARAM_TARGET_Z, z)
        SerialLoop.send_command(CMD_RASTER)




def job(jobdict):
    """Queue an .lsa job.
    A job dictionary can define vector and raster passes.
    Unlike gcode it's not procedural but declarative.
    The job dict looks like this:
    ###########################################################################
    {
        "vector":                          # optional
        {
            "passes":
            [
                {
                    "paths": [0],          # paths by index
                    "relative": True,      # optional, default: False
                    "seekrate": 6000,      # optional, rate to first vertex
                    "feedrate": 2000,      # optional, rate to other verteces
                    "intensity": 100,      # optional, default: 0 (in percent)
                    "pierce_time": 0,      # optional, default: 0
                    "air_assist": "pass",  # optional (feed, pass, off), default: pass
                    "aux1_assist": "off",  # optional (feed, pass, off), default: off
                }
            ],
            "paths":
            [                              # list of paths
                [                          # list of polylines
                    [                      # list of verteces
                        [0,-10, 0],        # list of coords
                    ],
                ],
            ],
            "colors": ["#FF0000"],         # color is matched to path by index
            "noreturn": True,              # do not return to origin, default: False
            "optimized": 0.08              # optional, tolerance to which it was optimized, default: 0 (not optimized)
        }
        "raster":                          # optional
        {
            "passes":
            [
                {
                    "images": [0]
                    "seekrate": 6000,      # optional
                    "feedrate": 3000,
                    "intensity": 100,
                    "air_assist": "pass",  # optional (feed, pass, off), default: pass
                    "aux1_assist": "off",  # optional (feed, pass, off), default: off
                },
            ]
            "images":
            [
                [pos, size, <data>],               # pos: [x,y], size: [w,h], data in base64
                {
                    "pos": (100,50),
                    "size": (320,240),
                    "data": <data in base64>
                }
            ]
        }
    }
    ###########################################################################
    """

    if not jobdict.has_key('raster') and not jobdict.has_key('vector'):
        print "ERROR: invalid job"
        return

    # ### rasters
    # if jobdict.has_key('raster'):
    #     if jobdict['raster'].has_key('passes') and jobdict['raster'].has_key('images'):
    #         passes = jobdict['raster']['passes']
    #         images = jobdict['raster']['images']
    #         for pass_ in passes:
    #             # turn on assists if set to 'pass'
    #             if 'air_assist' in pass_:
    #                 if pass_['air_assist'] == 'pass':
    #                     air_on()
    #             else:
    #                 air_on()    # also default this behavior
    #             if 'aux1_assist' in pass_ and pass_['aux1_assist'] == 'pass':
    #                 aux1_on()
    #             absolute()
    #             # loop through all images of this pass
    #             for img_index in pass_['images']:
    #                 if img_index < len(images):
    #                     img = images[img_index]
    #                     pos = img["pos"]
    #                     size = img["size"]
    #                     data = img["data"]
    #                     posx = pos[0]
    #                     posy = pos[1]
    #                     # calc leadin/out
    #                     leadinpos = posx - conf['raster_leadin']
    #                     if leadinpos < 0:
    #                         leadinpos = 0
    #                     posright = posx + size[0]
    #                     leadoutpos = posright + conf['raster_leadin']
    #                     if leadoutpos > conf['workspace'][0]:
    #                         leadoutpos = conf['workspace'][0]

    #                     ### go through lines ############### TODO!!!!
    #                         # move to start
    #                         if 'seekrate' in pass_:
    #                             feedrate(pass_['seekrate'])
    #                         else:
    #                             feedrate(conf['seekrate'])
    #                         move(leadinpos, posy)
    #                         # assists
    #                         if 'air_assist' in pass_ and pass_['air_assist'] == 'feed':
    #                             air_on()
    #                         else:
    #                             air_on()  # also default this behavior
    #                         if 'aux1_assist' in pass_ and pass_['aux1_assist'] == 'feed':
    #                             aux1_on()
    #                         # lead-in
    #                         if 'feedrate' in pass_:
    #                             feedrate(pass_['feedrate'])
    #                         else:
    #                             feedrate(conf['feedrate'])     
    #                         move(posx, posy)
    #                         rastermove(posright, posy)
    #                         move(leadoutpos, posy)
    #                         # assists
    #                         if 'air_assist' in pass_ and pass_['air_assist'] == 'feed':
    #                             air_off()
    #                         else:
    #                             air_off()  # also default this behavior
    #                         if 'aux1_assist' in pass_ and pass_['aux1_assist'] == 'feed':
    #                             aux1_off()


    #             # turn off assists if set to 'pass'
    #             if 'air_assist' in pass_:
    #                 if pass_['air_assist'] == 'pass':
    #                     air_off()
    #             else:
    #                 air_off()  # also default this behavior
    #             if 'aux1_assist' in pass_ and pass_['aux1_assist'] == 'pass':
    #                 aux1_off()







    ### vectors
    if jobdict.has_key('vector'):
        if jobdict['vector'].has_key('passes') and jobdict['vector'].has_key('paths'):
            passes = jobdict['vector']['passes']
            paths = jobdict['vector']['paths']
            for pass_ in passes:
                # turn on assists if set to 'pass'
                if 'air_assist' in pass_:
                    if pass_['air_assist'] == 'pass':
                        air_on()
                else:
                    air_on()    # also default this behavior
                if 'aux1_assist' in pass_ and pass_['aux1_assist'] == 'pass':
                    aux1_on()
                # set absolute/relative
                if 'relative' not in pass_ or not pass_['relative']:
                    absolute()
                else:
                    relative()
                # loop through all paths of this pass
                for path_index in pass_['paths']:
                    if path_index < len(paths):
                        path = paths[path_index]
                        for polyline in path:
                            if len(polyline) > 0:
                                # first vertex -> seek
                                if 'seekrate' in pass_:
                                    feedrate(pass_['seekrate'])
                                else:
                                    feedrate(conf['seekrate'])
                                intensity(0.0)
                                is_2d = len(polyline[0]) == 2
                                if is_2d:
                                    move(polyline[0][0], polyline[0][1])
                                else:
                                    move(polyline[0][0], polyline[0][1], polyline[0][2])
                                # remaining verteces -> feed
                                if len(polyline) > 1:
                                    if 'feedrate' in pass_:
                                        feedrate(pass_['feedrate'])
                                    else:
                                        feedrate(conf['feedrate'])
                                    if 'intensity' in pass_:
                                        intensity(pass_['intensity'])
                                    # turn on assists if set to 'feed'
                                    # also air_assist defaults to 'feed'                 
                                    if 'air_assist' in pass_ and pass_['air_assist'] == 'feed':
                                        air_on()
                                    if 'aux1_assist' in pass_ and pass_['aux1_assist'] == 'feed':
                                        aux1_on()
                                    # TODO dwell according to pierce time
                                    if is_2d:
                                        for i in xrange(1, len(polyline)):
                                            move(polyline[i][0], polyline[i][1])
                                    else:
                                        for i in xrange(1, len(polyline)):
                                            move(polyline[i][0], polyline[i][1], polyline[i][2])
                                    # turn off assists if set to 'feed'
                                    if 'air_assist' in pass_ and pass_['air_assist'] == 'feed':
                                        air_off()
                                    if 'aux1_assist' in pass_ and pass_['aux1_assist'] == 'feed':
                                        aux1_off()
                # turn off assists if set to 'pass'
                if 'air_assist' in pass_:
                    if pass_['air_assist'] == 'pass':
                        air_off()
                else:
                    air_off()  # also default this behavior
                if 'aux1_assist' in pass_ and pass_['aux1_assist'] == 'pass':
                    aux1_off()

    # return to origin
    feedrate(conf['seekrate'])
    intensity(0.0)
    if jobdict['vector'].has_key('noreturn') and jobdict['vector']['noreturn']:
        pass
    else:
        move(0, 0, 0)



def pause():
    global SerialLoop
    with SerialLoop.lock:
        if SerialLoop.tx_buffer:
            SerialLoop._paused = True

def unpause():
    global SerialLoop
    with SerialLoop.lock:
        SerialLoop._paused = False


def stop():
    """Force stop condition."""
    global SerialLoop
    with SerialLoop.lock:
        SerialLoop.tx_buffer.clear()
        SerialLoop.job_size = 0
        SerialLoop.request_stop = True


def unstop():
    """Resume from stop condition."""
    global SerialLoop
    with SerialLoop.lock:
        SerialLoop.request_resume = True


def air_on():
    global SerialLoop
    with SerialLoop.lock:
        SerialLoop.send_command(CMD_AIR_ENABLE)

def air_off():
    global SerialLoop
    with SerialLoop.lock:
        SerialLoop.send_command(CMD_AIR_DISABLE)


def aux1_on():
    global SerialLoop
    with SerialLoop.lock:
        SerialLoop.send_command(CMD_AUX1_ENABLE)

def aux1_off():
    global SerialLoop
    with SerialLoop.lock:
        SerialLoop.send_command(CMD_AUX1_DISABLE)


def aux2_on():
    global SerialLoop
    with SerialLoop.lock:
        SerialLoop.send_command(CMD_AUX2_ENABLE)

def aux2_off():
    global SerialLoop
    with SerialLoop.lock:
        SerialLoop.send_command(CMD_AUX2_DISABLE)


def set_offset_table():
    global SerialLoop
    with SerialLoop.lock:
        SerialLoop.send_command(CMD_SET_OFFSET_TABLE)

def set_offset_custom():
    global SerialLoop
    with SerialLoop.lock:
        SerialLoop.send_command(CMD_SET_OFFSET_CUSTOM)

def def_offset_table(x, y, z):
    global SerialLoop
    with SerialLoop.lock:
        SerialLoop.send_param(PARAM_OFFTABLE_X, x)
        SerialLoop.send_param(PARAM_OFFTABLE_Y, y)
        SerialLoop.send_param(PARAM_OFFTABLE_Z, z)

def def_offset_custom(x, y, z):
    global SerialLoop
    with SerialLoop.lock:
        SerialLoop.send_param(PARAM_OFFCUSTOM_X, x)
        SerialLoop.send_param(PARAM_OFFCUSTOM_Y, y)
        SerialLoop.send_param(PARAM_OFFCUSTOM_Z, z)

def sel_offset_table():
    global SerialLoop
    with SerialLoop.lock:
        SerialLoop.send_command(CMD_SEL_OFFSET_TABLE)

def sel_offset_custom():
    global SerialLoop
    with SerialLoop.lock:
        SerialLoop.send_command(CMD_SEL_OFFSET_CUSTOM)


def testjob(jobname="Lasersaur", feedrate=2000, intensity=10):
    j = json.load(open(os.path.join(conf['rootdir'], 'backend', 'testjobs', jobname+'.lsa')))
    if "vector" in j:
        j['vector']['passes'] = [{
            "paths":[0],
            "feedrate":feedrate,
            "intensity":intensity }]
    
    job(j)

def torturejob():
    testjob('k4', 4000)



if __name__ == "__main__":
    # run like this to profile: python -m cProfile lasersaur.py
    connect()
    if connected():
        testjob()
        time.sleep(0.5)
        while not status()['ready']:
            time.sleep(1)
            sys.stdout.write('.')
        close()
