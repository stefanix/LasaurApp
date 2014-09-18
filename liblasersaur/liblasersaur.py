# pyliblasersaur - control a Lasersaur from python
# Copyright (c) 2011 Nortd Labs
# Open Source by the terms of the Gnu Public License (GPL3) or higher.
# ###
#
# A Lasersaur runs LasaurApp on the machine. It runs a local web server
# providing the standard Lasersaur interface to any modern web bowser.
# Additionally LasaurApp can be controlled through an API, also over
# the local network. This allows alternative interfaces and direct
# control integration to apps like Inkscape, Rhino, FreeCAD.
#
# This library is an example client for the LasaurApp API.
#
# Usage:
# ------
# laser = Lasersaur()
# jobname = laser.load(open('Lasersaur.lsa').read())
# if laser.ready():
#   laser.run(jobname)
# 
# While not laser.ready():
#   pass
# 
# print "job done"
#




class Lasersaur(object):
    def __init__(self, host="lasersaur.local", ip=4444):


    def connect(self):


    def close(self):

    def status(self):

    def ready(self):

    def load(self, filestring):
        """Load a job file to the queue.
        Format can be: .lsa (native), .svg, .dxf, gcode
        """

    def run(self, jobname):
        """Send job from queue to the machine."""

    def percentage(self):
        """Get percentage done of job."""

    def pause(self):
    def unpause(self):

    def stop(self):
    def unstop(self):



    def list_library_jobs(self):
        """List all library jobs by name."""

    def get_library_job(self, name):
        """Get a library job in .lsa format."""

    def load_library_job(self, name):
        """Load a library job into the queue."""



    def list_queue_jobs(self):
        """List all queue jobs by name."""

    def get_queue_job(self, name):
        """Get a queue job in .lsa format."""

    def star_queue_job(self, name):

    def unstar_queue_job(self, name):

    def del_queue_job(self, name):

    def clear_queue_jobs(self):



    def build(self, firmware_name):

    def flash(self, firmware_name):

    def reset(self):
        """Reset MCU"""




