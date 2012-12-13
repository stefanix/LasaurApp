
import math
import re
import logging
import xml.etree.ElementTree as ET

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
        boundarys = {}
            # output path flattened (world coords)
            # hash of path by color
            # each path is a list of subpaths
            # each subpath is a list of verteces
        dpi = None
            # the dpi with which the svg's "user unit/px" unit was exported
        target_size = [1220,610]
            # what the svg size (typically page dimensions) should be mapped to
        style = {}  
            # style at current parsing position
        tolerance = 0.08
        tolerance2 = None
        tolerance2_px = None
        tolerance2_half = None
        epsilon = None
        epsilon2 = None
            # tolerance optimizing (tesselating, simplifying) curvy shapes (mm)
        join_count = 0
            # number of subpath joined
        ignore_tags = {'defs':None, 'pattern':None, 'clipPath':None}
            # tags to ignore for this parser
        optimize = true
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
            self.parseRoot(svgRootElement)
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



    def parseRoot(self, rootNode):
        # we are specifically interested in the width/height/viewBox attribute
        # this is used to determin the page size and consequently the implied dpi of px units
        tagName = self.getTag(rootNode)
        if tagName == 'svg':
            node = {}
            self._SVGTagMapping[tagName](this, rootNode, node)


    
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
                            if attr.nodeName and attr.nodeValue and self._SVGAttributeMapping[attr.nodeName]:
                                self._SVGAttributeMapping[attr.nodeName](self, node, attr.nodeValue)
                    
                    # 3.) accumulate transformations
                    node.xformToWorld = self.matrixMult(parentNode.xformToWorld, node.xform)
                    
                    # 4.) parse tag 
                    # with current attributes and transformation
                    if self._SVGTagMapping[tag.tagName]:
                        self._SVGTagMapping[tag.tagName](self, tag, node)
                    
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
                                self.boundarys[hexcolor].push(subpath)
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
            var multiplier = 1.0
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
        var sum = function(u,v) {return [u[0]+v[0], u[1]+v[1]];}
        var diff = function(u,v) {return [u[0]-v[0], u[1]-v[1]];}
        var prod = function(u,v) {return [u[0]*v[0], u[1]*v[1]];}
        var dot = function(u,v) {return u[0]*v[0] + u[1]*v[1];}
        var norm2 = function(v) {return v[0]*v[0] + v[1]*v[1];}
        var norm = function(v) {return Math.sqrt(norm2(v));}
        var d2 = function(u,v) {return norm2(diff(u,v));}
        var d = function(u,v) {return norm(diff(u,v));}
        
        var simplifyDP = function( tol2, v, j, k, mk ) {
            //  This is the Douglas-Peucker recursive simplification routine
            //  It just marks vertices that are part of the simplified polyline
            //  for approximating the polyline subchain v[j] to v[k].
            //  mk[] ... array of markers matching vertex array v[]
            if (k <= j+1) { // there is nothing to simplify
                return;
            }
            // check for adequate approximation by segment S from v[j] to v[k]
            var maxi = j;          // index of vertex farthest from S
            var maxd2 = 0;         // distance squared of farthest vertex
            S = [v[j], v[k]];  // segment from v[j] to v[k]
            u = diff(S[1], S[0]);   // segment direction vector
            var cu = norm2(u,u);     // segment length squared
            // test each vertex v[i] for max distance from S
            // compute using the Feb 2001 Algorithm's dist_Point_to_Segment()
            // Note: this works in any dimension (2D, 3D, ...)
            var  w;           // vector
            var Pb;                // point, base of perpendicular from v[i] to S
            var b, cw, dv2;        // dv2 = distance v[i] to S squared
            for (var i=j+1; i<k; i++) {
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
        
        var n = V.length;
        var sV = [];    
        var i, k, m, pv;               // misc counters
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








_SVGTagMapping : {
    svg : function(parser, tag, node) {
        // has style attributes
        node.fill = 'black'
        node.stroke = 'none'
        // figure out SVG's immplied dpi
        // SVGs have user units/pixel that have an implied dpi.
        // Inkscape typically uses 90dpi, Illustrator and Intaglio use 72dpi.
        // We can use the width/height and/or viewBox attributes on the svg tag
        // and map the document neatly onto the desired dimensions.
        var w = tag.getAttribute('width');
        var h = tag.getAttribute('height');
        if (!w || !h) {
            // get size from viewBox
            var vb = tag.getAttribute('viewBox');
            if (vb) {
                var vb_parts = vb.split(',');
                if (vb_parts.length != 4) {
                    vb_parts = vb.split(' ');
                }
                if (vb_parts.length == 4) {
                    w = vb_parts[2];
                    h = vb_parts[3];
                }
            }
        }
        if (w && h) {
            if (w.search(/cm$/i) != -1) {
                $().uxmessage('notice', "Page size in 'cm' -> setting up dpi to treat px (and no) units as 'cm'.");
                parser.dpi = 2.54
            } else if (w.search(/mm$/i) != -1) {
                $().uxmessage('notice', "Page size in 'mm' -> setting up dpi to treat px (and no) units as 'mm'.");
                parser.dpi = 25.4
            } else if (w.search(/pt$/i) != -1) {
                $().uxmessage('notice', "Page size in 'pt' -> setting up dpi to treat px (and no) units as 'pt'.");
                parser.dpi = 1.25
            } else if (w.search(/pc$/i) != -1) {
                $().uxmessage('notice', "Page size in 'pc' -> setting up dpi to treat px (and no) units as 'pc'.");
                parser.dpi = 15.0
            } else if (w.search(/in$/i) != -1) {
                $().uxmessage('notice', "Page size in 'in' -> setting up dpi to treat px (and no) units as 'in'.");
                parser.dpi = 1.0
            } else {
                // calculate scaling (dpi) from page size under the assumption the it equals the target size.
                w = parseFloat(w.strip());
                h = parseFloat(h.strip());       
                parser.dpi = Math.round(25.4*w/parser.target_size[0]);
            }
        }
    },
    
    
    g : function(parser, tag, node) {
        // http://www.w3.org/TR/SVG11/struct.html#Groups
        // has transform and style attributes
    },


    polygon : function(parser, tag, node) {
        // http://www.w3.org/TR/SVG11/shapes.html#PolygonElement
        // has transform and style attributes
        var d = this.__getPolyPath(tag)
        d.push('z')
        parser.addPath(d, node)      
    },


    polyline : function(parser, tag, node) {
        // http://www.w3.org/TR/SVG11/shapes.html#PolylineElement
        // has transform and style attributes
        var d = this.__getPolyPath(tag)
        parser.addPath(d, node)
    },
    
    __getPolyPath : function(tag) {
        // has transform and style attributes
        var subpath = []
        var vertnums = tag.getAttribute("points").toString().strip().split(/[\s,]+/).map(parseFloat)
        if (vertnums.length % 2 == 0) {
            var d = ['M']
            d.push(vertnums[0])
            d.push(vertnums[1])
            for (var i=2; i<vertnums.length; i+=2) {
                d.push(vertnums[i])
                d.push(vertnums[i+1])
            }
            return d
        } else {
            $().uxmessage('error', "in __getPolyPath: odd number of verteces");
        }
    },

    rect : function(parser, tag, node) {
        // http://www.w3.org/TR/SVG11/shapes.html#RectElement
        // has transform and style attributes      
        var w = parser.parseUnit(tag.getAttribute('width')) || 0
        var h = parser.parseUnit(tag.getAttribute('height')) || 0
        var x = parser.parseUnit(tag.getAttribute('x')) || 0
        var y = parser.parseUnit(tag.getAttribute('y')) || 0
        var rx = parser.parseUnit(tag.getAttribute('rx'))
        var ry = parser.parseUnit(tag.getAttribute('ry'))
        
        if(rx == null || ry == null) {  // no rounded corners
            var d = ['M', x, y, 'h', w, 'v', h, 'h', -w, 'z'];
            parser.addPath(d, node)
        } else {                       // rounded corners
            if ('ry' == null) { ry = rx; }
            if (rx < 0.0) { rx *=-1; }
            if (ry < 0.0) { ry *=-1; }
            d = ['M', x+rx , y ,
                     'h', w-2*rx,
                     'c', rx, 0.0, rx, ry, rx, ry,
                     'v', h-ry,
                     'c', '0.0', ry, -rx, ry, -rx, ry,
                     'h', -w+2*rx,
                     'c', -rx, '0.0', -rx, -ry, -rx, -ry,
                     'v', -h+ry,
                     'c', '0.0','0.0','0.0', -ry, rx, -ry,
                     'z'];
            parser.addPath(d, node)        
        }
    },


    line : function(parser, tag, node) {
        // http://www.w3.org/TR/SVG11/shapes.html#LineElement
        // has transform and style attributes
        var x1 = parser.parseUnit(tag.getAttribute('x1')) || 0
        var y1 = parser.parseUnit(tag.getAttribute('y1')) || 0
        var x2 = parser.parseUnit(tag.getAttribute('x2')) || 0
        var y2 = parser.parseUnit(tag.getAttribute('y2')) || 0      
        var d = ['M', x1, y1, 'L', x2, y2]
        parser.addPath(d, node)        
    },


    circle : function(parser, tag, node) {
        // http://www.w3.org/TR/SVG11/shapes.html#CircleElement
        // has transform and style attributes      
        var r = parser.parseUnit(tag.getAttribute('r'))
        var cx = parser.parseUnit(tag.getAttribute('cx')) || 0
        var cy = parser.parseUnit(tag.getAttribute('cy')) || 0
        
        if (r > 0.0) {
            var d = ['M', cx-r, cy,                  
                             'A', r, r, 0, 0, 0, cx, cy+r,
                             'A', r, r, 0, 0, 0, cx+r, cy,
                             'A', r, r, 0, 0, 0, cx, cy-r,
                             'A', r, r, 0, 0, 0, cx-r, cy,
                             'Z'];
            parser.addPath(d, node);
        }
    },


    ellipse : function(parser, tag, node) {
        // has transform and style attributes
        var rx = parser.parseUnit(tag.getAttribute('rx'))
        var ry = parser.parseUnit(tag.getAttribute('ry'))
        var cx = parser.parseUnit(tag.getAttribute('cx')) || 0
        var cy = parser.parseUnit(tag.getAttribute('cy')) || 0
        
        if (rx > 0.0 && ry > 0.0) {    
            var d = ['M', cx-rx, cy,                  
                             'A', rx, ry, 0, 0, 0, cx, cy+ry,
                             'A', rx, ry, 0, 0, 0, cx+rx, cy,
                             'A', rx, ry, 0, 0, 0, cx, cy-ry,
                             'A', rx, ry, 0, 0, 0, cx-rx, cy,
                             'Z'];          
            parser.addPath(d, node);
        }
    },

    
    path : function(parser, tag, node) {
        // http://www.w3.org/TR/SVG11/paths.html
        // has transform and style attributes
        var d = tag.getAttribute("d")
        parser.addPath(d, node) 
    },    
    
    image : function(parser, tag, node) {
        // not supported
        // has transform and style attributes
    },
    
    defs : function(parser, tag, node) {
        // not supported
        // http://www.w3.org/TR/SVG11/struct.html#Head
        // has transform and style attributes      
    },
    
    style : function(parser, tag, node) {
        # // not supported: embedded style sheets
        # // http://www.w3.org/TR/SVG11/styling.html#StyleElement
        # // instead presentation attributes and the 'style' attribute 
    }    
            
},






_SVGAttributeMapping : {
    DEG_TO_RAD : Math.PI / 180,
    RAD_TO_DEG : 180 / Math.PI,

    id : function(parser, node, val) {
        node.id = val
    },   

    transform : function(parser, node, val) {
        // http://www.w3.org/TR/SVG11/coords.html#EstablishingANewUserSpace
        var xforms = []
        var segs = val.match(/[a-z]+\s*\([^)]*\)/ig)
        for (var i=0; i<segs.length; i++) {
            var kv = segs[i].split("(");
            var xformKind = kv[0].strip();
            var paramsTemp = kv[1].strip().slice(0,-1);
            var params = paramsTemp.split(/[\s,]+/).map(parseFloat)
            // double check params
            for (var j=0; j<params.length; j++) {
                if ( isNaN(params[j]) ) {
                    $().uxmessage('warning', 'transform skipped; contains non-numbers');
                    continue  // skip this transform
                }
            }
            
            // translate
            if (xformKind == 'translate') {
                if (params.length == 1) {
                    xforms.push([1, 0, 0, 1, params[0], params[0]])
                } else if (params.length == 2) {
                    xforms.push([1, 0, 0, 1, params[0], params[1]])
                } else {
                    $().uxmessage('warning', 'translate skipped; invalid num of params');
                }
            // rotate         
            } else if (xformKind == 'rotate') {
                if (params.length == 3) {
                    var angle = params[0] * this.DEG_TO_RAD
                    xforms.push([1, 0, 0, 1, params[1], params[2]])
                    xforms.push([Math.cos(angle), Math.sin(angle), -Math.sin(angle), Math.cos(angle), 0, 0])
                    xforms.push([1, 0, 0, 1, -params[1], -params[2]])
                } else if (params.length == 1) {
                    var angle = params[0] * this.DEG_TO_RAD
                    xforms.push([Math.cos(angle), Math.sin(angle), -Math.sin(angle), Math.cos(angle), 0, 0])
                } else {
                    $().uxmessage('warning', 'rotate skipped; invalid num of params');
                }
            //scale       
            } else if (xformKind == 'scale') {
                if (params.length == 1) {
                    xforms.push([params[0], 0, 0, params[0], 0, 0])
                } else if (params.length == 2) {
                    xforms.push([params[0], 0, 0, params[1], 0, 0])
                } else {
                    $().uxmessage('warning', 'scale skipped; invalid num of params');
                }
            // matrix
            } else if (xformKind == 'matrix') {
                if (params.length == 6) {
                    xforms.push(params)
                }
            // skewX        
            } else if (xformKind == 'skewX') {
                if (params.length == 1) {
                    var angle = params[0]*this.DEG_TO_RAD
                    xforms.push([1, 0, Math.tan(angle), 1, 0, 0])
                } else {
                    $().uxmessage('warning', 'skewX skipped; invalid num of params');
                }
            // skewY
            } else if (xformKind == 'skewY') {
                if (params.length == 1) {
                    var angle = params[0]*this.DEG_TO_RAD
                    xforms.push([1, Math.tan(angle), 0, 1, 0, 0])
                } else {
                    $().uxmessage('warning', 'skewY skipped; invalid num of params');
                }
            }
        }

        //calculate combined transformation matrix
        xform_combined = [1,0,0,1,0,0]
        for (var i=0; i<xforms.length; i++) {
            xform_combined = parser.matrixMult(xform_combined, xforms[i])
        }
        
        // assign
        node.xform = xform_combined  
    },

    style : function(parser, node, val) {
        // style attribute
        // http://www.w3.org/TR/SVG11/styling.html#StyleAttribute
        // example: <rect x="200" y="100" width="600" height="300" 
        //          style="fill: red; stroke: blue; stroke-width: 3"/>
        
        // relay to parse style attributes the same as Presentation Attributes
        var segs = val.split(";")
        for (var i=0; i<segs.length; i++) {
            var kv = segs[i].split(":")
            var k = kv[0].strip()
            if (this[k]) {
                var v = kv[1].strip()
                this[k](parser, node, v)
            }
        }
    }, 
    
    ///////////////////////////
    // Presentations Attributes 
    // http://www.w3.org/TR/SVG11/styling.html#UsingPresentationAttributes
    // example: <rect x="200" y="100" width="600" height="300" 
    //          fill="red" stroke="blue" stroke-width="3"/>
    
    opacity : function(parser, node, val) {
        node.opacity = parseFloat(val)
    },

    display : function (parser, node, val) {
        node.display = val
    },

    visibility : function (parser, node, val) {
        node.visibility = val
    },

    fill : function(parser, node, val) {
        node.fill = this.__parseColor(val, node.color)
    },

    stroke : function(parser, node, val) {
        node.stroke = this.__parseColor(val, node.color)
    },

    color : function(parser, node, val) {
        if (val == 'inherit') return
        node.color = this.__parseColor(val, node.color)
    },

    'fill-opacity' : function(parser, node, val) {
        node.fillOpacity = Math.min(1,Math.max(0,parseFloat(val)))
    },

    'stroke-opacity' : function(parser, node, val) {
        node.strokeOpacity = Math.min(1,Math.max(0,parseFloat(val)))
    },

    // Presentations Attributes 
    ///////////////////////////

    __parseColor : function(val, currentColor) {

        if (val.charAt(0) == '#') {
            if (val.length == 4)
                val = val.replace(/([^#])/g, '$1$1')
            var a = val.slice(1).match(/../g).map(
                function(i) { return parseInt(i, 16) })
            return a

        } else if (val.search(/^rgb\(/) != -1) {
            var a = val.slice(4,-1).split(",")
            for (var i=0; i<a.length; i++) {
                var c = a[i].strip()
                if (c.charAt(c.length-1) == '%')
                    a[i] = Math.round(parseFloat(c.slice(0,-1)) * 2.55)
                else
                    a[i] = parseInt(c)
            }
            return a

        } else if (val.search(/^rgba\(/) != -1) {
            var a = val.slice(5,-1).split(",")
            for (var i=0; i<3; i++) {
                var c = a[i].strip()
                if (c.charAt(c.length-1) == '%')
                    a[i] = Math.round(parseFloat(c.slice(0,-1)) * 2.55)
                else
                    a[i] = parseInt(c)
            }
            var c = a[3].strip()
            if (c.charAt(c.length-1) == '%')
                a[3] = Math.round(parseFloat(c.slice(0,-1)) * 0.01)
            else
                a[3] = Math.max(0, Math.min(1, parseFloat(c)))
            return a

        } else if (val.search(/^url\(/) != -1) {
            $().uxmessage('error', "defs are not supported at the moment");
        } else if (val == 'currentColor') {
            return currentColor
        } else if (val == 'none') {
            return 'none'
        } else if (val == 'freeze') { // SMIL is evil, but so are we
            return null
        } else if (val == 'remove') {
            return null
        } else { // unknown value, maybe it's an ICC color
            return val
        }
    }
},






class _PathGeometryConverter:
    """
    Handle SVG path data.

    This is where all the geometry gets 
    converted for the boundarys output.
    """

    def __init__(self, tolerance2):
        # tolerance2 is in pixel units
        self._tolerance2_global = tolerance2
        self._tolerance2 = tolerance2

    def addPath(self, d, node):
        # http://www.w3.org/TR/SVG11/paths.html#PathData

        def _matrixExtractcale(mat):
            # extract absolute scale from matrix
            sx = math.sqrt(mat[0]*mat[0] + mat[1]*mat[1])
            sy = math.sqrt(mat[2]*mat[2] + mat[3]*mat[3])
            # return dominant axis
            if sx > sy:
                return sx
            else:
                return sy

        # adjust tolerance for possible transforms
        self._tolerance2 = self._tolerance2_global
        totalMaxScale = _matrixExtractScale(node.xformToWorld)
        if totalMaxScale != 0 and totalMaxScale != 1.0:
            self._tolerance2 /= (totalMaxScale)**2
        
        # parse path string
        # HINT: d would perform better as a linked list or iterator (re.finditer)
        d = re.findall('([A-Za-z]|-?[0-9]+\.?[0-9]*(?:e-?[0-9]*)?)', d)
        for i in range(len(d)):
            try:
                num = float(d[i])
                d[i] = num
            except ValueError:
                # probably a letter, do not convert
                pass
        
        def nextIsNum():
            return (len(d) > 0) and (type(d[0]) is float)
        }
        
        def getNext():
            if len(d) > 0:
                next = d[0]
                d = d[1:] # remove first item
                return next
            else:
                logging.error("not enough parameters")
                return None
        
        x = 0
        y = 0
        cmdPrev = ''
        xPrevCp
        yPrevCp
        subpath = []    
        
        while d:
            cmd = getNext()
            if cmd == 'M':  # moveto absolute
                # start new subpath
                if subpath:
                    node.path.append(subpath)
                    subpath = []
                implicitVerts = 0
                while nextIsNum():
                    x = getNext()
                    y = getNext()
                    subpath.append([x, y])
                    implicitVerts += 1
            elif cmd == 'm':  # moveto relative
                # start new subpath
                if subpath:
                    node.path.append(subpath)
                    subpath = []
                if cmdPrev == '':
                    # first treated absolute
                    x = getNext()
                    y = getNext()
                    subpath.append([x, y])
                implicitVerts = 0       
                while nextIsNum():
                    # subsequent treated realtive
                    x += getNext()
                    y += getNext()
                    subpath.append([x, y])
                    implicitVerts += 1            
            elif cmd == 'Z':  # closepath
                # loop and finalize subpath
                if ( subpath.length > 0) {
                    subpath.push(subpath[0]);  # close
                    node.path.push(subpath);
                    subpath = [];
                }      
                break;
            case 'z':  # closepath
                # loop and finalize subpath
                if ( subpath.length > 0) {
                    subpath.push(subpath[0]);  # close
                    node.path.push(subpath);
                    subpath = [];
                }  
                break          
            case 'L':  # lineto absolute
                while (nextIsNum()) {
                    x = getNext();
                    y = getNext();
                    subpath.push([x, y]);
                }
                break
            case 'l':  # lineto relative
                while (nextIsNum()) {
                    x += getNext();
                    y += getNext();
                    subpath.push([x, y]);
                }
                break
            case 'H':  # lineto horizontal absolute
                while (nextIsNum()) {
                    x = getNext();
                    subpath.push([x, y]);
                }
                break
            case 'h':  # lineto horizontal relative
                while (nextIsNum()) {
                    x += getNext();
                    subpath.push([x, y]);
                }
                break;
            case 'V':  # lineto vertical absolute
                while (nextIsNum()) {
                    y = getNext()
                    subpath.push([x, y])
                }
                break;
            case 'v':  # lineto vertical realtive
                while (nextIsNum()) {
                    y += getNext();
                    subpath.push([x, y]);
                }
                break;
            case 'C':  # curveto cubic absolute
                while (nextIsNum()) {
                    x2 = getNext();
                    y2 = getNext();
                    x3 = getNext();
                    y3 = getNext();
                    x4 = getNext();
                    y4 = getNext();
                    subpath.push([x,y]);
                    self.addCubicBezier(subpath, x, y, x2, y2, x3, y3, x4, y4, 0);
                    subpath.push([x4,y4]);
                    x = x4;
                    y = y4;
                    xPrevCp = x3;
                    yPrevCp = y3;
                }
                break
            case 'c':  # curveto cubic relative
                while (nextIsNum()) {
                    x2 = x + getNext();
                    y2 = y + getNext();
                    x3 = x + getNext();
                    y3 = y + getNext();
                    x4 = x + getNext();
                    y4 = y + getNext();
                    subpath.push([x,y]);
                    self.addCubicBezier(subpath, x, y, x2, y2, x3, y3, x4, y4, 0);
                    subpath.push([x4,y4]);
                    x = x4;
                    y = y4;
                    xPrevCp = x3;
                    yPrevCp = y3;
                }        
                break
            case 'S':  # curveto cubic absolute shorthand
                while (nextIsNum()) {
                    x2;
                    y2;
                    if (cmdPrev.match(/[CcSs]/)) {
                        x2 = x-(xPrevCp-x);
                        y2 = y-(yPrevCp-y); 
                    } else {
                        x2 = x;
                        y2 = y;              
                    }
                    x3 = getNext();
                    y3 = getNext();
                    x4 = getNext();
                    y4 = getNext();
                    subpath.push([x,y]);
                    self.addCubicBezier(subpath, x, y, x2, y2, x3, y3, x4, y4, 0);
                    subpath.push([x4,y4]);
                    x = x4;
                    y = y4;
                    xPrevCp = x3;
                    yPrevCp = y3;
                }                                 
                break
            case 's':  # curveto cubic relative shorthand
                while (nextIsNum()) {
                    x2;
                    y2;
                    if (cmdPrev.match(/[CcSs]/)) {
                        x2 = x-(xPrevCp-x);
                        y2 = y-(yPrevCp-y); 
                    } else {
                        x2 = x;
                        y2 = y;              
                    }
                    x3 = x + getNext();
                    y3 = y + getNext();
                    x4 = x + getNext();
                    y4 = y + getNext();
                    subpath.push([x,y]);
                    self.addCubicBezier(subpath, x, y, x2, y2, x3, y3, x4, y4, 0);
                    subpath.push([x4,y4]);
                    x = x4;
                    y = y4;
                    xPrevCp = x3;
                    yPrevCp = y3;
                }         
                break
            case 'Q':  # curveto quadratic absolute
                while (nextIsNum()) {
                    x2 = getNext();
                    y2 = getNext();
                    x3 = getNext();
                    y3 = getNext();
                    subpath.push([x,y]);
                    self.addQuadraticBezier(subpath, x, y, x2, y2, x3, y3, 0);
                    subpath.push([x3,y3]);
                    x = x3;
                    y = y3;        
                }
                break
            case 'q':  # curveto quadratic relative
                while (nextIsNum()) {
                    x2 = x + getNext();
                    y2 = y + getNext();
                    x3 = x + getNext();
                    y3 = y + getNext();
                    subpath.push([x,y]);
                    self.addQuadraticBezier(subpath, x, y, x2, y2, x3, y3, 0);
                    subpath.push([x3,y3]);
                    x = x3;
                    y = y3;        
                }
                break
            case 'T':  # curveto quadratic absolute shorthand
                while (nextIsNum()) {
                    x2;
                    y2;
                    if (cmdPrev.match(/[QqTt]/)) {
                        x2 = x-(xPrevCp-x);
                        y2 = y-(yPrevCp-y); 
                    } else {
                        x2 = x;
                        y2 = y;              
                    }
                    x3 = getNext();
                    y3 = getNext();
                    subpath.push([x,y]);
                    self.addQuadraticBezier(subpath, x, y, x2, y2, x3, y3, 0);
                    subpath.push([x3,y3]);
                    x = x3;
                    y = y3; 
                    xPrevCp = x2;
                    yPrevCp = y2;
                }        
                break
            case 't':  # curveto quadratic relative shorthand
                while (nextIsNum()) {
                    x2;
                    y2;
                    if (cmdPrev.match(/[QqTt]/)) {
                        x2 = x-(xPrevCp-x);
                        y2 = y-(yPrevCp-y); 
                    } else {
                        x2 = x;
                        y2 = y;              
                    }
                    x3 = x + getNext();
                    y3 = y + getNext();
                    subpath.push([x,y]);
                    self.addQuadraticBezier(subpath, x, y, x2, y2, x3, y3, 0);
                    subpath.push([x3,y3]);
                    x = x3;
                    y = y3; 
                    xPrevCp = x2;
                    yPrevCp = y2;
                }
                break
            case 'A':  # eliptical arc absolute
                while (nextIsNum()) {
                    rx = getNext();
                    ry = getNext();
                    xrot = getNext();
                    large = getNext();        
                    sweep = getNext();
                    x2 = getNext();
                    y2 = getNext();        
                    self.addArc(subpath, x, y, rx, ry, xrot, large, sweep, x2, y2); 
                    x = x2
                    y = y2
                }
                break
            case 'a':  # elliptical arc relative
                while (nextIsNum()) {
                    rx = getNext();
                    ry = getNext();
                    xrot = getNext();
                    large = getNext();        
                    sweep = getNext();
                    x2 = x + getNext();
                    y2 = y + getNext();        
                    self.addArc(subpath, x, y, rx, ry, xrot, large, sweep, x2, y2); 
                    x = x2
                    y = y2
                }
                break

            cmdPrev = cmd

        # finalize subpath
        if subpath:
            node.path.push(subpath)
            subpath = []
        
    

    def addCubicBezier(self, subpath, x1, y1, x2, y2, x3, y3, x4, y4, level):
        # for details see:
        # http://www.antigrain.com/research/adaptive_bezier/index.html
        # based on DeCasteljau Algorithm
        # The reason we use a subdivision algo over an incremental one
        # is we want to have control over the deviation to the curve.
        # This mean we subdivide more and have more curve points in
        # curvy areas and less in flatter areas of the curve.
        
        if (level > 18) {
            # protect from deep recursion cases
            # max 2**18 = 262144 segments
            return
        }
        
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

        d2 = Math.abs(((x2 - x4) * dy - (y2 - y4) * dx))
        d3 = Math.abs(((x3 - x4) * dy - (y3 - y4) * dx))

        if ( Math.pow(d2+d3, 2) < 5.0 * self._tolerance2 * (dx*dx + dy*dy) ) {
            # added factor of 5.0 to match circle resolution
            subpath.push([x1234, y1234])
            return
        }

        # Continue subdivision
        self.addCubicBezier(subpath, x1, y1, x12, y12, x123, y123, x1234, y1234, level+1);
        self.addCubicBezier(subpath, x1234, y1234, x234, y234, x34, y34, x4, y4, level+1);



    def addQuadraticBezier(self, subpath, x1, y1, x2, y2, x3, y3, level):
        if (level > 18) {
            # protect from deep recursion cases
            # max 2**18 = 262144 segments
            return
        }
        
        # Calculate all the mid-points of the line segments
        x12   = (x1 + x2) / 2.0                
        y12   = (y1 + y2) / 2.0
        x23   = (x2 + x3) / 2.0
        y23   = (y2 + y3) / 2.0
        x123  = (x12 + x23) / 2.0
        y123  = (y12 + y23) / 2.0

        dx = x3-x1
        dy = y3-y1
        d = Math.abs(((x2 - x3) * dy - (y2 - y3) * dx))

        if ( d*d <= 5.0 * self._tolerance2 * (dx*dx + dy*dy) ) {
            # added factor of 5.0 to match circle resolution      
            subpath.push([x123, y123])
            return                 
        }
        
        # Continue subdivision
        self.addQuadraticBezier(subpath, x1, y1, x12, y12, x123, y123, level + 1)
        self.addQuadraticBezier(subpath, x123, y123, x23, y23, x3, y3, level + 1)

    
    
    def addArc(self, subpath, x1, y1, rx, ry, phi, large_arc, sweep, x2, y2):
        # Implemented based on the SVG implementation notes
        # plus some recursive sugar for incrementally refining the
        # arc resolution until the requested tolerance is met.
        # http://www.w3.org/TR/SVG/implnote.html#ArcImplementationNotes
        cp = Math.cos(phi);
        sp = Math.sin(phi);
        dx = 0.5 * (x1 - x2);
        dy = 0.5 * (y1 - y2);
        x_ = cp * dx + sp * dy;
        y_ = -sp * dx + cp * dy;
        r2 = (Math.pow(rx*ry,2)-Math.pow(rx*y_,2)-Math.pow(ry*x_,2)) /
                         (Math.pow(rx*y_,2)+Math.pow(ry*x_,2));
        if (r2 < 0) { r2 = 0; }
        r = Math.sqrt(r2);
        if (large_arc == sweep) { r = -r; }
        cx_ = r*rx*y_ / ry;
        cy_ = -r*ry*x_ / rx;
        cx = cp*cx_ - sp*cy_ + 0.5*(x1 + x2);
        cy = sp*cx_ + cp*cy_ + 0.5*(y1 + y2);
        
        function angle(u, v) {
            a = Math.acos((u[0]*v[0] + u[1]*v[1]) /
                            Math.sqrt((Math.pow(u[0],2) + Math.pow(u[1],2)) *
                            (Math.pow(v[0],2) + Math.pow(v[1],2))));
            sgn = -1;
            if (u[0]*v[1] > u[1]*v[0]) { sgn = 1; }
            return sgn * a;
        }
    
        psi = angle([1,0], [(x_-cx_)/rx, (y_-cy_)/ry]);
        delta = angle([(x_-cx_)/rx, (y_-cy_)/ry], [(-x_-cx_)/rx, (-y_-cy_)/ry]);
        if (sweep && delta < 0) { delta += Math.PI * 2; }
        if (!sweep && delta > 0) { delta -= Math.PI * 2; }
        
        def _getVertex(pct):
            theta = psi + delta * pct
            ct = Math.cos(theta)
            st = Math.sin(theta)
            return [cp*rx*ct-sp*ry*st+cx, sp*rx*ct+cp*ry*st+cy]        
        
        # let the recursive fun begin
        def _recursiveArc(t1, t2, c1, c5, level, tolerance2):
            def _vertexDistanceSquared(self, v1, v2):
                return (v2[0]-v1[0])**2 + (v2[1]-v1[1])**2
            
            def _vertexMiddle(self, v1, v2):
                return [ (v2[0]+v1[0])/2.0, (v2[1]+v1[1])/2.0 ]

            if (level > 18) {
                # protect from deep recursion cases
                # max 2**18 = 262144 segments
                return
            }
            tRange = t2-t1
            tHalf = t1 + 0.5*tRange;
            c2 = _getVertex(t1 + 0.25*tRange);
            c3 = _getVertex(tHalf);
            c4 = _getVertex(t1 + 0.75*tRange);
            if (_vertexDistanceSquared(c2, _vertexMiddle(c1,c3)) > tolerance2) { 
                _recursiveArc(t1, tHalf, c1, c3, level+1, tolerance2);
            }
            subpath.push(c3);
            if (_vertexDistanceSquared(c4, _vertexMiddle(c3,c5)) > tolerance2) { 
                _recursiveArc(tHalf, t2, c3, c5, level+1, tolerance2);
            }
                
        t1Init = 0.0;
        t2Init = 1.0;
        c1Init = _getVertex(t1Init);
        c5Init = _getVertex(t2Init);
        subpath.push(c1Init);
        _recursiveArc(t1Init, t2Init, c1Init, c5Init, 0, self._tolerance2);
        subpath.push(c5Init);





