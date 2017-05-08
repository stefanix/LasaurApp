from __future__ import print_function
import os
import sys
import time
import serial
import json
from remotelogger import RemoteLogger
from datetime import datetime
from serial.tools import list_ports
from serial import dummy_serial
import datedecoder

dummy_serial.RESPONSES = {'\x14': '\x12'}
dummy_serial.DEFAULT_RESPONSE = '\n'


#extended Class of Lasersaur project
class SerialManagerClass(object):

    def __init__(self, accountingFile, influxConfig, dummyMode=False):

        self.device = None
        self.dummyMode = dummyMode

        self.rx_buffer = ""
        self.tx_buffer = ""
        self.tx_index = 0
        self.remoteXON = True

        # TX_CHUNK_SIZE - this is the number of bytes to be
        # written to the device in one go. It needs to match the device.
        self.TX_CHUNK_SIZE = 16
        self.RX_CHUNK_SIZE = 16
        self.nRequested = 0

        # used for calculating percentage done
        self.job_active = False

        # status flags
        self.status = {}
        self.job_accounting = {}
        self.LASAURGRBL_FIRST_STRING = "LasaurGrbl"

        self.fec_redundancy = 2  # use forward error correction
        # self.fec_redundancy = 1  # use error detection

        self.ready_char = '\x12'
        self.request_ready_char = '\x14'
        self.last_request_ready = 0

        self.logger = RemoteLogger('Lasaur-Accounting', influxConfig)

        self.job_accounting = {}
        self.lastJobs = []
        self.reset_status()
        self.accountingFile = accountingFile
        self.reset_accounting()

        self.odoo_service = -1
        self.odoo_product = -1
        self.job_comment = ""

        # Path to a json file, which stores the last n jobs.
        # stop_accounting is limiting the array size to a constant value
        if os.path.isfile(self.accountingFile):
            with open(self.accountingFile, 'r') as json_file:
                self.lastJobs = json.load(json_file, object_hook=datedecoder.object_hook)
        else:
            folder = os.path.dirname(self.accountingFile)
            if not os.path.exists(folder):
                os.makedirs(folder)
            with open(self.accountingFile, 'w+') as json_file:
                json.dump(self.lastJobs, json_file, default=datedecoder.default, indent=4, separators=(',', ': '))

        self.logger.info("Init Accounting")

    def start_accounting(self, num_gcode_lines=0, job_name='<unnamed>', user_id='<unknown>'):
        # initialize all accounting data, get start time, write log information
        self.job_accounting = {
            'running'    : True,
            'start_pause': None,
            'pause_time' : 0,
            'start_job'  : datetime.now(),
            'gcode_lines': num_gcode_lines,
            'job_name'   : job_name,
            'user_id'    : user_id,
            'odoo_service': self.odoo_service['id'],
            'odoo_product': self.odoo_product['id'],
            'comment'     : self.job_comment
        }
        self.logger.info(
            "Start Accounting: gcode-lines:", self.job_accounting['gcode_lines'],
            " jobname: ", self.job_accounting['job_name'])

    def stop_accounting(self):
        # final time calculation, write log information, cleanup
        runtime = datetime.now() - self.job_accounting['start_job']
        # Job summary
        jobtime = int(runtime.total_seconds()) - self.job_accounting['pause_time']
        #    start time, end time, job name, job duration (sec), gcode elements, cumulated time (sec)
        current_total = 0
        if len(self.lastJobs) > 0 and len(self.lastJobs[0]) > 5:
            current_total = self.lastJobs[0]["total"]
        job = {
            'start': self.job_accounting['start_job'],
            'end': datetime.now(),
            'name': self.job_accounting['job_name'],
            'duration': jobtime,
            'lines': self.job_accounting['gcode_lines'],
            'total': int(current_total + jobtime),
            'user_id': self.job_accounting['user_id'],
            'odoo_service_id': self.job_accounting['odoo_service'],
            'odoo_product_id': self.job_accounting['odoo_product'],
            'comment': self.job_accounting['comment']
        }

        self.lastJobs.insert(0, job)
        del self.lastJobs[200:] # only last 200 jobs
        #CHANGE_ME
        with open(self.accountingFile, 'w') as json_file:
            json.dump(self.lastJobs, json_file, default=datedecoder.default, indent=4, separators=(',', ': '))
        self.logger.info(
            "Stop Accounting: gcode-lines:", self.job_accounting['gcode_lines'],
            " jobname: ", self.job_accounting['job_name'],
            " job time: ", jobtime,
            " total time: ", int(self.lastJobs[0]["total"] + jobtime))
        self.reset_accounting()

    def reset_accounting(self):
        self.job_accounting = {
            'running'    : False,   # True, while accounting is running
            'start_pause': None,
            'pause_time' : 0,
            'start_job'  : None,
            'gcode_lines': 0,
            'job_name'   : '',
        }
        self.logger.info("Reset Accounting")

    def reset_status(self):
        self.status = {
            'ready': True,  # turns True by querying status
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
            'firmware_version': None
        }

    def open_serial(self, port, baudrate, timeout=0, writeTimeout=1):
        if self.dummyMode:
            return dummy_serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
        else:
            return serial.Serial(port, baudrate, timeout=timeout, writeTimeout=writeTimeout)

    def list_devices(self, baudrate):
        ports = []
        if os.name == 'posix':
            iterator = sorted(list_ports.grep('tty'))
            print("Found ports:")
            for port, desc, hwid in iterator:
                ports.append(port)
                print("%-20s" % (port,))
                print("    desc: %s" % (desc,))
                print("    hwid: %s" % (hwid,))
        else:
            # iterator = sorted(list_ports.grep(''))  # does not return USB-style
            # scan for available ports. return a list of tuples (num, name)
            available = []
            for i in range(24):
                try:
                    s = self.open_serial(i, baudrate)
                    ports.append(s.portstr)
                    available.append((i, s.portstr))
                    s.close()
                except serial.SerialException:
                    pass
            print("Found ports:")
            for n, s in available: print("(%d) %s" % (n,s))
        return ports

    def match_device(self, search_regex, baudrate):
        if os.name == 'posix':
            matched_ports = list_ports.grep(search_regex)
            if matched_ports:
                for match_tuple in matched_ports:
                    if match_tuple:
                        return match_tuple[0]
            print("No serial port match for anything like: " + search_regex)
            return None
        else:
            # windows hack because pyserial does not enumerate USB-style com ports
            print("Trying to find Controller ...")
            for i in range(24):
                try:
                    s = self.open_serial(i, baudrate, 2.0)
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
        self.tx_index = 0
        self.remoteXON = True
        self.reset_status()

        # Create serial device with both read timeout set to 0.
        # This results in the read() being non-blocking
        # Write on the other hand uses a large timeout but should not be blocking
        # much because we ask it only to write TX_CHUNK_SIZE at a time.
        # BUG WARNING: the pyserial write function does not report how
        # many bytes were actually written if this is different from requested.
        # Work around: use a big enough timeout and a small enough chunk size.
        self.device = self.open_serial(port, baudrate, 0, 1)

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

    def is_connected(self):
        return bool(self.device)

    def get_hardware_status(self):
        if self.is_queue_empty():
            # trigger a status report
            # will update for the next status request
            self.queue_gcode('?')
        return self.status

    def flush_input(self):
        if self.device:
            self.device.flushInput()

    def flush_output(self):
        if self.device:
            self.device.flushOutput()

    def queue_gcode(self, gcode, name=None, user_id=None):
        lines = gcode.split('\n')
        #print("Adding to queue %s lines" % len(lines))
        job_list = []
        for line in lines:
            line = line.strip()
            if line == '' or line[0] == '%':
                continue

            if line[0] == '!':
                self.cancel_queue()
                self.reset_status()
                job_list.append('!')
            else:
                if line != '?':  # not ready unless just a ?-query
                    self.status['ready'] = False

                if self.fec_redundancy > 0:  # using error correction
                    # prepend marker and checksum
                    checksum = 0
                    for c in line:
                        ascii_ord = ord(c)
                        if ascii_ord > ord(' ') and c != '~' and c != '!':  #ignore 32 and lower, ~, !
                            checksum += ascii_ord
                            if checksum >= 128:
                                checksum -= 128
                    checksum = (checksum >> 1) + 128
                    line_redundant = ""
                    for n in range(self.fec_redundancy-1):
                        line_redundant += '^' + chr(checksum) + line + '\n'
                    line = line_redundant + '*' + chr(checksum) + line

                job_list.append(line)

        gcode_processed = '\n'.join(job_list) + '\n'
        self.tx_buffer += gcode_processed
        self.job_active = True
        if (self.status['ready'] == False) and (len(lines) > 10):
            self.start_accounting(len(lines), name, user_id) # as soon, as jobname is vailable, can be passed as second param

    def cancel_queue(self):
        self.tx_buffer = ""
        self.tx_index = 0
        self.job_active = False


    def is_queue_empty(self):
        return self.tx_index >= len(self.tx_buffer)


    def get_queue_percentage_done(self):
        buflen = len(self.tx_buffer)
        if buflen == 0:
            return ""
        return str(100*self.tx_index/float(buflen))


    def set_pause(self, flag):
        # returns pause status
        if self.is_queue_empty():
            return False
        else:
            if flag:  # pause
                self.status['paused'] = True
                self.job_accounting['start_pause'] = datetime.now()
                return True
            else:     # unpause
                pause = datetime.now() - self.job_accounting['start_pause']
                self.job_accounting['pause_time'] += int(pause.total_seconds())
                self.job_accounting['start_pause'] = None
                self.status['paused'] = False
                return False

    def send_queue_as_ready(self):
        """Continuously call this to keep processing queue."""
        if self.device and not self.status['paused']:
            try:
                ### receiving
                chars = self.device.read(self.RX_CHUNK_SIZE)
                if len(chars) > 0:
                    ## check for data request
                    if self.ready_char in chars:
                        # print("=========================== READY")
                        self.nRequested = self.TX_CHUNK_SIZE
                        #remove control chars
                        chars = chars.replace(self.ready_char, "")
                    ## assemble lines
                    self.rx_buffer += chars
                    while True:  # process all lines in buffer
                        posNewline = self.rx_buffer.find('\n')
                        if posNewline == -1:
                            break  # no more complete lines
                        else:  # we got a line
                            line = self.rx_buffer[:posNewline]
                            self.rx_buffer = self.rx_buffer[posNewline+1:]
                        self.process_status_line(line)
                else:
                    if self.nRequested == 0:
                        time.sleep(0.001)  # no rx/tx, rest a bit

                ### sending
                if self.tx_index < len(self.tx_buffer):
                    if self.nRequested > 0:
                        try:
                            t_prewrite = time.time()
                            actuallySent = self.device.write(
                                self.tx_buffer[self.tx_index:self.tx_index+self.nRequested])
                            if time.time()-t_prewrite > 0.02:
                                sys.stdout.write("WARN: write delay 1\n")
                                sys.stdout.flush()
                        except serial.SerialTimeoutException:
                            # skip, report
                            actuallySent = 0  # assume nothing has been sent
                            sys.stdout.write("\nsend_queue_as_ready: writeTimeoutError\n")
                            sys.stdout.flush()
                        self.tx_index += actuallySent
                        self.nRequested -= actuallySent
                        if self.nRequested <= 0:
                            self.last_request_ready = 0  # make sure to request ready
                    elif self.tx_buffer[self.tx_index] in ['!', '~']:  # send control chars no matter what
                        try:
                            t_prewrite = time.time()
                            actuallySent = self.device.write(self.tx_buffer[self.tx_index])
                            if time.time()-t_prewrite > 0.02:
                                sys.stdout.write("WARN: write delay 2\n")
                                sys.stdout.flush()
                        except serial.SerialTimeoutException:
                            actuallySent = 0  # assume nothing has been sent
                            sys.stdout.write("\nsend_queue_as_ready: writeTimeoutError\n")
                            sys.stdout.flush()
                        self.tx_index += actuallySent
                    else:
                        if (time.time()-self.last_request_ready) > 2.0:
                            # ask to send a ready byte
                            # only ask for this when sending is on hold
                            # only ask once (and after a big time out)
                            # print("=========================== REQUEST READY")
                            try:
                                t_prewrite = time.time()
                                actuallySent = self.device.write(self.request_ready_char)
                                if time.time()-t_prewrite > 0.02:
                                    sys.stdout.write("WARN: write delay 3\n")
                                    sys.stdout.flush()
                            except serial.SerialTimeoutException:
                                # skip, report
                                actuallySent = self.nRequested  # pyserial does not report this sufficiently
                                sys.stdout.write("\nsend_queue_as_ready: writeTimeoutError, on ready request\n")
                                sys.stdout.flush()
                            if actuallySent == 1:
                                self.last_request_ready = time.time()

                else:
                    if self.job_active:
                        # print("\nG-code stream finished!")
                        # print("(LasaurGrbl may take some extra time to finalize)")
                        self.tx_buffer = ""
                        self.tx_index = 0
                        self.job_active = False
                        # ready whenever a job is done, including a status request via '?'
                        if (self.status['ready'] == False) and (self.job_accounting['running'] == True):
                            self.stop_accounting()
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
                if not self.dummyMode:
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
            # else:
            #     self.status['x'] = False

            if 'Y' in line:
                self.status['y'] = line[line.find('Y')+1:line.find('V')]
            # else:
            #     self.status['y'] = False

            if 'V' in line:
                self.status['firmware_version'] = line[line.find('V')+1:]
