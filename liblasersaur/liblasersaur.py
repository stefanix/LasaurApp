# liblasersaur - control a Lasersaur from python
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




class Lasersaur(object):
    def __init__(self, host="lasersaur.local", ip=4444):
        """Create a Lasersaur client object."""


    def connect(self):
        """Network-connect to the DriveBoard."""

    def close(self):
        """Close connection to DriveBoard."""

    def status(self):
        """Get status report of the machine."""

    def ready(self):
        """Get ready status, specifically."""


    ### JOBS QUEUE

    def load(self, filename):
        """Load a job file to the queue.
        Format can be: .lsa (native), .svg, .dxf, gcode
        """

    def loads(self, jobstring):
        """Same as load but for jobs in string."""

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


