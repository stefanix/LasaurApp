
import time
import sys, os
import os.path
import serial
import socket
import wsgiref.simple_server
from bottle import *
from serial_manager import SerialManager
from optparse import OptionParser


VERSION = "v12.01c"
SERIAL_PORT = None
BITSPERSECOND = 9600
CONFIG_FILE = "lasaurapp.conf"
GUESS_PPREFIX = "tty.usbmodem"
COOKIE_KEY = 'secret_key_jkn23489hsdf'


current_dir = os.path.dirname(os.path.abspath(__file__))


def run_with_callback(host, port=4444, timeout=0.01):
    """ Start a wsgiref server instance with control over the main loop.
        This is a function that I derived from the bottle.py run()
    """
    handler = default_app()
    server = wsgiref.simple_server.make_server(host, port, handler)
    server.timeout = timeout
    print "-----------------------------------------------------------------------------"
    print "Bottle server starting up ..."
    print "Serial is set to %d bps" % BITSPERSECOND
    print "Point your browser to: "    
    print "http://%s:%d/      (local)" % ('127.0.0.1', port)    
    if host == '':
        print "http://%s:%d/   (public)" % (socket.gethostbyname(socket.gethostname()), port)
    print "Use Ctrl-C to quit."
    print "-----------------------------------------------------------------------------"    
    print
    while 1:
        try:
            SerialManager.send_queue_as_ready()
            server.handle_request()
        except KeyboardInterrupt:
            break
    print "\nShutting down..."
    SerialManager.close()

        

@route('/hello')
def hello_handler():
    return "Hello World!!"

@route('/longtest')
def longtest_handler():
    fp = open("longtest.ngc")
    for line in fp:
        SerialManager.queue_for_sending(line)
    return "Longtest queued."
    


@route('/css/:path#.+#')
def static_css_handler(path):
    return static_file(path, root=os.path.join(current_dir, 'css'))
    
@route('/js/:path#.+#')
def static_css_handler(path):
    return static_file(path, root=os.path.join(current_dir, 'js'))
    
@route('/img/:path#.+#')
def static_css_handler(path):
    return static_file(path, root=os.path.join(current_dir, 'img'))

@route('/')
@route('/index.html')
@route('/app.html')
def default_handler():
    return static_file('app.html', root=current_dir)

@route('/canvas')
def default_handler():
    return static_file('testCanvas.html', root=current_dir)    

@route('/serial/:connect')
def serial_handler(connect):
    if connect == '1':
        print 'js is asking to connect serial'      
        if not SerialManager.is_connected():
            try:
                global SERIAL_PORT, BITSPERSECOND
                SerialManager.connect(SERIAL_PORT, BITSPERSECOND)
                ret = "Serial connected to %s:%d." % (SERIAL_PORT, BITSPERSECOND)  + '<br>'
                time.sleep(1.0) # allow some time to receive a prompt/welcome
                SerialManager.flush_input()
                SerialManager.flush_output()
                return ret
            except serial.SerialException:
                print "Failed to connect to serial."    
                return ""          
    elif connect == '0':
        print 'js is asking to close serial'    
        if SerialManager.is_connected():
            if SerialManager.close(): return "1"
            else: return ""  
    elif connect == "2":
        print 'js is asking if serial connected'
        if SerialManager.is_connected(): return "1"
        else: return ""
    else:
        print 'ambigious connect request from js: ' + connect            
        return ""
        

@route('/gcode/:gcode_line')
def gcode_handler(gcode_line):
    if SerialManager.is_connected():    
        print gcode_line
        SerialManager.queue_for_sending(gcode_line)
        return "Queued for sending."
    else:
        return ""

@route('/gcode', method='POST')
def gcode_handler_submit():
    gcode_program = request.forms.get('gcode_program')
    if gcode_program and SerialManager.is_connected():
        lines = gcode_program.split('\n')
        print "Adding to queue %s lines" % len(lines)
        for line in lines:
            SerialManager.queue_for_sending(line)
        return "Queued for sending."
    else:
        return ""

@route('/queue_pct_done')
def queue_pct_done_handler():
    return SerialManager.get_queue_percentage_done()


# @route('/svg_upload', method='POST')
# # file echo - used as a fall back for browser not supporting the file API
# def svg_upload():
#     data = request.files.get('data')
#     if data.file:
#         raw = data.file.read() # This is dangerous for big files
#         filename = data.filename
#         print "You uploaded %s (%d bytes)." % (filename, len(raw))
#         return raw
#     return "You missed a field."



# def check_user_credentials(username, password):
#     return username in allowed and allowed[username] == password
#     
# @route('/login')
# def login():
#     username = request.forms.get('username')
#     password = request.forms.get('password')
#     if check_user_credentials(username, password):
#         response.set_cookie("account", username, secret=COOKIE_KEY)
#         return "Welcome %s! You are now logged in." % username
#     else:
#         return "Login failed."
# 
# @route('/logout')
# def login():
#     username = request.forms.get('username')
#     password = request.forms.get('password')
#     if check_user_credentials(username, password):
#         response.delete_cookie("account", username, secret=COOKIE_KEY)
#         return "Welcome %s! You are now logged out." % username
#     else:
#         return "Already logged out."



oparser = OptionParser(usage="%prog [-p] [serial_port]", version=VERSION)
# parser.add_option("-s", "--serial", dest="serial",
#                   help="serial port to connect to")
oparser.add_option("-p", action="store_true", dest="host_on_all_interfaces")
(options, args) = oparser.parse_args()


if len(args) == 1:
    # (1) get the serial device from the argument list
    SERIAL_PORT = args[0]
    print "Using serial device '"+ SERIAL_PORT +"' from command line."
else:    
    if os.path.isfile(CONFIG_FILE):
        # (2) get the serial device from the config file
        fp = open(CONFIG_FILE)
        line = fp.readline().strip()
        if len(line) > 3:
            SERIAL_PORT = line
            print "Using serial device '"+ SERIAL_PORT +"' from '" + CONFIG_FILE + "'."
            
        

if not SERIAL_PORT:
    # (3) try best guess the serial device if on linux or osx
    devices = os.listdir("/dev")
    for device in devices:
        if device[:len(GUESS_PPREFIX)] == GUESS_PPREFIX:
            SERIAL_PORT = "/dev/" + device
            print "Using serial device '"+ SERIAL_PORT +"' by best guess."
            break
    
            

if SERIAL_PORT:
    # debug(True)
    if options.host_on_all_interfaces:
        run_with_callback('')
    else:
        run_with_callback('127.0.0.1')
else:         
    print "-----------------------------------------------------------------------------"
    print "ERROR: LasaurApp doesn't know what serial device to connect to!"
    print "On Linux or OSX this is something like '/dev/tty.usbmodemfd121' and on"
    print "Windows this is something like 'COM1', 'COM2', 'COM3', ..."
    print "The serial port can be supplied in one of the following ways:"
    print "(1) First argument on the  command line."
    print "(2) In a config file named '" + CONFIG_FILE + "' (located in same directory)"
    print "    with the serial port string on the first line."
    print "(3) Best guess. On Linux and OSX the app can guess the serial name by"
    print "    choosing the first device it finds starting with '"+ GUESS_PPREFIX +"'."
    print "-----------------------------------------------------------------------------"


