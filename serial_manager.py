
import time
import serial
from collections import deque



class SerialManagerClass:
    
    def __init__(self):
        self.device = None

        self.rx_buffer = ""
        self.tx_buffer = ""
        self.CHUNK_SIZE = 256

        # buffer_tracker - tracks the number of 
        # characters in the Lasersaur serial buffer
        self.remote_buffer_tracker = deque()
        
        # REMOTE_BUFFER_SIZE - has to match the
        # serial rx buffer of the Lasersaur controller.
        self.REMOTE_BUFFER_SIZE = 256
        
        # used for calculating percentage done
        self.job_size = 0    



    def connect(self, port, baudrate):
        tx_buffer = ""
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
            self.device.close()
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
        gcode = gcode.strip()
    
        if gcode[:4] == 'M112':
          # cancel current job
          self.tx_buffer = ""
          self.job_size = 0
        elif gcode[0] == '%':
            return
    
        if gcode:
            print "adding to queue: %s" % (gcode)
            self.tx_buffer += gcode + '\n'
            self.job_size += len(gcode) + 1

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
                chars = self.device.read(self.CHUNK_SIZE)
                self.rx_buffer += chars
                posNewline = self.rx_buffer.find('\n')
                if posNewline >= 0:  # we got a line
                    line = self.rx_buffer[:posNewline]
                    self.rx_buffer = self.rx_buffer[posNewline+1:]
                    print "grbl: " + line
                    if line.find('ok') >= 0 or line.find('error') >= 0:
                        self.remote_buffer_tracker.popleft()
                
                if len(self.tx_buffer) > 0:
                    lasersaur_buffer_count = sum(self.remote_buffer_tracker)
                    if lasersaur_buffer_count < self.REMOTE_BUFFER_SIZE:
                        nToSend = min(self.REMOTE_BUFFER_SIZE-lasersaur_buffer_count, self.CHUNK_SIZE)
                        toSend = self.tx_buffer[:nToSend]
                        print "sending chunk: %s" % (toSend)
                        actuallySent = self.device.write(toSend)
                        self.tx_buffer = self.tx_buffer[actuallySent:]
                        self.remote_buffer_tracker.append(actuallySent)
                else:
                    self.job_size = 0
            except OSError:
                # Serial port appears closed => reset
                close()
            except ValueError:
                # Serial port appears closed => reset
                close()            

            
# singelton
SerialManager = SerialManagerClass()
