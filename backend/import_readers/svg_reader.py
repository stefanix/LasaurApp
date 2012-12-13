
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

    def __init__(self, target_size, tolerance):
        self.boundarys = {}
            # output path flattened (world coords)
            # hash of path by color
            # each path is a list of subpaths
            # each subpath is a list of verteces
        self.dpi = None
            # the dpi with which the svg's "user unit/px" unit was exported
        self.target_size = target_size
            # what the svg size (typically page dimensions) should be mapped to
        self.style = {}  
            # style at current parsing position
        self.tolerance = tolerance
        self.tolerance2 = tolerance**2
        self.tolerance2_half = (0.5*tolerance)**2
        self.tolerance2_px = None
            # tolerance optimizing (tesselating, simplifying) curvy shapes (mm)
        self.join_count = 0
            # number of subpath joined
        self.ignore_tags = {'defs':None, 'pattern':None, 'clipPath':None}
            # tags to ignore for this parser
        self.optimize = true
            # do all kinds of path optimizations


        
    def parse(self, svgstring, dpi=None):
        self.dpi = None
        self.join_count = 0
        self.boundarys = {}
        
        if dpi is not None:
            self.dpi = dpi
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
        self.tolerance2_px = (mm2px*self.tolerance)*(mm2px*self.tolerance)
        
        # let the fun begin
        # recursively parse children
        # output will be in self.boundarys    
        node = {}
        node.stroke = [0,0,0]
        node.xformToWorld = [1,0,0,1,0,0]    
        self.parseChildren(svgRootElement, node)
        
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



    def parseUnit(val):
        if val is None:
            return None
        else:
            p = re.search('(-?[0-9]+\.?[0-9]*(?:e-?[0-9]*)?)(cm|mm|pt|pc|in)?',
                          val, re.IGNORECASE).groups()
            num = p[0]
            unit = p[1]
            multiplier = 1.0
            if unit is not None:
                unit = unit.lower()
                if unit == 'cm':
                    multiplier = this.dpi/2.54
                elif unit == 'mm':
                    multiplier = this.dpi/25.4
                elif unit == 'pt':
                    multiplier = 1.25
                elif unit == 'pc':
                    multiplier = 15.0
                elif unit == 'in':
                    multiplier = this.dpi
            return multiplier * float(num)

    
    
    def matrixMult(mA, mB):
        return [ mA[0]*mB[0] + mA[2]*mB[1],
                         mA[1]*mB[0] + mA[3]*mB[1],
                         mA[0]*mB[2] + mA[2]*mB[3],
                         mA[1]*mB[2] + mA[3]*mB[3],
                         mA[0]*mB[4] + mA[2]*mB[5] + mA[4],
                         mA[1]*mB[4] + mA[3]*mB[5] + mA[5] ]
    
    
    def matrixApply(mat, vec):
        return [ mat[0]*vec[0] + mat[2]*vec[1] + mat[4],
                         mat[1]*vec[0] + mat[3]*vec[1] + mat[5] ]


    def vertexScale(v, f):
        return [ v[0]*f, v[1]*f ]
    
