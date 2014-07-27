
import os
import sys
import time
import serial
from serial.tools import list_ports
from collections import deque


__author__  = 'Stefan Hechenberger <stefan@nortd.com>'
__all__ = [
    'connect', 'connected', 'close',
    'process', 'percentage', 'homing',
    'feedrate', 'intensity', 'move',
    'pause', 'unpause', 'stop', 'unstop',
    'air_on', 'air_off', 'aux1_on', 'aux1_off', 'aux2_on', 'aux2_off',
    'set_offset_table', 'set_offset_custom',
    'def_offset_table', 'def_offset_custom',
    'sel_offset_table', 'sel_offset_custom' ]


CMD_NONE = "A"
CMD_LINE = "B"
CMD_DWELL = "C"
CMD_RASTER = "D"
CMD_HOMING = "E"

CMD_REF_RELATIVE = "F" 
CMD_REF_ABSOLUTE = "G"

CMD_SET_OFFSET_TABLE = "H"
CMD_SET_OFFSET_CUSTOM = "I"
CMD_DEF_OFFSET_TABLE = "J"
CMD_DEF_OFFSET_CUSTOM = "K"
CMD_SEL_OFFSET_TABLE = "L"
CMD_SEL_OFFSET_CUSTOM = "M"

CMD_AIR_ENABLE = "N"
CMD_AIR_DISABLE = "O"
CMD_AUX1_ENABLE = "P"
CMD_AUX1_DISABLE = "Q"
CMD_AUX2_ENABLE = "R"
CMD_AUX2_DISABLE = "S"

CMD_RASTER_DATA_START = '\x02'
CMD_RASTER_DATA_END = '\x03'

CMD_GET_STATUS = "?"

PARAM_TARGET_X = "x"
PARAM_TARGET_Y = "y" 
PARAM_TARGET_Z = "z" 
PARAM_FEEDRATE = "f"
PARAM_INTENSITY = "s"
PARAM_DURATION = "d"
PARAM_PIXEL_WIDTH = "p"

CMD_STOP = '!'
CMD_RESUME = '~'


class LasersaurClass:
    """Lasersaur serial control.
    Use Lasersaur singelton instead of instancing.
    """

    def __init__(self):
        self.device = None

        self.rx_buffer = ""
        self.tx_buffer = ""        
        self.remoteXON = True

        # TX_CHUNK_SIZE - this is the number of bytes to be 
        # written to the device in one go. It needs to match the device.
        self.TX_CHUNK_SIZE = 64
        self.RX_CHUNK_SIZE = 256
        self.nRequested = 0
        
        # used for calculating percentage done
        self.job_size = 0
        self.job_active = False

        # status flags
        self.status = {}
        self.reset_status()

        self.LASAURGRBL_FIRST_STRING = "LasaurGrbl"

        self.fec_redundancy = 2  # use forward error correction
        # self.fec_redundancy = 1  # use error detection

        self.ready_char = '\x12'
        self.request_ready_char = '\x14'
        self.last_request_ready = 0


    def reset_status(self):
        self.status = {
            'ready': True,
            'paused': False,  # this is also a control flag
            'buffer_overflow': False,
            'transmission_error': False,
            'bad_number_format_error': False,
            'expected_command_letter_error': False,
            'unsupported_statement_error': False,
            'power_off': False,
            'limit_hit': False,
            'serial_stop_request': False,
            'door_open': False,
            'chiller_off': False,
            'x': False,
            'y': False,
            'z': False,
            'firmware_version': None
        }


    def cancel_queue(self):
        self.tx_buffer = ''
        self.job_size = 0
        self.job_active = False
    
    
    def send_queue_as_ready(self):
        """Continuously call this to keep processing queue."""    
        if self.device and not self.status['paused']:
            try:
                ### receiving
                chars = self.device.read(self.RX_CHUNK_SIZE)
                if len(chars) > 0:
                    ## check for data request
                    if self.ready_char in chars:
                        # print "=========================== READY"
                        self.nRequested = self.TX_CHUNK_SIZE
                        #remove control chars
                        chars = chars.replace(self.ready_char, "")
                    ## assemble lines
                    self.rx_buffer += chars
                    while(1):  # process all lines in buffer
                        posNewline = self.rx_buffer.find('\n')
                        if posNewline == -1:
                            break  # no more complete lines
                        else:  # we got a line
                            line = self.rx_buffer[:posNewline]
                            self.rx_buffer = self.rx_buffer[posNewline+1:]
                        self.process_status_line(line)
                
                ### sending
                if self.tx_buffer:
                    if self.nRequested > 0:
                        try:
                            actuallySent = self.device.write(self.tx_buffer[:self.nRequested])
                        except serial.SerialTimeoutException:
                            # skip, report
                            actuallySent = self.nRequested  # pyserial does not report this sufficiently
                            sys.stdout.write("\nsend_queue_as_ready: writeTimeoutError\n")
                            sys.stdout.flush()
                        # sys.stdout.write(self.tx_buffer[:actuallySent])  # print w/ newline
                        self.tx_buffer = self.tx_buffer[actuallySent:]
                        self.nRequested -= actuallySent
                        if self.nRequested <= 0:
                            self.last_request_ready = 0  # make sure to request ready
                    elif self.tx_buffer[0] in ['!', '~']:  # send control chars no matter what
                        try:
                            actuallySent = self.device.write(self.tx_buffer[:1])
                        except serial.SerialTimeoutException:
                            actuallySent = self.nRequested
                            sys.stdout.write("\nsend_queue_as_ready: writeTimeoutError\n")
                            sys.stdout.flush()
                        self.tx_buffer = self.tx_buffer[actuallySent:]
                    else:
                        if (time.time()-self.last_request_ready) > 2.0:
                            # ask to send a ready byte
                            # only ask for this when sending is on hold
                            # only ask once (and after a big time out)
                            # print "=========================== REQUEST READY"
                            try:
                                actuallySent = self.device.write(self.request_ready_char)
                            except serial.SerialTimeoutException:
                                # skip, report
                                actuallySent = self.nRequested  # pyserial does not report this sufficiently
                                sys.stdout.write("\nsend_queue_as_ready: writeTimeoutError, on ready request\n")
                                sys.stdout.flush()
                            if actuallySent == 1:
                                self.last_request_ready = time.time()
                         
                else:
                    if self.job_active:
                        # print "\nG-code stream finished!"
                        # print "(LasaurGrbl may take some extra time to finalize)"
                        self.job_size = 0
                        self.job_active = False
                        # ready whenever a job is done, including a status request via '?'
                        self.status['ready'] = True
            except OSError:
                # Serial port appears closed => reset
                self.close()
            except ValueError:
                # Serial port appears closed => reset
                self.close()     
        else:
            # serial disconnected    
            self.status['ready'] = False  



    def process_status_line(self, line):
        if '#' in line[:3]:
            # print and ignore
            sys.stdout.write(line + "\n")
            sys.stdout.flush()
        elif '^' in line:
            sys.stdout.write("\nFEC Correction!\n")
            sys.stdout.flush()                                              
        else:
            if '!' in line:
                # in stop mode
                self.cancel_queue()
                # not ready whenever in stop mode
                self.status['ready'] = False
                sys.stdout.write(line + "\n")
                sys.stdout.flush()
            else:
                sys.stdout.write(".")
                sys.stdout.flush()

            if 'N' in line:
                self.status['bad_number_format_error'] = True
            if 'E' in line:
                self.status['expected_command_letter_error'] = True
            if 'U' in line:
                self.status['unsupported_statement_error'] = True

            if 'B' in line:  # Stop: Buffer Overflow
                self.status['buffer_overflow'] = True
            else:
                self.status['buffer_overflow'] = False

            if 'T' in line:  # Stop: Transmission Error
                self.status['transmission_error'] = True
            else:
                self.status['transmission_error'] = False                                

            if 'P' in line:  # Stop: Power is off
                self.status['power_off'] = True
            else:
                self.status['power_off'] = False

            if 'L' in line:  # Stop: A limit was hit
                self.status['limit_hit'] = True
            else:
                self.status['limit_hit'] = False

            if 'R' in line:  # Stop: by serial requested
                self.status['serial_stop_request'] = True
            else:
                self.status['serial_stop_request'] = False

            if 'D' in line:  # Warning: Door Open
                self.status['door_open'] = True
            else:
                self.status['door_open'] = False

            if 'C' in line:  # Warning: Chiller Off
                self.status['chiller_off'] = True
            else:
                self.status['chiller_off'] = False

            if 'X' in line:
                self.status['x'] = line[line.find('X')+1:line.find('Y')]

            if 'Y' in line:
                self.status['y'] = line[line.find('Y')+1:line.find('V')]

            if 'Z' in line:
                self.status['z'] = line[line.find('Z')+1:line.find('Z')]

            if 'V' in line:
                self.status['firmware_version'] = line[line.find('V')+1:]                     






    ###########################################################################
    ### API ###################################################################
    ###########################################################################

    def list_devices(self, baudrate):
        ports = []
        if os.name == 'posix':
            iterator = sorted(list_ports.grep('tty'))
            print "Found ports:"
            for port, desc, hwid in iterator:
                ports.append(port)
                print "%-20s" % (port,)
                print "    desc: %s" % (desc,)
                print "    hwid: %s" % (hwid,)            
        else:
            # iterator = sorted(list_ports.grep(''))  # does not return USB-style
            # scan for available ports. return a list of tuples (num, name)
            available = []
            for i in range(24):
                try:
                    s = serial.Serial(port=i, baudrate=baudrate)
                    ports.append(s.portstr)                
                    available.append( (i, s.portstr))
                    s.close()
                except serial.SerialException:
                    pass
            print "Found ports:"
            for n,s in available: print "(%d) %s" % (n,s)
        return ports

            
    def match_device(self, search_regex, baudrate):
        if os.name == 'posix':
            matched_ports = list_ports.grep(search_regex)
            if matched_ports:
                for match_tuple in matched_ports:
                    if match_tuple:
                        return match_tuple[0]
            print "No serial port match for anything like: " + search_regex
            return None
        else:
            # windows hack because pyserial does not enumerate USB-style com ports
            print "Trying to find Controller ..."
            for i in range(24):
                try:
                    s = serial.Serial(port=i, baudrate=baudrate, timeout=2.0)
                    lasaur_hello = s.read(32)
                    if lasaur_hello.find(self.LASAURGRBL_FIRST_STRING) > -1:
                        return s.portstr
                    s.close()
                except serial.SerialException:
                    pass      
            return None      
        

    def connect(self, port, baudrate):
        self.rx_buffer = ""
        self.tx_buffer = ""        
        self.remoteXON = True
        self.job_size = 0
        self.reset_status()
                
        # Create serial device with both read timeout set to 0.
        # This results in the read() being non-blocking
        # Write on the other hand uses a large timeout but should not be blocking
        # much because we ask it only to write TX_CHUNK_SIZE at a time.
        # BUG WARNING: the pyserial write function does not report how
        # many bytes were actually written if this is different from requested.
        # Work around: use a big enough timeout and a small enough chunk size.
        self.device = serial.Serial(port, baudrate, timeout=0, writeTimeout=0.1)

        # clear throat
        time.sleep(1.0) # allow some time to receive a prompt/welcome
        self.device.flushInput()
        self.device.flushOutput()


    def connected(self):
        return bool(self.device)


    def close(self):
        if self.device:
            try:
                self.device.flushOutput()
                self.device.flushInput()
                self.device.close()
                self.device = None
            except:
                self.device = None
            self.status['ready'] = False
            return True
        else:
            return False

            
    def process(self):
        """Keep calling this to process serial"""
        self.send_queue_as_ready()


    def percentage(self):
        """Return the percentage done as an integer between 0-100.
        Return -1 if no job is active."""
        if self.job_size == 0 or not self.job_active:
            return -1
        return int(100-100*len(self.tx_buffer)/float(self.job_size))


    def homing(self):
        """Run homing cycle."""
        if not self.job_active:
            self.send_command(CMD_HOMING)
        else:
            print "WARN: ignoring homing command while job running"




    def send_command(self, command):
        self.tx_buffer += command
        self.job_size += 1
        self.job_active = True


    def send_param(self, param, val):



    def feedrate(self, val):
        self.send_param(PARAM_FEEDRATE, val)

    def intensity(self, val):
        self.send_param(PARAM_INTENSITY, val)

    def move(self, x, y, z=0.0):
        self.send_param(PARAM_TARGET_X, x)
        self.send_param(PARAM_TARGET_Y, y)
        self.send_param(PARAM_TARGET_Z, z)
        self.send_command(CMD_LINE)




    def job(jobdict):
        """Queue a job.
        A job dictionary can define vector and raster passes.
        It can set the feedrate, intensity, and pierce time.
        The job dictionary with the following keys:
        { passes,
            colors,
            seekrate,
            feedrate,
            intensity,
            pierce_time,
            relative,
            air_assist,
          paths,
          rasterpass,
            seekrate,
            feedrate,
            intensity,
          rasters,
        }
        """

        if jobdict.has_key('rasterpass') and jobdict.has_key('rasters'):
            rseekrate = jobdict['rasterpass']['seekrate']
            rfeedrate = jobdict['rasterpass']['feedrate']
            rintensity = jobdict['rasterpass']['intensity']
            # TODO: queue raster


        if jobdict.has_key('passes') and jobdict.has_key('paths'):
            for ppass in jobdict['passes']:
                for color in ppass['colors']:
                    if jobdict.['paths'].has_key(color):
                        for path in jobdict['paths'][color]
                            if len(path) > 0:
                                # first vertex, seek
                                self.feedrate(ppass['seekrate'])
                                self.intensity(0.0)
                                self.move(path[0][0], path[0][1], path[0][2])
                            elif len(path) > 1:
                                self.feedrate(ppass['feedrate'])
                                self.intensity(ppass['intensity'])                                
                                for i in xrange(1, len(path)):
                                    # rest, feed
                                    self.move(path[i][0], path[i][1], path[i][2])


    def pause(self):        
        if len(self.tx_buffer) == 0:
            return False
        else:
            self.status['paused'] = True
            return True

    def unpause(self, flag):
        if len(self.tx_buffer) == 0:
            return False
        else:
            self.status['paused'] = False
            return False


    def stop(self):
        """Force stop condition."""
        self.cancel_queue()
        self.reset_status()
        self.send_command(CMD_STOP)


    def unstop(self):
        """Resume from stop condition."""
        self.send_command(CMD_RESUME)


    def air_on(self):
        self.send_command(CMD_AIR_ENABLE)
    def air_off(self):
        self.send_command(CMD_AIR_DISABLE)


    def aux1_on(self):
        self.send_command(CMD_AUX1_ENABLE)
    def aux1_off(self):
        self.send_command(CMD_AUX1_DISABLE)


    def aux2_on(self):
        self.send_command(CMD_AUX2_ENABLE)
    def aux2_off(self):
        self.send_command(CMD_AUX2_DISABLE)


    def set_offset_table(self):
        self.send_command(CMD_SET_OFFSET_TABLE)
    def set_offset_custom(self):
        self.send_command(CMD_SET_OFFSET_CUSTOM)
    def def_offset_table(self, x, y, z):
        self.send_param(PARAM_TARGET_X, x)
        self.send_param(PARAM_TARGET_Y, y)
        self.send_param(PARAM_TARGET_Z, z)
        self.send_command(CMD_DEF_OFFSET_TABLE)
    def def_offset_custom(self, x, y, z):
        self.send_param(PARAM_TARGET_X, x)
        self.send_param(PARAM_TARGET_Y, y)
        self.send_param(PARAM_TARGET_Z, z)
        self.send_command(CMD_DEF_OFFSET_CUSTOM)
    def sel_offset_table(self):
        self.send_command(CMD_SEL_OFFSET_TABLE)
    def sel_offset_custom(self):
        self.send_command(CMD_SEL_OFFSET_CUSTOM)


            
### SINGLETON
Lasersaur = LasersaurClass()

### ALIASES
connect = Lasersaur.connect
connected = Lasersaur.connected
close =  Lasersaur.close

process =  Lasersaur.process
percentage =  Lasersaur.percentage
homing =  Lasersaur.homing

feedrate =  Lasersaur.feedrate
intensity =  Lasersaur.intensity
move =  Lasersaur.move
job =  Lasersaur.job

pause =  Lasersaur.pause
unpause =  Lasersaur.unpause
stop =  Lasersaur.stop
unstop =  Lasersaur.unstop

air_on = Lasersaur.air_on
air_off = Lasersaur.air_off
aux1_on = Lasersaur.aux1_on
aux1_off = Lasersaur.aux1_off
aux2_on = Lasersaur.aux2_on
aux2_off = Lasersaur.aux2_off

set_offset_table = Lasersaur.set_offset_table
set_offset_custom = Lasersaur.set_offset_custom

def_offset_table = Lasersaur.def_offset_table
def_offset_custom = Lasersaur.def_offset_custom

sel_offset_table = Lasersaur.sel_offset_table
sel_offset_custom = Lasersaur.sel_offset_custom