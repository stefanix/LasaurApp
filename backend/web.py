
import sys
import os
import time
import glob
import json
import copy
import tempfile
import threading
import webbrowser
import wsgiref.simple_server
import bottle
from config import conf
import lasersaur
import jobimport


__author__  = 'Stefan Hechenberger <stefan@nortd.com>'


bottle.BaseRequest.MEMFILE_MAX = 1024*1024*20 # max 20Mb files


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

@bottle.route('/')
def default_handler():
    return bottle.static_file('app.html', root=os.path.join(conf['rootdir'], 'frontend') )


@bottle.route('/css/:path#.+#')
def static_css_handler(path):
    return bottle.static_file(path, root=os.path.join(conf['rootdir'], 'frontend', 'css'))
    
@bottle.route('/js/:path#.+#')
def static_js_handler(path):
    return bottle.static_file(path, root=os.path.join(conf['rootdir'], 'frontend', 'js'))
    
@bottle.route('/img/:path#.+#')
def static_img_handler(path):
    return bottle.static_file(path, root=os.path.join(conf['rootdir'], 'frontend', 'img'))

@bottle.route('/favicon.ico')
def favicon_handler():
    return bottle.static_file('favicon.ico', root=os.path.join(conf['rootdir'], 'frontend', 'img'))


@bottle.route('/temp', method='POST')
@bottle.auth_basic(checkuser)
def temp():
    """Create temp file for downloading."""
    filedata = request.forms.get('filedata')
    fp = tempfile.NamedTemporaryFile(mode='w', delete=False)
    filename = fp.name
    with fp:
        fp.write(filedata)
        fp.close()
    print filedata
    print "file stashed: " + os.path.basename(filename)
    return os.path.basename(filename)


@bottle.route('/download/<filename>/<dlname>')
@bottle.auth_basic(checkuser)
def download(filename, dlname):
    print "requesting: " + filename
    return static_file(filename, root=tempfile.gettempdir(), download=dlname)



### LOW-LEVEL

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

@bottle.route('/offset/<x:float>/<y:float>/<z:float>')
@bottle.auth_basic(checkuser)
@checkserial
def offset(x, y, z):
    lasersaur.def_offset_custom(x, y, z)
    lasersaur.sel_offset_custom()

@bottle.route('/clear_offset')
@bottle.auth_basic(checkuser)
@checkserial
def clear_offset():
    lasersaur.def_offset_custom(0,0,0)
    lasersaur.sel_offset_table()




### JOBS QUEUE

def _get_sorted(globpattern):
    files = []
    cwd_temp = os.getcwd()
    try:
        os.chdir(conf['stordir'])
        files = filter(os.path.isfile, glob.glob(globpattern))
        files.sort(key=lambda x: os.path.getmtime(x))
    finally:
        os.chdir(cwd_temp)
    return files

def _get(jobpath):
    # get job as sting
    if os.path.exists(jobpath):
        pass
    elif os.path.exists(jobpath + '.starred'):
        jobpath = jobpath + '.starred'
    else:
        bottle.abort(400, "No such file.")
    with open(jobpath) as fp:
        job = fp.read()
    return job

def _clear(limit=None):
    files = _get_sorted('*.lsa')
    if type(limit) is not int and limit is not None:
        raise ValueError
    for filename in files:
        if type(limit) is int and limit <= 0:
            break
        filename = os.path.join(conf['stordir'], filename)
        os.remove(filename);
        print "file deleted: " + filename
        if type(limit) is int:
            limit -= 1

def _add(job, name):
    # add job (lsa string)
    # delete excessive job files
    num_to_del = (len(_get_sorted('*.lsa')) +1) - conf['max_jobs_in_list']  
    _clear(num_to_del)
    # add
    namepath = os.path.join(conf['stordir'], name)
    if os.path.exists(namepath) or os.path.exists(namepath+'.starred'):
        bottle.abort(400, "File name exists.")
    with open(namepath, 'w') as fp:
        fp.write(job)
        print "file saved: " + name


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
    load_request = json.loads(bottle.request.forms.get('load_request'))
    job = load_request.get('job')  # always a string
    name = load_request.get('name')
    type_ = load_request.get('type')
    optimize = load_request.get('optimize')

    # sanity check
    if job is None or name is None or type_ is None or optimize is None:
        bottle.abort(400, "Invalid request data.")

    # name fix, TODO: think about this
    namend = name[-4:]
    if namend == '.lsa':
        pass
    elif namend == '.svg' or  namend == '.dxf' or namend == '.ngc' \
      or namend == '.SVG' or  namend == '.DXF' or namend == '.NGC' \
      or namend == '.LSA':
        name = name[:-4] + '.lsa'
    else:
        name = name + '.lsa'

    # check file name available
    if os.path.exists(name) or os.path.exists(name+'.starred'):
        bottle.abort(400, "File name exists.")

    if type_ == 'lsa':
        if optimize:
            job = json.loads(job)
            if optimize and 'vector' in job and 'paths' in job['vector']:
                pathoptimizer.optimize(job['vector']['paths'], conf['tolerance'])
                job['vector']['optimized'] = conf['tolerance']
            _add(json.dumps(job), name)
        else:
            _add(job, name)
    elif type_ == 'svg':
        job = jobimport.read_svg(job, conf['workspace'], 
                                 conf['tolerance'], optimize=optimize)
        _add(json.dumps(job), name)
    elif type_ == 'dxf':
        job = jobimport.read_dxf(job, conf['tolerance'], optimize=optimize)
        _add(json.dumps(job), name)
    elif type_ == 'ngc':
        job = jobimport.read_ngc(job, conf['tolerance'], optimize=optimize)
        _add(json.dumps(job), name)
    else:
        print "ERROR: unsupported file type"
        bottle.abort(400, "Invalid file type.")

    return name
    


@bottle.route('/list')
@bottle.route('/list/<kind>')
@bottle.auth_basic(checkuser)
def list(kind=None):
    """List all queue jobs by name."""
    if kind is None:
        files = _get_sorted('*.lsa*')
    elif kind == 'starred':
        files = _get_sorted('*.lsa.starred')
        print files
        for i in range(len(files)):
            if files[i].endswith('.starred'):
                files[i] = files[i][:-8]
    elif kind == 'unstarred':
        files = _get_sorted('*.lsa')
    else:
        bottle.abort(400, "Invalid kind.")
    return json.dumps(files)


@bottle.route('/get/<jobname>')
@bottle.auth_basic(checkuser)
def get(jobname):
    """Get a queue job in .lsa format."""
    filename = os.path.join(conf['stordir'], jobname.strip('/\\'))
    if os.path.exists(filename):
        pass
    elif os.path.exists(filename + '.starred'):
        filename = filename + '.starred'
    else:
        bottle.abort(400, "No such file.")
    return bottle.static_file(jobname, root=conf['stordir'], mimetype='text/plain')


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
        pass
    elif os.path.exists(filename + '.starred'):
        filename = filename + '.starred'
    else:
        bottle.abort(400, "No such file.")
    os.remove(filename);
    print "file deleted: " + filename


@bottle.route('/clear')
@bottle.auth_basic(checkuser)
def clear():
    """Clear job list."""
    _clear()



### LIBRARY

@bottle.route('/list_library')
@bottle.auth_basic(checkuser)
def list_library():
    """List all library jobs by name."""
    file_list = []
    cwd_temp = os.getcwd()
    try:
        os.chdir(os.path.join(conf['rootdir'], 'library'))
        file_list = glob.glob('*.lsa')
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
    job = _get(os.path.join(conf['rootdir'], 'library', jobname))
    _add(job, jobname)



### JOB EXECUTION

@bottle.route('/run/<jobname>')
@bottle.auth_basic(checkuser)
@checkserial
def run(jobname):
    """Send job from queue to the machine."""
    job = _get(os.path.join(conf['stordir'], jobname.strip('/\\')))
    if not lasersaur.status()['idle']:
        bottle.abort(400, "Machine not ready.")
    lasersaur.job(json.loads(job))


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




###############################################################################
###############################################################################


class Server(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.server = None
        self.lock = threading.Lock()
        self.stop_server = False

    def run(self):
        while 1:
            try:
                with self.lock:
                    if self.stop_server:
                        break
                self.server.handle_request()
            except KeyboardInterrupt:
                break
        print "\nShutting down..."
        lasersaur.close()

    def stop(self):
        with self.lock:
            self.stop_server = True
        self.join()

S = Server()


def start(threaded=True, browser=False, debug=False):
    """ Start a bottle web server.
        Derived from WSGIRefServer.run() 
        to have control over the main loop.
    """
    class FixedHandler(wsgiref.simple_server.WSGIRequestHandler):
        def address_string(self): # Prevent reverse DNS lookups please.
            return self.client_address[0]
        def log_request(*args, **kw):
            if debug:
                return wsgiref.simple_server.WSGIRequestHandler.log_request(*args, **kw)

    S.server = wsgiref.simple_server.make_server(
        conf['network_host'],
        conf['network_port'], 
        bottle.default_app(), 
        wsgiref.simple_server.WSGIServer,
        FixedHandler
    )
    S.server.timeout = 0.01
    S.server.quiet = not debug
    if debug:
        bottle.debug(True)
    print "Persistent storage root is: " + conf['stordir']
    print "-----------------------------------------------------------------------------"
    print "Bottle server starting up ..."
    # print "Serial is set to %d bps" % BITSPERSECOND
    print "Point your browser to: "    
    print "http://%s:%d/      (local)" % ('127.0.0.1', conf['network_port'])  
    print "Use Ctrl-C to quit."
    print "-----------------------------------------------------------------------------"    
    print
    lasersaur.connect(server=True)  # also start websocket stat server
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
    # start server
    if threaded:
        print "INFO: Starting web server thread."
        S.start()
    else:
        print "INFO: Entering main loop."
        S.run()



def stop():
    global S
    S.stop()
    # recreate server to unbind 
    # and allow restarting
    del S
    S = Server()



if __name__ == "__main__":
    start(threaded=True, browser=False, debug=False)
    while 1:  # wait until keyboard interrupt
        try:
            time.sleep(0.1)
        except KeyboardInterrupt:
            break
    stop()
    print "END of LasaurApp"





    


