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
        global args

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

        if args.animate:
            self.timer = True
            if args.fast:
                glib.timeout_add(10, self.on_timer)  #100fps
                self.inc = 8
            else:
                glib.timeout_add(40, self.on_timer)  #25fps
                self.inc = 4                
            self.todraw = self.inc

        self.show_all()


    def on_timer(self):
        if not self.timer: return False
        self.darea.queue_draw()
        return True

    
    def expose(self, widget, event):
        global job, args, total_points
        cr = widget.window.cairo_create()
        cr.set_line_width(1)
        cr.set_source_rgb(0.0, 0.0, 0.0)


        if args.animate:
            count = 0
            break_ = False
            for i in xrange(len(job['vector']['paths'])):
                path = job['vector']['paths'][i]
                if break_: break
                for polyline in path:
                    if count >= self.todraw:
                        break_ = True
                    if break_: break
                    cr.move_to(polyline[0][0], polyline[0][1])
                    count += 1
                    for i in xrange(1, len(polyline)):
                        if count >= self.todraw:
                            break_ = True
                        if break_: break
                        cr.line_to(polyline[i][0], polyline[i][1])
                        count += 1
            if self.todraw >= total_points:
                # all drawn
                # self.timer = False
                self.todraw = 0
            self.todraw += self.inc
        else:
            for path in job['vector']['paths']:
                for polyline in path:
                    cr.move_to(polyline[0][0], polyline[0][1])
                    for i in xrange(1, len(polyline)):
                        cr.line_to(polyline[i][0], polyline[i][1])
                            
        cr.stroke()


    


if __name__ == '__main__':
    ### Setup Argument Parser
    argparser = argparse.ArgumentParser(description='Show job file.', prog='show.py')
    argparser.add_argument('jobfile', metavar='jobfile', nargs='?', default=None,
                           help='Lasersaur job file to show.')
    argparser.add_argument('-a', '--animate', dest='animate', action='store_true',
                           default=False, help='animate job')
    argparser.add_argument('-f', '--fast', dest='fast', action='store_true',
                           default=False, help='animate fast')
    argparser.add_argument('-n', '--nooptimize', dest='nooptimize', action='store_true',
                           default=False, help='do not optimize geometry')
    argparser.add_argument('-t', '--tolerance', dest='tolerance',
                           default=0.08, help='tolerance in mm')
    args = argparser.parse_args()

    thislocation = os.path.dirname(os.path.realpath(__file__))
    if args.jobfile:
        jobfile = os.path.join(thislocation, "testjobs", args.jobfile)
        with open(jobfile) as fp:
            job = fp.read()
        job = jobimport.convert(job, tolerance=float(args.tolerance), 
                                     optimize=not(args.nooptimize))

        # stats
        total_points = 0
        for path in job['vector']['paths']:
            for polyline in path:
                for point in polyline:
                    total_points += 1
        print "STATS:"
        print "\ttotal points: %s" % total_points
        if 'vector' in job and 'optimized' in job['vector']:
            print "\ttolerance: %s" % job['vector']['optimized']

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



