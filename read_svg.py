"""SVG Importer

Copyright (c) 2008 Martin O'Leary
Copyright (c) 2011 Nortd Labs

Derived from Squirtle 0.2.4 by Martin O'Leary
Open Source by the terms of the BSD license.

Example usage:
    from read_SVG import SVG
    boundarys = SVG(svgdata).get_boundarys()
    
    'boundarys' is a list of layers which is a list of
    segments which is a list of verteces which is a
    list of coodinates.
"""

import re
import math
import sys
from string import strip
import xml.etree.cElementTree

    
TOLERANCE = 0.2
MIN_CIRCLE_POINTS = 6
LOOP_TOLERANCE = 0.001

DEFAULT_CUT_COLOR = [255,0,0,255]


def parse_list(string):
    return re.findall("([A-Za-z]|-?[0-9]+\.?[0-9]*(?:e-?[0-9]*)?)", string)

        
class Matrix(object):
    def __init__(self, string=None):
        self.values = [1, 0, 0, 1, 0, 0] #Identity matrix seems a sensible default
        if isinstance(string, str):
            if string.startswith('matrix('):
                self.values = [float(x) for x in parse_list(string[7:-1])]
            elif string.startswith('translate('):
                x, y = [float(x) for x in parse_list(string[10:-1])]
                self.values = [1, 0, 0, 1, x, y]
            elif string.startswith('scale('):
                sx, sy = [float(x) for x in parse_list(string[6:-1])]
                self.values = [sx, 0, 0, sy, 0, 0]           
        elif string is not None:
            self.values = list(string)
    
    def __call__(self, other):
        return (self.values[0]*other[0] + self.values[2]*other[1] + self.values[4],
                self.values[1]*other[0] + self.values[3]*other[1] + self.values[5])
    
    def inverse(self):
        d = float(self.values[0]*self.values[3] - self.values[1]*self.values[2])
        return Matrix([self.values[3]/d, -self.values[1]/d, -self.values[2]/d, self.values[0]/d,
                       (self.values[2]*self.values[5] - self.values[3]*self.values[4])/d,
                       (self.values[1]*self.values[4] - self.values[0]*self.values[5])/d])

    def __mul__(self, other):
        a, b, c, d, e, f = self.values
        u, v, w, x, y, z = other.values
        return Matrix([a*u + c*v, b*u + d*v, a*w + c*x, b*w + d*x, a*y + c*z + e, b*y + d*z + f])
        



        
class SVG(object):
    
    def __init__(self, svgdata, anchor_x=0, anchor_y=0, tolerance=TOLERANCE, min_circle_points=MIN_CIRCLE_POINTS):
        """Creates an SVG object from a .svg or .svgz file.
        
            `svgdata`: str
                The actual SVG.
            `tolerance`: float
                The maximum deviation from the curve, circle, ellipse, arc.
            `min_circle_points`: int
                num of circles points are calculated based on radius and to achive the specified
                TOLERANCE. In some cases (e.g: svg with wild transformation on the circles) it might
                be necessary to overwrite this. You can do this with this arg.                
        """
        
        self.boundarys = [[]]
        self.svgdata = svgdata
        self.tolerance_squared = (10.0*tolerance)**2  #hack, added factor of 10
        self.min_circle_points = min_circle_points
        self.fill = [0, 0, 0, 255]
        self.stroke = [0, 0, 0, 255]          
        # parse on initiation
        self.parse()
        
        
    def get_boundarys(self):
        return self.boundarys


    def parse(self):
        self.tree = xml.etree.cElementTree.fromstring(self.svgdata)
        self.parse_doc()
     
        self.n_tris = 0
        self.n_lines = 0
        for path, stroke, tris, fill, transform in self.paths:
            if path:
                for loop in path:
                    self.n_lines += len(loop) - 1
                    loop_plus = []
                    for i in xrange(len(loop) - 1):
                        loop_plus += [loop[i], loop[i+1]]
                    if isinstance(stroke, str):
                        g = self.gradients[stroke]
                        strokes = [g.interp(x) for x in loop_plus]
                    else:
                        strokes = [stroke for x in loop_plus]

                    self.boundarys[0].append([])  # add a segment
                    segment = self.boundarys[0][-1]
                    for vtx, clr in zip(loop_plus, strokes):
                        vtx = transform(vtx)
                        #glColor4ub(*clr)
                        #glVertex3f(vtx[0], vtx[1], 0)
                        segment.append([vtx[0], vtx[1], 0])
                        

    def parse_doc(self):
        self.paths = []
        self.width = self.parse_float(self.tree.get("width", '0'))
        self.height = self.parse_float(self.tree.get("height", '0'))
        if self.height:
            # self.transform = Matrix([1, 0, 0, -1, 0, self.height])  # original
            self.transform = Matrix([1, 0, 0, 1, 0, 0])  # flip y axis for lasersaur
        else:
            x, y, w, h = (self.parse_float(x) for x in parse_list(self.tree.get("viewBox")))
            # self.transform = Matrix([1, 0, 0, -1, -x, h + y])  # original
            self.transform = Matrix([1, 0, 0, 1, -x, -y])  # flip y axis for lasersaur
            self.height = h
            self.width = w
        self.opacity = 1.0
        for e in self.tree.getchildren():
            try:
                self.parse_element(e)
            except Exception, ex:
                print 'Exception while parsing element', e
                raise
            
    def parse_element(self, e):
        # self.fill = parse_fill_color(e.get('fill'))
        self.stroke = self.parse_stroke_color(e.get('stroke'))
        oldopacity = self.opacity
        self.opacity *= float(e.get('opacity', 1))
        fill_opacity = float(e.get('fill-opacity', 1))
        stroke_opacity = float(e.get('stroke-opacity', 1))
        
        oldtransform = self.transform
        self.transform = self.transform * Matrix(e.get('transform'))
        
        self.parse_style(e.get('style'))
        if DEFAULT_CUT_COLOR[0] == self.stroke[0] \
        and DEFAULT_CUT_COLOR[1] == self.stroke[1] \
        and DEFAULT_CUT_COLOR[2] == self.stroke[2]:
            # we have an outline in the designated cut color
            self.parse_geometry(e)
        
        for c in e.getchildren():
            try:
                self.parse_element(c)
            except Exception, ex:
                print 'Exception while parsing element', c
                raise
                        
        self.transform = oldtransform
        self.opacity = oldopacity         
        
        
    def parse_geometry(self, e):        
        if e.tag.endswith('path'):
            #print e.get('style', '')
            pathdata = e.get('d', '')               
            pathdata = re.findall("([A-Za-z]|-?[0-9]+\.?[0-9]*(?:e-?[0-9]*)?)", pathdata)

            def pnext():
                return (float(pathdata.pop(0)), float(pathdata.pop(0)))
                
            def pnext_is_num():
                try:
                    float(pathdata[0])
                    float(pathdata[1])
                    return True
                except (ValueError, IndexError):
                    return False

            self.new_path()
            while pathdata:
                # for SVG specs see:
                # http://www.w3.org/TR/SVG11/paths.html#PathData
                #
                opcode = pathdata.pop(0)
                if opcode == 'M':
                    self.next_path()
                    while pnext_is_num():
                        self.set_position(*pnext())
                elif opcode == 'm':
                    self.next_path()
                    while pnext_is_num():
                        x, y = pnext()
                        self.set_position(self.x + x, self.y + y)
                elif opcode == 'C':
                    while pnext_is_num():
                        self.cubic_curve_to(*(pnext() + pnext() + pnext()))
                elif opcode == 'c':
                    while pnext_is_num():
                        mx = self.x
                        my = self.y
                        x1, y1 = pnext()
                        x2, y2 = pnext()
                        x, y = pnext()
                        self.cubic_curve_to(mx + x1, my + y1, mx + x2, my + y2, mx + x, my + y)
                elif opcode == 'S':
                    while pnext_is_num():
                        self.cubic_curve_to(2 * self.x - self.last_cx, 2 * self.y - self.last_cy, *(pnext() + pnext()))
                elif opcode == 's':
                    while pnext_is_num():
                        mx = self.x
                        my = self.y
                        x1, y1 = 2 * self.x - self.last_cx, 2 * self.y - self.last_cy
                        x2, y2 = pnext()
                        x, y = pnext()
                        self.cubic_curve_to(x1, y1, mx + x2, my + y2, mx + x, my + y)
                elif opcode == 'Q':
                    #not tested
                    while pnext_is_num():
                        self.quadratic_curve_to(*(pnext() + pnext()))
                elif opcode == 'q':
                    #not tested
                    while pnext_is_num():
                        mx = self.x
                        my = self.y
                        x1, y1 = pnext()
                        x, y = pnext()
                        self.quadratic_curve_to(mx + x1, my + y1, mx + x, my + y)
                elif opcode == 'T':
                    #not tested
                    while pnext_is_num():
                        self.quadratic_curve_to(2 * self.x - self.last_cx, 2 * self.y - self.last_cy, *(pnext()))
                elif opcode == 't':
                    #not tested
                    while pnext_is_num():
                        mx = self.x
                        my = self.y
                        x1, y1 = 2 * self.x - self.last_cx, 2 * self.y - self.last_cy
                        x, y = pnext()
                        self.quadratic_curve_to(x1, y1, mx + x, my + y)
                elif opcode == 'A':
                    while pnext_is_num():                    
                        rx, ry = pnext()
                        phi = float(pathdata.pop(0))
                        large_arc = int(pathdata.pop(0))
                        sweep = int(pathdata.pop(0))
                        x, y = pnext()
                        self.arc_to(rx, ry, phi, large_arc, sweep, x, y)
                elif opcode == 'a':
                    # not tested
                    while pnext_is_num():                    
                        rx, ry = pnext()
                        phi = float(pathdata.pop(0))
                        large_arc = int(pathdata.pop(0))
                        sweep = int(pathdata.pop(0))
                        x, y = pnext()
                        self.arc_to(rx, ry, phi, large_arc, sweep, self.x + x, self.y + y)
                elif opcode in 'zZ':
                    self.close_path()
                elif opcode == 'L':
                    while pnext_is_num():
                        self.line_to(*pnext())
                elif opcode == 'l':
                    while pnext_is_num():
                        x, y = pnext()
                        self.line_to(self.x + x, self.y + y)
                elif opcode == 'H':
                    while pnext_is_num():
                        x = float(pathdata.pop(0))
                        self.line_to(x, self.y)
                elif opcode == 'h':
                    while pnext_is_num():
                        x = float(pathdata.pop(0))
                        self.line_to(self.x + x, self.y)
                elif opcode == 'V':
                    while pnext_is_num():
                        y = float(pathdata.pop(0))
                        self.line_to(self.x, y)
                elif opcode == 'v':
                    while pnext_is_num():
                        y = float(pathdata.pop(0))
                        self.line_to(self.x, self.y + y)
                else:
                    self.warn("Unrecognised opcode: " + opcode)
            self.end_path()
        elif e.tag.endswith('rect'):
            x = float(e.get('x'))
            y = float(e.get('y'))
            h = float(e.get('height'))
            w = float(e.get('width'))
            self.new_path()
            self.set_position(x, y)
            self.line_to(x+w,y)
            self.line_to(x+w,y+h)
            self.line_to(x,y+h)
            self.line_to(x,y)
            self.end_path()
        elif e.tag.endswith('polyline') or e.tag.endswith('polygon'):
            pathdata = e.get('points')
            pathdata = re.findall("(-?[0-9]+\.?[0-9]*(?:e-?[0-9]*)?)", pathdata)
            def pnext():
                return (float(pathdata.pop(0)), float(pathdata.pop(0)))
            self.new_path()
            while pathdata:
                self.line_to(*pnext())
            if e.tag.endswith('polygon'):
                self.close_path()
            self.end_path()
        elif e.tag.endswith('line'):
            x1 = float(e.get('x1'))
            y1 = float(e.get('y1'))
            x2 = float(e.get('x2'))
            y2 = float(e.get('y2'))
            self.new_path()
            self.set_position(x1, y1)
            self.line_to(x2, y2)
            self.end_path()
        elif e.tag.endswith('circle'):
            cx = float(e.get('cx'))
            cy = float(e.get('cy'))
            r = float(e.get('r'))
            circle_points = self.get_circle_steps_for_tolerance(r, self.tolerance_squared)
            self.new_path()
            for i in xrange(circle_points):
                theta = 2 * i * math.pi / circle_points
                self.line_to(cx + r * math.cos(theta), cy + r * math.sin(theta))
            self.close_path()
            self.end_path()
        elif e.tag.endswith('ellipse'):
            cx = float(e.get('cx'))
            cy = float(e.get('cy'))
            rx = float(e.get('rx'))
            ry = float(e.get('ry'))
            circle_points = self.get_circle_steps_for_tolerance(max([rx,ry]), self.tolerance_squared)
            self.new_path()
            for i in xrange(circle_points):
                theta = 2 * i * math.pi / circle_points
                self.line_to(cx + rx * math.cos(theta), cy + ry * math.sin(theta))
            self.close_path()
            self.end_path()
         

    def parse_float(self, txt):
        # assume 90dpi
        if txt.endswith('px'):
            return float(txt[:-2])
        elif txt.endswith('pt'):
            return float(txt[:-2]) * 1.25
        elif txt.endswith('pc'):
            return float(txt[:-2]) * 15.0
        elif txt.endswith('mm'):
            return float(txt[:-2]) * 3.5433070869
        elif txt.endswith('cm'):
            return float(txt[:-2]) * 35.433070869
        elif txt.endswith('in'):
            return float(txt[:-2]) * 90.0
        else:
            return float(txt)

    def parse_style_dict(self, string):
        sdict = {}
        for item in string.split(';'):
            if ':' in item:
                key, value = item.split(':')
                sdict[key] = value
        return sdict

    
    def parse_stroke_color(self, c):
        if not c:
            return self.stroke
        if c[0] == '#':
            c = c[1:]
            try:
                if len(c) == 6:
                    r = int(c[0:2], 16)
                    g = int(c[2:4], 16)
                    b = int(c[4:6], 16)
                elif len(c) == 3:
                    r = int(c[0], 16) * 17
                    g = int(c[1], 16) * 17
                    b = int(c[2], 16) * 17
                else:
                    raise Exception("Incorrect length for colour " + str(c) + " length " + str(len(c)))            
                return [r,g,b,255]
            except Exception, ex:
                print 'Exception parsing hex color', ex
                return self.stroke
        elif c.startswith('rgb('):
            # not tested
            try:          
                rgb = c[4:-1].split(',')
                return [int(rgb[0]), int(rgb[1]), int(rgb[2])]
            except Exception, ex:
                print 'Exception parsing rgb color', ex
                return self.stroke


    def parse_style(self, style):
        if style:
            sdict = self.parse_style_dict(style)
            if 'stroke' in sdict:
                self.stroke = self.parse_stroke_color(sdict['stroke'])
            # if 'fill' in sdict:
            #     self.fill = parse_fill_color(sdict['fill'])
            # if 'fill-opacity' in sdict:
            #     self.fill[3] *= float(sdict['fill-opacity'])                
            # if 'stroke-opacity' in sdict:
            #     self.stroke[3] *= float(sdict['stroke-opacity'])
                
                                       

    def new_path(self):
        self.x = 0
        self.y = 0
        self.close_index = 0
        self.path = []
        self.loop = [] 
    def close_path(self):
        self.loop.append(self.loop[0][:])
        self.path.append(self.loop)
        self.loop = []
    def next_path(self):
        self.path.append(self.loop)
        self.loop = []
    def set_position(self, x, y):
        self.x = x
        self.y = y
        self.loop.append([x,y])
    
    def arc_to(self, rx, ry, phi, large_arc, sweep, x, y):
        # This function is made out of magical fairy dust
        # http://www.w3.org/TR/2003/REC-SVG11-20030114/implnote.html#ArcImplementationNotes
        x1 = self.x
        y1 = self.y
        x2 = x
        y2 = y
        cp = math.cos(phi)
        sp = math.sin(phi)
        dx = .5 * (x1 - x2)
        dy = .5 * (y1 - y2)
        x_ = cp * dx + sp * dy
        y_ = -sp * dx + cp * dy
        r2 = (((rx * ry)**2 - (rx * y_)**2 - (ry * x_)**2)/
	      ((rx * y_)**2 + (ry * x_)**2))
        if r2 < 0: r2 = 0
        r = math.sqrt(r2)
        if large_arc == sweep:
            r = -r
        cx_ = r * rx * y_ / ry
        cy_ = -r * ry * x_ / rx
        cx = cp * cx_ - sp * cy_ + .5 * (x1 + x2)
        cy = sp * cx_ + cp * cy_ + .5 * (y1 + y2)
        def angle(u, v):
            a = math.acos((u[0]*v[0] + u[1]*v[1]) / math.sqrt((u[0]**2 + u[1]**2) * (v[0]**2 + v[1]**2)))
            sgn = 1 if u[0]*v[1] > u[1]*v[0] else -1
            return sgn * a
        
        psi = angle((1,0), ((x_ - cx_)/rx, (y_ - cy_)/ry))
        delta = angle(((x_ - cx_)/rx, (y_ - cy_)/ry), 
                      ((-x_ - cx_)/rx, (-y_ - cy_)/ry))
        if sweep and delta < 0: delta += math.pi * 2
        if not sweep and delta > 0: delta -= math.pi * 2
        
        circle_points = self.get_circle_steps_for_tolerance(max([rx,ry]), self.tolerance_squared)
        n_points = max(int(abs(circle_points * delta / (2 * math.pi))), 1)
        print 'num arc points: ' + str(n_points)
        
        for i in xrange(n_points + 1):
            theta = psi + i * delta / n_points
            ct = math.cos(theta)
            st = math.sin(theta)
            self.line_to(cp * rx * ct - sp * ry * st + cx,
                         sp * rx * ct + cp * ry * st + cy)


    def recursive_bezier_cubic(self, x1, y1, x2, y2, x3, y3, x4, y4, level):
        # for details see:
        # http://www.antigrain.com/research/adaptive_bezier/index.html
        # based on DeCasteljau Algorithm
        # The reason we use a subdivision algo over an incremental one
        # is we want to have control over the deviation to the curve.
        # This mean we subdivide more and have more curve points in
        # curvy areas and less in flatter areas of the curve.
        
        if(level > 32):
            # protect from deep recursion cases
            return
        
        # Calculate all the mid-points of the line segments
        x12   = (x1 + x2) / 2.0
        y12   = (y1 + y2) / 2.0
        x23   = (x2 + x3) / 2.0
        y23   = (y2 + y3) / 2.0
        x34   = (x3 + x4) / 2.0
        y34   = (y3 + y4) / 2.0
        x123  = (x12 + x23) / 2.0
        y123  = (y12 + y23) / 2.0
        x234  = (x23 + x34) / 2.0
        y234  = (y23 + y34) / 2.0
        x1234 = (x123 + x234) / 2.0
        y1234 = (y123 + y234) / 2.0

        # Try to approximate the full cubic curve by a single straight line
        dx = x4-x1
        dy = y4-y1

        d2 = math.fabs(((x2 - x4) * dy - (y2 - y4) * dx))
        d3 = math.fabs(((x3 - x4) * dy - (y3 - y4) * dx))

        if (d2 + d3)*(d2 + d3) < self.tolerance_squared * (dx*dx + dy*dy):
            self.loop.append([x1234, y1234])
            return

        # Continue subdivision
        self.recursive_bezier_cubic(x1, y1, x12, y12, x123, y123, x1234, y1234, level+1)
        self.recursive_bezier_cubic(x1234, y1234, x234, y234, x34, y34, x4, y4, level+1)


    def recursive_bezier_quadratic(self, x1, y1, x2, y2, x3, y3, level):
        if level > 32:
            # protect from deep recursion cases
            return
        
        # Calculate all the mid-points of the line segments
        x12   = (x1 + x2) / 2.0                
        y12   = (y1 + y2) / 2.0
        x23   = (x2 + x3) / 2.0
        y23   = (y2 + y3) / 2.0
        x123  = (x12 + x23) / 2.0
        y123  = (y12 + y23) / 2.0

        dx = x3-x1
        dy = y3-y1
        d = math.fabs(((x2 - x3) * dy - (y2 - y3) * dx))

        if d * d <= self.tolerance_squared * (dx*dx + dy*dy):
            self.loop.append([x123, y123])
            return                 

        # Continue subdivision
        self.recursive_bezier_quadratic(x1, y1, x12, y12, x123, y123, level + 1)
        self.recursive_bezier_quadratic(x123, y123, x23, y23, x3, y3, level + 1)
    

    def cubic_curve_to(self, x1, y1, x2, y2, x, y):
        self.loop.append([self.x, self.y])
        self.recursive_bezier_cubic(self.x, self.y, x1, y1, x2, y2, x, y, 0)
        self.loop.append([x, y])
        self.x, self.y = x, y

    
    def quadratic_curve_to(self, x1, y1, x, y):
        self.loop.append([self.x, self.y])
        self.recursive_bezier_quadratic(self.x, self.y, x1, y1, x, y, 0)
        self.loop.append([x, y])
        self.x, self.y = x, y

    
    def line_to(self, x, y):
        self.set_position(x, y)


    def end_path(self):
        self.path.append(self.loop)
        if self.path:
            path = []
            for orig_loop in self.path:
                if not orig_loop: continue
                loop = [orig_loop[0]]
                for pt in orig_loop:
                    if (pt[0] - loop[-1][0])**2 + (pt[1] - loop[-1][1])**2 > LOOP_TOLERANCE:
                        loop.append(pt)
                path.append(loop)
            self.paths.append((path if self.stroke else None, self.stroke, None, self.fill,self.transform))
        self.path = []


    def get_circle_steps_for_tolerance(self, r, tolerance_squared):
        # This calculation may lead to bad results when 
        # circles are under scale transformations because it will
        # the radii - would basically have to apply all transforms
        # to the radii to make this stable
        numSteps = MIN_CIRCLE_POINTS/2
        def sagitta_squared(r, steps):
            angle = 2*math.pi/steps
            chord = 2*r*math.sin(angle/2.0)
            sagitta2 = (r - math.sqrt(r**2 - (chord/2.0)**2))**2
            # sagitta2 = (r**2 - (r**2 - (chord/2.0)**2))
            return sagitta2
                                
        while sagitta_squared(r, numSteps) > tolerance_squared:
            print 'num of circle steps: ' + str(numSteps)
            numSteps *= 1.5
            
        # added *2 to better match the resolution of the bezier accuracy
        numSteps *= 2
            
        return int(numSteps)


    def warn(self, message):
        print "Warning: SVG Parser - %s" % (message)
