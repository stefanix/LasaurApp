# pyliblasersaur - control a Lasersaur from python
# Copyright (c) 2011 Nortd Labs
# Open Source by the terms of the Gnu Public License (GPL3) or higher.
#
# A Lasersaur runs LasaurApp on the machine. It runs a local web server
# providing the standard Lasersaur interface to any modern web bowser.
# Additionally LasaurApp can be controlled through an API, also over
# the local network. This allows alternative interfaces and direct
# control integration to apps like Inkscape, Rhino, FreeCAD.
#
# This library is an example implementation in python to use the
# LasaurApp API.




class Lasersaur:
    def __init__(self, host="lasersaur.local", ip=4444):


    def connect(self):


    def close(self):

    def get_status(self):

    def is_ready(self):

    def send_job(self, job):

    def pause(self, val=True):

    def stop(self):



    def list_library(self):

    def get_library_job(self, name):



    def list_queue(self):

    def get_queue_job(self):

    def save_queue_job(self, job):

    def star_queue_job(self, name):

    def unstar_queue_job(self, name):

    def del_queue_job(self, name):

    def clear_queue(self):








    def 


