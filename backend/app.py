
import sys, os, time
import glob, json, argparse, copy
import socket, webbrowser
import wsgiref.simple_server
from bottle import *
from serial_manager import SerialManager
from flash import flash_upload
from filereaders import read_svg


APPNAME = "lasaurapp"
VERSION = "12.08g"
COMPANY_NAME = "com.nortd.labs"
SERIAL_PORT = None
BITSPERSECOND = 57600
NETWORK_PORT = 4444
CONFIG_FILE = "lasaurapp.conf"
COOKIE_KEY = 'secret_key_jkn23489hsdf'

if os.name == 'nt': #sys.platform == 'win32': 
    GUESS_PREFIX = "Arduino"   
elif os.name == 'posix':
    if sys.platform == "linux" or sys.platform == "linux2":
        GUESS_PREFIX = "2341"  # match by arduino VID
    else:
        GUESS_PREFIX = "tty.usbmodem"    
else:
    GUESS_PREFIX = "no prefix"    


def resources_dir():
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
        
        
def storage_dir():
    directory = ""
    if sys.platform == 'darwin':
        # from AppKit import NSSearchPathForDirectoriesInDomains
        # # NSApplicationSupportDirectory = 14
        # # NSUserDomainMask = 1
        # # True for expanding the tilde into a fully qualified path
        # appdata = path.join(NSSearchPathForDirectoriesInDomains(14, 1, True)[0], APPNAME)
        directory = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', COMPANY_NAME, APPNAME)
    elif sys.platform == 'win32':
        directory = os.path.join(os.path.expandvars('%APPDATA%'), COMPANY_NAME, APPNAME)
    else:
        directory = os.path.join(os.path.expanduser('~'), "." + APPNAME)
        
    if not os.path.exists(directory):
        os.makedirs(directory)
        
    return directory
        



def run_with_callback(host):
    """ Start a wsgiref server instance with control over the main loop.
        This is a function that I derived from the bottle.py run()
    """
    handler = default_app()
    server = wsgiref.simple_server.make_server(host, NETWORK_PORT, handler)
    server.timeout = 0.01
    server.quiet = True
    print "-----------------------------------------------------------------------------"
    print "Bottle server starting up ..."
    print "Serial is set to %d bps" % BITSPERSECOND
    print "Point your browser to: "    
    print "http://%s:%d/      (local)" % ('127.0.0.1', NETWORK_PORT)    
    if host == '':
        try:
            print "http://%s:%d/   (public)" % (socket.gethostbyname(socket.gethostname()), NETWORK_PORT)
        except socket.gaierror:
            # print "http://beaglebone.local:4444/      (public)"
            pass
    print "Use Ctrl-C to quit."
    print "-----------------------------------------------------------------------------"    
    print
    try:
        webbrowser.open_new_tab('http://127.0.0.1:'+str(NETWORK_PORT))
        pass
    except webbrowser.Error:
        print "Cannot open Webbrowser, please do so manually."
    sys.stdout.flush()  # make sure everything gets flushed
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
        SerialManager.queue_gcode_line(line)
    return "Longtest queued."
    


@route('/css/:path#.+#')
def static_css_handler(path):
    return static_file(path, root=os.path.join(resources_dir(), 'frontend/css'))
    
@route('/js/:path#.+#')
def static_js_handler(path):
    return static_file(path, root=os.path.join(resources_dir(), 'frontend/js'))
    
@route('/img/:path#.+#')
def static_img_handler(path):
    return static_file(path, root=os.path.join(resources_dir(), 'frontend/img'))

@route('/favicon.ico')
def favicon_handler():
    return static_file('favicon.ico', root=os.path.join(resources_dir(), 'frontend/img'))
    

### LIBRARY

@route('/library/get/:path#.+#')
def static_library_handler(path):
    return static_file(path, root=os.path.join(resources_dir(), 'library'), mimetype='text/plain')
    
@route('/library/list')
def library_list_handler():
    # return a json list of file names
    file_list = []
    cwd_temp = os.getcwd()
    try:
        os.chdir(os.path.join(resources_dir(), 'library'))
        file_list = glob.glob('*')
    finally:
        os.chdir(cwd_temp)
    return json.dumps(file_list)



### QUEUE

def encode_filename(name):
    str(time.time()) + '-' + base64.urlsafe_b64encode(name)
    
def decode_filename(name):
    index = name.find('-')
    return base64.urlsafe_b64decode(name[index+1:])
    

@route('/queue/get/:name#.+#')
def static_queue_handler(name): 
    return static_file(name, root=storage_dir(), mimetype='text/plain')

@route('/queue/list')
def library_list_handler():
    # base64.urlsafe_b64encode()
    # base64.urlsafe_b64decode()
    # return a json list of file names
    files = []
    cwd_temp = os.getcwd()
    try:
        os.chdir(storage_dir())
        files = filter(os.path.isfile, glob.glob("*"))
        files.sort(key=lambda x: os.path.getmtime(x))
    finally:
        os.chdir(cwd_temp)
    return json.dumps(files)
    
@route('/queue/save', method='POST')
def queue_save_handler():
    ret = '0'
    if 'gcode_name' in request.forms and 'gcode_program' in request.forms:
        name = request.forms.get('gcode_name')
        gcode_program = request.forms.get('gcode_program')
        filename = os.path.abspath(os.path.join(storage_dir(), name.strip('/\\')))
        if os.path.exists(filename) or os.path.exists(filename+'.starred'):
            return "file_exists"
        try:
            fp = open(filename, 'w')
            fp.write(gcode_program)
            print "file saved: " + filename
            ret = '1'
        finally:
            fp.close()
    else:
        print "error: save failed, invalid POST request"
    return ret

@route('/queue/rm/:name')
def queue_rm_handler(name):
    # delete gcode item, on success return '1'
    ret = '0'
    filename = os.path.abspath(os.path.join(storage_dir(), name.strip('/\\')))
    if filename.startswith(storage_dir()):
        if os.path.exists(filename):
            try:
                os.remove(filename);
                print "file deleted: " + filename
                ret = '1'
            finally:
                pass
    return ret   
    
@route('/queue/star/:name')
def queue_star_handler(name):
    ret = '0'
    filename = os.path.abspath(os.path.join(storage_dir(), name.strip('/\\')))
    if filename.startswith(storage_dir()):
        if os.path.exists(filename):
            os.rename(filename, filename + '.starred')
            ret = '1'
    return ret    

@route('/queue/unstar/:name')
def queue_unstar_handler(name):
    ret = '0'
    filename = os.path.abspath(os.path.join(storage_dir(), name.strip('/\\')))
    if filename.startswith(storage_dir()):
        if os.path.exists(filename + '.starred'):
            os.rename(filename + '.starred', filename)
            ret = '1'
    return ret 

    

@route('/')
@route('/index.html')
@route('/app.html')
def default_handler():
    return static_file('app.html', root=os.path.join(resources_dir(), 'frontend') )

@route('/canvas')
def canvas_handler():
    return static_file('testCanvas.html', root=os.path.join(resources_dir(), 'frontend'))    

@route('/serial/:connect')
def serial_handler(connect):
    if connect == '1':
        # print 'js is asking to connect serial'      
        if not SerialManager.is_connected():
            try:
                global SERIAL_PORT, BITSPERSECOND, GUESS_PREFIX
                if not SERIAL_PORT:
                    SERIAL_PORT = SerialManager.match_device(GUESS_PREFIX, BITSPERSECOND)
                SerialManager.connect(SERIAL_PORT, BITSPERSECOND)
                ret = "Serial connected to %s:%d." % (SERIAL_PORT, BITSPERSECOND)  + '<br>'
                time.sleep(1.0) # allow some time to receive a prompt/welcome
                SerialManager.flush_input()
                SerialManager.flush_output()
                return ret
            except serial.SerialException:
                SERIAL_PORT = None
                print "Failed to connect to serial."    
                return ""          
    elif connect == '0':
        # print 'js is asking to close serial'    
        if SerialManager.is_connected():
            if SerialManager.close(): return "1"
            else: return ""  
    elif connect == "2":
        # print 'js is asking if serial connected'
        if SerialManager.is_connected(): return "1"
        else: return ""
    else:
        print 'ambigious connect request from js: ' + connect            
        return ""



@route('/status')
def get_status():
    status = copy.deepcopy(SerialManager.get_hardware_status())
    status['serial_connected'] = SerialManager.is_connected()
    return json.dumps(status)


@route('/flash_firmware')
def flash_firmware_handler():
    global SERIAL_PORT, GUESS_PREFIX
    return_code = 1
    if SerialManager.is_connected():
        SerialManager.close()
    # get serial port by url argument
    # e.g: /flash_firmware?port=COM3
    if 'port' in request.GET.keys():
        serial_port = request.GET['port']
        if serial_port[:3] == "COM" or serial_port[:4] == "tty.":
            SERIAL_PORT = serial_port
    # get serial port by enumeration method
    # currenty this works on windows only for updating the firmware
    if not SERIAL_PORT:
        SERIAL_PORT = SerialManager.match_device(GUESS_PREFIX, BITSPERSECOND)
    # resort to brute force methode
    # find available com ports and try them all
    if not SERIAL_PORT:
        comport_list = SerialManager.list_devices(BITSPERSECOND)
        for port in comport_list:
            print "Trying com port: " + port
            return_code = flash_upload(port, resources_dir())
            if return_code == 0:
                print "Success with com port: " + port
                SERIAL_PORT = port
                break
    else:
        return_code = flash_upload(SERIAL_PORT, resources_dir())
    ret = []
    ret.append('Using com port: %s<br>' % (SERIAL_PORT))    
    if return_code == 0:
        print "SUCCESS: Arduino appears to be flashed."
        ret.append('<h2>Successfully Flashed!</h2><br>')
        ret.append('<a href="/">return</a>')
        return ''.join(ret)
    else:
        SERIAL_PORT = None
        print "ERROR: Failed to flash Arduino."
        ret.append('<h2>Flashing Failed!</h2> Check Log window for possible errors. ')
        ret. append('Most likely LasaurApp could not find the right serial port.<br><a href="/">return</a><br><br>')
        if os.name != 'posix':
            ret. append('If you know the COM ports the Arduino is connected to you can specifically select it here:')
            for i in range(1,13):
                ret. append('<br><a href="/flash_firmware?port=COM%s">COM%s</a>' % (i, i))
        return ''.join(ret)
    

# @route('/gcode/:gcode_line')
# def gcode_handler(gcode_line):
#     if SerialManager.is_connected():    
#         print gcode_line
#         SerialManager.queue_gcode_line(gcode_line)
#         return "Queued for sending."
#     else:
#         return ""

@route('/gcode', method='POST')
def gcode_submit_handler():
    gcode_program = request.forms.get('gcode_program')
    if gcode_program and SerialManager.is_connected():
        lines = gcode_program.split('\n')
        print "Adding to queue %s lines" % len(lines)
        for line in lines:
            SerialManager.queue_gcode_line(line)
        return "__ok__"
    else:
        return "serial disconnected"

@route('/queue_pct_done')
def queue_pct_done_handler():
    return SerialManager.get_queue_percentage_done()


@route('/svg_reader', method='POST')
def svg_upload():
    """Parse SVG string."""
    filename = request.forms.get('filename')
    filedata = request.forms.get('filedata')
    dpi_forced = None
    try:
        dpi_forced = float(request.forms.get('dpi'))
    except:
        pass

    optimize = True
    try:
        optimize = bool(int(request.forms.get('optimize')))
    except:
        pass

    if filename and filedata:
        print "You uploaded %s (%d bytes)." % (filename, len(filedata))
        res = read_svg(filedata, [1220,610], 0.08, dpi_forced, optimize)
        # print boundarys
        jsondata = json.dumps(res)
        # print "returning %d items as %d bytes." % (len(res['boundarys']), len(jsondata))
        return jsondata
    return "You missed a field."


# @route('/svg_reader', method='POST')
# def svg_upload():
#     """Parse SVG string."""
#     data = request.files.get('data')
#     if data.file:
#         raw = data.file.read() # This is dangerous for big files
#         filename = data.filename
#         print "You uploaded %s (%d bytes)." % (filename, len(raw))
#         boundarys = read_svg(raw, [1220,610], 0.08)
#         return json.dumps(boundarys)
#     return "You missed a field."


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
  


### Setup Argument Parser
argparser = argparse.ArgumentParser(description='Run LasaurApp.', prog='lasaurapp')
argparser.add_argument('port', metavar='serial_port', nargs='?', default=False,
                    help='serial port to the Lasersaur')
argparser.add_argument('-v', '--version', action='version', version='%(prog)s ' + VERSION)
argparser.add_argument('-p', '--public', dest='host_on_all_interfaces', action='store_true',
                    default=False, help='bind to all network devices (default: bind to 127.0.0.1)')
argparser.add_argument('-f', '--flash', dest='build_and_flash', action='store_true',
                    default=False, help='flash Arduino with LasaurGrbl firmware')
argparser.add_argument('-l', '--list', dest='list_serial_devices', action='store_true',
                    default=False, help='list all serial devices currently connected')
argparser.add_argument('-d', '--debug', dest='debug', action='store_true',
                    default=False, help='print more verbose for debugging')
argparser.add_argument('--beaglebone', dest='beaglebone', action='store_true',
                    default=False, help='use this for running on beaglebone')
argparser.add_argument('-m', '--match', dest='match',
                    default=GUESS_PREFIX, help='match serial device with this string')                                        
args = argparser.parse_args()



def run_helper():
    if args.debug:
        debug(True)
        if hasattr(sys, "_MEIPASS"):
            print "Data root is: " + sys._MEIPASS             
        print "Persistent storage root is: " + storage_dir()
    if args.build_and_flash:
        return_code = flash_upload(SERIAL_PORT, resources_dir())
        if return_code == 0:
            print "SUCCESS: Arduino appears to be flashed."
        else:
            print "ERROR: Failed to flash Arduino."
    else:
        if args.host_on_all_interfaces:
            run_with_callback('')
        else:
            run_with_callback('127.0.0.1')    
            

print "LasaurApp " + VERSION

if args.beaglebone:
    ### if running on beaglebone, setup (pin muxing) and use UART1
    # for details see: http://www.nathandumont.com/node/250
    SERIAL_PORT = "/dev/ttyO1"
    # echo 0 > /sys/kernel/debug/omap_mux/uart1_txd
    fw = file("/sys/kernel/debug/omap_mux/uart1_txd", "w")
    fw.write("%X" % (0))
    fw.close()
    # echo 20 > /sys/kernel/debug/omap_mux/uart1_rxd
    fw = file("/sys/kernel/debug/omap_mux/uart1_rxd", "w")
    fw.write("%X" % ((1 << 5) | 0))
    fw.close()

if args.list_serial_devices:
    SerialManager.list_devices(BITSPERSECOND)
else:
    if not SERIAL_PORT:
        if args.port:
            # (1) get the serial device from the argument list
            SERIAL_PORT = args.port
            print "Using serial device '"+ SERIAL_PORT +"' from command line."
        else:
            # (2) get the serial device from the config file        
            if os.path.isfile(CONFIG_FILE):
                fp = open(CONFIG_FILE)
                line = fp.readline().strip()
                if len(line) > 3:
                    SERIAL_PORT = line
                    print "Using serial device '"+ SERIAL_PORT +"' from '" + CONFIG_FILE + "'."

    if not SERIAL_PORT:
        if args.match:
            GUESS_PREFIX = args.match
            SERIAL_PORT = SerialManager.match_device(GUESS_PREFIX, BITSPERSECOND)
            if SERIAL_PORT:
                print "Using serial device '"+ str(SERIAL_PORT)
                if os.name == 'posix':
                    # not for windows for now
                    print "(first device to match: " + args.match + ")"            
        else:
            SERIAL_PORT = SerialManager.match_device(GUESS_PREFIX, BITSPERSECOND)
            if SERIAL_PORT:
                print "Using serial device '"+ str(SERIAL_PORT) +"' by best guess."
    
    if not SERIAL_PORT:
        print "-----------------------------------------------------------------------------"
        print "WARNING: LasaurApp doesn't know what serial device to connect to!"
        print "Make sure the Lasersaur hardware is connectd to the USB interface."
        if os.name == 'nt':
            print "ON WINDOWS: You will also need to setup the virtual com port."
            print "See 'Installing Drivers': http://arduino.cc/en/Guide/Windows"
        print "-----------------------------------------------------------------------------"      
    
    # run
    run_helper()     

        


