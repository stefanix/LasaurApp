
__author__ = 'Stefan Hechenberger <stefan@nortd.com>'


import math
import sys
import os.path
import StringIO
import string
from json import loads
import re
import ast

class NGCReader:
    """Parse subset of G-Code.


    """

    def __init__(self, tolerance):
        # tolerance settings, used in tessalation, path simplification, etc         
        self.tolerance = tolerance
        self.tolerance2 = tolerance**2


    def parse(self, ngcstring):
        # Parse GCode
        
        # Supports subset of GCode ideally the following
        '''
G0, G1: Linear Motions
G2, G3: Arc and Helical Motions
G4: Dwell
G10 L2, G10 L20: Set Work Coordinate Offsets
G17, G18, G19: Plane Selection
G20, G21: Units
G28, G30: Go to Pre-Defined Position
G28.1, G30.1: Set Pre-Defined Position
G53: Move in Absolute Coordinates
G54, G55, G56, G57, G58, G59: Work Coordinate Systems
G80: Motion Mode Cancel
G90, G91: Distance Modes
G92: Coordinate Offset
G92.1: Clear Coordinate System Offsets
G93, G94: Feedrate Modes
M0, M2, M30: Program Pause and End
         '''
        self.colors = {'#ff0000', '#00ff00', '#ff0000', '#ff00ff', '#ffff00', '#00ffff',
                  '#880000', '#008800', '#880000', '#880088', '#888800', '#008888', 
                  '#ff0088', '#ff8800', '#ff8888', '#88ff00', '#00ff88', '#88ff88', 
                  '#8800ff', '#0088ff', '#8888ff', '#1111ff', '#22ff22', '#ff3333', 
                  '#4444ff', '#55ff55', '#ff6666', '#6666ff', '#c81188', '#99ff99',
                  '#ffaaaa', '#bbbbff', '#ccffcc', '#ffdddd'}
        self.colormap = {}
        
        # parsed path data, paths by color
        # {'#ff0000': [[path0, path1, ..], [path0, ..], ..]}
        # Each path is a list of vertices which is a list of two floats.        
        self.boundarys = {}
        self.boundary = None
        
        self.feed = 1500
        self.speed = 64
        self.pos_x = 0
        self.pos_y = 0
        self.off_x = 0
        self.off_y = 0
        
        # Coordinate systems 1-9 x offset, y offset and rotation
        self.coords = [[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0]]
        self.coord = self.coords[0] # default to G54 
        self.scale = 1
        self.relative = False
        self.cutting = False

        self.linecount = 0
        self.infile = StringIO.StringIO(ngcstring)

        self.gcode_comment_re = re.compile(r"(\([^)]*\))|(#.*$)")
        self.gcode_word_re = re.compile(r"([A-DF-NP-Z][+-]?\d+(?:\.\d+)?)")
        for self.line in self.infile:
            self.linecount += 1
            self.line = self.gcode_comment_re.sub('',self.line)
            self.line = self.line.translate(None,string.whitespace).upper();
            if len(self.line)==0:
                continue

            self.words = self.gcode_word_re.findall(self.line)
            # Handle leading line number
            if self.words[0][0] == 'N':
                self.linenumber = self.words[0][1]
                self.words = self.words[1:]

            # Handle leading G53 modifier by moving it after command
            if self.words[0] == 'G53': 
                self.words[0] = self.words[1]
                self.words[1] = 'G53';
            
            if   self.words[0] == 'G0': self.do_move()
            elif self.words[0] == 'G1': self.do_cut()
            elif self.words[0] == 'G2': self.do_cut()
            elif self.words[0] == 'G3': self.do_cut()
            elif self.words[0] == 'G4': ''' Pause '''
            elif self.words[0] == 'G10': self.do_coordinates()
            elif self.words[0] == 'G20': self.scale=25.4
            elif self.words[0] == 'G21': self.scale=1
            elif self.words[0] == 'G28': self.do_recall(28)
            elif self.words[0] == 'G30': self.do_recall(30)
            elif self.words[0] == 'G28.1': self.do_store(28)
            elif self.words[0] == 'G30.1': self.do_store(30)
            elif self.words[0] == 'G54': self.do_coordinates()
            elif self.words[0] == 'G55': self.do_coordinates()
            elif self.words[0] == 'G56': self.do_coordinates()
            elif self.words[0] == 'G57': self.do_coordinates()
            elif self.words[0] == 'G58': self.do_coordinates()
            elif self.words[0] == 'G59': self.do_coordinates()
            elif self.words[0] == 'G90': self.relative = False
            elif self.words[0] == 'G91': self.relative = True
            elif self.words[0] == 'G92': self.do_coordinates()
            elif self.words[0] == 'G92.1': self.do_coordinates()
            elif self.words[0] == 'G94': ''' Others unsupported '''
            elif self.words[0] == 'M0': ''' ignore pause '''
            elif self.words[0] == 'M2': break
            elif self.words[0] == 'M30': break
            elif self.words[0] == 'M80': '''ignore air'''
            elif self.words[0] == 'M81': '''ignore air'''
            elif self.words[0][0] == 'S': self.do_set_speed(self.words[0][1:])
            elif self.words[0][0] == 'F': self.do_set_feed(self.words[0][1:])
            else: self.complain_invalid()

        self.infile.close()
        print "Done!"
        return {'boundarys':self.boundarys}



    ################
    # Update speed
    def do_set_speed(self, speed):
        try: speed = int(speed)
        except: 
            print "Bad speed value line " + str(self.line_num)
            raise ValueError
            
        if self.speed!=speed:
            self.speed = speed
            self.boundary = None

    ################
    # Update feed
    def do_set_feed(self, feed):
        try: feed = float(feed) * self.scale
        except: 
            print "Bad feed value line " + str(self.line_num)
            raise ValueError
            
        if self.feed!=feed:
            self.feed = feed
            self.boundary = None

    ################
    # Parse axis into X Y S F values
    
    def do_parse_param(self):
        x = None
        y = None
        z = None
        i = None
        j = None
        k = None
        r = None
        p = None

        # Look for axis and feed parameters
        #TODO: Try for value parsing
        for word in self.words:
            if   word[0] == 'X': x = float(word[1:]) * self.scale
            elif word[0] == 'Y': y = float(word[1:]) * self.scale
            elif word[0] == 'Z': z = float(word[1:]) * self.scale
            elif word[0] == 'S': self.do_set_speed(word[1:])
            elif word[0] == 'F': self.do_set_feed(word[1:])
            elif word[0] == 'I': i = float(word[1:]) * self.scale
            elif word[0] == 'J': j = float(word[1:]) * self.scale
            elif word[0] == 'K': k = float(word[1:]) * self.scale
            elif word[0] == 'R': r = float(word[1:])
            elif word[0] == 'P': p = float(word[1:])

        return {'x':x, 'y':y, 'z':z, 'i':i, 'j':j, 'k':k, 'r':r, 'p':p}
    
    
    ################
    # Manage changes in coordinate systems

    def do_coordinates(self):
        if self.words[0] in {'G54','G55', 'G56', 'G57', 'G58', 'G59'}:
            self.coord = self.coords[int(self.words[0][2])-4]
            return
        
        param = self.do_parse_param()
        if self.words[0] == 'G10':
            p = self.coord
            if param['p']!=None and param['p']>0:p = self.coords[int(param['p'])-1]

            if self.words[1] == 'L2' and self.words[2][0]=='P':
                # Set coordinate system relative to offset origin
                if param['x'] != None: p[0] = param['x']
                if param['y'] != None: p[1] = param['y']
                if param['r'] != None: p[2] = param['r']
            elif self.words[1] == 'L20' and self.words[2][0]=='P':
                # Set coordinate system such that parameters describe the current position 
                # TODO: I will need to write this down to manage rotation
                if param['r'] != None: p[2] = param['r']
                if param['x'] != None: p[0] = self.pos_x - param['x'] - self.off_x
                if param['y'] != None: p[1] = self.pos_y - param['y'] - self.off_y
            else: self.complain_invalid()
        elif self.words[0] == 'G92':
            # Set global offset to specified values
            if param['x'] != None: self.off_x = param['x']
            if param['y'] != None: self.off_y = param['y']
        elif self.words[0] == 'G92.1':
            self.off_x = 0
            self.off_y = 0
        else: self.complain_invalid()
        

    ################
    # Handle move command

    def do_move(self):
        param = self.do_parse_param() 
        if param['x'] == None and param['y'] == None and param['z'] == None: return
        if 'G53' in self.words:
            if param['x'] != None: self.pos_x = param['x']
            if param['y'] != None: self.pos_y = param['y']
        elif self.relative:
            #TODO: Handle rotational coord
            if param['x'] != None: self.pos_x += param['x']
            if param['y'] != None: self.pos_y += param['y']
        else:
            #TODO: Handle rotational coord
            if param['x'] != None: self.pos_x = param['x'] + self.off_x + self.coord[0]
            if param['y'] != None: self.pos_y = param['y'] + self.off_x + self.coord[1]


    ################
    # Return color for these settings

    def set_boundry(self):
        lookup = 'S'+str(self.speed)+'F'+str(self.feed)
        # Find or create color mapping for this speed and feed
        if self.colormap.has_key(lookup) == False:
            if len(self.colors)==0:
                print 'All available colors have been used!'
                raise ValueError
            self.colormap[lookup] = self.colors.pop()

        # Find or create boundarys for color
        if self.boundarys.has_key(self.colormap[lookup]) == False:
            self.boundarys[self.colormap[lookup]] = []
            
        self.boundary = self.boundarys[self.colormap[lookup]]


    ################
    # Handle cut command

    def do_cut(self):
        # for cuts determine the color, convert coords to set the curve

        # Look for axis and cut parameters
        param = self.do_parse_param()
        if param['x'] == None and param['y'] == None and param['z'] == None: return
        
        # Find color
        self.set_boundry()
        
        # Cut line
        if self.words[0]=='G1':            
            #TODO: Handle rotation, single param
            if 'G53' in self.words:
                if param['x'] == None: param['x'] = self.pos_x
                if param['y'] == None: param['y'] = self.pos_y
                self.do_line(self.pos_x, self.pos_y, param['x'], param['y'])
            elif self.relative:
                if param['x'] == None: param['x'] = 0
                if param['y'] == None: param['y'] = 0
                self.do_line(self.pos_x, self.pos_y, self.pos_x + param['x'], self.pos_y + param['y'])
            else:
                if param['x']==None: x = self.pos_x
                else: x = param['x']+self.off_x+self.coord[0]
                if param['y']==None: y = self.pos_y
                else: y = param['y']+self.off_y+self.coord[1]
                self.do_line(self.pos_x, self.pos_y, x, y)

        elif self.words[0] in ['G2', 'G3']:
            # Parameters are endpoint(coord) and offset of center
            # Do_arc needs center, major, minor and start and end angles
            #TODO:Supporting relative arc offsets and rotated coordinates
            
            x1 = x2 = self.pos_x
            y1 = y2 = self.pos_y
            if param['x']!= None: x2 = param['x']+self.off_x+self.coord[0]
            if param['y']!= None: y2 = param['y']+self.off_y+self.coord[1]
            
            dx1 = 0.0  # center offset in X
            dy1 = 0.0  # center offset in y
            if param['i']!= None: dx1 -= param['i']
            if param['j']!= None: dy1 -= param['j']
            r1 = math.hypot(dx1,dy1)

            # Find center
            cx = x1 - dx1
            cy = y1 - dy1
            
            dx2 = x2 - cx
            dy2 = y2 - cy
            r2 = math.hypot(dx2,dy2)
    
            if r1==0 or r2==0: return
            
            # Find angles
            theta1 = math.atan2(dy1,dx1)
            theta2 = math.atan2(dy2,dx2)

            if self.words[0] == 'G2': # Clockwise
                if theta1 < theta2: theta1 += 2*math.pi
            else: # counter clockwise
                if theta1 > theta2: theta2 += 2*math.pi
            
            def _arc(cx, cy, x, y, r, r2, theta, theta2):
                dtheta = theta2-theta
                if dtheta >= math.pi:
                    # This approximation really isn't right for ellipses 
                    r1 = r + (r2 - r)*math.pi/2/dtheta
                    theta1 = theta + math.pi/2
                    x1 = r1*math.cos(theta1)+cx
                    y1 = r1*math.sin(theta1)+cy
                    _arc(cx, cy, x, y, r, r1, theta, theta1 )
                    _arc(cx, cy, x1, y1, r1, r2, theta1, theta2)
                    return
                elif dtheta <= -1*math.pi:
                    r1 = r + (r - r2)*math.pi/2/dtheta
                    theta1 = theta - math.pi/2
                    x1 = r1*math.cos(theta1)+cx
                    y1 = r1*math.sin(theta1)+cy
                    _arc(cx, cy, x, y, r, r1, theta, theta1)
                    _arc(cx, cy, x1, y1, r1, r2, theta1, theta2)
                    return                    
                
                # find half angle and radius
                theta1 = theta + dtheta/2
                r1 = r+(r2-r)/2
                # find arc halfway point
                x1 = r1*math.cos(theta1)+cx
                y1 = r1*math.sin(theta1)+cy
                # find endpoint and midpoint of chord endpoint 
                x2 = r2*math.cos(theta2)+cx
                y2 = r2*math.sin(theta2)+cy
                xm = x+(x2-x)/2
                ym = y+(y2-y)/2
                if math.hypot(x1-xm, y1-ym)>self.tolerance:
                    # Too much error, split art
                    _arc(cx, cy, x, y, r, r1, theta, theta1)
                    _arc(cx, cy, x1, y1, r1, r2, theta1, theta2)
                    return
                # error is within tolerance, replace arc with line
                self.do_line(x,y,x2,y2)

            self.do_line(x1, y1, x1, y2)
            self.do_line(x1, y2, x2, y2)
            self.do_line(x2, y2, x2, y1)
            self.do_line(x2, y1, x1, y1)
            _arc(cx, cy, x1, y1, r1, r2, theta1, theta2)
            self.pos_x = x2
            self.pos_y = y2

    ################
    # Translate each type of entity (line, circle, arc)

    def do_line(self, x1, y1, x2, y2):
        self.boundary.append([[x1,y1],[x2,y2]])
        self.pos_x = x2
        self.pos_y = y2

    def complain_invalid(self):
        print "Invalid element '" + self.line + "' on line", self.linecount
        print "Can't process this G Code. Sorry!"
        raise ValueError

    def addArc(self, path, x1, y1, rx, ry, phi, large_arc, sweep, x2, y2):
        # Implemented based on the SVG implementation notes
        # plus some recursive sugar for incrementally refining the
        # arc resolution until the requested tolerance is met.
        # http://www.w3.org/TR/SVG/implnote.html#ArcImplementationNotes
        cp = math.cos(phi)
        sp = math.sin(phi)
        dx = 0.5 * (x1 - x2)
        dy = 0.5 * (y1 - y2)
        x_ = cp * dx + sp * dy
        y_ = -sp * dx + cp * dy
        r2 = ((rx*ry)**2-(rx*y_)**2-(ry*x_)**2) / ((rx*y_)**2+(ry*x_)**2)
        if r2 < 0:
            r2 = 0
        r = math.sqrt(r2)
        if large_arc == sweep:
            r = -r
        cx_ = r*rx*y_ / ry
        cy_ = -r*ry*x_ / rx
        cx = cp*cx_ - sp*cy_ + 0.5*(x1 + x2)
        cy = sp*cx_ + cp*cy_ + 0.5*(y1 + y2)
        
        def _angle(u, v):
            a = math.acos((u[0]*v[0] + u[1]*v[1]) /
                            math.sqrt(((u[0])**2 + (u[1])**2) *
                            ((v[0])**2 + (v[1])**2)))
            sgn = -1
            if u[0]*v[1] > u[1]*v[0]:
                sgn = 1
            return sgn * a
    
        psi = _angle([1,0], [(x_-cx_)/rx, (y_-cy_)/ry])
        delta = _angle([(x_-cx_)/rx, (y_-cy_)/ry], [(-x_-cx_)/rx, (-y_-cy_)/ry])
        if sweep and delta < 0:
            delta += math.pi * 2
        if not sweep and delta > 0:
            delta -= math.pi * 2
        
        def _getVertex(pct):
            theta = psi + delta * pct
            ct = math.cos(theta)
            st = math.sin(theta)
            return [cp*rx*ct-sp*ry*st+cx, sp*rx*ct+cp*ry*st+cy]        
        
        # let the recursive fun begin
        def _recursiveArc(t1, t2, c1, c5, level, tolerance2):
            def _vertexDistanceSquared(v1, v2):
                return (v2[0]-v1[0])**2 + (v2[1]-v1[1])**2
            
            def _vertexMiddle(v1, v2):
                return [ (v2[0]+v1[0])/2.0, (v2[1]+v1[1])/2.0 ]

            if level > 18:
                # protect from deep recursion cases
                # max 2**18 = 262144 segments
                return

            tRange = t2-t1
            tHalf = t1 + 0.5*tRange
            c2 = _getVertex(t1 + 0.25*tRange)
            c3 = _getVertex(tHalf)
            c4 = _getVertex(t1 + 0.75*tRange)
            if _vertexDistanceSquared(c2, _vertexMiddle(c1,c3)) > tolerance2:
                _recursiveArc(t1, tHalf, c1, c3, level+1, tolerance2)
            path.append(c3)
            if _vertexDistanceSquared(c4, _vertexMiddle(c3,c5)) > tolerance2:
                _recursiveArc(tHalf, t2, c3, c5, level+1, tolerance2)
                
        t1Init = 0.0
        t2Init = 1.0
        c1Init = _getVertex(t1Init)
        c5Init = _getVertex(t2Init)
        path.append(c1Init)
        _recursiveArc(t1Init, t2Init, c1Init, c5Init, 0, self.tolerance2)
        path.append(c5Init)

