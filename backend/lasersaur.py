# lasersaur.py - control a networked Lasersaur from python
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
# jobname = lasersaur.load_library('Lasersaur.lsa')
# if lasersaur.ready():
#   lasersaur.run(jobname)
#
# while not lasersaur.ready():
#   print "%s% done!" % (lasersaur.status()['progress'])
#   time.sleep(1)
#
# print "job done"
#

import os
import sys
import time
import json
import base64
import requests
import logging


__author__  = 'Stefan Hechenberger <stefan@nortd.com>'


thislocation = os.path.dirname(os.path.realpath(__file__))

logging.basicConfig()
logging.getLogger().setLevel(logging.ERROR)


class Lasersaur(object):

    def __init__(self, host="lasersaur.local", port=80, user="laser", pass_="laser"):
        """Create a Lasersaur client object."""
        self.host = host
        self.port = port
        self.user = user
        self.pass_ = pass_

    def _request(self, url, postdict=None, ret=False):
        """Make a http request.

        Raises:
            requests.ConnectionError: Host not reachable.
            requests.HTTPError: Web server responded with an error code.
        """

        url = "http://%s:%s%s" % (self.host, self.port, url)
        if postdict is None:
            r = requests.get(url, auth=(self.user, self.pass_))
        else:
            r = requests.post(url, auth=(self.user, self.pass_), data=postdict)

        if not r.ok:
            if r.status_code == 400:
                print "WEB ERROR: "+r.text[r.text.find('<pre>')+5:r.text.find('</pre>')]
            r.raise_for_status()

        if ret:
            return r.json()




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
            'pulses_per_mm': 0.0,
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

    def open_file(self, jobfile, optimize=True, tolerance=None):
        """Load and convert a job file locally.

        Args:
            jobfile: Path to job file (lsa, svg, dxf, or ngc).
            optimize: Flag for optimizing path tolerances.
            tolerance: Tolerance used in convert/optimization.

        Returns:
            A parsed .lsa job.
        """
        import jobimport # dependancy only when actually needed
        name_f = os.path.basename(jobfile)
        with open(jobfile) as fp:
            job = fp.read()
        name_f, ext = os.path.splitext(name_f)
        if tolerance:
            job = jobimport.convert(job, optimize=optimize, tolerance=tolerance)
        else:
            job = jobimport.convert(job, optimize=optimize)
        return job


    def convert_file(self, jobfile, optimize=True, tolerance=None):
        """Convert any job file to a .lsa file.

        Args:
            jobfile: Path to job file (lsa, svg, dxf, or gcode).
            optimize: Flag for optimizing path tolerances.
            tolerance: Tolerance used in convert/optimization.

        Output:
            A .lsa file in the same directory called <name>.conv.lsa
        """
        import jobimport # dependancy only when actually needed
        base, name = os.path.split(jobfile)
        name, ext = os.path.splitext(name)
        job = self.open_file(jobfile, optimize=optimize, tolerance=tolerance)
        job = json.dumps(job)
        outfile = os.path.join(base, "%s.conv.lsa" % (name))
        with open(outfile,'w') as fp:
            fp.write(job)
        print "INFO: job file written to: %s" % outfile



    def load(self, job, name="job", optimize=True):
        """Load a job to the machine.

        This will place a job in the job list on the machine. From
        there it can be run by calling the run(jobname) function.

        Typically a job is sent in the native lsa format. Supported
        file types can be converted with the open_file() function.
        Alternatively, any supported file types can be loaded and will
        then be converted on the machine (this is usually slower).

        Args:
            job: Parsed lsa job OR job string (lsa, svg, dxf, or ngc).
            name: Name the job. If not unique gets a post-numeral.
            optimize: Flag for optimizing path tolerances on machine.

        Returns:
            Unique name give to the job. This is either name or
            name_<numeral>.
        """
        if type(job) is dict:
            job =  json.dumps(job)
        load_request = json.dumps({"job": job, "name":name, "optimize": optimize})
        return self._request('/load', postdict={'load_request'}, ret=True)


    def load_file(self, jobfile, optimize=True, tolerance=None):
        """Convert any job file to a .lsa file.

        Args:
            jobfile: Path to job file (lsa, svg, dxf, or gcode).
            optimize: Flag for optimizing path tolerances.
            tolerance: Tolerance used in convert/optimization.

        Returns:
            Unique name give to the job. This is either name or
            name_<numeral>.
        """
        import jobimport # dependancy only when actually needed
        base, name = os.path.split(jobfile)
        name, ext = os.path.splitext(name)
        job = self.open_file(jobfile, optimize=optimize, tolerance=tolerance)
        return self.load(job, name, optimize=False)


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
        return self.load(json.dumps(job))

    def load_image(self, image, pos, size, feedrate=6000, intensity=50):
        """Create and load a raster engraving job.

        Args;
            image: image file path to PNG image
            pos: (x,y), position of top-left corner
            size: (width, height), dimensions of output
            feedrate: raster speed
            intensity: raster intensity
        """
        with open(image,'rb') as fp:
            img = fp.read()
        img_b64 = base64.encodestring(img).decode("utf8")
        job = {
            "raster":{
                "passes":[
                    {
                        "images": [0],
                        "feedrate": feedrate,
                        "intensity": intensity,
                    },
                ],
                "images":[
                    {
                        "pos": pos,
                        "size": size,
                        "data": img_b64
                    }
                ]
            }
        }
        return self.load(json.dumps(job))

    def listing(self, kind=None):
        """List all queue jobs by name."""
        if kind is None:
            jobs = self._request('/listing', ret=True)
        elif kind == 'starred':
            jobs = self._request('/listing/starred', ret=True)
        elif kind == 'unstarred':
            jobs = self._request('/listing/unstarred', ret=True)
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

    def remove(self, jobname):
        """Delete a job."""
        self._request('/remove/%s' % jobname)

    def clear(self):
        """Clear job list (does not delete starred jobs)."""
        self._request('/clear')


    ### LIBRARY

    def listing_library(self):
        """List all library jobs by name."""
        return self._request('/listing_library', ret=True)

    def get_library(self, jobname):
        """Get a library job in .lsa format."""
        return self._request('/get_library/'+jobname, ret=True)

    def load_library(self, jobname):
        """Load a library job into the queue."""
        return self._request('/load_library/%s' % (jobname), ret=True)


    ### JOB EXECUTION

    def run(self, jobname, progress=True):
        """Send job from queue to the machine."""
        self._request('/run/%s' % jobname)
        if progress:
            print 'Processing [                                        ]',
            print '\b'*42,
            sys.stdout.flush()
            time.sleep(0.6)
            stat = self.status()
            level = 0.025
            while not stat['ready']:
                while stat['progress'] > level:
                    print '\b.',
                    sys.stdout.flush()
                    level += 0.025
                time.sleep(1)
                stat = self.status()
            print '\b]  Done!'


    def run_file(self, jobfile, feedrate=None, intensity=0, progress=True, local=False):
        """A quick way to run a job"""
        base, name = os.path.split(jobfile)
        name, ext = os.path.splitext(name)
        job = lasersaur.open_file(jobfile, optimize=True)
        if 'vector' in job and 'paths' in job['vector'] and type(job['vector']['paths']) is list:
            if 'passes' not in job['vector'] or feedrate is not None:
                # file has no pass info | feedrate is specified
                if feedrate is None: feedrate = 4000
                job['vector']['passes'] = [{
                        "paths":range(len(job['vector']['paths'])),  # apply to all path
                        "feedrate":feedrate,
                        "intensity":intensity
                    }]
        if local:
            self.host = '127.0.0.1'
            self.port = 4444
        jobname = lasersaur.load(job, name=name, optimize=False)
        lasersaur.run(jobname, progress=progress)
        return jobname


    def pause(self):
        """Pause a job gracefully."""
        self._request('/pause')

    def unpause(self):
        """Resume a paused job."""
        self._request('/unpause')

    def stop(self):
        """Halt machine immediately and purge job."""
        self._request('/stop')

    def unstop(self):
        """Recover machine from stop mode."""
        self._request('/unstop')

    def cancel(self):
        """Gracefully cancel a job."""
        self.pause()
        time.sleep(1)
        while not self.status()['ready']:
            time.sleep(1)
        self.stop()
        self.unstop()
        self.move(0,0,0)


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




###########################################################################
### API ###################################################################
###########################################################################

lasersaur = Lasersaur()
### LOW-LEVEL
config = lasersaur.config
status = lasersaur.status
homing = lasersaur.homing
feedrate = lasersaur.feedrate
intensity = lasersaur.intensity
relative = lasersaur.relative
absolute = lasersaur.absolute
move = lasersaur.move
air_on = lasersaur.air_on
air_off = lasersaur.air_off
aux1_on = lasersaur.aux1_on
aux1_off = lasersaur.aux1_off
offset = lasersaur.offset
clear_offset = lasersaur.clear_offset
### JOBS QUEUE
open_file = lasersaur.open_file
convert_file = lasersaur.convert_file
load = lasersaur.load
load_file = lasersaur.load_file
load_path = lasersaur.load_path
load_image = lasersaur.load_image
listing = lasersaur.listing
get = lasersaur.get
star = lasersaur.star
unstar = lasersaur.unstar
remove = lasersaur.remove
clear = lasersaur.clear
### LIBRARY
listing_library = lasersaur.listing_library
get_library = lasersaur.get_library
load_library = lasersaur.load_library
### JOB EXECUTION
run = lasersaur.run
run_file = lasersaur.run_file
pause = lasersaur.pause
unpause = lasersaur.unpause
stop = lasersaur.stop
unstop = lasersaur.unstop
cancel = lasersaur.cancel
### MCU MANAGMENT
build = lasersaur.build
flash = lasersaur.flash
reset = lasersaur.reset


def local():
    """Configure for server running on same machine."""
    lasersaur.host = "127.0.0.1"
    lasersaur.port = 4444




if __name__ == '__main__':
    jobname = lasersaur.load_library('Lasersaur.lsa')
    if lasersaur.ready():
      lasersaur.run(jobname)

    while not lasersaur.ready():
      print "%s done!" % (lasersaur.status()['progress'])
      time.sleep(1)

    print "job done"
