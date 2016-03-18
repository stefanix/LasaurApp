
import os
import sys
import time
import math
import json
import copy
import numpy
import threading
import serial
import serial.tools.list_ports
from config import conf
import statserver


__author__  = 'Stefan Hechenberger <stefan@nortd.com>'

markers_tx = {
    "\x01": "CMD_STOP",
    "\x02": "CMD_RESUME",
    "\x03": "CMD_STATUS",
    "\x04": "CMD_SUPERSTATUS",
    "\x05": "CMD_CHUNK_PROCESSED",
    "\x09": "STATUS_END",

    "A": "CMD_NONE",
    "B": "CMD_LINE",
    "C": "CMD_DWELL",

    "E": "CMD_REF_RELATIVE",
    "F": "CMD_REF_ABSOLUTE",

    "G": "CMD_HOMING",

    "H": "CMD_SET_OFFSET_TABLE",
    "I": "CMD_SET_OFFSET_CUSTOM",
    "J": "CMD_SEL_OFFSET_TABLE",
    "K": "CMD_SEL_OFFSET_CUSTOM",

    "L": "CMD_AIR_ENABLE",
    "M": "CMD_AIR_DISABLE",
    "N": "CMD_AUX1_ENABLE",
    "O": "CMD_AUX1_DISABLE",
    "P": "CMD_AUX2_ENABLE",
    "Q": "CMD_AUX2_DISABLE",

    "x": "PARAM_TARGET_X",
    "y": "PARAM_TARGET_Y",
    "z": "PARAM_TARGET_Z",
    "f": "PARAM_FEEDRATE",
    "p": "PARAM_PULSE_FREQUENCY",
    "d": "PARAM_PULSE_DURATION",
    "r": "PARAM_RASTER_BYTES",
    "h": "PARAM_OFFTABLE_X",
    "i": "PARAM_OFFTABLE_Y",
    "j": "PARAM_OFFTABLE_Z",
    "k": "PARAM_OFFCUSTOM_X",
    "l": "PARAM_OFFCUSTOM_Y",
    "m": "PARAM_OFFCUSTOM_Z",
}

markers_rx = {
    # status: error flags
    '!': "ERROR_SERIAL_STOP_REQUEST",
    '"': "ERROR_RX_BUFFER_OVERFLOW",

    '$': "ERROR_LIMIT_HIT_X1",
    '%': "ERROR_LIMIT_HIT_X2",
    '&': "ERROR_LIMIT_HIT_Y1",
    '*': "ERROR_LIMIT_HIT_Y2",
    '+': "ERROR_LIMIT_HIT_Z1",
    '-': "ERROR_LIMIT_HIT_Z2",

    '#': "ERROR_INVALID_MARKER",
    ':': "ERROR_INVALID_DATA",
    '<': "ERROR_INVALID_COMMAND",
    '>': "ERROR_INVALID_PARAMETER",
    "(": "ERROR_VALUE_OUT_OF_RANGE",
    '=': "ERROR_TRANSMISSION_ERROR",
    ',': "ERROR_USART_DATA_OVERRUN",

    # status: info flags
    'A': "INFO_IDLE_YES",
    'B': "INFO_DOOR_OPEN",
    'C': "INFO_CHILLER_OFF",

    # status: info params
    'x': "INFO_POS_X",
    'y': "INFO_POS_Y",
    'z': "INFO_POS_Z",
    'v': "INFO_VERSION",
    'w': "INFO_BUFFER_UNDERRUN",
    'u': "INFO_STACK_CLEARANCE",
    't': "INFO_DELAYED_MICROSTEPS",

    '~': "INFO_HELLO",

    'a': "INFO_OFFCUSTOM_X",
    'b': "INFO_OFFCUSTOM_Y",
    'c': "INFO_OFFCUSTOM_Z",
    # 'd': "INFO_TARGET_X",
    # 'e': "INFO_TARGET_Y",
    # 'f': "INFO_TARGET_Z",
    'g': "INFO_FEEDRATE",
    'h': "INFO_PULSE_FREQUENCY",
    'i': "INFO_PULSE_DURATION",
}

# create a global constant for each of the names above
for char, name in markers_tx.items():
    globals()[name] = char
for char, name in markers_rx.items():
    globals()[name] = char

## more firmware constants, they need wo match device firmware
TX_CHUNK_SIZE = 16 # number of bytes written to the device in one go
RX_CHUNK_SIZE = 32
FIRMBUF_SIZE = 256
RASTER_BYTES_MAX = 60
PULSE_SECONDS = 31.875e-6 # see laser.c
MINIMUM_PULSE_TICKS = 3 # unit: PULSE_SECONDS
MAXIMUM_PULSE_TICKS = 127 # unit: PULSE_SECONDS
ACCELERATION = 1800000.0 # mm/min^2, divide by (60*60) to get mm/sec^2

SerialLoop = None

class SerialLoopClass(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

        self.device = None
        self.tx_buffer = []
        self.tx_pos = 0

        self.firmbuf_used = 0

        # used for calculating percentage done
        self.job_size = 0

        # status flags
        self._status = {}
        self._s = {}
        self.reset_status()
        self._paused = False

        self.request_stop = False
        self.request_resume = False
        self.request_status = 2       # 0: no request, 1: normal request, 2: super request

        self.pdata_count = 0
        self.pdata_chars = [None, None, None, None]

        self.stop_processing = False

        self.deamon = True  # kill thread when main thread exits

        # lock mechanism for shared data
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
            'underruns': 0,
            'stackclear': 999999,
            'delayed_microsteps': 0,

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
            'pulse_frequency': 0.0,
            'pulse_duration': 0.0
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


    def send_raster_data(self, data):
        for byte in data:
            v = byte + 128
            assert v <= 255
            # FIXME: not very memory efficient, check if it is a problem when large files are queued
            self.tx_buffer.append(chr(v))
        self.job_size += len(data)


    def run(self):
        """Main loop of the serial thread."""
        last_write = 0
        last_status_request = 0
        while True:
            if self.stop_processing:
                break
            with self.lock:
                # read/write
                if self.device:
                    try:
                        self._serial_read()
                        # (1/0.008)*16 = 2000 bytes/s
                        # for raster we need: 10(10000/60.0) = 1660 bytes/s
                        self._serial_write()
                        # if time.time()-last_write > 0.01:
                        #     sys.stdout.write('~')
                        # last_write = time.time()
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
                # status request
                if time.time()-last_status_request > 0.5:
                    if self._status['ready']:
                        self.request_status = 2  # ready -> super request
                    else:
                        self.request_status = 1  # processing -> normal request
                    last_status_request = time.time()
                # flush stdout, so print shows up timely
                sys.stdout.flush()
            time.sleep(0.004)



    def _serial_read(self):
        for char in self.device.read(RX_CHUNK_SIZE):
            # sys.stdout.write('('+char+','+str(ord(char))+')')
            if ord(char) < 32:  ### flow
                if char == CMD_CHUNK_PROCESSED:
                    self.firmbuf_used -= TX_CHUNK_SIZE
                    if self.firmbuf_used < 0:
                        print "ERROR: firmware buffer tracking to low"
                elif char == STATUS_END:
                    # status frame complete, compile status
                    self._status, self._s = self._s, self._status
                    self._status['paused'] = self._paused
                    self._status['serial'] = bool(self.device)
                    if self.job_size == 0:
                        self._status['progress'] = 1.0
                    else:
                        self._status['progress'] = \
                          round(SerialLoop.tx_pos/float(SerialLoop.job_size),3)
                    self._s['stops'].clear()
                    self._s['info'].clear()
                    self._s['ready'] = False
                    self._s['underruns'] = self._status['underruns']
                    self._s['stackclear'] = self._status['stackclear']
                    self._s['delayed_microsteps'] = self._status['delayed_microsteps']
                    # send through status server
                    if self.server_enabled:
                        statusjson = json.dumps(self._status)
                        statserver.send(statusjson)
                        statserver.on_connected_message(statusjson)
            elif 31 < ord(char) < 65:  ### stop error markers
                # chr is in [!-@], process flag
                if char == ERROR_LIMIT_HIT_X1:
                    self._s['stops']['x1'] = True
                    print "ERROR firmware: limit hit x1"
                elif char == ERROR_LIMIT_HIT_X2:
                    self._s['stops']['x2'] = True
                    print "ERROR firmware: limit hit x2"
                elif char == ERROR_LIMIT_HIT_Y1:
                    self._s['stops']['y1'] = True
                    print "ERROR firmware: limit hit y1"
                elif char == ERROR_LIMIT_HIT_Y2:
                    self._s['stops']['y2'] = True
                    print "ERROR firmware: limit hit y2"
                elif char == ERROR_LIMIT_HIT_Z1:
                    self._s['stops']['z1'] = True
                    print "ERROR firmware: limit hit z1"
                elif char == ERROR_LIMIT_HIT_Z2:
                    self._s['stops']['z2'] = True
                    print "ERROR firmware: limit hit z2"
                elif char == ERROR_SERIAL_STOP_REQUEST:
                    self._s['stops']['requested'] = True
                    print "ERROR firmware: stop request"
                elif char == ERROR_RX_BUFFER_OVERFLOW:
                    self._s['stops']['buffer'] = True
                    print "ERROR firmware: rx buffer overflow"
                elif char == ERROR_INVALID_MARKER:
                    self._s['stops']['marker'] = True
                    print "ERROR firmware: invalid marker"
                elif char == ERROR_INVALID_DATA:
                    self._s['stops']['data'] = True
                    print "ERROR firmware: invalid data"
                elif char == ERROR_INVALID_COMMAND:
                    self._s['stops']['command'] = True
                    print "ERROR firmware: invalid command"
                elif char == ERROR_INVALID_PARAMETER:
                    self._s['stops']['parameter'] = True
                    print "ERROR firmware: invalid parameter"
                elif char == ERROR_TRANSMISSION_ERROR:
                    self._s['stops']['transmission'] = True
                    print "ERROR firmware: transmission"
                elif char == ERROR_USART_DATA_OVERRUN:
                    self._s['stops']['usart'] = True
                    print "ERROR firmware: USART data overrun"
                else:
                    print "ERROR: invalid stop error marker"
                # in stop mode, print recent transmission
                recent_chars = self.tx_buffer[max(0,self.tx_pos-128):self.tx_pos]
                print "RECENT TX BUFFER:"
                for char in recent_chars:
                    if markers_tx.has_key(char):
                        print "\t%s" % (markers_tx[char])
                    elif 127 < ord(char) < 256:
                        print "\t(data byte)"
                    else:
                        print "\t(invalid)"
                print "----------------"
                # stop mode housekeeping
                self.tx_buffer = []
                self.tx_pos = 0
                self.job_size = 0
                self._paused = False
                self.device.flushOutput()
                self.pdata_count = 0
            elif 64 < ord(char) < 91:  # info flags
                # chr is in [A-Z], info flag
                if char == INFO_IDLE_YES:
                    if not self.tx_buffer:
                        self._s['ready'] = True
                elif char == INFO_DOOR_OPEN:
                    self._s['info']['door'] = True
                elif char == INFO_CHILLER_OFF:
                    self._s['info']['chiller'] = True
                else:
                    print "ERROR: invalid info flag"
                    sys.stdout.write('('+char+','+str(ord(char))+')')
                self.pdata_count = 0
            elif 96 < ord(char) < 123:  # parameter
                # char is in [a-z], process parameter
                num = ((((ord(self.pdata_chars[3])-128)*2097152
                       + (ord(self.pdata_chars[2])-128)*16384
                       + (ord(self.pdata_chars[1])-128)*128
                       + (ord(self.pdata_chars[0])-128) )- 134217728)/1000.0)
                if char == INFO_POS_X:
                    self._s['pos'][0] = num
                elif char == INFO_POS_Y:
                    self._s['pos'][1] = num
                elif char == INFO_POS_Z:
                    self._s['pos'][2] = num
                elif char == INFO_VERSION:
                    num = str(int(num)/100.0)
                    self._s['firmver'] = num
                elif char == INFO_BUFFER_UNDERRUN:
                    self._s['underruns'] = num
                elif char == INFO_STACK_CLEARANCE:
                    self._s['stackclear'] = num
                elif char == INFO_DELAYED_MICROSTEPS:
                    self._s['delayed_microsteps'] = num
                # super status
                elif char == INFO_OFFCUSTOM_X:
                    self._s['offset'][0] = num
                elif char == INFO_OFFCUSTOM_Y:
                    self._s['offset'][1] = num
                elif char == INFO_OFFCUSTOM_Z:
                    self._s['offset'][2] = num
                elif char == INFO_FEEDRATE:
                    self._s['feedrate'] = num
                elif char == INFO_PULSE_FREQUENCY:
                    self._s['pulse_frequency'] = num
                elif char == INFO_PULSE_DURATION:
                    self._s['pulse_duration'] = num
                else:
                    print "ERROR: invalid param"
                self.pdata_count = 0
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
                self.pdata_count = 0




    def _serial_write(self):
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
        ### send buffer chunk
        if self.tx_buffer and len(self.tx_buffer) > self.tx_pos:
            if not self._paused:
                if (FIRMBUF_SIZE - self.firmbuf_used) > TX_CHUNK_SIZE:
                    try:
                        # to_send = ''.join(islice(self.tx_buffer, 0, TX_CHUNK_SIZE))
                        to_send = self.tx_buffer[self.tx_pos:self.tx_pos+TX_CHUNK_SIZE]
                        expectedSent = len(to_send)
                        # by protocol duplicate every char
                        to_send_double = []
                        for c in to_send:
                            to_send_double.append(c)
                            to_send_double.append(c)
                        to_send = ''.join(to_send_double)
                        #
                        t_prewrite = time.time()
                        actuallySent = self.device.write(to_send)
                        if actuallySent != expectedSent*2:
                            print "ERROR: write did not complete"
                            assumedSent = 0
                        else:
                            assumedSent = expectedSent
                            self.firmbuf_used += assumedSent
                            if self.firmbuf_used > FIRMBUF_SIZE:
                                print "ERROR: firmware buffer tracking too high"
                        if time.time() - t_prewrite > 0.1:
                            print "WARN: write delay 1"
                    except serial.SerialTimeoutException:
                        assumedSent = 0
                        print "ERROR: writeTimeoutError 2"
                    # for i in range(assumedSent):
                    #     self.tx_buffer.popleft()
                    self.tx_pos += assumedSent
        else:
            if self.tx_buffer:  # job finished sending
                self.job_size = 0
                self.tx_buffer = []
                self.tx_pos = 0




    def _send_char(self, char):
        try:
            t_prewrite = time.time()
            # self.device.write(char)
            # print "send_char: [%s,%s]" % (str(ord(char)),str(ord(char)))
            self.device.write(char+char)  # by protocol send twice
            if time.time() - t_prewrite > 0.1:
                pass
                # print "WARN: write delay 2"
        except serial.SerialTimeoutException:
            print "ERROR: writeTimeoutError 1"





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
                if INFO_HELLO in lasaur_hello:
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
                if INFO_HELLO in lasaur_hello:
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

        # Create serial device with read timeout set to 0.
        # This results in the read() being non-blocking.
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
        print SerialLoop._status
        # FIXME: the check below breaks for python scripts that import
        # this file and start with a homing comand in a very bad way:
        # it skips the homing because _status[] has not yet been
        # changed from the defaults, and then continues the job. Do we
        # really need this check at this level? If yes, we probably
        # should throw an exception to prevent the script from sending
        # the commands that follow the homing.
        #
        #if SerialLoop._status['ready'] or SerialLoop._status['stops']:
        #    SerialLoop.send_command(CMD_HOMING)
        #else:
        #    print "WARN: ignoring homing command while job running"

        SerialLoop.send_command(CMD_HOMING)
    current_parameters['x'] = 0
    current_parameters['y'] = 0
    current_parameters['z'] = 0

current_parameters = {
    'feedrate': None,
    'pulse_frequency': None,
    'pulse_duration': None,
    'x': None,
    'y': None,
    'z': None,
}

def feedrate(val):
    global SerialLoop
    with SerialLoop.lock:
        SerialLoop.send_param(PARAM_FEEDRATE, val)
    current_parameters['feedrate'] = val

def intensity(percent, emulate_old_method=False):
    """Set laser intensity (in percent)

    This selects a suitable pulse frequency and duration for the next
    move, calling pulse_frequency() and pulse_duration() on your behalf.
    """
    assert percent <= 100 and percent >= 0
    if emulate_old_method:
        # approximate what the old firmware did
        old_intensity = percent / 100.0 * 255.0
        if old_intensity > 40:
            freq_hz = 3900
        elif old_intensity > 10:
            freq_hz = 489
        else:
            freq_hz = 122
        # find closest feasible pulse duration (rounding up to avoid higher frequencies)
        pulse = math.ceil((percent/100.0) * 1.0/freq_hz / PULSE_SECONDS)
        if pulse > 0:
            # find a slightly better frequency
            freq_hz = 1.0 / (pulse * PULSE_SECONDS / (percent/100.0))
    else:
        if percent == 0:
            pulse = 0
            freq_hz = 0
        else:
            pulse = 3 + math.floor(6 * percent/100)
            freq_hz = 1.0 / (pulse * PULSE_SECONDS / (percent/100.0))

    if percent > 99:
        pulse += 1 # make sure pulses overlap slightly

    #print '--> %d Hz, pulse duration %dus' % (freq_hz, pulse * PULSE_SECONDS / 1e-6)
    pulse_frequency(freq_hz)
    pulse_duration(pulse)

def pulse_frequency(freq):
    """Set laser pulse frequency (pulses per second)

    This affects the laser intensity of the next move, in combination
    with pulse_duration().
    """
    global SerialLoop
    with SerialLoop.lock:
        SerialLoop.send_param(PARAM_PULSE_FREQUENCY, freq)
    current_parameters['pulse_frequency'] = freq

def pulse_duration(duration):
    """Set laser pulse duration (integer ticks)

    Sets the pulse duration of the next move, in integer ticks between
    0 and 255. One tick is 31.875e-6 seconds (PULSE_SECONDS).
    """
    assert duration >= 0 and duration <= 255
    global SerialLoop
    with SerialLoop.lock:
        SerialLoop.send_param(PARAM_PULSE_DURATION, duration)
    current_parameters['pulse_duration'] = duration

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
    current_parameters['x'] = x
    current_parameters['y'] = y
    current_parameters['z'] = z

def _raster_move_raw(x, y, data):
    """Raster move with data length limited by firmware"""
    global SerialLoop
    with SerialLoop.lock:
        assert len(data) <= RASTER_BYTES_MAX
        SerialLoop.send_param(PARAM_TARGET_X, x)
        SerialLoop.send_param(PARAM_TARGET_Y, y)
        SerialLoop.send_param(PARAM_RASTER_BYTES, len(data))
        SerialLoop.send_command(CMD_LINE)
        SerialLoop.send_raster_data(data)
        SerialLoop.send_param(PARAM_RASTER_BYTES, 0)

def raster_move(x, y, data, verbose=False):
    """Execute a raster move from the current position

    Each data byte corresponds to a pulse. The number of pulses per mm
    can be calculated from the data length.  The raster move starts
    with a pulse and ends at (x, y) where the next pulse would be
    expected.
    
    Data bytes must be <= 127. They encode the pulse length in
    firmware ticks, like pulse_duration() does.  One tick is 31.875e-6
    seconds (PULSE_SECONDS).
    
    Calls to intensity(), pulse_duration() or pulse_frequency() do not
    affect the raster move.  The laser power is already fully defined
    by the raster move itself. For example, you can double the power
    by repeating every data byte once.
    """
    global SerialLoop
    data = numpy.array(data, dtype='uint8', copy=False)
    x0, y0 = current_parameters['x'], current_parameters['y']
    length = math.hypot(x0-x, y0-y)
    bytes_total = len(data)
    mm_per_second = current_parameters['feedrate'] / 60.0
    freq = bytes_total * mm_per_second / length
    if verbose:
        print 'raster_move from (%.3f, %.3f) to (%.3f, %.3f) at %.0f mm/min' % (x0, y0, x, y, current_parameters['feedrate'])
        print '  length %.1f mm, %d bytes, data rate %.0f bytes/sec (%.f%% of serial capacity)' % (length, bytes_total, freq, 100*freq/(conf['baudrate']/10/2))
        print '  byte duration %.0f us, pulse density %.3f ppmm (%.3f mm between pulses)' % (1.0/freq/1e-6, bytes_total/length, length/bytes_total)
        print '  max pulse duration in data: %d ticks (%.0f us)' % (data.max(), data.max()*PULSE_SECONDS/1e-6)
    freq_old = current_parameters['pulse_frequency']
    pulse_frequency(freq)
    n = RASTER_BYTES_MAX
    while len(data) > 0:
        chunk, data = data[:n], data[n:] 
        fac = float(len(data))/bytes_total
        px = fac*x0 + (1-fac)*x
        py = fac*y0 + (1-fac)*y
        _raster_move_raw(px, py, chunk)
    pulse_frequency(freq_old)
    current_parameters['x'] = x
    current_parameters['y'] = y

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
        SerialLoop.tx_buffer = []
        SerialLoop.tx_pos = 0
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
    # run like this to profile: python -m cProfile driveboard.py
    connect()
    if connected():
        testjob()
        time.sleep(0.5)
        while not status()['ready']:
            time.sleep(1)
            sys.stdout.write('.')
        close()
