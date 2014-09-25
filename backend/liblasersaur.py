# liblasersaur - control a networked Lasersaur from python
# Copyright (c) 2011 Nortd Labs
# Open Source by the terms of the Gnu Public License (GPL3) or higher.
# ###
#
# This is a client implementation that connects to the LasaurApp
# control software on a Lasersaur. 
#
# This library is an example client for the Lasersaur net API.
#
# Usage:
# ------
# import time
# import lasersaur
#
# laser = lasersaur.Lasersaur()
# jobname = laser.load('Lasersaur.lsa')
# if laser.ready():
#   laser.run(jobname)
# 
# while not laser.ready():
#   print "%s% done!" % (laser.progress())
#   time.sleep(1)
# 
# print "job done"
#

import os
import time
import urllib
import urllib2
import jobimport
import jobimport.path_optimizers

__author__  = 'Stefan Hechenberger <stefan@nortd.com>'




class Lasersaur(object):
    def __init__(self, host="lasersaur.local", port=4444):
        """Create a Lasersaur client object."""
        self.conf = None

        # fetch config
        self.conf = self.config()

        # urllib2: enable auth
        password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        top_level_url = "http://%s:%s/" % (host, port)
        password_mgr.add_password(None, top_level_url, username, password)
        handler = urllib2.HTTPBasicAuthHandler(password_mgr)
        opener = urllib2.build_opener(handler)
        urllib2.install_opener(opener) # use auth for all urllib2.urlopen()

    def _request(self, postdict=None, ret=False):
        postdata = urllib.urlencode(postdict)
        req = urllib2.Request(url, postdata)
        response = urllib2.urlopen(req)
        if response.code != 200:
            print "RESPONSE: %s, %s" % (response.code, response.msg)
            raise urllib2.HTTPError
        if ret:
            return json.loads(response.read())


    def config(self):
        """Get config from machine."""

    def status(self):
        """Get status report of machine."""

    def ready(self):
        """Get ready status, specifically."""


    ### LOW-LEVEL CONTROL

    def homing(self):
        self._request('/homing')

    def feedrate(self, val):
        self._request('/feedrate/%.2f' % val)

    def intensity(self, val):
        self._request('/intensity/%.2f' % val)

    def relative(self):
        self._request('/relative')
        
    def absolute(self):
        self._request('/absolute')

    def move(self, x, y, z=0.0):
        self._request('/intensity/%.4f/%.4f/%.4f' % (x,y,z))

    def pos(self):
        return self._request('/pos', ret=True)

    def air_on(self):
        self._request('/air_on')

    def air_off(self):
        self._request('/air_off')

    def aux1_on(self):
        self._request('/aux1_on')

    def aux1_off(self):
        self._request('/aux1_off')

    def set_offset(self, x, y, z):
        self._request('/set_offset/%.4f/%.4f/%.4f' % (x,y,z))

    def get_offset(self):
        return self._request('/get_offset', ret=True)

    def clear_offset(self):
        self._request('/clear_offset')


    ### JOBS QUEUE

    def load(self, job, name=None, locally=True, optimize=True):
        """Loads a job from string or file.
        'job' can be: lsa (native), svg, dxf, or gcode
        'name' can be omitted and defaults a unique string.
        'locally' flag for converting/optimizing locally
        'optimize' flag for optimizing path tolerances at all
        """
        type_ = None

        if len(job) < 256 and os.path.exists(job):
            # job is a file
            name_ = os.path.basename(job)
            job = open(job).read()
            # set name from filename if not specified
            base, ext = os.path.splitext(name_)
            if not name:
                name = base+'-'+str(int(time.time()))
            # se type_ from file extension
            # if len(ext) > 2:
            #     type_ = ext[1:]
        # job is already in string format
        if not name:
            # use a default name
            name = "job-"+str(int(time.time()))
        # figure out type
        if not type_:
            jobheader = job[:256].lstrip()
            if jobheader and jobheader[0] == '{':
                type_ = 'lsa'
            elif '<?xml' in jobheader and '<svg' in jobheader:
                type_ = 'svg'
            elif 'SECTION' in jobheader and 'HEADER' in jobheader:
                type_ = 'dxf'
            elif 'G0' in jobheader or 'G1' in jobheader or \
                 'G00' in jobheader or 'G01' in jobheader or \
                 'g0' in jobheader or 'g1' in jobheader or \
                 'g00' in jobheader or 'g01' in jobheader:
                type_ = 'ngc'


        if locally:
            if type_ == 'lsa':
                if optimize:
                    job = json.loads(job)
                    if 'vector' in job and 'paths' in job['vector']:
                        jobimport.pathoptimizer.optimize(
                            job['vector']['paths'], self.conf['tolerance'])
                        job['vector']['optimized'] = self.conf['tolerance']
                    job = json.dumps(job)
                    optimize = False  # optimization done
            elif type_ == 'svg':
                job = jobimport.read_svg(job, self.conf['workspace'],
                                         self.conf['tolerance'], optimize=optimize)
                job = json.dumps(job)
                type_ = 'lsa'         # conversion done
                if optimize:
                    optimize = False  # optimization done
            elif type_ == 'dxf':
                job = jobimport.read_dxf(job, self.conf['tolerance'], optimize=optimize)
                job = json.dumps(job)
                type_ = 'lsa'         # conversion done
                if optimize:
                    optimize = False  # optimization done
            elif type_ == 'ngc':
                job = jobimport.read_ngc(job, self.conf['tolerance'], optimize=optimize)
                job = json.dumps(job)
                type_ = 'lsa'         # conversion done
                if optimize:
                    optimize = False  # optimization done
            else:
                print "ERROR: file type not recognized"

        load_request = {"job": job, "name":name, "type": type_, "optimize": optimize}
        load_request = json.dumps(load_request)
        # upload



    def load_path(self, path, feedrate, intensity):
        """Create and load a job from list of polylines.
        boundary looks like this:
        [ [[x,y,z], ...], [[x,y,z], ...], ... ]
        And can be 2D or 3D.
        """
        job = {
            "vector":{
                "passes":[
                    {
                        "path":[0],
                        "feedrate":feedrate,
                        "intensity":intensity
                    }
                ],
                "paths":[
                    path
                ]
            }
        }
        self.load(json.dumps(job))

    def list(self):
        """List all queue jobs by name."""

    def get(self, jobname):
        """Get a queue job in .lsa format."""

    def star(self, jobname):
        """Star a job."""

    def unstar(self, jobname):
        """Unstar a job."""

    def delete(self, jobname):
        """Delete a job."""

    def clear(self):
        """Clear job list."""


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


    ### MCU MANAGMENT

    def build(self, firmware_name=None):
        """Build firmware from firmware/src files."""

    def flash(self, firmware_name=None):
        """Flash firmware to MCU."""

    def reset(self):
        """Reset MCU"""


