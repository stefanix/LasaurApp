# -*- coding: utf-8 -*-

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
import driveboard
import jobimport


__author__  = 'Stefan Hechenberger <stefan@nortd.com>'


bottle.BaseRequest.MEMFILE_MAX = 1024*1024*100 # max 100Mb files


def checkuser(user, pw):
    """Check login credentials, used by auth_basic decorator."""
    return bool(user in conf['users'] and conf['users'][user] == pw)

def checkserial(func):
    """Decorator to call function only when machine connected."""
    def _decorator(*args, **kwargs):
            if driveboard.connected():
                return func(*args, **kwargs)
            else:
                bottle.abort(400, "No machine.")
    return _decorator




### STATIC FILES

@bottle.route('/')
def default_handler():
    return bottle.static_file('app.html', root=os.path.join(conf['rootdir'], 'frontend') )

@bottle.route('/<file>')
def static_bin_handler(file):
    return bottle.static_file(file, root=os.path.join(conf['rootdir'], 'frontend'))

@bottle.route('/css/<path:path>')
def static_css_handler(path):
    return bottle.static_file(path, root=os.path.join(conf['rootdir'], 'frontend', 'css'))

@bottle.route('/fonts/<path:path>')
def static_font_handler(path):
    return bottle.static_file(path, root=os.path.join(conf['rootdir'], 'frontend', 'fonts'))

@bottle.route('/js/<path:path>')
def static_js_handler(path):
    return bottle.static_file(path, root=os.path.join(conf['rootdir'], 'frontend', 'js'))

@bottle.route('/img/<path:path>')
def static_img_handler(path):
    return bottle.static_file(path, root=os.path.join(conf['rootdir'], 'frontend', 'img'))

@bottle.route('/favicon.ico')
def favicon_handler():
    return bottle.static_file('favicon.ico', root=os.path.join(conf['rootdir'], 'frontend', 'img'))


@bottle.route('/temp', method='POST')
@bottle.auth_basic(checkuser)
def temp():
    """Create temp file for downloading."""
    filedata = bottle.request.forms.get('filedata')
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
    return bottle.static_file(filename, root=tempfile.gettempdir(), download=dlname)



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
    return json.dumps(driveboard.status())

@bottle.route('/homing')
@bottle.auth_basic(checkuser)
@checkserial
def homing():
    driveboard.homing()

@bottle.route('/feedrate/<val:float>')
@bottle.auth_basic(checkuser)
@checkserial
def feedrate(val):
    driveboard.feedrate(val)

@bottle.route('/intensity/<val:float>')
@bottle.auth_basic(checkuser)
@checkserial
def intensity(val):
    driveboard.intensity(val)

@bottle.route('/relative')
@bottle.auth_basic(checkuser)
@checkserial
def relative():
    driveboard.relative()

@bottle.route('/absolute')
@bottle.auth_basic(checkuser)
@checkserial
def absolute():
    driveboard.absolute()

@bottle.route('/move/<x:float>/<y:float>/<z:float>')
@bottle.auth_basic(checkuser)
@checkserial
def move(x, y, z):
    driveboard.move(x, y, z)

@bottle.route('/air_on')
@bottle.auth_basic(checkuser)
@checkserial
def air_on():
    driveboard.air_on()

@bottle.route('/air_off')
@bottle.auth_basic(checkuser)
@checkserial
def air_off():
    driveboard.air_off()

@bottle.route('/aux1_on')
@bottle.auth_basic(checkuser)
@checkserial
def aux1_on():
    driveboard.aux1_on()

@bottle.route('/aux1_off')
@bottle.auth_basic(checkuser)
@checkserial
def aux1_off():
    driveboard.aux1_off()

@bottle.route('/offset/<x:float>/<y:float>/<z:float>')
@bottle.auth_basic(checkuser)
@checkserial
def offset(x, y, z):
    driveboard.def_offset_custom(x, y, z)
    driveboard.sel_offset_custom()

@bottle.route('/clear_offset')
@bottle.auth_basic(checkuser)
@checkserial
def clear_offset():
    driveboard.def_offset_custom(0,0,0)
    driveboard.sel_offset_table()




### JOBS QUEUE

def _get_sorted(globpattern, library=False, stripext=False):
    files = []
    cwd_temp = os.getcwd()
    try:
        if library:
            os.chdir(os.path.join(conf['rootdir'], 'library'))
            files = filter(os.path.isfile, glob.glob(globpattern))
            files.sort()
        else:
            os.chdir(conf['stordir'])
            files = filter(os.path.isfile, glob.glob(globpattern))
            files.sort(key=lambda x: os.path.getmtime(x))
        if stripext:
            for i in range(len(files)):
                if files[i].endswith('.lsa'):
                    files[i] = files[i][:-4]
                elif files[i].endswith('.lsa.starred'):
                    files[i] = files[i][:-12]
    finally:
        os.chdir(cwd_temp)
    return files

def _get(jobname, library=False):
    # get job as sting
    if library:
        jobpath = os.path.join(conf['rootdir'], 'library', jobname.strip('/\\'))
    else:
        jobpath = os.path.join(conf['stordir'], jobname.strip('/\\'))
    if os.path.exists(jobpath+'.lsa'):
        jobpath = jobpath+'.lsa'
    elif os.path.exists(jobpath + '.lsa.starred'):
        jobpath = jobpath + '.lsa.starred'
    else:
        bottle.abort(400, "No such file.")
    with open(jobpath) as fp:
        job = fp.read()
    return job

def _get_path(jobname, library=False):
    if library:
        jobpath = os.path.join(conf['rootdir'], 'library', jobname.strip('/\\'))
    else:
        jobpath = os.path.join(conf['stordir'], jobname.strip('/\\'))
    if os.path.exists(jobpath+'.lsa'):
        return jobpath+'.lsa'
    elif os.path.exists(jobpath+'.lsa.starred'):
        return jobpath+'.lsa.starred'
    else:
        bottle.abort(400, "No such file.")

def _exists(jobname):
    namepath = os.path.join(conf['stordir'], jobname.strip('/\\'))
    if os.path.exists(namepath+'.lsa') or os.path.exists(namepath+'.lsa.starred'):
        bottle.abort(400, "File name exists.")

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
    namepath = os.path.join(conf['stordir'], name.strip('/\\')+'.lsa')
    if os.path.exists(namepath):
        bottle.abort(400, "File name exists.")
    with open(namepath, 'w') as fp:
        fp.write(job)
        print "file saved: " + namepath

def _unique_name(jobname):
    files = _get_sorted('*.lsa*', stripext=True)
    if jobname in files:
        for i in xrange(2,999):
            altname = "%s_%s" % (jobname, i)
            if altname in files:
                continue
            else:
                jobname = altname
                break
    return jobname



@bottle.route('/load', method='POST')
@bottle.auth_basic(checkuser)
def load():
    """Load a lsa, svg, dxf, or gcode job.

    Args:
        (Args come in through the POST request.)
        job: Parsed lsa or job string (lsa, svg, dxf, or ngc).
        name: name of the job (string)
        optimize: flag whether to optimize (bool)
    """
    load_request = json.loads(bottle.request.forms.get('load_request'))
    job = load_request.get('job')  # always a string
    name = load_request.get('name')
    optimize = load_request.get('optimize')
    # sanity check
    if job is None or name is None or optimize is None:
        bottle.abort(400, "Invalid request data.")
    # convert
    try:
        job = jobimport.convert(job, optimize=optimize)
    except TypeError:
        bottle.abort(400, "Invalid file type.")

    altname = _unique_name(name)
    _add(json.dumps(job), altname)
    return json.dumps(altname)



@bottle.route('/listing')
@bottle.route('/listing/<kind>')
@bottle.auth_basic(checkuser)
def listing(kind=None):
    """List all queue jobs by name."""
    if kind is None:
        files = _get_sorted('*.lsa*', stripext=True)
    elif kind == 'starred':
        files = _get_sorted('*.lsa.starred', stripext=True)
        print files
    elif kind == 'unstarred':
        files = _get_sorted('*.lsa', stripext=True)
    else:
        bottle.abort(400, "Invalid kind.")
    return json.dumps(files)


@bottle.route('/get/<jobname>')
@bottle.auth_basic(checkuser)
def get(jobname='woot'):
    """Get a queue job in .lsa format."""
    base, name = os.path.split(_get_path(jobname))
    return bottle.static_file(name, root=base, mimetype='text/plain')


@bottle.route('/star/<jobname>')
@bottle.auth_basic(checkuser)
def star(jobname):
    """Star a job."""
    jobpath = _get_path(jobname)
    if jobpath.endswith('.lsa'):
        os.rename(jobpath, jobpath + '.starred')
    else:
        bottle.abort(400, "No such file.")


@bottle.route('/unstar/<jobname>')
@bottle.auth_basic(checkuser)
def unstar(jobname):
    """Unstar a job."""
    jobpath = _get_path(jobname)
    if jobpath.endswith('.starred'):
        os.rename(jobpath, jobpath[:-8])
    else:
        bottle.abort(400, "No such file.")


@bottle.route('/remove/<jobname>')
@bottle.auth_basic(checkuser)
def remove(jobname):
    """Delete a job."""
    jobpath = _get_path(jobname)
    os.remove(jobpath)
    print "INFO: file deleted: " + jobpath


@bottle.route('/clear')
@bottle.auth_basic(checkuser)
def clear():
    """Clear job list."""
    _clear()



### LIBRARY

@bottle.route('/listing_library')
@bottle.auth_basic(checkuser)
def listing_library():
    """List all library jobs by name."""
    files = _get_sorted('*.lsa', library=True, stripext=True)
    return json.dumps(files)


@bottle.route('/get_library/<jobname>')
@bottle.auth_basic(checkuser)
def get_library(jobname):
    """Get a library job in .lsa format."""
    base, name = os.path.split(_get_path(jobname, library=True))
    return bottle.static_file(name, root=base, mimetype='text/plain')


@bottle.route('/load_library/<jobname>')
@bottle.auth_basic(checkuser)
def load_library(jobname):
    """Load a library job into the queue."""
    job = _get(jobname, library=True)
    jobname = _unique_name(jobname)
    _add(job, jobname)
    return json.dumps(jobname)

@bottle.route('/test')
@bottle.auth_basic(checkuser)
def test(jobname):
    return 100/0.0


### JOB EXECUTION

@bottle.route('/run/<jobname>')
@bottle.auth_basic(checkuser)
@checkserial
def run(jobname):
    """Send job from queue to the machine."""
    job = _get(jobname)
    if not driveboard.status()['ready']:
        bottle.abort(400, "Machine not ready.")
    driveboard.job(json.loads(job))


@bottle.route('/pause')
@bottle.auth_basic(checkuser)
@checkserial
def pause():
    """Pause a job gracefully."""
    driveboard.pause()


@bottle.route('/unpause')
@bottle.auth_basic(checkuser)
@checkserial
def unpause():
    """Resume a paused job."""
    driveboard.unpause()


@bottle.route('/stop')
@bottle.auth_basic(checkuser)
@checkserial
def stop_():
    """Halt machine immediately and purge job."""
    driveboard.stop()


@bottle.route('/unstop')
@bottle.auth_basic(checkuser)
@checkserial
def unstop():
    """Recover machine from stop mode."""
    driveboard.unstop()




### MCU MANAGMENT

@bottle.route('/build')
@bottle.route('/build/<firmware>')
@bottle.auth_basic(checkuser)
def build(firmware_name=None):
    """Build firmware from firmware/src files."""
    buildname = "LasaurGrbl_from_src"
    if firmware_name is None:
        return_code = driveboard.build()
    else:
        return_code = driveboard.build(firmware_name=buildname)
    if return_code != 0:
        bottle.abort(400, "Build failed.")


@bottle.route('/flash')
@bottle.route('/flash/<firmware>')
@bottle.auth_basic(checkuser)
def flash(firmware=None):
    """Flash firmware to MCU."""
    if firmware is None:
        return_code = driveboard.flash()
    else:
        return_code = driveboard.flash(firmware_file=firmware)
    if return_code != 0:
        bottle.abort(400, "Flashing failed.")


@bottle.route('/reset')
@bottle.auth_basic(checkuser)
def reset():
    """Reset MCU"""
    connected = driveboard.connected()
    if connected:
        driveboard.close()
    driveboard.reset()
    if connected:
        driveboard.connect()


@bottle.route('/hello/<name>')
def hello(name):
    return bottle.template('<b>Hello {{name}}</b>!', name=name)

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
        driveboard.close()

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
    driveboard.connect(server=True)  # also start websocket stat server
    if not driveboard.connected():
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
    start()
    while 1:  # wait until keyboard interrupt
        try:
            time.sleep(0.1)
        except KeyboardInterrupt:
            break
    stop()
    print "END of LasaurApp"
