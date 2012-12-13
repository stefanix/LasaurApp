
import math
import re
import logging
import xml.etree.ElementTree as ET

from svg_tag_reader import svgTagReader
from svg_attribute_reader import svgAttributeReader
from svg_path_reader import svgPathReader



# SVG parser for the Lasersaur.
# Converts SVG DOM to a flat collection of paths.
#
# Copyright (c) 2011 Nortd Labs
# Open Source by the terms of the Gnu Public License (GPL3) or higher.
#
# Code inspired by cake.js, canvg.js, svg2obj.py, and Squirtle.
# Thank you for open sourcing your work!
#
# Usage:
# boundarys = SVGReader.parse(svgstring, config)
#
# Features:
#   * <svg> width and height, viewBox clipping.
#   * paths, rectangles, ellipses, circles, lines, polylines and polygons
#   * nested transforms
#   * transform lists (transform="rotate(30) translate(2,2) scale(4)")
#   * non-pixel units (cm, mm, in, pt, pc)
#   * 'style' attribute and presentation attributes
#   * curves, arcs, cirles, ellipses tesellated according to tolerance
#  
# Intentinally not Supported:
#   * markers
#   * masking
#   * em, ex, % units
#   * text (needs to be converted to paths)
#   * raster images
#   * style sheets
#
# ToDo:
#   * check for out of bounds geometry


class SVGReader:

    def __init__(self):
        self.boundarys = {}
            # output path flattened (world coords)
            # hash of path by color
            # each path is a list of subpaths
            # each subpath is a list of verteces
        self.dpi = None
            # the dpi with which the svg's "user unit/px" unit was exported
        self.target_size = [1220,610]
            # what the svg size (typically page dimensions) should be mapped to
        self.style = {}  
            # style at current parsing position
        self.tolerance = 0.08
        self.tolerance2 = None
        self.tolerance2_px = None
        self.tolerance2_half = None
        self.epsilon = None
        self.epsilon2 = None
            # tolerance optimizing (tesselating, simplifying) curvy shapes (mm)
        self.join_count = 0
            # number of subpath joined
        self.ignore_tags = {'defs':None, 'pattern':None, 'clipPath':None}
            # tags to ignore for this parser
        self.optimize = true
            # do all kinds of path optimizations


        
    def parse(self, svgstring, config):
        self.join_count = 0
        self.boundarys = {}
        if 'optimize' in config:
            self.optimize = config['optimize']
        self.dpi = None
        
        if 'dpi' in config and config['dpi']:
            self.dpi = config['dpi']
            logging.info("SVG import forced to "+str(self.dpi)+"dpi.")
        else:
            # look for clues  of svg generator app and it's DPI
            svghead = svgstring[0:400]
            if 'Inkscape' in svghead:
                self.dpi = 90
                logging.info("SVG exported with Inkscape -> 90dpi.")      
            elif 'Illustrator' in svghead:
                self.dpi = 72
                logging.info("SVG exported with Illustrator -> 72dpi.")
            elif 'Intaglio' in svghead:
                self.dpi = 72
                logging.info("SVG exported with Intaglio -> 72dpi.")
            elif 'CorelDraw' in svghead:
                self.dpi = 96
                logging.info("SVG exported with CorelDraw -> 96dpi.")
            elif 'Qt' in svghead:
                self.dpi = 90
                logging.info("SVG exported with Qt lib -> 90dpi.")
        
        # parse xml
        svgRootElement = ET.fromstring(svgstring)
                
        # figure out how to map px to mm, using document page size, if necessary
        if not self.dpi:
            # we are specifically interested in the width/height/viewBox attribute
            # this is used to determin the page size and consequently the implied dpi of px units
            tagName = self.getTag(svgRootElement)
            if tagName == 'svg':
                node = {}
                self.dpi = self.SVGTagReader['svg'](rootNode, node, self.target_size)

            if self.dpi:
                logging.info("Unit conversion from page size: " + str(round(self.dpi,4)) + 'dpi')
            else:
                logging.warn("Failed to use page size to infere implied px unit conversion -> defaulting to 90dpi.")
                self.dpi = 90
        
        # adjust tolerances to px units
        mm2px = self.dpi/25.4
        self.tolerance2 = self.tolerance*self.tolerance
        self.tolerance2_px = (mm2px*self.tolerance)*(mm2px*self.tolerance)
        self.tolerance2_half = (0.5*self.tolerance)*(0.5*self.tolerance)
        self.epsilon = 0.1*self.tolerance
        self.epsilon2 = self.epsilon*self.epsilon
        
        
        # let the fun begin
        # recursively parse children
        # output will be in self.boundarys    
        node = {}
        node.stroke = [0,0,0]
        node.xformToWorld = [1,0,0,1,0,0]    
        self.parseChildren(svgRootElement, node)
        
        # optimize and sort polylines
        if self.optimize:
            totalverts = 0
            optiverts = 0
            for col in self.boundarys:
                subpaths = self.boundarys[col]  # by color
                # optimize polylines with high-vertex counts
                # as many apps export highly tesselated polylines
                for u in range(len(subpaths)):
                    totalverts += subpaths[u].length
                    subpaths[u] = self.poly_simplify(subpaths[u], self.tolerance2)
                    optiverts += subpaths[u].length
                # sort subpath to optimize seek distances in between
                endpoint = [0,0]  # start at the origin
                for i in range(len(subpaths)):
                    if i > 0:
                        endpoint = subpaths[i-1][subpaths[i-1].length-1]
                    # search the rest of array for closest subpath start point
                    d2_hash = {}  # distance2:index pairs
                    for j in range(i,len(subpaths)):
                        startpoint = subpaths[j][0]
                        d2_hash[Math.pow(endpoint[0]-startpoint[0],2) + Math.pow(endpoint[1]-startpoint[1],2)] = j
                    d2min = 9999999999999999.9
                    d2minIndex = None
                    for d2 in d2_hash:
                        if parseFloat(d2) < d2min:
                            d2min = d2 
                            d2minIndex = d2_hash[d2]
                    # make closest subpath next item
                    if d2minIndex != i:
                        tempItem = subpaths[i]
                        subpaths[i] = subpaths[d2minIndex]
                        subpaths[d2minIndex] = tempItem

            # report pseudo-polyline joining operations
            if self.join_count > 100:
                logging.info("SVGReader: joined many line segments: " + str(self.join_count))
            }
            # report polyline optimizations    
            difflength = totalverts - optiverts
            diffpct = (100*difflength/totalverts)
            if diffpct > 10):  # if diff more than 10%
                logging.info("SVGReader: polylines optimized by " + str(int(diffpct)) + '%')
        
        return self.boundarys


    
    def parseChildren(self, domNode, parentNode):
        childNodes = []
        for i in range(len(domNode.childNodes)):
            tag = domNode.childNodes[i]
            if tag.childNodes:
                if tag.tagName:
                    if tag.tagName in self.ignore_tags:
                        # ignore certain tags that are not relevant for this parser
                        continue
                    # we are looping here through 
                    # all nodes with child nodes
                    # others are irrelevant

                    # 1.) setup a new node
                    # and inherit from parent
                    node = {}
                    node.path = []
                    node.xform = [1,0,0,1,0,0]
                    node.opacity = parentNode.opacity
                    node.display = parentNode.display
                    node.visibility = parentNode.visibility
                    node.fill = parentNode.fill
                    node.stroke = parentNode.stroke
                    node.color = parentNode.color
                    node.fillOpacity = parentNode.fillOpacity
                    node.strokeOpacity = parentNode.strokeOpacity
                    
                    # 2.) parse own attributes and overwrite
                    if tag.attributes:
                        for j in range(len(tag.attributes)):
                            attr = tag.attributes[j]
                            if attr.nodeName and attr.nodeValue and self._svgAttributeReader[attr.nodeName]:
                                self._svgAttributeReader[attr.nodeName](self, node, attr.nodeValue)
                    
                    # 3.) accumulate transformations
                    node.xformToWorld = self.matrixMult(parentNode.xformToWorld, node.xform)
                    
                    # 4.) parse tag 
                    # with current attributes and transformation
                    if self.SVGTagReader[tag.tagName]:
                        self.SVGTagReader[tag.tagName](self, tag, node)
                    
                    # 5.) compile boundarys + conversions
                    for k in range(len(node.path)):
                        subpath = node.path[k]
                        if len(subpath) == 0:
                            continue  # skip if empty subpath
                        # 5a.) convert to world coordinates and then to mm units
                        for l in range(len(subpath)):
                            subpath[l] = self.matrixApply(node.xformToWorld, subpath[l])
                            subpath[l] = self.vertexScale(subpath[l], 25.4/self.dpi)
                        # 5b.) sort output by color
                        hexcolor = self.rgbToHex(node.stroke[0], node.stroke[1], node.stroke[2])
                        if hexcolor in self.boundarys:
                            # 5c.) join subpaths with congruent end/start points
                            # may apps export many short line segments instead of nice polylines              
                            colsubpaths = self.boundarys[hexcolor]
                            lastsubpath = colsubpaths[len(colsubpaths)-1]
                            endpoint = lastsubpath[len(lastsubpath)-1]
                            d2 = (endpoint[0]-subpath[0][0])**2 + (endpoint[1]-subpath[0][1])**2
                            if (d2 < self.epsilon2) and self.optimize:
                                # previous subpath (of same color) end where this one starts
                                # concat subpath to previous subpath, drop first point
                                self.join_count += 1
                                lastsubpath.push.apply(lastsubpath, subpath.slice(1))  #in-place concat
                            else:
                                self.boundarys[hexcolor].append(subpath)
                        else:
                            self.boundarys[hexcolor] = [subpath]
                
                # recursive call
                self.parseChildren(tag, node)

    
    
    def rgbToHex(self, r, g, b):
        return '%02x%02x%02x' % (r, g, b)


    

    def getTag(self, node):
        """Get tag name without possible namespace prefix."""
        tag = node.tag
        return tag[tag.rfind('}')+1:]



    parseUnit : function(val) {
        if (val == null) {
            return null
        } else {
            multiplier = 1.0
            if (val.search(/cm$/i) != -1) {
                multiplier = this.dpi/2.54
            } else if (val.search(/mm$/i) != -1) {
                multiplier = this.dpi/25.4
            } else if (val.search(/pt$/i) != -1) {
                multiplier = 1.25
            } else if (val.search(/pc$/i) != -1) {
                multiplier = 15.0
            } else if (val.search(/in$/i) != -1) {
                multiplier = this.dpi
            }
            return multiplier * parseFloat(val.strip())
        }
    },
    
    
    matrixMult : function(mA, mB) {
        return [ mA[0]*mB[0] + mA[2]*mB[1],
                         mA[1]*mB[0] + mA[3]*mB[1],
                         mA[0]*mB[2] + mA[2]*mB[3],
                         mA[1]*mB[2] + mA[3]*mB[3],
                         mA[0]*mB[4] + mA[2]*mB[5] + mA[4],
                         mA[1]*mB[4] + mA[3]*mB[5] + mA[5] ]
    },
    
    
    matrixApply : function(mat, vec) {
        return [ mat[0]*vec[0] + mat[2]*vec[1] + mat[4],
                         mat[1]*vec[0] + mat[3]*vec[1] + mat[5] ] ;
    },  

    


    vertexScale : function(v, f) {
        return [ v[0]*f, v[1]*f ];
    },  



    poly_simplify : function(V, tol2) {
        // V ... [[x1,y1],[x2,y2],...] polyline
        // tol2  ... approximation tolerance squared
        // ============================================== 
        // Copyright 2002, softSurfer (www.softsurfer.com)
        // This code may be freely used and modified for any purpose
        // providing that this copyright notice is included with it.
        // SoftSurfer makes no warranty for this code, and cannot be held
        // liable for any real or imagined damage resulting from its use.
        // Users of this code must verify correctness for their application.
        // http://softsurfer.com/Archive/algorithm_0205/algorithm_0205.htm
        sum = function(u,v) {return [u[0]+v[0], u[1]+v[1]];}
        diff = function(u,v) {return [u[0]-v[0], u[1]-v[1]];}
        prod = function(u,v) {return [u[0]*v[0], u[1]*v[1]];}
        dot = function(u,v) {return u[0]*v[0] + u[1]*v[1];}
        norm2 = function(v) {return v[0]*v[0] + v[1]*v[1];}
        norm = function(v) {return Math.sqrt(norm2(v));}
        d2 = function(u,v) {return norm2(diff(u,v));}
        d = function(u,v) {return norm(diff(u,v));}
        
        simplifyDP = function( tol2, v, j, k, mk ) {
            //  This is the Douglas-Peucker recursive simplification routine
            //  It just marks vertices that are part of the simplified polyline
            //  for approximating the polyline subchain v[j] to v[k].
            //  mk[] ... array of markers matching vertex array v[]
            if (k <= j+1) { // there is nothing to simplify
                return;
            }
            // check for adequate approximation by segment S from v[j] to v[k]
            maxi = j;          // index of vertex farthest from S
            maxd2 = 0;         // distance squared of farthest vertex
            S = [v[j], v[k]];  // segment from v[j] to v[k]
            u = diff(S[1], S[0]);   // segment direction vector
            cu = norm2(u,u);     // segment length squared
            // test each vertex v[i] for max distance from S
            // compute using the Feb 2001 Algorithm's dist_Point_to_Segment()
            // Note: this works in any dimension (2D, 3D, ...)
             w;           // vector
            Pb;                // point, base of perpendicular from v[i] to S
            b, cw, dv2;        // dv2 = distance v[i] to S squared
            for (i=j+1; i<k; i++) {
                // compute distance squared
                w = diff(v[i], S[0]);
                cw = dot(w,u);
                if ( cw <= 0 ) {
                    dv2 = d2(v[i], S[0]);
                } else if ( cu <= cw ) {
                    dv2 = d2(v[i], S[1]);
                } else {
                    b = cw / cu;
                    Pb = [S[0][0]+b*u[0], S[0][1]+b*u[1]];
                    dv2 = d2(v[i], Pb);
                }
                // test with current max distance squared
                if (dv2 <= maxd2) {
                    continue;
                }
                // v[i] is a new max vertex
                maxi = i;
                maxd2 = dv2;
            }
            if (maxd2 > tol2) {      // error is worse than the tolerance
                // split the polyline at the farthest vertex from S
                mk[maxi] = 1;      // mark v[maxi] for the simplified polyline
                // recursively simplify the two subpolylines at v[maxi]
                simplifyDP( tol2, v, j, maxi, mk );  // polyline v[j] to v[maxi]
                simplifyDP( tol2, v, maxi, k, mk );  // polyline v[maxi] to v[k]
            }
            // else the approximation is OK, so ignore intermediate vertices
            return;
        }    
        
        n = V.length;
        sV = [];    
        i, k, m, pv;               // misc counters
        vt = [];                       // vertex buffer, points
        mk = [];                       // marker buffer, ints

        // STAGE 1.  Vertex Reduction within tolerance of prior vertex cluster
        vt[0] = V[0];              // start at the beginning
        for (i=k=1, pv=0; i<n; i++) {
            if (d2(V[i], V[pv]) < tol2) {
                continue;
            }
            vt[k++] = V[i];
            pv = i;
        }
        if (pv < n-1) {
            vt[k++] = V[n-1];      // finish at the end
        }

        // STAGE 2.  Douglas-Peucker polyline simplification
        mk[0] = mk[k-1] = 1;       // mark the first and last vertices
        simplifyDP( tol2, vt, 0, k-1, mk );

        // copy marked vertices to the output simplified polyline
        for (i=m=0; i<k; i++) {
            if (mk[i]) {
                sV[m++] = vt[i];
            }
        }
        return sV;
    },
    
}




