
import sys
import os
import time
import glob
import json
import argparse
import tempfile
import webbrowser
import wsgiref.simple_server
# from bottle import *
import bottle
from config import conf
import lasersaur
import jobimport


__author__  = 'Stefan Hechenberger <stefan@nortd.com>'



def checkuser(user, pw):
    return bool(user in conf['users'] and conf['users'][user] == pw)


### STATIC FILES

@bottle.route('/css/:path#.+#')
def static_css_handler(path):
    return bottle.static_file(path, root=os.path.join(conf['rootdir'], 'frontend/css'))
    
@bottle.route('/js/:path#.+#')
def static_js_handler(path):
    return bottle.static_file(path, root=os.path.join(conf['rootdir'], 'frontend/js'))
    
@bottle.route('/img/:path#.+#')
def static_img_handler(path):
    return bottle.static_file(path, root=os.path.join(conf['rootdir'], 'frontend/img'))

@bottle.route('/favicon.ico')
def favicon_handler():
    return bottle.static_file('favicon.ico', root=os.path.join(conf['rootdir'], 'frontend/img'))
    


### LOW-LEVEL CONTROL

@bottle.route('/homing')
@bottle.auth_basic(checkuser)
def homing():
    lasersaur.homing()

@bottle.route('/feedrate/<val:float>')
@bottle.auth_basic(checkuser)
def feedrate(val):
    args = json.loads(request.forms.get('args'))
    lasersaur.feedrate(args['val'])

@bottle.route('/intensity/<val:float>')
@bottle.auth_basic(checkuser)
def intensity(val):
    lasersaur.intensity(val)

@bottle.route('/relative')
@bottle.auth_basic(checkuser)
def relative():
    lasersaur.relative()

@bottle.route('/absolute')
@bottle.auth_basic(checkuser)
def absolute():
    lasersaur.absolute()

@bottle.route('/move/<x:float>/<y:float>/<z:float>')
@bottle.auth_basic(checkuser)
def move(x, y, z):
    lasersaur.move(x, y, z)

@bottle.route('/pos')
@bottle.auth_basic(checkuser)
def pos():
    return json.dumps(lasersaur.status()['pos'])

@bottle.route('/air_on')
@bottle.auth_basic(checkuser)
def air_on():
    lasersaur.air_on()

@bottle.route('/air_off')
@bottle.auth_basic(checkuser)
def air_off():
    lasersaur.air_off()

@bottle.route('/aux1_on')
@bottle.auth_basic(checkuser)
def aux1_on():
    lasersaur.aux1_on()

@bottle.route('/aux1_off')
@bottle.auth_basic(checkuser)
def aux1_off():
    lasersaur.aux1_off()

@bottle.route('/set_offset/<x:float>/<y:float>/<z:float>')
@bottle.auth_basic(checkuser)
def set_offset(x, y, z):
    lasersaur.def_offset_custom(x, y, z)
    lasersaur.sel_offset_custom()

@bottle.route('/get_offset')
@bottle.auth_basic(checkuser)
def get_offset():
    return json.dumps(lasersaur.status()['offcustom'])

@bottle.route('/clear_offset')
@bottle.auth_basic(checkuser)
def clear_offset():
    lasersaur.sel_offset_table()



### JOBS QUEUE

def _add(job, name):
    ret = {"ok": False}
    if os.path.exists(name) or os.path.exists(name+'.starred'):
        return "file_exists"
    try:
        fp = open(name, 'w')
        fp.write(job)
        print "file saved: " + name
        ret['ok'] = True
    finally:
        fp.close()
    return ret


@bottle.route('/load', method='POST')
def load():
    """Load a lsa, svg, dxf, or gcode job.

    Args:
        (Args come in through the POST request.)
        job: lsa, svg, dxf, or ngc string
        name: name of the job (string)
        type: 'lsa', 'svg', 'dxf', or 'ngc' (string)
        optimize: flag whether to optimize (bool)
    """
    load_request = json.loads(request.forms.get('load_request'))
    job = load_request.get('job')  # always a string
    name = load_request.get('name')
    type_ = load_request.get('type')
    optimize = load_request.get('optimize')

    # sanity check
    if job is None or name is None or type_ is None or optimize is None:
        raise ValueError

    if type_ == 'lsa' and optimize:
        job = json.loads(job)
        if optimize and 'vector' in job and 'paths' in job['vector']:
            pathoptimizer.optimize(job['vector']['paths'], conf['tolerance'])
            job['vector']['optimized'] = conf['tolerance']
    elif type_ == 'svg':
        job = jobimport.read_svg(job, conf['workspace'], 
                                 conf['tolerance'], optimize=optimize)
    elif type_ == 'dxf':
        job = jobimport.read_dxf(job, conf['tolerance'], optimize=optimize)
    elif type_ == 'ngc':
        job = jobimport.read_ngc(job, conf['tolerance'], optimize=optimize)
    else:
        print "ERROR: unsupported file type"

    # finally add to queue
    _add(json.dumps(job), name)



def list():
    """List all queue jobs by name."""

def get(jobname):
    """Get a queue job in .lsa format."""

def star(jobname):
    """Star a job."""

def unstar(jobname):
    """Unstar a job."""

def delete(jobname):
    """Delete a job."""

def clear():
    """Clear job list."""



@bottle.route('/queue/get/:name#.+#')
def static_queue_handler(name): 
    return static_file(name, root=conf['stordir'], mimetype='text/plain')


@bottle.route('/queue/list')
def library_list_handler():
    # base64.urlsafe_b64encode()
    # base64.urlsafe_b64decode()
    # return a json list of file names
    files = []
    cwd_temp = os.getcwd()
    try:
        os.chdir(conf['stordir'])
        files = filter(os.path.isfile, glob.glob("*"))
        files.sort(key=lambda x: os.path.getmtime(x))
    finally:
        os.chdir(cwd_temp)
    return json.dumps(files)
    


@bottle.route('/queue/rm/:name')
def queue_rm_handler(name):
    # delete queue item, on success return '1'
    ret = '0'
    filename = os.path.abspath(os.path.join(conf['stordir'], name.strip('/\\')))
    if filename.startswith(conf['stordir']):
        if os.path.exists(filename):
            try:
                os.remove(filename);
                print "file deleted: " + filename
                ret = '1'
            finally:
                pass
    return ret 

@bottle.route('/queue/clear')
def queue_clear_handler():
    # delete all queue items, on success return '1'
    ret = '0'
    files = []
    cwd_temp = os.getcwd()
    try:
        os.chdir(conf['stordir'])
        files = filter(os.path.isfile, glob.glob("*"))
        files.sort(key=lambda x: os.path.getmtime(x))
    finally:
        os.chdir(cwd_temp)
    for filename in files:
        if not filename.endswith('.starred'):
            filename = os.path.join(conf['stordir'], filename)
            try:
                os.remove(filename);
                print "file deleted: " + filename
                ret = '1'
            finally:
                pass
    return ret
    
@bottle.route('/queue/star/:name')
def queue_star_handler(name):
    ret = '0'
    filename = os.path.abspath(os.path.join(conf['stordir'], name.strip('/\\')))
    if filename.startswith(conf['stordir']):
        if os.path.exists(filename):
            os.rename(filename, filename + '.starred')
            ret = '1'
    return ret    

@bottle.route('/queue/unstar/:name')
def queue_unstar_handler(name):
    ret = '0'
    filename = os.path.abspath(os.path.join(conf['stordir'], name.strip('/\\')))
    if filename.startswith(conf['stordir']):
        if os.path.exists(filename + '.starred'):
            os.rename(filename + '.starred', filename)
            ret = '1'
    return ret 


def encode_filename(name):
    str(time.time()) + '-' + base64.urlsafe_b64encode(name)
    
def decode_filename(name):
    index = name.find('-')
    return base64.urlsafe_b64decode(name[index+1:])





### JOB EXECUTION

def run(self, jobname):
    """Send job from queue to the machine."""

def progress(self):
    """Get percentage of job done."""

def pause(self):
    """Pause a job gracefully."""
def resume(self):
    """Resume a paused job."""

def stop(self):
    """Halt machine immediately and purge job."""
def unstop(self):
    """Recover machine from stop mode."""


### LIBRARY

def list_library(self):
    """List all library jobs by name."""

def get_library(self, jobname):
    """Get a library job in .lsa format."""

def load_library(self, jobname):
    """Load a library job into the queue."""


@bottle.route('/library/get/:path#.+#')
def static_library_handler(path):
    return static_file(path, root=os.path.join(conf['rootdir'], 'library'), mimetype='text/plain')
    
@bottle.route('/library/list')
def library_list_handler():
    # return a json list of file names
    file_list = []
    cwd_temp = os.getcwd()
    try:
        os.chdir(os.path.join(conf['rootdir'], 'library'))
        file_list = glob.glob('*')
    finally:
        os.chdir(cwd_temp)
    return json.dumps(file_list)


### MCU MANAGMENT

def build(self, firmware_name=None):
    """Build firmware from firmware/src files."""

def flash(self, firmware_name=None):
    """Flash firmware to MCU."""

def reset(self):
    """Reset MCU"""


















### ROOT

@bottle.route('/')
def default_handler():
    return bottle.static_file('app.html', root=os.path.join(conf['rootdir'], 'frontend') )


@bottle.route('/stash_download', method='POST')
def stash_download():
    """Create a download file event from string."""
    filedata = request.forms.get('filedata')
    fp = tempfile.NamedTemporaryFile(mode='w', delete=False)
    filename = fp.name
    with fp:
        fp.write(filedata)
        fp.close()
    print filedata
    print "file stashed: " + os.path.basename(filename)
    return os.path.basename(filename)

@bottle.route('/download/:filename/:dlname')
def download(filename, dlname):
    print "requesting: " + filename
    return static_file(filename, root=tempfile.gettempdir(), download=dlname)
  



@bottle.route('/status')
def get_status():
    status = lasersaur.status()  # this returns a copy
    return json.dumps(status)


@bottle.route('/pause/:flag')
def set_pause(flag):
    # returns pause status
    if flag == '1':
        if lasersaur.pause():
            print "pausing ..."
            return '1'
        else:
            return '0'
    elif flag == '0':
        print "resuming ..."
        if lasersaur.unpause(False):
            return '1'
        else:
            return '0'



@bottle.route('/flash_firmware')
@bottle.route('/flash_firmware/:firmware_file')
def flash_firmware_handler(firmware_file=None):
    # get serial port by url argument
    # e.g: /flash_firmware?port=COM3
    serial_port = request.GET.get('port')
    if not (serial_port and (serial_port[:3] == "COM" or serial_port[:4] == "tty.")):
        serial_port = None
    return_code = lasersaur.flash(serial_port=serial_port, firmware_file=firmware_file)

    ret = []
    # ret.append('Using com port: %s<br>' % (SERIAL_PORT))
    ret.append('Using firmware: %s<br>' % (firmware_file))    
    if return_code == 0:
        print "SUCCESS: Arduino appears to be flashed."
        ret.append('<h2>Successfully Flashed!</h2><br>')
        ret.append('<a href="/">return</a>')
        return ''.join(ret)
    else:
        print "ERROR: Failed to flash Arduino."
        ret.append('<h2>Flashing Failed!</h2> Check terminal window for possible errors. ')
        ret.append('Most likely LasaurApp could not find the right serial port.')
        ret.append('<br><a href="/flash_firmware/'+firmware_file+'">try again</a> or <a href="/">return</a><br><br>')
        if os.name != 'posix':
            ret. append('If you know the COM ports the Arduino is connected to you can specifically select it here:')
            for i in range(1,13):
                ret. append('<br><a href="/flash_firmware?port=COM%s">COM%s</a>' % (i, i))
        return ''.join(ret)


@bottle.route('/build_firmware')
def build_firmware_handler():
    ret = []
    buildname = "LasaurGrbl_from_src"
    return_code = lasersaur.build(firmware_name=buildname)
    if return_code != 0:
        print ret
        ret.append('<h2>FAIL: build error!</h2>')
        ret.append('Syntax error maybe? Try builing in the terminal.')
        ret.append('<br><a href="/">return</a><br><br>')
    else:
        print "SUCCESS: firmware built."
        ret.append('<h2>SUCCESS: new firmware built!</h2>')
        ret.append('<br><a href="/flash_firmware/'+buildname+'.hex">Flash Now!</a><br><br>')
    return ''.join(ret)


@bottle.route('/reset_atmega')
def reset_atmega_handler():
    return lasersaur.reset()


@bottle.route('/job', method='POST')
def job_submit_handler():
    """Submit a job in lsa format."""
    if not lasersaur.connected():
        return "serial disconnected"

    job_data = request.forms.get('job_data')
    if not job_data:
        return "no job data"

    # print job_data
    jobdict = json.loads(job_data)
    lasersaur.job(jobdict)
    return "__ok__"
        

@bottle.route('/queue_pct_done')
def queue_pct_done_handler():
    return lasersaur.percentage()





def start_server(debug=False, browser=False):
    """ Start a wsgiref server instance with control over the main loop.
        Derived from bottle.py's WSGIRefServer.run()
    """
    class FixedHandler(wsgiref.simple_server.WSGIRequestHandler):
        def address_string(self): # Prevent reverse DNS lookups please.
            return self.client_address[0]
        def log_request(*args, **kw):
            if debug:
                return wsgiref.simple_server.WSGIRequestHandler.log_request(*args, **kw)

    server = wsgiref.simple_server. make_server(
        conf['network_host'],
        conf['network_port'], 
        bottle.default_app(), 
        wsgiref.simple_server.WSGIServer,
        FixedHandler
    )
    server.timeout = 0.01
    server.quiet = not debug
    if debug:
        bottle.debug(True)
    # server.serve_forever()

    print "Persistent storage root is: " + conf['stordir']
    print "-----------------------------------------------------------------------------"
    print "Bottle server starting up ..."
    # print "Serial is set to %d bps" % BITSPERSECOND
    print "Point your browser to: "    
    print "http://%s:%d/      (local)" % ('127.0.0.1', conf['network_port'])  
    print "Use Ctrl-C to quit."
    print "-----------------------------------------------------------------------------"    
    print
    lasersaur.connect()
    # open web-browser
    if browser:
        try:
            webbrowser.open_new_tab('http://127.0.0.1:'+str(conf['network_port']))
        except webbrowser.Error:
            print "Cannot open Webbrowser, please do so manually."
    sys.stdout.flush()  # make sure everything gets flushed
    while 1:
        try:
            server.handle_request()
        except KeyboardInterrupt:
            break
    print "\nShutting down..."
    lasersaur.close()



if __name__ == "__main__":

    ### Setup Argument Parser
    argparser = argparse.ArgumentParser(description='Run LasaurApp.', prog='lasaurapp')
    argparser.add_argument('port', metavar='serial_port', nargs='?', default=False,
                        help='serial port to the Lasersaur')
    argparser.add_argument('-v', '--version', action='version', version='%(prog)s ' + conf['version'],
                        default=False, help='bind to all network devices (default: bind to 127.0.0.1)')
    argparser.add_argument('-l', '--list', dest='list_serial_devices', action='store_true',
                        default=False, help='list all serial devices currently connected')
    argparser.add_argument('-d', '--debug', dest='debug', action='store_true',
                        default=False, help='print more verbose for debugging')
    argparser.add_argument('-b', '--browser', dest='browser', action='store_true',
                        default=False, help='launch interface in browser')
    args = argparser.parse_args()



    print "LasaurApp " + conf['version']


        
    # run
    if args.debug:
        if hasattr(sys, "_MEIPASS"):
            print "Data root is: " + sys._MEIPASS             

    start_server(debug=args.debug, browser=args.browser)

    


