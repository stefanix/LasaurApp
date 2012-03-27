
import time
import sys, os
import os.path
import serial
import socket
import argparse
import webbrowser
import wsgiref.simple_server
from bottle import *
import threading
from serial_manager import SerialManager
from flash import flash_upload

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtWebKit import *

if sys.platform == "darwin":  # OSX
    # inform search path about Homebrew installation
    sys.path.append("/usr/local/lib/python2.7/site-packages/") 


VERSION = "v12.03a"
SERIAL_PORT = None
BITSPERSECOND = 9600
CONFIG_FILE = "lasaurapp.conf"
GUESS_PPREFIX = "tty.usbmodem"
NETWORK_PORT = 4444
COOKIE_KEY = 'secret_key_jkn23489hsdf'

server = None
b_run_webserver = True



def data_root():
    """This is to be used with all relative file access.
       _MEIPASS is a special location for data files when creating
       standalone, single file python apps with pyInstaller.
       Standalone is created by calling from 'other' directory:
       python pyinstaller/pyinstaller.py --onefile app.spec
    """
    if hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    else:
        # root is one up from this file
        return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../'))


def webserver_thread():
    global server, b_run_webserver
    while b_run_webserver:
        SerialManager.send_queue_as_ready()
        server.handle_request()
    print "\nShutting down webserver_thread..."
    sys.stdout.flush()
    SerialManager.close()



def init_app(host):
    """ Start a wsgiref server instance with control over the main loop.
        This is a function that I derived from the bottle.py run()
    """
    global server, b_run_webserver
    handler = default_app()
    server = wsgiref.simple_server.make_server(host, NETWORK_PORT, handler)
    server.timeout = 0.01
    print "-----------------------------------------------------------------------------"
    print "Bottle server starting up ..."
    print "Serial is set to %d bps" % BITSPERSECOND
    print "Point your browser to: "    
    print "http://%s:%d/      (local)" % ('127.0.0.1', NETWORK_PORT)    
    if host == '':
        print "http://%s:%d/   (public)" % (socket.gethostbyname(socket.gethostname()), NETWORK_PORT)
    print "Use Ctrl-C to quit."
    print "-----------------------------------------------------------------------------"    
    print
    
    t = threading.Thread(target=webserver_thread)
    t.start()
    
    ### qtWebKit
    app = QApplication(sys.argv)
    web = QWebView()
    web.setGeometry(50, 80, 1020, 680)
    web.load( QUrl('http://127.0.0.1:'+str(NETWORK_PORT)) )
    web.show()
    web.raise_()
    # Post a call to your python code.
    # QTimer.singleShot(100, loop_along)
    ret = app.exec_()
    
    print "\nShutting down..."
    b_run_webserver = False
    t.join()  # wait for thread to terminate
    sys.exit(ret)

        

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
    return static_file(path, root=os.path.join(data_root(), 'frontend/css'))
    
@route('/js/:path#.+#')
def static_css_handler(path):
    return static_file(path, root=os.path.join(data_root(), 'frontend/js'))
    
@route('/img/:path#.+#')
def static_css_handler(path):
    return static_file(path, root=os.path.join(data_root(), 'frontend/img'))

@route('/')
@route('/index.html')
@route('/app.html')
def default_handler():
    return static_file('app.html', root=os.path.join(data_root(), 'frontend') )

@route('/canvas')
def default_handler():
    return static_file('testCanvas.html', root=os.path.join(data_root(), 'frontend'))    

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



if not SERIAL_PORT:
    # (3) try best guess the serial device if on linux or osx
    if os.path.isdir("/dev"):
        devices = os.listdir("/dev")
        for device in devices:
            if device[:len(GUESS_PPREFIX)] == GUESS_PPREFIX:
                SERIAL_PORT = "/dev/" + device
                print "Using serial device '"+ SERIAL_PORT +"' by best guess."
                break   

    
# if args.build_and_flash:
#     flash_upload(SERIAL_PORT, data_root())
# else:
#     # debug(True)
#     if args.host_on_all_interfaces:
#         init_app('')
#     else:
#         init_app('127.0.0.1')
    
init_app('127.0.0.1')    



