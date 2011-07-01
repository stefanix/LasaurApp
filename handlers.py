
import os.path

import serialQueue
import cherrypy
import pystache


class GCodeHandler(object):
    
    @cherrypy.expose
    def default(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(current_dir, 'index.html')
        return cherrypy.lib.static.serve_file(path) 
        
    @cherrypy.expose
    def serial(self, connect=None):
        if connect == '1' and not serialQueue.is_serial_connected():
            if serialQueue.connect_serial():
                return "True"
            else:
                return "False"
        elif connect == '0' and serialQueue.is_serial_connected():
            if serialQueue.disconnect_serial():
                return "True"
            else:
                return "False"  
        elif connect == '2':
            if serialQueue.is_serial_connected():
                return 'True'
            else:
                return 'False'
        else:
            print 'got neither: ' + connect            
            return "False"
            
        
    @cherrypy.expose
    def add_moveto(self, x=None, y=None):
        got_numbers = False
        try:
            x = float(x)
            y = float(y)
            got_numbers = True
        except ValueError:
            print "Invalid input numbers for x or y."
        
        if got_numbers:
            if x < 0: x = 0
            if x > 1220: x = 1220
            if y < 0: y = 0
            if y > 620: y = 620
    
            gcode = 'G1 X%.3f Y%.3f\n' % (x, y)
            serialQueue.send_serial(gcode)
              
            return "coords: %.3f, %.3f" % (x,y)          
            
        else:
            return "No coordinates!"

    @cherrypy.expose
    def gcode(self, s=None):        
        if s:
            print s
            ret = serialQueue.send_serial(s + '\n')
            if ret: return "True"
            else: return "False"
        else:
            return "False"

       