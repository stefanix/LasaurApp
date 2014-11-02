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
import json
import urllib
import urllib2

import jobimport
import jobimport.path_optimizers
# from config import conf

__author__  = 'Stefan Hechenberger <stefan@nortd.com>'


USERNAME = "laser"
PASSWORD = "laser"


class Lasersaur(object):
    def __init__(self, host="lasersaur.local", port=4444):
        """Create a Lasersaur client object."""
        self.host = host
        self.port = port
        # urllib2: enable auth
        password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
        top_level_url = "http://%s:%s/" % (host, port)
        password_mgr.add_password(None, top_level_url, USERNAME, PASSWORD)
        handler = urllib2.HTTPBasicAuthHandler(password_mgr)
        opener = urllib2.build_opener(handler)
        urllib2.install_opener(opener) # use auth for all urllib2.urlopen()
        # fetch config
        self.conf = None
        self.conf = self.config()

    def _request(self, url, postdict=None, ret=False):
        # TODO: url encode
        url = "http://%s:%s%s" % (self.host, self.port, url)

        if postdict:
            postdata = urllib.urlencode(postdict)
        else:
            postdata = None
        req = urllib2.Request(url, postdata)
        try:
            response = urllib2.urlopen(req)
        except urllib2.HTTPError as e:
            nomachine = "No machine."
            if e.code == 400 and nomachine in e.read():
                print "ERROR: %s" % nomachine
            raise e
        if ret:
            return json.loads(response.read())
                


    ### LOW-LEVEL

    def config(self):
        """Get config from machine."""
        return self._request('/config', ret=True)

    def status(self):
        """Get status report of machine.
        {
            "appver": 15.00,
            'firmver': 15.00,
            'ready': False,
            'paused': False,
            'serial': False
            'pos':[0.0, 0.0, 0.0],
            'stops': {},        # x1, x2, y1, y2, z1, z2
                                # requested, buffer, marker, data, command, parameter, transmission
            'info': {},         # door, chiller

            ### super
            'offset': [0.0, 0.0, 0.0],
            'feedrate': 0.0,
            'intensity': 0.0,
            'duration': 0.0,
            'pixelwidth': 0.0,
        }
        """
        return self._request('/status', ret=True)

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
        self._request('/move/%.4f/%.4f/%.4f' % (x,y,z))

    def air_on(self):
        self._request('/air_on')

    def air_off(self):
        self._request('/air_off')

    def aux1_on(self):
        self._request('/aux1_on')

    def aux1_off(self):
        self._request('/aux1_off')

    def offset(self, x, y, z=0.0):
        self._request('/offset/%.4f/%.4f/%.4f' % (x,y,z))

    def clear_offset(self):
        self._request('/clear_offset')




    ### JOBS QUEUE

    def load(self, job, name=None, convert=True, optimize=True, tofile=False):
        """Loads a job from string or file.
        'job' can be: lsa (native), svg, dxf, or gcode
        'name' can be omitted and defaults to a unique string.
        'convert' flag for converting/optimizing locally
        'optimize' flag for optimizing path tolerances at all
        'tofile' instead of uploading, write to file (converted)
        """
        if len(job) < 256 and os.path.exists(job):
            # job is a file
            name_ = os.path.basename(job)
            with open(job) as fp:
                job = fp.read()
            # set name from filename if not specified
            base, ext = os.path.splitext(name_)
            if not name:
                name = base+'-'+str(int(time.time()))
        # job is already in string format
        if not name:
            # use a default name
            name = "job-"+str(int(time.time()))
        # now we have:
        # job, name
        if convert or tofile:
            type_ = jobimport.get_type(job)
            if type_ == 'lsa' and optimize:
                job = json.loads(job)
                if 'vector' in job and 'paths' in job['vector']:
                    jobimport.pathoptimizer.optimize(
                        job['vector']['paths'], self.conf['tolerance'])
                    job['vector']['optimized'] = self.conf['tolerance']
                job = json.dumps(job)
            elif type_ == 'svg':
                job = jobimport.read_svg(job, self.conf['workspace'],
                                         self.conf['tolerance'], optimize=optimize)
                job = json.dumps(job)
            elif type_ == 'dxf':
                job = jobimport.read_dxf(job, self.conf['tolerance'], optimize=optimize)
                job = json.dumps(job)
            elif type_ == 'ngc':
                job = jobimport.read_ngc(job, self.conf['tolerance'], optimize=optimize)
                job = json.dumps(job)
            else:
                print "ERROR: file type not recognized"
                raise TypeError
            if optimize:
                optimize = False
        if tofile:
            outfile = "%s.lsa" % (name)
            with open(outfile,'w') as fp:
                fp.write(job)
            print "INFO: written to %s" % outfile
        else:
            # assemble request data
            load_request = {"job": job, "name":name, "optimize": optimize}
            load_request = json.dumps(load_request)
            # upload
            self._request('/load', postdict={'load_request':load_request})



    def load_path(self, path, feedrate, intensity):
        """Create and load a job from list of polylines.
        boundary looks like this:
        [ [[x,y,z], ...], [[x,y,z], ...], ... ]
        and can be 2D or 3D.
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

    def list(self, kind=None):
        """List all queue jobs by name."""
        if kind is None:
            jobs = self._request('/list', ret=True)
        elif kind == 'starred':
            jobs = self._request('/list/starred', ret=True)
        elif kind == 'unstarred':
            jobs = self._request('/list/unstarred', ret=True)
        return jobs

    def get(self, jobname):
        """Get a queue job in .lsa format."""
        return self._request('/get/%s' % jobname, ret=True)

    def star(self, jobname):
        """Star a job."""
        self._request('/star/%s' % jobname)

    def unstar(self, jobname):
        """Unstar a job."""
        self._request('/unstar/%s' % jobname)

    def delete(self, jobname):
        """Delete a job."""
        self._request('/delete/%s' % jobname)

    def clear(self):
        """Clear job list (does not delete starred jobs)."""
        self._request('/clear')


    ### LIBRARY

    def list_library(self):
        """List all library jobs by name."""
        return self._request('/list_library', ret=True)

    def get_library(self, jobname):
        """Get a library job in .lsa format."""
        return self._request('/get_library/'+jobname, ret=True)

    def load_library(self, jobname):
        """Load a library job into the queue."""
        self._request('/load_library/'+jobname)


    ### JOB EXECUTION

    def run(self, jobname, async=True):
        """Send job from queue to the machine."""
        self._request('/run/%s' % jobname)
        if not async:
            while not self.ready(cache=0):
                time.sleep(1)

    def progress(self):
        """Get percentage of job done."""
        return self._request('/progress', ret=True)

    def pause(self):
        """Pause a job gracefully."""
        self._request('/pause')

    def resume(self):
        """Resume a paused job."""
        self._request('/unpause')

    def stop(self):
        """Halt machine immediately and purge job."""
        self._request('/stop')

    def unstop(self):
        """Recover machine from stop mode."""
        self._request('/unstop')


    ### MCU MANAGMENT

    def build(self, firmware_name=None):
        """Build firmware from firmware/src files."""
        if firmware_name:
            self._request('/build')
        else:
            self._request('/build/'+firmware_name)

    def flash(self, firmware_name=None):
        """Flash firmware to MCU."""
        if firmware_name:
            self._request('/flash')
        else:
            self._request('/flash/'+firmware_name)

    def reset(self):
        """Reset MCU"""
        self._request('/reset')


