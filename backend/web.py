
import sys
import os
import time
import glob
import json
import copy
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
    """Check login credentials, used by auth_basic decorator."""
    return bool(user in conf['users'] and conf['users'][user] == pw)

def checkserial(func):
    """Decorator to call function only when machine connected."""
    def _decorator(*args, **kwargs):
            if lasersaur.connected():
                return func(*args, **kwargs)
            else:
                bottle.abort(400, "No machine.")
    return _decorator


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
    

### STATE

@bottle.route('/config')
@bottle.auth_basic(checkuser)
def config():
    confcopy = copy.deepcopy(conf)
    del confcopy['users']
    return json.dumps(confcopy)

@bottle.route('/status')
@bottle.auth_basic(checkuser)
@checkserial
def status():
    return json.dumps(lasersaur.status())


### LOW-LEVEL CONTROL

@bottle.route('/homing')
@bottle.auth_basic(checkuser)
@checkserial
def homing():
    lasersaur.homing()

@bottle.route('/feedrate/<val:float>')
@bottle.auth_basic(checkuser)
@checkserial
def feedrate(val):
    lasersaur.feedrate(val)

@bottle.route('/intensity/<val:float>')
@bottle.auth_basic(checkuser)
@checkserial
def intensity(val):
    lasersaur.intensity(val)

@bottle.route('/relative')
@bottle.auth_basic(checkuser)
@checkserial
def relative():
    lasersaur.relative()

@bottle.route('/absolute')
@bottle.auth_basic(checkuser)
@checkserial
def absolute():
    lasersaur.absolute()

@bottle.route('/move/<x:float>/<y:float>/<z:float>')
@bottle.auth_basic(checkuser)
@checkserial
def move(x, y, z):
    lasersaur.move(x, y, z)

@bottle.route('/pos')
@bottle.auth_basic(checkuser)
@checkserial
def pos():
    return json.dumps(lasersaur.status()['pos'])

@bottle.route('/air_on')
@bottle.auth_basic(checkuser)
@checkserial
def air_on():
    lasersaur.air_on()

@bottle.route('/air_off')
@bottle.auth_basic(checkuser)
@checkserial
def air_off():
    lasersaur.air_off()

@bottle.route('/aux1_on')
@bottle.auth_basic(checkuser)
@checkserial
def aux1_on():
    lasersaur.aux1_on()

@bottle.route('/aux1_off')
@bottle.auth_basic(checkuser)
@checkserial
def aux1_off():
    lasersaur.aux1_off()

@bottle.route('/set_offset/<x:float>/<y:float>/<z:float>')
@bottle.auth_basic(checkuser)
@checkserial
def set_offset(x, y, z):
    lasersaur.def_offset_custom(x, y, z)
    lasersaur.sel_offset_custom()

@bottle.route('/get_offset')
@bottle.auth_basic(checkuser)
@checkserial
def get_offset():
    return json.dumps(lasersaur.status()['offcustom'])

@bottle.route('/clear_offset')
@bottle.auth_basic(checkuser)
@checkserial
def clear_offset():
    lasersaur.sel_offset_table()



### JOBS QUEUE

def _get_sorted():
    files = []
    cwd_temp = os.getcwd()
    try:
        os.chdir(conf['stordir'])
        files = filter(os.path.isfile, glob.glob("*"))
        files.sort(key=lambda x: os.path.getmtime(x))
    finally:
        os.chdir(cwd_temp)
    return files

def _get(path, jobname):
    jobpath = os.path.join(path, jobname)
    if not os.path.exists(jobpath):
        bottle.abort(400, "No such file.")
    try:
        fp = open(jobpath)
        job = fp.read()
    finally:
        fp.close()
    return job

def _clear(limit=None):
    files = _get_sorted()
    if type(limit) is not int and not None:
        raise ValueError
    for filename in files:
        if type(limit) is int and limit <= 0:
            break
        if not filename.endswith('.starred'):
            filename = os.path.join(conf['stordir'], filename)
            os.remove(filename);
            print "file deleted: " + filename
            if type(limit) is int:
                limit -= 1

def _add(job, name):
    # delete excessive job files
    num_to_del = (len(_get_sorted()) +1) - conf['max_jobs_in_list']  
    _clear(num_to_del)
    # add
    namepath = os.path.join(conf['stordir'], name)
    if os.path.exists(namepath) or os.path.exists(namepath+'.starred'):
        bottle.abort(400, "File name exists.")
    try:
        fp = open(namepath, 'w')
        fp.write(job)
        print "file saved: " + name
    finally:
        fp.close()


@bottle.route('/load', method='POST')
@bottle.auth_basic(checkuser)
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

    # check file name available
    if os.path.exists(name) or os.path.exists(name+'.starred'):
        bottle.abort(400, "File name exists.")

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


@bottle.route('/list')
@bottle.auth_basic(checkuser)
def list():
    """List all queue jobs by name."""
    files = _get_sorted()
    return json.dumps(files)


@bottle.route('/get/<jobname>')
@bottle.auth_basic(checkuser)
def get(jobname):
    """Get a queue job in .lsa format."""
    return static_file(jobname, root=conf['stordir'], mimetype='text/plain')


@bottle.route('/star/<jobname>')
@bottle.auth_basic(checkuser)
def star(jobname):
    """Star a job."""
    filename = os.path.join(conf['stordir'], jobname.strip('/\\'))
    if os.path.exists(filename):
        os.rename(filename, filename + '.starred')
    else:
        bottle.abort(400, "No such file.")


@bottle.route('/unstar/<jobname>')
@bottle.auth_basic(checkuser)
def unstar(jobname):
    """Unstar a job."""
    filename = os.path.join(conf['stordir'], jobname.strip('/\\'))
    if os.path.exists(filename + '.starred'):
        os.rename(filename + '.starred', filename)
    else:
        bottle.abort(400, "No such file.")


@bottle.route('/delete/<jobname>')
@bottle.auth_basic(checkuser)
def delete(jobname):
    """Delete a job."""
    filename = os.path.join(conf['stordir'], jobname.strip('/\\'))
    if os.path.exists(filename):
        try:
            os.remove(filename);
            print "file deleted: " + filename
        finally:
            pass
    else:
        bottle.abort(400, "No such file.")


@bottle.route('/clear')
@bottle.auth_basic(checkuser)
def clear():
    """Clear job list."""
    _clear()





### JOB EXECUTION

@bottle.route('/run/<jobname>')
@bottle.auth_basic(checkuser)
@checkserial
def run(jobname):
    """Send job from queue to the machine."""
    job = _get(conf['stordir'], jobname.strip('/\\'))
    if not status()['idle']:
        bottle.abort(400, "Machine not ready.")
    lasersaur.job(job)


@bottle.route('/progress')
@bottle.auth_basic(checkuser)
@checkserial
def progress():
    """Get percentage of job done, 0-100, -1 if none active."""
    return lasersaur.percentage()


@bottle.route('/pause')
@bottle.auth_basic(checkuser)
@checkserial
def pause():
    """Pause a job gracefully."""
    lasersaur.pause()


@bottle.route('/unpause')
@bottle.auth_basic(checkuser)
@checkserial
def unpause():
    """Resume a paused job."""
    lasersaur.unpause()


@bottle.route('/stop')
@bottle.auth_basic(checkuser)
@checkserial
def stop():
    """Halt machine immediately and purge job."""
    lasersaur.stop()


@bottle.route('/unstop')
@bottle.auth_basic(checkuser)
@checkserial
def unstop():
    """Recover machine from stop mode."""
    lasersaur.unstop()



### LIBRARY

@bottle.route('/list_library')
@bottle.auth_basic(checkuser)
def list_library():
    """List all library jobs by name."""
    file_list = []
    cwd_temp = os.getcwd()
    try:
        os.chdir(os.path.join(conf['rootdir'], 'library'))
        file_list = glob.glob('*')
    finally:
        os.chdir(cwd_temp)
    return json.dumps(file_list)


@bottle.route('/get_library/<jobname>')
@bottle.auth_basic(checkuser)
def get_library(jobname):
    """Get a library job in .lsa format."""
    return bottle.static_file(jobname, root=os.path.join(conf['rootdir'], 'library'), mimetype='text/plain')


@bottle.route('/load_library/<jobname>')
@bottle.auth_basic(checkuser)
def load_library(jobname):
    """Load a library job into the queue."""
    job = _get(os.path.join(conf['rootdir'], 'library'), jobname)
    _add(job, jobname)




### MCU MANAGMENT

@bottle.route('/build')
@bottle.route('/build/<firmware>')
@bottle.auth_basic(checkuser)
def build(self, firmware_name=None):
    """Build firmware from firmware/src files."""
    buildname = "LasaurGrbl_from_src"
    return_code = lasersaur.build(firmware_name=buildname)
    if return_code != 0:
        bottle.abort(400, "Build failed.")


@bottle.route('/flash')
@bottle.route('/flash/<firmware>')
@bottle.auth_basic(checkuser)
def flash(self, firmware=None):
    """Flash firmware to MCU."""
    return_code = lasersaur.flash(firmware_file=firmware)
    if return_code != 0:
        bottle.abort(400, "Flashing failed.")


@bottle.route('/reset')
@bottle.auth_basic(checkuser)
def reset():
    """Reset MCU"""
    connected = lasersaur.connected()
    if connected:
        lasersaur.close()
    lasersaur.reset()
    if connected:
        lasersaur.connect()


















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
  




@bottle.route('/flash_firmware')
@bottle.route('/flash_firmware/:firmware_file')
def flash_firmware_handler(firmware_file=None):
    return_code = lasersaur.flash(firmware_file=firmware_file)
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
        ret.append('<h2>Flashing Failed!</h2>. ')
        ret.append('Most likely LasaurApp could not find the right serial port.')
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
    if not lasersaur.connected():
        print "---------------"
        print "HOW TO configure the SERIAL PORT:"
        print "in LasaurApp/backend/ create a configuration file" 
        print "userconfig.py, and add something like:"
        print "conf = {"
        print "    'serial_port': 'COM3'," 
        print "}"
        print "Any settings in this conf dictionary will overwrite config.py"
        print "---------------"
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
    argparser.add_argument('-u', '--usbhack', dest='usbhack', action='store_true',
                        default=False, help='use usb reset hack (advanced)')
    argparser.add_argument('-b', '--browser', dest='browser', action='store_true',
                        default=False, help='launch interface in browser')
    args = argparser.parse_args()



    print "LasaurApp " + conf['version']
    conf['usb_reset_hack'] = args.usbhack

    # run
    if args.debug:
        if hasattr(sys, "_MEIPASS"):
            print "Data root is: " + sys._MEIPASS



    start_server(debug=args.debug, browser=args.browser)

    


