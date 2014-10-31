
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
CMD_STOP = "!"
CMD_RESUME = "~"
CMD_STATUS = "?"
CMD_SUPERSTATUS = "&"

CMD_RASTER_DATA_START = '\x02'
CMD_RASTER_DATA_END = '\x03'

CMD_NONE = "A"
CMD_LINE = "B"
CMD_DWELL = "C"
CMD_RASTER = "D"

# CMD_SET_FEEDRATE = "E"
# CMD_SET_INTENSITY = "F"

CMD_REF_RELATIVE = "G" 
CMD_REF_ABSOLUTE = "H"

CMD_HOMING = "I"

CMD_SET_OFFSET_TABLE = "J"
CMD_SET_OFFSET_CUSTOM = "K"
# CMD_DEF_OFFSET_TABLE = "L"
# CMD_DEF_OFFSET_CUSTOM = "M"
CMD_SEL_OFFSET_TABLE = "N"
CMD_SEL_OFFSET_CUSTOM = "O"

CMD_AIR_ENABLE = "P"
CMD_AIR_DISABLE = "Q"
CMD_AUX1_ENABLE = "R"
CMD_AUX1_DISABLE = "S"
CMD_AUX2_ENABLE = "T"
CMD_AUX2_DISABLE = "U"


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

REQUEST_READY = '\x14'
################


################ RECEIVING PROTOCOL
STATUS_END = '\x17'

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
INFO_READY_NO = 'B'
INFO_DOOR_OPEN = 'C'
INFO_DOOR_CLOSED = 'D'
INFO_CHILLER_OFF = 'E'
INFO_CHILLER_ON = 'F'
INFO_FEC_CORRECTION = 'G'
INFO_BUFFER_UNDERRUN = 'H'

# status: info params
INFO_POS_X = 'x'
INFO_POS_Y = 'y'
INFO_POS_Z = 'z'
INFO_VERSION = 'v'

INFO_HELLO = '~'
READY = '\x12'

INFO_OFFCUSTOM_X = 'a'
INFO_OFFCUSTOM_Y = 'b'
INFO_OFFCUSTOM_Z = 'c'
INFO_TARGET_X = 'd'
INFO_TARGET_Y = 'e'
INFO_TARGET_Z = 'f'
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
        self.remoteXON = True

        # TX_CHUNK_SIZE - this is the number of bytes to be 
        # written to the device in one go. It needs to match the device.
        self.TX_CHUNK_SIZE = 64
        self.RX_CHUNK_SIZE = 256
        self.nRequested = 0
        self.last_request_ready = 0
        self.saidhello = False
        
        # used for calculating percentage done
        self.job_size = 0

        # status flags
        self.ready = False
        self._status = {}
        self.reset_status()

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



    def reset_status(self):
        self._status = {
            'appver':conf['version'],
            'firmver': None,
            'ready': False,
            'paused': False,
            'serial': False,

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

            ### info
            # door
            # chiller
            'info': {},

            # head position
            'pos':[0.0, 0.0, 0.0],

            ### super
            'offset': [0.0, 0.0, 0.0],
            # 'pos_target': [0.0, 0.0, 0.0],
            'feedrate': 0.0,
            'intensity': 0.0,
            'duration': 0.0,
            'pixelwidth': 0.0


            # removed
            # limit_hit
            # 'bad_number_format_error': False,
            # 'expected_command_letter_error': False,
            # 'unsupported_statement_error': False,            
        }


    def print_status(self):
        symap = {False:'[ ]', True:'[x]' }
        keys = self._status.keys()
        keys.sort()
        for k in keys:
            if k not in ['firmver', 'feedrate', 'intensity', 'duration', 'pixelwidth']:
                if k == 'pos':
                    print  'x: ' + str(self._status['pos'][0])
                    print  'y: ' + str(self._status['pos'][1])
                    print  'z: ' + str(self._status['pos'][2])
                # elif k == 'pos_target':
                #     print  'x_target: ' + str(self._status['pos_target'][0])
                #     print  'y_target: ' + str(self._status['pos_target'][1])
                #     print  'z_target: ' + str(self._status['pos_target'][2])
                else:
                    print symap[self._status[k]] + ' ' + k

        print  'firmver: ' + str(self._status['firmver'])
        print  "%smm/min %s% %ss %smm" % (str(self._status['feedrate']), 
            str(self._status['intensity']), str(self._status['duration']), 
            str(self._status['pixelwidth']))


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
            with self.lock:
                self._process()
                if time.time()-last_status_request > 0.5:
                    if self.ready:
                        self.request_status = 2  # ready -> super request
                    else:
                        self.request_status = 1  # processing -> normal request
                    last_status_request = time.time()
            if self.stop_processing:
                break

    
    def _process(self):
        """Continuously call this to keep processing queue."""    
        if self.device and not self._status['paused']:
            try:
                ### receiving
                chars = self.device.read(self.RX_CHUNK_SIZE)
                # # discard until machine says hello
                # if not self.saidhello:
                #     hellopos = chars.find(INFO_HELLO)
                #     if hellopos == -1:  # still no hello
                #         chars = ''  # discard
                #     else:  # now got hello
                #         self.saidhello = True
                #         chars = chars[hellopos:]
                if len(chars) > 0:
                    ## process chars
                    for char in chars:
                        # sys.stdout.write('('+char+','+str(ord(char))+')')
                        # sys.stdout.flush()
                        if ord(char) < 32:  ### flow
                            ## check for data request
                            if char == READY:
                                self.nRequested = self.TX_CHUNK_SIZE
                            elif char == STATUS_END:
                                # status block complete -> send through status server
                                self._status['ready'] = self.ready
                                self._status['serial'] = bool(self.device)
                                statusjson = json.dumps(self._status)
                                statserver.send(statusjson)
                                statserver.on_connected_message(statusjson)
                        elif ord(char) < 128:  ### markers
                            if 32 < ord(char) < 65: # stop error flags                            
                                # chr is in [!-@], process flag
                                if char == ERROR_LIMIT_HIT_X1:
                                    self._status['stops']['x1'] = True
                                elif char == ERROR_LIMIT_HIT_X2:
                                    self._status['stops']['x2'] = True
                                elif char == ERROR_LIMIT_HIT_Y1:
                                    self._status['stops']['y1'] = True
                                elif char == ERROR_LIMIT_HIT_Y2:
                                    self._status['stops']['y2'] = True
                                elif char == ERROR_LIMIT_HIT_Z1:
                                    self._status['stops']['z1'] = True
                                elif char == ERROR_LIMIT_HIT_Z2:
                                    self._status['stops']['z2'] = True
                                elif char == ERROR_SERIAL_STOP_REQUEST:
                                    self._status['stops']['requested'] = True
                                elif char == ERROR_RX_BUFFER_OVERFLOW:
                                    self._status['stops']['buffer'] = True                                    
                                elif char == ERROR_INVALID_MARKER:
                                    self._status['stops']['marker'] = True
                                elif char == ERROR_INVALID_DATA:
                                    self._status['stops']['data'] = True
                                elif char == ERROR_INVALID_COMMAND:
                                    self._status['stops']['command'] = True
                                elif char == ERROR_INVALID_PARAMETER:
                                    self._status['stops']['parameter'] = True
                                elif char == ERROR_TRANSMISSION_ERROR:
                                    self._status['stops']['transmission'] = True
                                # in stop mode
                                self.tx_buffer.clear()
                                self.job_size = 0
                                # not ready whenever in stop mode
                                self.ready = False

                            elif 64 < ord(char) < 91:  # info flags
                                # chr is in [A-Z], info flag
                                if char == INFO_FEC_CORRECTION:
                                    sys.stdout.write("\nFEC Correction!\n")
                                    sys.stdout.flush()                                              
                                    # self._status['fec_correction'] = True
                                elif char == INFO_READY_YES:
                                    self.ready = True
                                elif char == INFO_READY_NO:
                                    self.ready = False
                                elif char == INFO_DOOR_OPEN:
                                    self._status['info']['door'] = True
                                elif char == INFO_DOOR_CLOSED:
                                    del self._status['info']['door']
                                elif char == INFO_CHILLER_OFF:
                                    self._status['info']['chiller'] = True
                                elif char == INFO_CHILLER_ON:
                                    del self._status['info']['chiller']
                                elif char == INFO_BUFFER_UNDERRUN:
                                    sys.stdout.write("INFO: Firmware rx buffer empty.\n")
                                    sys.stdout.flush()  
                                else:
                                    print "ERROR: invalid flag"
                            elif 96 < ord(char) < 123:  # parameter
                                # char is in [a-z], process parameter
                                num = ((((ord(self.pdata_chars[3])-128)*2097152
                                       + (ord(self.pdata_chars[2])-128)*16384
                                       + (ord(self.pdata_chars[1])-128)*128
                                       + (ord(self.pdata_chars[0])-128) )- 134217728)/1000.0)
                                if char == INFO_POS_X:
                                    self._status['pos'][0] = num
                                elif char == INFO_POS_Y:
                                    self._status['pos'][1] = num
                                elif char == INFO_POS_Z:
                                    self._status['pos'][2] = num
                                elif char == INFO_VERSION:
                                    num = 'v' + str(int(num)/100.0)
                                    self._status['firmver'] = num
                                # super status
                                elif char == INFO_OFFCUSTOM_X:
                                    self._status['offset'][0] = num
                                elif char == INFO_OFFCUSTOM_Y:
                                    self._status['offset'][1] = num
                                elif char == INFO_OFFCUSTOM_Z:
                                    self._status['offset'][2] = num
                                # elif char == INFO_TARGET_X:
                                #     self._status['pos_target'][0] = num
                                # elif char == INFO_TARGET_Y:
                                #     self._status['pos_target'][1] = num
                                # elif char == INFO_TARGET_Z:
                                #     self._status['pos_target'][2] = num
                                elif char == INFO_FEEDRATE:
                                    self._status['feedrate'] = num
                                elif char == INFO_INTENSITY:
                                    self._status['intensity'] = num
                                elif char == INFO_DURATION:
                                    self._status['duration'] = num
                                elif char == INFO_PIXEL_WIDTH:
                                    self._status['pixelwidth'] = num
                                else:
                                    print "ERROR: invalid param"
                            # elif char == INFO_HELLO:
                                # print "Controller says Hello!"
                            else:
                                print ord(char)
                                print char
                                print "ERROR: invalid marker"
                            self.pdata_count = 0
                        else:  ### data
                            # char is in [128,255]
                            if self.pdata_count < 4:
                                self.pdata_chars[self.pdata_count] = char
                                self.pdata_count += 1
                            else:
                                print "ERROR: invalid data"                
                ### sending super commands (handled in serial rx interrupt)
                if self.request_status:
                    try:
                        if self.request_status == 1:
                            self.device.write(CMD_STATUS)
                        elif self.request_status == 2:
                            self.device.write(CMD_SUPERSTATUS)
                        self.device.flushOutput()
                        self.request_status = 0
                    except serial.SerialTimeoutException:
                        sys.stdout.write("\nsending status request: writeTimeoutError\n")
                        sys.stdout.flush()
                if self.request_stop:
                    try:
                        self.device.write(CMD_STOP)
                        self.device.flushOutput()
                        self.request_stop = False
                    except serial.SerialTimeoutException:
                        sys.stdout.write("\nsending stop request: writeTimeoutError\n")
                        sys.stdout.flush()
                if self.request_resume:
                    try:
                        self.device.write(CMD_RESUME)
                        self.device.flushOutput()
                        self.request_resume = False
                        # update status
                        self.reset_status()
                        self.request_status = 2  # super request
                    except serial.SerialTimeoutException:
                        sys.stdout.write("\nsending resume request: writeTimeoutError\n")
                        sys.stdout.flush()
                ### sending from buffer
                if self.tx_buffer:
                    if self.nRequested > 0:
                        try:
                            to_send = ''.join(islice(self.tx_buffer, 0, self.nRequested))
                            actuallySent = self.device.write(to_send)
                        except serial.SerialTimeoutException:
                            # skip, report
                            actuallySent = 0  # assume nothing has been sent
                            sys.stdout.write("\n_process: writeTimeoutError\n")
                            sys.stdout.flush()
                        for i in range(actuallySent):
                            self.tx_buffer.popleft()
                        self.nRequested -= actuallySent
                        if self.nRequested <= 0:
                            self.last_request_ready = 0  # make sure to request ready
                    else:
                        if (time.time()-self.last_request_ready) > 2.0:
                            # ask to send a ready byte
                            # only ask for this when sending is on hold
                            # only ask once (and after a big time out)
                            # print "=========================== REQUEST READY"
                            try:
                                actuallySent = self.device.write(REQUEST_READY)
                            except serial.SerialTimeoutException:
                                # skip, report
                                actuallySent = self.nRequested  # pyserial does not report this sufficiently
                                sys.stdout.write("\n_process: writeTimeoutError, on ready request\n")
                                sys.stdout.flush()
                            if actuallySent == 1:
                                self.last_request_ready = time.time()
                         
                else:
                    if self.job_size:
                        # print "\nstream finished!"
                        # print "(firmware may take some extra time to finalize)"
                        self.job_size = 0
            except OSError:
                # Serial port appears closed => reset
                self.close()
            except ValueError:
                # Serial port appears closed => reset
                self.close()     
        else:
            # serial disconnected
            self.ready = False

        # flush stdout, so print shows up timely
        sys.stdout.flush()






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

    

def connect(port=conf['serial_port'], baudrate=conf['baudrate']):
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
            SerialLoop.device = serial.Serial(port, baudrate, timeout=0.0001, writeTimeout=0.1)
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
        except serial.SerialException:
            SerialLoop = None
            print "ERROR: Cannot connect serial on port: %s" % (port)

        # start up status server
        statserver.start()
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
    else:
        ret = False
    SerialLoop = None
    # stop status server
    statserver.stop()
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


def print_status():
    global SerialLoop
    with SerialLoop.lock:
        SerialLoop.print_status()


def homing():
    """Run homing cycle."""
    global SerialLoop
    with SerialLoop.lock:
        if SerialLoop.ready or status()['stops']:
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
                    "air_assist": "pass",   # optional (feed, pass, off), default: pass
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
                    "image": [0]
                    "seekrate": 6000,      # optional
                    "feedrate": 3000,
                    "intensity": 100,
                },
            ]
            "images":
            [
                [pos, size, <data>],               # pos: [x,y], size: [w,h], data in base64
            ]
        }
    }
    ###########################################################################
    """

    ### rasters
    # if jobdict.has_key('rasterpass') and jobdict.has_key('rasters'):
    #     rseekrate = jobdict['rasterpass']['seekrate']
    #     rfeedrate = jobdict['rasterpass']['feedrate']
    #     rintensity = jobdict['rasterpass']['intensity']
    #     # TODO: queue raster

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
                                    if 'air_assist' in pass_:
                                        if pass_['air_assist'] == 'feed':
                                            air_on()
                                    else:
                                        air_on()  # also default this behavior
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
                                    # also air_assist defaults to 'feed'                 
                                    if 'air_assist' in pass_:
                                        if pass_['air_assist'] == 'feed':
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
            if jobdict['vector'].has_key('noreturn') and jobdict['vector']['noreturn']:
                pass
            else:
                move(0, 0, 0)



def pause():
    global SerialLoop
    with SerialLoop.lock:
        if SerialLoop.tx_buffer:
            SerialLoop._status['paused'] = True

def unpause():
    global SerialLoop
    with SerialLoop.lock:
        SerialLoop._status['paused'] = False


def stop():
    """Force stop condition."""
    global SerialLoop
    with SerialLoop.lock:
        SerialLoop.tx_buffer.clear()
        SerialLoop.job_size = 0
        # SerialLoop.reset_status()
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



def testjob():
    j = json.load(open(os.path.join(conf['rootdir'], 'backend', 'testjobs', 'Lasersaur.lsa')))
    job(j)

def torturejob():
    j = json.load(open(os.path.join(conf['rootdir'], 'backend', 'testjobs', 'k4.lsa')))
    job(j)


if __name__ == "__main__":
    # run like this to profile: python -m cProfile lasersaur.py
    connect()
    testjob()
    while not status()['ready']:
        time.sleep(1)
        sys.stdout.write('.')
    close()