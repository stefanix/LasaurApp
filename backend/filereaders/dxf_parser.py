#
# new dxf parser using dxfgrabber.  Loosely based on work by Stephan
# and the lasersaur team.
#
#
__author__ = 'jet <jet@allartburns.org>'

from math import *
import io
import StringIO

import dxfgrabber

import sys
import linecache

class DXFParser:
    """Parse DXF using dxfgrabber-0.7.4

    Usage:
    reader = DXFParser(tolerance)
    returns dictionary of layers using found colors
    """

    def __init__(self, tolerance):
        self.debug = False
        self.verbose = True
        # tolerance settings, used in tessalation, path simplification, etc         
        self.tolerance = tolerance
        self.tolerance2 = tolerance**2

        self.bedwidth = [1220, 610]
        
        # parsed path data, paths by color
        # {'#ff0000': [[path0, path1, ..], [path0, ..], ..]}
        # Each path is a list of vertices which is a list of two floats.        
        # using iso pen colors from dxfwrite
        # 0 is undefined in DXF, it specifies no color, not black
        # 1 red
        # 2 yellow
        # 3 green
        # 4 cyan
        # 5 blue
        # 6 magenta
        # 7 black
        # TODO: support up to 255 colors

        self.colorLayers = {'#FF0000':[],
                          '#FFFF00':[],
                          '#00FF00':[],
                          '#00FFFF':[],
                          '#0000FF':[],
                          '#CC33CC':[],
                          '#000000':[]}

        self.red_colorLayer = self.colorLayers['#FF0000']
        self.yellow_colorLayer = self.colorLayers['#FFFF00']
        self.green_colorLayer = self.colorLayers['#00FF00']
        self.cyan_colorLayer = self.colorLayers['#00FFFF']
        self.blue_colorLayer = self.colorLayers['#0000FF']
        self.magenta_colorLayer = self.colorLayers['#CC33CC']
        self.black_colorLayer = self.colorLayers['#000000']
        
        #assume we're reading metric files and that
        #we round to four decimal places.  There is no Lasersaur
        # that can move from [60, 20] to 
        # [60.00000000000001, 20.00000000000002]
        # if we're reading other units we'll do this rounding after
        # conversion to mm 
        self.round = 4
        self.linecount = 0
        self.line = ''
        self.dxfcode = ''

        # flip/adjust globals
        self.cos180 = round(cos(radians(180)))
        self.sin180 = round(sin(radians(180)))
        self.x_min = self.bedwidth[0]
        self.x_max = 0.0
	#because the y bed is inverted and we are going to flip it
        self.y_min = -self.bedwidth[1]
        self.y_max = 0.0
        
    def parse(self, dxfInput, forced_unit):
        dxfStream = io.StringIO(unicode(dxfInput.replace('\r\n','\n')))
        dwg = dxfgrabber.read(dxfStream)
        if not dwg:
            print ("DXFGRABBER FAIL")
            raise ValueError

        # TODO: check DXF version to see if INSUNITS is expected
        # TODO: try and guess mm vs in based on max x/y
        # set up unit conversion
        if forced_unit == 0 or forced_unit == None:
            self.units = dwg.header.setdefault('$INSUNITS', 0)
        else:
            print("using forced_unit", forced_unit)
            self.units = forced_unit
        if self.verbose:
            print("dxf units read %s, default 0 " % self.units)
        if self.units == 0:
            self.unitsString = "unitless"
        elif self.units == 1:
            self.unitsString = "inches"
        elif self.units == 4:
            self.unitsString = "mm"
        else:
            print("DXF units: >%s< unsupported" % self.units)
            raise ValueError
            
        if self.verbose:
            print("DXF version: {}".format(dwg.dxfversion))
            print("header var count: ", len(dwg.header))
            print("layer count: ", len(dwg.layers)) 
            print("block def count: ", len(dwg.blocks))
            print("entitiy count: ", len(dwg.entities))
            print("units: ", self.unitsString)

        for entity in dwg.entities:
            if entity.color == dxfgrabber.BYLAYER:
                layer = dwg.layers[entity.layer]
                entity.color = layer.color
                if self.debug:
                    print("set entity color to layer color %d" % layer.color)

            if entity.dxftype == "LINE":
                self.addLine(entity)
            elif entity.dxftype == "ARC":
                self.addArc(entity)
            elif entity.dxftype == "CIRCLE":
                self.addCircle(entity)
            elif entity.dxftype == "LWPOLYLINE":
                self.addPolyLine(entity)
            elif entity.dxftype == "SPLINE":
                print("TODO ADD: ", entity.dxftype)
                #self.addSpline(entity)
            else:
                if self.verbose:
                    print("unknown entity: ", entity.dxftype)

        print "Done!"

        if self.verbose:
            print ("pre flipped");
            print ("x min %f" % self.x_min)
            print ("x max %f" % self.x_max)
            print ("y min %f" % self.y_min)
            print ("y max %f" % self.y_max)

        if self.x_min < 0 or self.y_max > -self.bedwidth[1]:
            if self.verbose:
                print("doing shiftPositive")
            self.shiftPositive()

        self.validateBoundaries()

        self.returnColorLayers = {}
        for color in self.colorLayers:
            if len(self.colorLayers[color]) > 0:
                if self.debug:
                    print ("returning color ", color)
                self.returnColorLayers[color] = self.colorLayers[color]
        #TODO: teach the UI to report units read in the file
        return {'boundaries':self.returnColorLayers, 'units':self.unitsString}

    ################
    # Translate each type of entity (line, circle, arc, lwpolyline)

    def addLine(self, entity):
        path = [[self.unitize(entity.start[0]),
                 self.unitize(entity.start[1])],
                [self.unitize(entity.end[0]),
                 self.unitize(entity.end[1])]]
        self.add_path_by_color(entity.color, path)

    def addArc(self, entity):
        cx = self.unitize(entity.center[0])
        cy = self.unitize(entity.center[1])
        r = self.unitize(entity.radius)
        theta1deg = entity.startangle
        theta2deg = entity.endangle
        thetadiff = theta2deg - theta1deg
        if thetadiff < 0 :
            thetadiff = thetadiff + 360
        large_arc_flag = int(thetadiff >= 180)
        sweep_flag = 1
        theta1 = theta1deg/180.0 * pi;
        theta2 = theta2deg/180.0 * pi;
        x1 = cx + r * cos(theta1)
        y1 = cy + r * sin(theta1)
        x2 = cx + r * cos(theta2)
        y2 = cy + r * sin(theta2)
        path = []
        self.makeArc(path, x1, y1, r, r, 0, large_arc_flag, sweep_flag, x2, y2)
        self.add_path_by_color(entity.color, path)

    def addCircle(self, entity):
        cx = self.unitize(entity.center[0])
        cy = self.unitize(entity.center[1])
        r = self.unitize(entity.radius)
        path = []

        self.makeArc(path, cx-r, cy, r, r, 0, 0, 0, cx, cy+r)
        self.makeArc(path, cx, cy+r, r, r, 0, 0, 0, cx+r, cy)
        self.makeArc(path, cx+r, cy, r, r, 0, 0, 0, cx, cy-r)
        self.makeArc(path, cx, cy-r, r, r, 0, 0, 0, cx-r, cy)
        self.add_path_by_color(entity.color, path)

    def addPolyLine(self, entity):
        path = []
        for point in entity.points:
            path.append([self.unitize(point[0]),
                        self.unitize(point[1])])
        self.add_path_by_color(entity.color, path)

    def add_path_by_color(self, color, path):
        flippedPath = self.flipPathAxis(path, "X")
        if self.debug:
            if flippedPath == path:
                print("caution: flippedPath %s == path %s" % (flippedPath, path))
        if color == 1:
            self.red_colorLayer.append(flippedPath)
        elif color == 2:
            self.yellow_colorLayer.append(flippedPath)
        elif color == 3:
            self.green_colorLayer.append(flippedPath)
        elif color == 4:
            self.cyan_colorLayer.append(flippedPath)
        elif color == 5:
            self.blue_colorLayer.append(flippedPath)
        elif color == 6:
            self.magenta_colorLayer.append(flippedPath) 
        elif color == 7:
            self.black_colorLayer.append(flippedPath)
        else:
            if self.verbose:
                print("unrecognized color %d, setting to cyan" % color)
            #TODO: we need a better way to handle this
            #don't know what to do with this color, assigning to red/cut
            self.cyan_colorLayer.append(flippedPath)
            
    def flipPathAxis(self, path, axis):
        flippedPath = []
        
        xFlip = [[1, 0, 0],
                 [0, self.cos180, -self.sin180],
                 [0, self.sin180, self.cos180]]
        
        yFlip = [[self.cos180, 0, self.sin180],
                 [0, 1, 0],
                 [-self.sin180, 0, self.cos180]]
        
        zFlip = [[self.cos180, -self.sin180, 0],
                 [self.sin180, self.cos180, 0],
                 [0, 0, 1]]
        
        for x, y in path:
            if axis == 'X':
                x1 = x
                y1 = round(self.cos180 * y, self.round)
            elif axis == 'Y':
                x1 = round(self.cos180 * x, self.round)
                y1 = y
            elif axis == 'Z':
                x1 = round(self.cos180 * x - self.sin180 * y, self.round)
                y1 = round(self.sin180 * x + self.cos180 * y, self.round)
            self.setMinMax(x1, y1)
            flippedPath.append([x1, y1])

        return flippedPath

    
    def complain_spline(self):
        print "Encountered a SPLINE at line", self.linecount
        print "This program cannot handle splines at present."
        print "Convert the spline to an LWPOLYLINE using Save As options in SolidWorks."
        raise ValueError

    def complain_invalid(self):
        print "Skipping unrecognized element '" + self.line + "' on line", self.linecount

    def makeArc(self, path, x1, y1, rx, ry, phi, large_arc, sweep, x2, y2):
        # Implemented based on the SVG implementation notes
        # plus some recursive sugar for incrementally refining the
        # arc resolution until the requested tolerance is met.
        # http://www.w3.org/TR/SVG/implnote.html#ArcImplementationNotes
        cp = cos(phi)
        sp = sin(phi)
        dx = 0.5 * (x1 - x2)
        dy = 0.5 * (y1 - y2)
        x_ = cp * dx + sp * dy
        y_ = -sp * dx + cp * dy
        r2 = ((rx*ry)**2-(rx*y_)**2-(ry*x_)**2) / ((rx*y_)**2+(ry*x_)**2)
        if r2 < 0:
            r2 = 0
        r = sqrt(r2)
        if large_arc == sweep:
            r = -r
        cx_ = r*rx*y_ / ry
        cy_ = -r*ry*x_ / rx
        cx = cp*cx_ - sp*cy_ + 0.5*(x1 + x2)
        cy = sp*cx_ + cp*cy_ + 0.5*(y1 + y2)
        
        def _angle(u, v):
            a = acos((u[0]*v[0] + u[1]*v[1]) /
                            sqrt(((u[0])**2 + (u[1])**2) *
                            ((v[0])**2 + (v[1])**2)))
            sgn = -1
            if u[0]*v[1] > u[1]*v[0]:
                sgn = 1
            return sgn * a
    
        psi = _angle([1,0], [(x_-cx_)/rx, (y_-cy_)/ry])
        delta = _angle([(x_-cx_)/rx, (y_-cy_)/ry], [(-x_-cx_)/rx, (-y_-cy_)/ry])
        if sweep and delta < 0:
            delta += pi * 2
        if not sweep and delta > 0:
            delta -= pi * 2
        
        def _getVertex(pct):
            theta = psi + delta * pct
            ct = cos(theta)
            st = sin(theta)
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

    def validateBoundaries(self):
        for color in self.colorLayers:
            if len(self.colorLayers[color]) > 0:
                thisColor = self.colorLayers[color]
                for i in range(0, len(thisColor)):
                    if thisColor[i][0][0] < 0 or thisColor[i][0][0] > self.bedwidth[0]:
                        print("WARN: outside of bounds x0 ",  thisColor[i][0][0])
                        raise ValueError
                    elif thisColor[i][0][1] < 0 or thisColor[i][0][1] > self.bedwidth[1]:
                        print("WARN: outside of bounds y0 ",  thisColor[i][0][1])
                        raise ValueError
                    elif thisColor[i][1][0] < 0 or thisColor[i][1][0] > self.bedwidth[0]:
                        print("WARN: outside of bounds x1 ",  thisColor[i][1][0])
                        raise ValueError
                    elif thisColor[i][1][1] < 0 or thisColor[i][1][1] > self.bedwidth[1]:
                        print("WARN: outside of bounds y1 ",  thisColor[i][1][1])
                        raise ValueError
        

    def shiftPositive(self):
        xShift = 0;
        yShift = 0;
        if self.x_min < 0:
            xShift = 0.0 - self.x_min - self.x_max
            if self.debug:
                print("x_min %f" % self.x_min)
                print("x_max %f" % self.x_max)
                print("xShift %f" % xShift)
        if self.y_min < self.bedwidth[1]:
            self.y_min += 0
            if self.y_min == 0:
                yShift = 0.0 - self.y_max
            else:
                yShift = self.bedwidth[1]
            if self.debug:
                print("y bedwidth %f" % self.bedwidth[1])
                print("y_min %f" % self.y_min)
                print("y_max %f" % self.y_max)
                print("yShift %f" % yShift)

        for color in self.colorLayers:
            if len(self.colorLayers[color]) > 0:
                thisColor = self.colorLayers[color]
                for line in range(0, len(thisColor)):
                    i = 0
                    for x, y in thisColor[line]:
                        thisColor[line][i][0] = x + xShift
                        thisColor[line][i][1] = y + yShift
                        i += 1


    def setMinMax(self, x, y):
        if x < self.x_min:
            self.x_min = x
        elif x > self.x_max:
            self.x_max = x
            
        if y > self.y_min:
            self.y_min = y
        elif y < self.y_max:
            self.y_max = y

    def unitize(self, value):
        if self.units == 0 or self.units == 1:
            return round(value * 25.4, self.round)
        elif self.units == 4:
            return round(value, self.round)
        print ("don't know how to convert units ", units)
        raise ValueError

