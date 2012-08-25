
import os
import sys
import time
import serial
from serial.tools import list_ports
from collections import deque


class SerialManagerClass:
    
    def __init__(self):
        self.device = None

        self.rx_buffer = ""
        self.tx_buffer = ""        
        self.remoteXON = True

        # TX_CHUNK_SIZE - this is the number of bytes to be 
        # written to the device in one go.
        # IMPORTANT: The remote device is required to send an
        # XOFF if TX_CHUNK_SIZE bytes would overflow it's buffer.
        # BUG WARNING: it appears pyserial's write() does not
        # report back the correct size of actually written bytes.
        # It simply returns the num is was handed to. This is a problem
        # when it cannot write at least TX_CHUNK_SIZE. 8 seems to be fine.
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

        self.ready_char = '\x12'
        self.request_ready_char = '\x14'
        self.last_request_ready = 0



    def reset_status(self):
        self.status = {
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
            'firmware_version': None
        }



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
        self.device = serial.Serial(port, baudrate, timeout=0)
        
        # I would like to use write with a timeout but it appears from checking
        # serialposix.py that the write function does not correctly report the
        # number of bytes actually written. It appears to simply report back
        # the number of bytes passed to the function.
        # self.device = serial.Serial(port, baudrate, timeout=0, writeTimeout=0.1)

    def close(self):
        if self.device:
            try:
                self.device.flushOutput()
                self.device.flushInput()
                self.device.close()
                self.device = None
            except:
                self.device = None
            return True
        else:
            return False
                    
    def is_connected(self):
        return bool(self.device)

    def get_hardware_status(self):
        if self.is_queue_empty():
            # trigger a status report
            # will update for the next status request
            self.queue_gcode_line('?')
        return self.status


    def flush_input(self):
        if self.device:
            self.device.flushInput()

    def flush_output(self):
        if self.device:
            self.device.flushOutput()


    def queue_gcode_line(self, gcode):
        if gcode:
            gcode = gcode.strip()
    
            if gcode[0] == '%':
                return
            else:
                if self.fec_redundancy > 0:  # using error correction
                    # prepend marker and checksum
                    checksum = 0
                    for c in gcode:
                        ascii_ord = ord(c)
                        if ascii_ord > ord(' ') and c != '~' and c != '!':  #ignore 32 and lower, ~, !
                            checksum += ascii_ord
                            if checksum >= 128:
                                checksum -= 128
                    checksum = (checksum >> 1) + 128
                    gcode_redundant = ""
                    for n in range(self.fec_redundancy-1):
                        gcode_redundant += '^' + chr(checksum) + gcode + '\n'
                    gcode = gcode_redundant + '*' + chr(checksum) + gcode

                if gcode.find('!') > -1:
                  # cancel current job
                  self.tx_buffer = gcode + '\n'
                  self.job_size = 0
                  self.reset_status()  
                else:                    
                    self.tx_buffer += gcode + '\n'
                    self.job_size += len(gcode) + 1
                    
                self.job_active = True

                  

    def is_queue_empty(self):
        return len(self.tx_buffer) == 0
        
    
    def get_queue_percentage_done(self):
        if self.job_size == 0:
            return ""
        return str(100-100*len(self.tx_buffer)/self.job_size)


    
    def send_queue_as_ready(self):
        """Continuously call this to keep processing queue."""    
        if self.device:
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
                    posNewline = self.rx_buffer.find('\n')
                    if posNewline >= 0:  # we got a line
                        line = self.rx_buffer[:posNewline]
                        self.rx_buffer = self.rx_buffer[posNewline+1:]
                        if '#' in line[:3]:
                            # print and ignore
                            sys.stdout.write(line + "\n")
                            sys.stdout.flush()
                        elif '^' in line:
                            sys.stdout.write("\nFEC Correction!\n")
                            sys.stdout.flush()                                              
                        else:
                            # sys.stdout.write(line + "\n")
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

                            if 'V' in line:
                                self.status['firmware_version'] = line[line.find('V')+1:]                     
                
                ### sending
                if self.tx_buffer:
                    if self.nRequested > 0:
                        actuallySent = self.device.write(self.tx_buffer[:self.nRequested])
                        # sys.stdout.write(self.tx_buffer[:actuallySent])  # print w/ newline
                        self.tx_buffer = self.tx_buffer[actuallySent:]
                        self.nRequested -= actuallySent
                        if self.nRequested <= 0:
                            self.last_request_ready = 0  # make sure to request ready
                    else:
                        if (time.time()-self.last_request_ready) > 2.0:
                            # ask to send a ready indicator
                            # only ask for this when sending is on hold
                            # only ask once and after time out
                            # print "=========================== REQUEST READY"
                            actuallySent = self.device.write(self.request_ready_char)
                            if actuallySent == 1:
                                self.last_request_ready = time.time()
                         
                else:
                    if self.job_active:
                        # print "\nG-code stream finished!"
                        # print "(LasaurGrbl may take some extra time to finalize)"
                        self.job_size = 0
                        self.job_active = False
            except OSError:
                # Serial port appears closed => reset
                self.close()
            except ValueError:
                # Serial port appears closed => reset
                self.close()            

            
# singelton
SerialManager = SerialManagerClass()
