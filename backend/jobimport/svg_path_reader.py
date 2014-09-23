
__author__ = 'Stefan Hechenberger <stefan@nortd.com>'

import re
import math
import logging

log = logging.getLogger("svg_reader")


class SVGPathReader:
    """
    Handle SVG path data.

    This is where all the geometry gets converted for the
    boundarys output.

    Use this by importing the singleton:
    from svg_path_reader import svgPathReader
    """

    def __init__(self, svgreader):
        self.svgreader = svgreader
        # tolerance2 is in pixel units
        self._tolerance2 = self.svgreader.tolerance2


    def add_path(self, d, node):
        """Convert svg path data to normalized polylines.

        d is the path data as a list of elements.
        """
        # http://www.w3.org/TR/SVG11/paths.html#PathData

        def _matrixExtractScale(mat):
            # extract absolute scale from matrix
            sx = math.sqrt(mat[0]*mat[0] + mat[1]*mat[1])
            sy = math.sqrt(mat[2]*mat[2] + mat[3]*mat[3])
            # return dominant axis
            if sx > sy:
                return sx
            else:
                return sy

        # adjust tolerance for possible transforms
        self._tolerance2 = self.svgreader.tolerance2
        totalMaxScale = _matrixExtractScale(node['xformToWorld'])
        if totalMaxScale != 0 and totalMaxScale != 1.0:
            self._tolerance2 /= (totalMaxScale)**2
        
        idx = [0]  # using a list to be mutable in helper functions

        def _nextIsNum(d, idx, howmany):
            ret = True
            for ii in range(howmany):
                if not (idx[0]+ii < len(d) and isinstance(d[idx[0]+ii], float)):
                    ret = False
            return ret

        
        def _getNext(d, idx):
            i = idx[0]
            idx[0] += 1
            if d and i < len(d):
                f = d[i]
                return f
            else:
                return None
        
        x = 0
        y = 0
        cmdPrev = ''
        xPrevCp = 0
        yPrevCp = 0
        subpath = []  

        while 1:
            cmd = _getNext(d, idx)
            if cmd is None:
                break
            if cmd == 'M':  # moveto absolute
                # start new subpath
                if subpath:
                    node['paths'].append(subpath)
                    subpath = []
                while _nextIsNum(d, idx, 2):
                    # subsequent coords are treated 
                    # the same as absolute lineto
                    x = _getNext(d, idx)
                    y = _getNext(d, idx)
                    subpath.append([x, y])
            elif cmd == 'm':  # moveto relative
                # start new subpath
                if subpath:
                    node['paths'].append(subpath)
                    subpath = []
                if cmdPrev == '':
                    # first treated absolute
                    x = _getNext(d, idx)
                    y = _getNext(d, idx)
                    subpath.append([x, y])
                while _nextIsNum(d, idx, 2):
                    # subsequent coords are treated 
                    # the same as relative lineto
                    x += _getNext(d, idx)
                    y += _getNext(d, idx)
                    subpath.append([x, y])
            elif cmd == 'Z' or cmd == 'z':  # closepath
                # loop and finalize subpath
                if subpath:
                    subpath.append([subpath[0][0],subpath[0][1]])  # close
                    node['paths'].append(subpath)
                    x = subpath[-1][0]
                    y = subpath[-1][1]
                    subpath = []
            elif cmd == 'L':  # lineto absolute
                while _nextIsNum(d, idx, 2):
                    x = _getNext(d, idx)
                    y = _getNext(d, idx)
                    subpath.append([x, y])
            elif cmd == 'l':  # lineto relative
                while _nextIsNum(d, idx, 2):
                    x += _getNext(d, idx)
                    y += _getNext(d, idx)
                    subpath.append([x, y])
            elif cmd == 'H':  # lineto horizontal absolute
                while _nextIsNum(d, idx, 1):
                    x = _getNext(d, idx)
                    subpath.append([x, y])
            elif cmd == 'h':  # lineto horizontal relative
                while _nextIsNum(d, idx, 1):
                    x += _getNext(d, idx)
                    subpath.append([x, y])
            elif cmd == 'V':  # lineto vertical absolute
                while _nextIsNum(d, idx, 1):
                    y = _getNext(d, idx)
                    subpath.append([x, y])
            elif cmd == 'v':  # lineto vertical realtive
                while _nextIsNum(d, idx, 1):
                    y += _getNext(d, idx)
                    subpath.append([x, y])
            elif cmd == 'C':  # curveto cubic absolute
                while _nextIsNum(d, idx, 6):
                    x2 = _getNext(d, idx)
                    y2 = _getNext(d, idx)
                    x3 = _getNext(d, idx)
                    y3 = _getNext(d, idx)
                    x4 = _getNext(d, idx)
                    y4 = _getNext(d, idx)
                    subpath.append([x,y])
                    self.addCubicBezier(subpath, x, y, x2, y2, x3, y3, x4, y4, 0)
                    subpath.append([x4,y4])
                    x = x4
                    y = y4
                    xPrevCp = x3
                    yPrevCp = y3
            elif cmd == 'c':  # curveto cubic relative
                while _nextIsNum(d, idx, 6):
                    x2 = x + _getNext(d, idx)
                    y2 = y + _getNext(d, idx)
                    x3 = x + _getNext(d, idx)
                    y3 = y + _getNext(d, idx)
                    x4 = x + _getNext(d, idx)
                    y4 = y + _getNext(d, idx)
                    subpath.append([x,y])
                    self.addCubicBezier(subpath, x, y, x2, y2, x3, y3, x4, y4, 0)
                    subpath.append([x4,y4])
                    x = x4
                    y = y4
                    xPrevCp = x3
                    yPrevCp = y3
            elif cmd == 'S':  # curveto cubic absolute shorthand
                while _nextIsNum(d, idx, 4):
                    if cmdPrev in 'CcSs]':
                        x2 = x-(xPrevCp-x)
                        y2 = y-(yPrevCp-y) 
                    else:
                        x2 = x
                        y2 = y              
                    x3 = _getNext(d, idx)
                    y3 = _getNext(d, idx)
                    x4 = _getNext(d, idx)
                    y4 = _getNext(d, idx)
                    subpath.append([x,y])
                    self.addCubicBezier(subpath, x, y, x2, y2, x3, y3, x4, y4, 0)
                    subpath.append([x4,y4])
                    x = x4
                    y = y4
                    xPrevCp = x3
                    yPrevCp = y3
            elif cmd == 's':  # curveto cubic relative shorthand
                while _nextIsNum(d, idx, 4):
                    if cmdPrev in 'CcSs]':
                        x2 = x-(xPrevCp-x)
                        y2 = y-(yPrevCp-y) 
                    else:
                        x2 = x
                        y2 = y              
                    x3 = x + _getNext(d, idx)
                    y3 = y + _getNext(d, idx)
                    x4 = x + _getNext(d, idx)
                    y4 = y + _getNext(d, idx)
                    subpath.append([x,y])
                    self.addCubicBezier(subpath, x, y, x2, y2, x3, y3, x4, y4, 0)
                    subpath.append([x4,y4])
                    x = x4
                    y = y4
                    xPrevCp = x3
                    yPrevCp = y3
            elif cmd == 'Q':  # curveto quadratic absolute
                while _nextIsNum(d, idx, 4):
                    x2 = _getNext(d, idx)
                    y2 = _getNext(d, idx)
                    x3 = _getNext(d, idx)
                    y3 = _getNext(d, idx)
                    subpath.append([x,y])
                    self.addQuadraticBezier(subpath, x, y, x2, y2, x3, y3, 0)
                    subpath.append([x3,y3])
                    x = x3
                    y = y3
            elif cmd == 'q':  # curveto quadratic relative
                while _nextIsNum(d, idx, 4):
                    x2 = x + _getNext(d, idx)
                    y2 = y + _getNext(d, idx)
                    x3 = x + _getNext(d, idx)
                    y3 = y + _getNext(d, idx)
                    subpath.append([x,y])
                    self.addQuadraticBezier(subpath, x, y, x2, y2, x3, y3, 0)
                    subpath.append([x3,y3])
                    x = x3
                    y = y3        
            elif cmd == 'T':  # curveto quadratic absolute shorthand
                while _nextIsNum(d, idx, 2):
                    if cmdPrev in 'QqTt':
                        x2 = x-(xPrevCp-x)
                        y2 = y-(yPrevCp-y) 
                    else:
                        x2 = x
                        y2 = y              
                    x3 = _getNext(d, idx)
                    y3 = _getNext(d, idx)
                    subpath.append([x,y])
                    self.addQuadraticBezier(subpath, x, y, x2, y2, x3, y3, 0)
                    subpath.append([x3,y3])
                    x = x3
                    y = y3 
                    xPrevCp = x2
                    yPrevCp = y2
            elif cmd == 't':  # curveto quadratic relative shorthand
                while _nextIsNum(d, idx, 2):
                    if cmdPrev in 'QqTt':
                        x2 = x-(xPrevCp-x)
                        y2 = y-(yPrevCp-y) 
                    else:
                        x2 = x
                        y2 = y
                    x3 = x + _getNext(d, idx)
                    y3 = y + _getNext(d, idx)
                    subpath.append([x,y])
                    self.addQuadraticBezier(subpath, x, y, x2, y2, x3, y3, 0)
                    subpath.append([x3,y3])
                    x = x3
                    y = y3 
                    xPrevCp = x2
                    yPrevCp = y2
            elif cmd == 'A':  # eliptical arc absolute
                while _nextIsNum(d, idx, 7):
                    rx = _getNext(d, idx)
                    ry = _getNext(d, idx)
                    xrot = _getNext(d, idx)
                    large = _getNext(d, idx)
                    sweep = _getNext(d, idx)
                    x2 = _getNext(d, idx)
                    y2 = _getNext(d, idx)        
                    self.addArc(subpath, x, y, rx, ry, xrot, large, sweep, x2, y2)
                    x = x2
                    y = y2
            elif cmd == 'a':  # elliptical arc relative
                while _nextIsNum(d, idx, 7):
                    rx = _getNext(d, idx)
                    ry = _getNext(d, idx)
                    xrot = _getNext(d, idx)
                    large = _getNext(d, idx)
                    sweep = _getNext(d, idx)
                    x2 = x + _getNext(d, idx)
                    y2 = y + _getNext(d, idx)
                    self.addArc(subpath, x, y, rx, ry, xrot, large, sweep, x2, y2)
                    x = x2
                    y = y2

            cmdPrev = cmd

        # finalize subpath
        if subpath:
            node['paths'].append(subpath)
            subpath = []
        
    

    def addCubicBezier(self, subpath, x1, y1, x2, y2, x3, y3, x4, y4, level):
        # for details see:
        # http://www.antigrain.com/research/adaptive_bezier/index.html
        # based on DeCasteljau Algorithm
        # The reason we use a subdivision algo over an incremental one
        # is we want to have control over the deviation to the curve.
        # This mean we subdivide more and have more curve points in
        # curvy areas and less in flatter areas of the curve.
        
        if level > 18:
            # protect from deep recursion cases
            # max 2**18 = 262144 segments
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

        d2 = abs(((x2 - x4) * dy - (y2 - y4) * dx))
        d3 = abs(((x3 - x4) * dy - (y3 - y4) * dx))

        if (d2+d3)**2 < 5.0 * self._tolerance2 * (dx*dx + dy*dy):
            # added factor of 5.0 to match circle resolution
            subpath.append([x1234, y1234])
            return

        # Continue subdivision
        self.addCubicBezier(subpath, x1, y1, x12, y12, x123, y123, x1234, y1234, level+1)
        self.addCubicBezier(subpath, x1234, y1234, x234, y234, x34, y34, x4, y4, level+1)



    def addQuadraticBezier(self, subpath, x1, y1, x2, y2, x3, y3, level):
        if level > 18:
            # protect from deep recursion cases
            # max 2**18 = 262144 segments
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
        d = abs(((x2 - x3) * dy - (y2 - y3) * dx))

        if d*d <= 5.0 * self._tolerance2 * (dx*dx + dy*dy):
            # added factor of 5.0 to match circle resolution      
            subpath.append([x123, y123])
            return                 
        
        # Continue subdivision
        self.addQuadraticBezier(subpath, x1, y1, x12, y12, x123, y123, level + 1)
        self.addQuadraticBezier(subpath, x123, y123, x23, y23, x3, y3, level + 1)

    
    
    def addArc(self, subpath, x1, y1, rx, ry, phi, large_arc, sweep, x2, y2):
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
            subpath.append(c3)
            if _vertexDistanceSquared(c4, _vertexMiddle(c3,c5)) > tolerance2:
                _recursiveArc(tHalf, t2, c3, c5, level+1, tolerance2)
                
        t1Init = 0.0
        t2Init = 1.0
        c1Init = _getVertex(t1Init)
        c5Init = _getVertex(t2Init)
        subpath.append(c1Init)
        _recursiveArc(t1Init, t2Init, c1Init, c5Init, 0, self._tolerance2)
        subpath.append(c5Init)
