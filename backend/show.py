#!/usr/bin/python

import os
import json
import glob
import argparse
import gtk
import glib

import lasersaur
import jobimport


__author__  = 'Stefan Hechenberger <stefan@nortd.com>'



class PyApp(gtk.Window):

    def __init__(self):
        super(PyApp, self).__init__()

        self.set_title("Lasersaur")
        self.resize(1220, 610)
        self.set_position(gtk.WIN_POS_CENTER)

        self.connect("destroy", gtk.main_quit)
        # exit with ctr-q
        accel_group = gtk.AccelGroup()
        accel_group.connect_group(ord('q'), gtk.gdk.CONTROL_MASK, 
        gtk.ACCEL_LOCKED, gtk.main_quit)
        self.add_accel_group(accel_group)

        self.darea = gtk.DrawingArea()
        self.darea.connect("expose-event", self.expose)
        self.add(self.darea)

        self.timer = True
        glib.timeout_add(1400, self.on_timer)
        self.path_idx = 0
        self.poly_idx = 0
        self.inc = 20
        self.first = 0
        self.last = self.inc

        self.show_all()


    def on_timer(self):
        if not self.timer: return False
        self.darea.queue_draw()
        return True

    
    def expose(self, widget, event):
        global job, args
        cr = widget.window.cairo_create()
        cr.set_line_width(1)
        cr.set_source_rgb(0.0, 0.0, 0.0)

        if self.first >= len(job['vector']['paths'][self.path_idx][self.poly_idx]):
            self.poly_idx += 1
            if self.poly_idx >= len(job['vector']['paths'][self.path_idx]):
                self.poly_idx = 0
                self.path_idx += 1
                if self.path_idx >= len(job['vector']['paths']):
                    # done
                    # cr.paint()
                    self.timer = False
                    return
                else:
                    self.first = 0
                    self.last = min(self.inc, len(job['vector']['paths'][self.path_idx][self.poly_idx]))    
            else:
                self.first = 0
                self.last = min(self.inc, len(job['vector']['paths'][self.path_idx][self.poly_idx]))
        else:
            if self.last >= len(job['vector']['paths'][self.path_idx][self.poly_idx]):
                self.last = len(job['vector']['paths'][self.path_idx][self.poly_idx]) - 1

        # polyline = job['vector']['paths'][self.path_idx][self.poly_idx]
        # cr.move_to(polyline[0][0], polyline[0][1])
        # for i in xrange(self.first+1, self.last+1):
        #     cr.line_to(polyline[i][0], polyline[i][1])

        for i in xrange(self.path_idx):
            path = job['vector']['paths'][i]
            for ii in xrange(self.poly_idx):
                polyline = path[ii]
                cr.move_to(polyline[0][0], polyline[0][1])
                for i in xrange(1, self.last+1):
                    cr.line_to(polyline[i][0], polyline[i][1])


        break_ = False
        for path in job['vector']['paths']:
            if break_: break
            for polyline in path:
                if self.count >= todraw:
                    break_ = True
                if break_: break
                cr.move_to(polyline[0][0], polyline[0][1])
                self.count += 1
                for i in xrange(1, len(polyline)):
                    if self.count >= todraw:
                        break_ = True
                    if break_: break
                    cr.line_to(polyline[i][0], polyline[i][1])
                    self.count += 1
                        
        cr.stroke()

        self.first = self.last + 1
        self.last += self.inc

    


if __name__ == '__main__':
    ### Setup Argument Parser
    argparser = argparse.ArgumentParser(description='Show job file.', prog='show.py')
    argparser.add_argument('jobfile', metavar='jobfile', nargs='?', default=None,
                           help='Lasersaur job file to show.')
    argparser.add_argument('-a', '--animate', dest='animate', action='store_true',
                           default=False, help='animate job')
    args = argparser.parse_args()

    thislocation = os.path.dirname(os.path.realpath(__file__))
    if args.jobfile:
        jobfile = os.path.join(thislocation, "testjobs", args.jobfile)
        with open(jobfile) as fp:
            job = jobimport.convert(fp.read(), optimize=True)
        # run gtk window
        PyApp()
        gtk.main()
    else:
        jobpath = os.path.join(thislocation, "testjobs")
        cwd_temp = os.getcwd()
        os.chdir(jobpath)
        files = glob.glob("*.*")
        os.chdir(cwd_temp)
        print "Name one of the following files:"
        for file_ in files:
            print file_    



