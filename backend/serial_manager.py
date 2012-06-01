
import os
import sys
import time
import serial
from collections import deque
import serial_list_ports


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
        self.TX_CHUNK_SIZE = 8
        self.RX_CHUNK_SIZE = 256
        
        # used for calculating percentage done
        self.job_size = 0
        self.job_active = False


    def list_devices(self):
        if os.name == 'posix':
            iterator = sorted(serial_list_ports.grep('tty'))
        else:
            iterator = sorted(serial_list_ports.grep(''))
        for port, desc, hwid in iterator:
            print "%-20s" % (port,)
            print "    desc: %s" % (desc,)
            print "    hwid: %s" % (hwid,)

            
    def match_device(self, search_regex):
        matched_ports = serial_list_ports.grep(search_regex)
        if matched_ports:
            for match_tuple in matched_ports:
                if match_tuple:
                    return match_tuple[0]
        print "No serial port match for anything like: " + search_regex
        return None
        

    def connect(self, port, baudrate):
        self.rx_buffer = ""
        self.tx_buffer = ""        
        self.remoteXON = True
        self.job_size = 0
                
        # Create serial device with both read timeout set to 0.
        # This results in the read() being non-blocking
        self.device = serial.Serial(port, baudrate, timeout=0)
        
        # I would like to use write with a timeout but it appears from checking
        # serialposix.py that the write function does not correctly report the
        # number of bytes actually written. It appears to simply report back
        # the number of bytes passed to the function.
        # self.device = serial.Serial(port, baudrate, timeout=0, writeTimeout=0)

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

    def flush_input(self):
        if self.device:
            self.device.flushInput()

    def flush_output(self):
        if self.device:
            self.device.flushOutput()


    def queue_for_sending(self, gcode):
        if gcode:
            gcode = gcode.strip()
    
            if gcode[:4] == '!':
              # cancel current job
              self.tx_buffer = ""
              self.job_size = 0
            elif gcode[0] == '%':
                return
                    
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
                chars = self.device.read(self.RX_CHUNK_SIZE)
                if len(chars) > 0:
                    ## check for flow control chars
                    iXON = chars.rfind(serial.XON)
                    iXOFF = chars.rfind(serial.XOFF)
                    if iXON != -1 or iXOFF != -1:
                        if iXON > iXOFF:
                            # print "=========================== XON"
                            self.remoteXON = True
                        else:
                            # print "=========================== XOFF"
                            self.remoteXON = False
                        #remove control chars
                        for c in serial.XON+serial.XOFF: 
                            chars = chars.replace(c, "")
                    ## assemble lines
                    self.rx_buffer += chars
                    posNewline = self.rx_buffer.find('\n')
                    if posNewline >= 0:  # we got a line
                        line = self.rx_buffer[:posNewline]
                        self.rx_buffer = self.rx_buffer[posNewline+1:]
                        if line.find('ok') > -1:
                            sys.stdout.write(".")  # print w/ newline
                            sys.stdout.flush()
                        # else if line.find('error:') > -1:
                        #     
                        else:
                            sys.stdout.write(line + '\n')
                            sys.stdout.flush()
                
                if self.tx_buffer:
                    if self.remoteXON:
                        actuallySent = self.device.write(self.tx_buffer[:self.TX_CHUNK_SIZE])
                        # sys.stdout.write(self.tx_buffer[:actuallySent])  # print w/ newline
                        self.tx_buffer = self.tx_buffer[actuallySent:]  
                else:
                    if self.job_active:
                        print "\nG-code stream finished!"
                        print "(LasaurGrbl may take some extra time to finalize)"
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
