
import os
import sys
import time
import serial
import serial.tools.list_ports


__author__  = 'Stefan Hechenberger <stefan@nortd.com>'




class LasersaurClass:
    """Lasersaur serial control.
    Use Lasersaur singelton instead of instancing.
    """

    CMD_STOP = '!'
    CMD_RESUME = '~'
    CMD_STATUS = '?'

    CMD_RASTER_DATA_START = '\x02'
    CMD_RASTER_DATA_END = '\x03'

    CMD_NONE = "A"
    CMD_LINE = "B"
    CMD_DWELL = "C"
    CMD_RASTER = "D"

    CMD_SET_FEEDRATE = "E"
    CMD_SET_INTENSITY = "F"

    CMD_REF_RELATIVE = "G" 
    CMD_REF_ABSOLUTE = "H"

    CMD_HOMING = "I"

    CMD_SET_OFFSET_TABLE = "J"
    CMD_SET_OFFSET_CUSTOM = "K"
    CMD_DEF_OFFSET_TABLE = "L"
    CMD_DEF_OFFSET_CUSTOM = "M"
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
    INFO_IDLE_YES = 'A'
    INFO_IDLE_NO = 'B'
    INFO_DOOR_OPEN = 'C'
    INFO_DOOR_CLOSED = 'D'
    INFO_CHILLER_OFF = 'E'
    INFO_CHILLER_ON = 'F'
    INFO_FEC_CORRECTION = 'G'

    # status: info params
    INFO_POS_X = 'x'
    INFO_POS_Y = 'y'
    INFO_POS_Z = 'z'
    INFO_VERSION = 'v'




    def __init__(self):
        self.device = None

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
        self._status = {}
        self.reset_status()

        self.LASAURGRBL_FIRST_STRING = "LasaurGrbl"

        self.fec_redundancy = 2  # use forward error correction
        # self.fec_redundancy = 1  # use error detection

        self.READY = '\x12'
        self.REQUEST_READY = '\x14'
        self.last_request_ready = 0


    def reset_status(self):
        self._status = {
            'ready': True,
            'paused': False,

            'buffer_overflow': False,
            'serial_stop_request': False,
            'limit_x1': False,
            'limit_x2': False,
            'limit_y1': False,
            'limit_y2': False,
            'limit_z1': False,
            'limit_z2': False,
            'invalid_marker': False,
            'invalid_data': False,
            'invalid_command': False,
            'invalid_parameter': False,
            'transmission_error': False,

            'door_open': False,
            'chiller_off': False,

            'x': False,
            'y': False,
            'z': False,
            'firmware_version': None

            # removed
            # limit_hit
            # 'bad_number_format_error': False,
            # 'expected_command_letter_error': False,
            # 'unsupported_statement_error': False,            
        }


    def print_status(self):
        print self._status


    def cancel_queue(self):
        self.tx_buffer = ''
        self.job_size = 0
        self.job_active = False
    
    
    def send_queue_as_ready(self):
        """Continuously call this to keep processing queue."""    
        if self.device and not self._status['paused']:
            try:
                ### receiving
                chars = self.device.read(self.RX_CHUNK_SIZE)
                if len(chars) > 0:
                    ## check for data request
                    if self.READY in chars:
                        # print "=========================== READY"
                        self.nRequested = self.TX_CHUNK_SIZE
                        #remove control chars
                        chars = chars.replace(self.READY, "")
                    ## process chars
                    for char in chars:
                        if ord(char) < 128:  ### marker
                            if 32 < ord(char) < 65: # stop error flags                            
                                # chr is in [!-@], process flag
                                if char == ERROR_SERIAL_STOP_REQUEST:
                                    self._status['serial_stop_request'] = True
                                elif char == ERROR_RX_BUFFER_OVERFLOW:
                                    self._status['buffer_overflow'] = True
                                elif char == ERROR_LIMIT_HIT_X1:
                                    self._status['limit_x1'] = True
                                elif char == ERROR_LIMIT_HIT_X2:
                                    self._status['limit_x2'] = True
                                elif char == ERROR_LIMIT_HIT_Y1:
                                    self._status['limit_y1'] = True
                                elif char == ERROR_LIMIT_HIT_Y2:
                                    self._status['limit_y2'] = True
                                elif char == ERROR_LIMIT_HIT_Z1:
                                    self._status['limit_z1'] = True
                                elif char == ERROR_LIMIT_HIT_Z2:
                                    self._status['limit_z2'] = True
                                elif char == ERROR_INVALID_MARKER:
                                    self._status['invalid_marker'] = True
                                elif char == ERROR_INVALID_DATA:
                                    self._status['invalid_data'] = True
                                elif char == ERROR_INVALID_COMMAND:
                                    self._status['invalid_command'] = True
                                elif char == ERROR_INVALID_PARAMETER:
                                    self._status['invalid_parameter'] = True
                                elif char == ERROR_TRANSMISSION_ERROR:
                                    self._status['transmission_error'] = True
                                # in stop mode
                                self.cancel_queue()
                                # not ready whenever in stop mode
                                self._status['ready'] = False
                                self.print_status()

                            elif 64 < ord(char) < 91:  # info flags
                                # chr is in [A-Z], info flag
                                elif char == WARN_FEC_CORRECTION:
                                    sys.stdout.write("\nFEC Correction!\n")
                                    sys.stdout.flush()                                              
                                    # self._status['fec_correction'] = True
                                elif char == INFO_IDLE_YES:
                                    # self._status['ready'] = True
                                elif char == INFO_IDLE_NO:

                                elif char == INFO_DOOR_OPEN:
                                    self._status['door_open'] = True
                                elif char == INFO_DOOR_CLOSED:
                                    self._status['door_open'] = False
                                elif char == INFO_CHILLER_OFF:
                                    self._status['chiller_off'] = True
                                elif char == INFO_CHILLER_ON:
                                    self._status['chiller_off'] = False
                                else:
                                    print "ERROR: invalid flag"
                            elif 96 < ord(char) < 123:  # parameter
                                # char is in [a-z], process parameter
                                num = ((((pdata_chars[3]-128)*2097152 
                                       + (pdata_chars[2]-128)*16384 
                                       + (pdata_chars[1]-128)*128 
                                       + (pdata_chars[0]-128) )- 134217728)/1000.0)
                                if char == INFO_POS_X:
                                    self._status['x'] = num
                                elif char == INFO_POS_Y:
                                    self._status['y'] = num
                                elif char == INFO_POS_Z:
                                    self._status['z'] = num
                                elif char == STATUS_VERSION:
                                    num = 'v' + str(int(num)/100.0)
                                    self._status['firmware_version'] = num
                                else:
                                    print "ERROR: invalid param"
                            else:
                                print "ERROR: invalid marker"
                            pdata_count = 0
                        else:  ### data
                            # char is in [128,255]
                            if pdata_count < 4:
                                pdata_chars[pdata_count] = char
                                pdata_count += 1
                            else:
                                print "ERROR: invalid data"



                        if char == '^':
                        else:
                            if '!' in line:
                                # in stop mode
                                self.cancel_queue()
                                # not ready whenever in stop mode
                                self._status['ready'] = False
                                sys.stdout.write(line + "\n")
                                sys.stdout.flush()
                            else:
                                sys.stdout.write(".")
                                sys.stdout.flush()

                            if 'N' in line:
                                self._status['bad_number_format_error'] = True
                            if 'E' in line:
                                self._status['expected_command_letter_error'] = True
                            if 'U' in line:
                                self._status['unsupported_statement_error'] = True

                            if 'B' in line:  # Stop: Buffer Overflow
                                self._status['buffer_overflow'] = True
                            else:
                                self._status['buffer_overflow'] = False

                            if 'T' in line:  # Stop: Transmission Error
                                self._status['transmission_error'] = True
                            else:
                                self._status['transmission_error'] = False                                

                            if 'L' in line:  # Stop: A limit was hit
                                self._status['limit_hit'] = True
                            else:
                                self._status['limit_hit'] = False

                            if 'R' in line:  # Stop: by serial requested
                                self._status['serial_stop_request'] = True
                            else:
                                self._status['serial_stop_request'] = False

                            if 'D' in line:  # Warning: Door Open
                                self._status['door_open'] = True
                            else:
                                self._status['door_open'] = False

                            if 'C' in line:  # Warning: Chiller Off
                                self._status['chiller_off'] = True
                            else:
                                self._status['chiller_off'] = False

                            if 'X' in line:
                                self._status['x'] = line[line.find('X')+1:line.find('Y')]

                            if 'Y' in line:
                                self._status['y'] = line[line.find('Y')+1:line.find('V')]

                            if 'Z' in line:
                                self._status['z'] = line[line.find('Z')+1:line.find('Z')]

                            if 'V' in line:
                                self._status['firmware_version'] = line[line.find('V')+1:]                     



               
                
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
                    elif self.tx_buffer[0] in [self.CMD_STOP, self.CMD_RESUME]:  # send control chars no matter what
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
                                actuallySent = self.device.write(self.REQUEST_READY)
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
                        # ready whenever a job is done, including a status request
                        self._status['ready'] = True
            except OSError:
                # Serial port appears closed => reset
                self.close()
            except ValueError:
                # Serial port appears closed => reset
                self.close()     
        else:
            # serial disconnected    
            self._status['ready'] = False  







    ###########################################################################
    ### API ###################################################################
    ###########################################################################

    def list_devices(self, baudrate):
        ports = []
        if os.name == 'posix':
            iterator = sorted(serial.tools.list_ports.grep('tty'))
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
            matched_ports = serial.tools.list_ports.grep(search_regex)
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
        

    def connect(self, port="/dev/ttyACM0", baudrate=57600):
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
            self._status['ready'] = False
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


    def status(self):
        """Request status."""
        if not self.job_active:
            self.send_command(self.CMD_GET_STATUS)
        else:
            print "WARN: ignoring status request while job running"


    def homing(self):
        """Run homing cycle."""
        if not self.job_active:
            self.send_command(self.CMD_HOMING)
        else:
            print "WARN: ignoring homing command while job running"




    def send_command(self, command):
        self.tx_buffer += command
        self.job_size += 1
        self.job_active = True


    def send_param(self, param, val):
        # num to be [-134217.728, 134217.727]
        # three decimals are retained
        num = int(round((val*1000)+(2**27)))
        char0 = chr((num&127)+128)
        char1 = chr(((num&(127<<7))>>7)+128)
        char2 = chr(((num&(127<<14))>>14)+128)
        char3 = chr(((num&(127<<21))>>21)+128)
        self.tx_buffer += char0 + char1 + char2 + char3 + param
        self.job_size += 5
        self.job_active = True



    def feedrate(self, val):
        self.send_param(self.PARAM_FEEDRATE, val)

    def intensity(self, val):
        self.send_param(self.PARAM_INTENSITY, val)

    def move(self, x, y, z=0.0):
        self.send_param(self.PARAM_TARGET_X, x)
        self.send_param(self.PARAM_TARGET_Y, y)
        self.send_param(self.PARAM_TARGET_Z, z)
        self.send_command(self.CMD_LINE)




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
                    if jobdict['paths'].has_key(color):
                        for path in jobdict['paths'][color]:
                            if len(path) > 0:
                                # first vertex, seek
                                self.feedrate(ppass['seekrate'])
                                self.intensity(0.0)
                                self.move(path[0][0], path[0][1], path[0][2])
                            elif len(path) > 1:
                                self.feedrate(ppass['feedrate'])
                                self.intensity(ppass['intensity'])                                
                                # TODO dwell according to pierce time
                                for i in xrange(1, len(path)):
                                    # rest, feed
                                    self.move(path[i][0], path[i][1], path[i][2])


    def pause(self):        
        if len(self.tx_buffer) == 0:
            return False
        else:
            self._status['paused'] = True
            return True

    def unpause(self, flag):
        if len(self.tx_buffer) == 0:
            return False
        else:
            self._status['paused'] = False
            return False


    def stop(self):
        """Force stop condition."""
        self.cancel_queue()
        self.reset_status()
        self.send_command(self.CMD_STOP)


    def unstop(self):
        """Resume from stop condition."""
        self.send_command(self.CMD_RESUME)


    def air_on(self):
        self.send_command(self.CMD_AIR_ENABLE)
    def air_off(self):
        self.send_command(self.CMD_AIR_DISABLE)


    def aux1_on(self):
        self.send_command(self.CMD_AUX1_ENABLE)
    def aux1_off(self):
        self.send_command(self.CMD_AUX1_DISABLE)


    def aux2_on(self):
        self.send_command(self.CMD_AUX2_ENABLE)
    def aux2_off(self):
        self.send_command(self.CMD_AUX2_DISABLE)


    def set_offset_table(self):
        self.send_command(self.CMD_SET_OFFSET_TABLE)
    def set_offset_custom(self):
        self.send_command(self.CMD_SET_OFFSET_CUSTOM)
    def def_offset_table(self, x, y, z):
        self.send_param(self.PARAM_TARGET_X, x)
        self.send_param(self.PARAM_TARGET_Y, y)
        self.send_param(self.PARAM_TARGET_Z, z)
        self.send_command(self.CMD_DEF_OFFSET_TABLE)
    def def_offset_custom(self, x, y, z):
        self.send_param(self.PARAM_TARGET_X, x)
        self.send_param(self.PARAM_TARGET_Y, y)
        self.send_param(self.PARAM_TARGET_Z, z)
        self.send_command(self.CMD_DEF_OFFSET_CUSTOM)
    def sel_offset_table(self):
        self.send_command(self.CMD_SEL_OFFSET_TABLE)
    def sel_offset_custom(self):
        self.send_command(self.CMD_SEL_OFFSET_CUSTOM)


            
### SINGLETON
Lasersaur = LasersaurClass()

### ALIASES
connect = Lasersaur.connect
connected = Lasersaur.connected
close =  Lasersaur.close

process =  Lasersaur.process
percentage =  Lasersaur.percentage
status =  Lasersaur.status
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