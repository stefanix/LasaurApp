
import math
import re
import logging
import xml.etree.ElementTree as ET

from .webcolors import hex_to_rgb
from .utilities import matrixMult, matrixApply, vertexScale


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
        # init helper object for tag reading
        self.tagReader = SVGTagReader(tolerance, target_size)

        self.boundarys = {}
            # output path flattened (world coords)
            # hash of path by color
            # each path is a list of subpaths
            # each subpath is a list of verteces
            # each vertex is two floats
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
                self.tagReader.readTag(svgRootElement, node)
                if node.has_key('dpi'):
                    self.dpi = node['dpi']

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
        for child in domNode.getchildren():
            if child.getchildren():
                if node.tag:
                    tagName = self.tagReader._getTag(child)
                    if tagName in self.ignore_tags:
                        # ignore certain tags that are not relevant for this parser
                        continue
                    # we are looping here through 
                    # all nodes with child nodes
                    # others are irrelevant

                    # 1. setup a new node
                    # and inherit from parent
                    node = {}
                    node.paths = []
                    node.xform = [1,0,0,1,0,0]
                    node.opacity = parentNode.opacity
                    node.display = parentNode.display
                    node.visibility = parentNode.visibility
                    node.fill = parentNode.fill
                    node.stroke = parentNode.stroke
                    node.color = parentNode.color
                    node.fillOpacity = parentNode.fillOpacity
                    node.strokeOpacity = parentNode.strokeOpacity

                    # 2. parse child 
                    # with current attributes and transformation
                    self.tagReader.readTag(child, node)
                    
                    # 3.) compile boundarys + conversions
                    for path in node.paths:
                        if path:  # skip if empty subpath
                            # 3a.) convert to world coordinates and then to mm units
                            for vert in path:
                                vert = matrixApply(node.xformToWorld, vert)
                                vert = vertexScale(vert, 25.4/self.dpi)
                            # 3b.) sort output by color
                            hexcolor = rgb_to_hex(node.stroke)
                            if hexcolor in self.boundarys:
                                self.boundarys[hexcolor].append(path)
                            else:
                                self.boundarys[hexcolor] = [path]
                
                # recursive call
                self.parseChildren(child, node)





# if __name__ == "__main__":
#     # do something here when used directly
