
from collections import deque
import time
import serial

serial_port = None

gcode_queue = deque()  # could use a list, but deque is faster
GRBL_BUFFER_MAX = 20
grbl_buffer_current = 0
gcode_queue_count = 0
total_items_queued_in_batch = 0  # used for calculating percentage done

responses = deque()
RESPONSES_MAX = 50
responses_current = 0



def append_response(line):
    # ring buffer-style responses queuing
    global responses, responses_current, RESPONSES_MAX
    if responses_current >= RESPONSES_MAX:
        responses.popleft()
        responses_current -= 1
    responses.append(line)
    responses_current += 1

def get_responses(line_separator='<br>'):
    global responses, responses_current, serial_port
    
    if serial_port:
        lines = serial_port.readlines()
        for line in lines:
            append_response("grbl: " + line)          
    responce_text = ""
    while responses:
        responce_text += responses.popleft() + line_separator
    responses.clear()
    responses_current = 0
    return responce_text
    
    


def connect(port, baudrate):
    global serial_port
    clear_queue()
    # serial_port = serial.Serial(port, baudrate, timeout=0.1)
    serial_port = serial.Serial(port, baudrate, timeout=0)

def close():
    global serial_port
    if serial_port:
        serial_port.close()
        serial_port = None
        return True
    else:
        return False
                    
def is_connected():
    global serial_port
    return bool(serial_port)



def queue_for_sending(gcode):
    global gcode_queue, total_items_queued_in_batch, gcode_queue_count
    gcode = gcode.strip()
    
    if gcode[:4] == 'M112':
      # cancel current job
      clear_queue()
    
    if gcode:
        print "adding to queue: %s" % (gcode)
        gcode_queue.append(gcode + '\n')
        gcode_queue_count += 1
        total_items_queued_in_batch += 1

def is_queue_empty():
    global gcode_queue
    return not bool(gcode_queue)

def clear_queue():
    global gcode_queue, gcode_queue_count, total_items_queued_in_batch
    gcode_queue.clear()
    gcode_queue_count = 0
    total_items_queued_in_batch = 0
    
def get_queue_percentage_done():
    global total_items_queued_in_batch, gcode_queue_count
    if total_items_queued_in_batch == 0: 
        print get_responses('\n')
        return ""
    return str(100-100*gcode_queue_count/total_items_queued_in_batch)
    
def send_queue_as_ready():
    """Continuously call this to keep processing queue."""
    global serial_port, gcode_queue, grbl_buffer_current, GRBL_BUFFER_MAX
    global total_items_queued_in_batch, gcode_queue_count
    
    if serial_port:
        try:
            lines = serial_port.readlines()
            for line in lines:
                print "grbl: " + line
                # append_response("grbl: " + line)
                grbl_buffer_current -= 1
    
            if gcode_queue:
                if grbl_buffer_current < GRBL_BUFFER_MAX:
                    line = gcode_queue.popleft()
                    gcode_queue_count -= 1
                    print "sending to grbl: %s" % (line)
                    serial_port.write(line)
                    grbl_buffer_current += 1
                    # append_response("sent to grbl: %s - buffer_current: %d" % (line,grbl_buffer_current))
            else:
                total_items_queued_in_batch = 0
        except OSError:
            # Serial port appears closed => reset
            close()
        except ValueError:
            # Serial port appears closed => reset
            close()            
            

