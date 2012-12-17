
import math
import re
import logging
import xml.etree.ElementTree as ET

from .webcolors import hex_to_rgb
from .utilities import matrixMult, matrixApply, vertexScale, parseFloats


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

    def __init__(self, tolerance, target_size):
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
        self._target_size = target_size
            # what the svg size (typically page dimensions) should be mapped to
        self.style = {}  
            # style at current parsing position
        self.tolerance = tolerance
        self.tolerance2 = tolerance**2
        self.tolerance2_half = (0.5*tolerance)**2
        self.tolerance2_px = None
            # tolerance optimizing (tesselating, simplifying) curvy shapes (mm)
        self.ignore_tags = {'defs':None, 'pattern':None, 'clipPath':None}
            # tags to ignore for this parser
        self.optimize = true
            # do all kinds of path optimizations


        
    def parse(self, svgstring, force_dpi=None):
        """ Parse a SVG document.

        This traverses through the document tree and collects all path
        data and converts it to polylines of the requested tolerance.

        Path data is returned as paths by color:
        {'#ff0000': [[path0, path1, ..], [path0, ..], ..]}
        Each path is a list of vertices which is a list of two floats.
        
        One issue with svg documents is that they use px (or unit-less)
        dimensions and most vector apps are not explicit how to convert
        these to real-world units. This method tries to be smart about
        figuring the implied px unit DPIs with the following strategy:

        1. from argument (force_dpi)
        2. from units of page size 
        3. from hints of (known) originating apps
        4. from ratio of page and target size
        5. defaults to 90 DPI
        """        
        self.dpi = None
        self.boundarys = {}

        # parse xml
        svgRootElement = ET.fromstring(svgstring)
        tagName = self.getTag(svgRootElement)

        if tagName != 'svg':
            logging.error("Invalid file, no 'svg' tag found.")
            return self.boundarys

        # 1. Get px unit DPIs from argument
        if force_dpi is not None:
            self.dpi = force_dpi
            logging.info("SVG import forced to "+str(self.dpi)+"dpi.")            

        # get page size
        w = svgRootElement.attrib.get('width')
        h = svgRootElement.attrib.get('height')
        if !w or !h:
            # get size from viewBox
            # http://www.w3.org/TR/SVG11/coords.html#ViewBoxAttribute
            vb = tag.attrib.get('viewBox')
            if vb:
                floats = parseFloats(vb)
                if len(floats) == 4):
                    w = vb_parts[2]
                    h = vb_parts[3]        

        # 2. Try to get px unit DPIs from page size unit.
        # If page size has real-world units make px (and unit-less) the same.
        if w and h:
            if w.endswith('cm'):
                logging.info("Page size in 'cm' -> setting up dpi to treat px (and no) units as 'cm'.")
                self.dpi = 2.54
            elif w.endswith('mm'):
                logging.info("Page size in 'mm' -> setting up dpi to treat px (and no) units as 'mm'.")
                self.dpi = 25.4
            elif w.endswith('pt'):
                logging.info("Page size in 'pt' -> setting up dpi to treat px (and no) units as 'pt'.")
                self.dpi = 1.25
            elif w.endswith('pc'):
                logging.info("Page size in 'pc' -> setting up dpi to treat px (and no) units as 'pc'.")
                self.dpi = 15.0
            elif w.endswith('in'):
                logging.info("Page size in 'in' -> setting up dpi to treat px (and no) units as 'in'.")
                self.dpi = 1.0

        # 3. Try to get px unit DPIs from hints about the originating SVG app
        if not self.dpi:
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
        

                
        # 4. Try to get px unit DPIs from the ratio of page size to target size
        if not self.dpi and w and h:
            try:
                lw = parseFloats(w)
                lh = parseFloats(h)
                if lw and lh:
                    w = lw[0]
                    h = lh[0]
                    self.dpi = round(25.4*w/self._target_size[0])  # round, assume integer dpi
                    logging.info("px unit DPIs from page and target size -> " + str(round(self.dpi,2))
            except ValueError:
                logging.warn("invalid w, h numerals") 

        # 5. Fall back on px unit DPIs default value
        if not self.dpi:
            logging.warn("All smart px unit DPIs infering methods failed -> defaulting to 90dpi.")
            self.dpi = 90.0
        
        # adjust tolerances to px units
        mm2px = self.dpi/25.4
        self.tolerance2_px = (mm2px*self.tolerance)*(mm2px*self.tolerance)
        
        # let the fun begin
        # recursively parse children
        # output will be in self.boundarys    
        node = {
            'fill': 'black',
            'stroke': 'none',
            'stroke' = [0,0,0],
            'xformToWorld' = [1,0,0,1,0,0]
        }
        self.parseChildren(svgRootElement, node)
        
        # paths by colors will be returned
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
