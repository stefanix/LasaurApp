
__author__ = 'Stefan Hechenberger <stefan@nortd.com>'

import re
import math
import logging

from .webcolors import hex_to_rgb, rgb_to_hex
from .utilities import matrixMult, matrixApply, vertexScale, parseFloats
from .svg_tag_reader import SVGTagReader


logging.basicConfig()
log = logging.getLogger("svg_reader")
# log.setLevel(logging.DEBUG)
# log.setLevel(logging.INFO)
log.setLevel(logging.WARN)


try:
    import xml.etree.cElementTree as ET
except ImportError:
    print log.warn("Using non-C (slow) XML parser.")
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
    """SVG parser.

    Usage:
    reader = SVGReader(0.08, [1220,610])
    boundarys = reader.parse(open('filename').read())
    """

    def __init__(self, tolerance, target_size):
        # parsed path data, paths by color
        # {'#ff0000': [[[x,y], [x,y], ...], [], ..], '#0000ff':[]}
        # Each path is a list of vertices which is a list of two floats.        
        self.boundarys = {}

        # the px unit DPIs, conversion to real-world dimensions
        self.dpi = None
        self.px2mm = None

        # what the svg size (typically page dimensions) should be mapped to
        self._target_size = target_size

        # tolerance settings, used in tessalation, path simplification, etc         
        self.tolerance = tolerance
        self.tolerance2 = tolerance**2
        self.tolerance2_half = (0.5*tolerance)**2
        self.tolerance2_px = None

        # init helper object for tag reading
        self._tagReader = SVGTagReader(self)
        
        # lasersaur cut setting from SVG file
        # list of triplets ... [(pass#, key, value), ...]
        # pass# designates the pass this lasertag controls
        # key is the kind of setting (one of: intensity, feedrate, color)
        # value is the actual value to use
        self.lasertags = []
        
        # # tags that should not be further traversed
        # self.ignore_tags = {'defs':None, 'pattern':None, 'clipPath':None}


        
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
        tagName = self._tagReader._get_tag(svgRootElement)

        if tagName != 'svg':
            log.error("Invalid file, no 'svg' tag found.")
            return self.boundarys

        # 1. Get px unit DPIs from argument
        if force_dpi is not None:
            self.dpi = force_dpi
            log.info("SVG import forced to "+str(self.dpi)+"dpi.")            

        # get page size
        w = svgRootElement.attrib.get('width')
        h = svgRootElement.attrib.get('height')
        if not w or not h:
            # get size from viewBox
            # http://www.w3.org/TR/SVG11/coords.html#ViewBoxAttribute
            vb = svgRootElement.attrib.get('viewBox')
            if vb:
                vb_parts = vb.split(',')
                if len(vb_parts) != 4:
                    vb_parts = vb.split(' ')
                if len(vb_parts) == 4:
                    w = vb_parts[2];
                    h = vb_parts[3];     

        # 2. Try to get px unit DPIs from page size unit.
        # If page size has real-world units make px (and unit-less) the same.
        if w and h:
            if w.endswith('cm'):
                log.info("Page size in 'cm' -> setting up dpi to treat px (and no) units as 'cm'.")
                self.dpi = 2.54
            elif w.endswith('mm'):
                log.info("Page size in 'mm' -> setting up dpi to treat px (and no) units as 'mm'.")
                self.dpi = 25.4
            elif w.endswith('pt'):
                log.info("Page size in 'pt' -> setting up dpi to treat px (and no) units as 'pt'.")
                self.dpi = 72
            elif w.endswith('pc'):
                log.info("Page size in 'pc' -> setting up dpi to treat px (and no) units as 'pc'.")
                self.dpi = 72.0/12.0
            elif w.endswith('in'):
                log.info("Page size in 'in' -> setting up dpi to treat px (and no) units as 'in'.")
                self.dpi = 1.0

        # 3. Try to get px unit DPIs from hints about the originating SVG app
        if not self.dpi:
            # look for clues  of svg generator app and it's DPI
            svghead = svgstring[0:400]
            if 'Inkscape' in svghead:
                self.dpi = 90.0
                log.info("SVG exported with Inkscape -> 90dpi.")      
            elif 'Illustrator' in svghead:
                self.dpi = 72.0
                log.info("SVG exported with Illustrator -> 72dpi.")
            elif 'Intaglio' in svghead:
                self.dpi = 72.0
                log.info("SVG exported with Intaglio -> 72dpi.")
            elif 'CorelDraw' in svghead:
                self.dpi = 96.0
                log.info("SVG exported with CorelDraw -> 96dpi.")
            elif 'Qt' in svghead:
                self.dpi = 90.0
                log.info("SVG exported with Qt lib -> 90dpi.")            
        

                
        # 4. Try to get px unit DPIs from the ratio of page size to target size
        if not self.dpi and w and h:
            try:
                lw = parseFloats(w)
                lh = parseFloats(h)
                if lw and lh:
                    w = lw[0]
                    h = lh[0]
                    self.dpi = round(25.4*w/self._target_size[0])  # round, assume integer dpi
                    log.info("px unit DPIs from page and target size -> " + str(round(self.dpi,2)))
            except ValueError, TypeError:
                log.warn("invalid w, h numerals or no target_size") 

        # 5. Fall back on px unit DPIs default value
        if not self.dpi:
            log.warn("All smart px unit DPIs infering methods failed -> defaulting to 90dpi.")
            self.dpi = 90.0

        # 6. Set the conversion factor
        self.px2mm = 25.4/self.dpi
        
        # adjust tolerances to px units
        self.tolerance2_px = (self.tolerance/self.px2mm)*(self.tolerance/self.px2mm)
        
        # let the fun begin
        # recursively parse children
        # output will be in self.boundarys    
        node = {
            'xformToWorld': [1,0,0,1,0,0],
            'display': 'visible',
            'visibility': 'visible',
            'fill': '#000000',
            'stroke': '#000000',
            'color': '#000000',
            'fill-opacity': 1.0,
            'stroke-opacity': 1.0,
            'opacity': 1.0
        }
        self.bbox = [0, 0]
        self.parse_children(svgRootElement, node)
        
        # build result dictionary
        parse_results = {'boundarys':self.boundarys, 'dpi':self.dpi, 'bbox':self.bbox}
        if self.lasertags:
            parse_results['lasertags'] = self.lasertags

        return parse_results


    
    def parse_children(self, domNode, parentNode):
        for child in domNode:
            # log.debug("considering tag: " + child.tag)
            if self._tagReader.has_handler(child):
                # 1. setup a new node
                # and inherit from parent
                node = {
                    'paths': [],
                    'xform': [1,0,0,1,0,0],
                    'xformToWorld': parentNode['xformToWorld'],
                    'display': parentNode.get('display'),
                    'visibility': parentNode.get('visibility'),
                    'fill': parentNode.get('fill'),
                    'stroke': parentNode.get('stroke'),
                    'color': parentNode.get('color'),
                    'fill-opacity': parentNode.get('fill-opacity'),
                    'stroke-opacity': parentNode.get('stroke-opacity'),
                    'opacity': parentNode.get('opacity')
                }

                # 2. parse child 
                # with current attributes and transformation
                self._tagReader.read_tag(child, node)
                
                # 3. compile boundarys + conversions
                for path in node['paths']:
                    if path:  # skip if empty subpath
                        # 3a.) convert to world coordinates and then to mm units
                        for vert in path:
                            # print isinstance(vert[0],float) and isinstance(vert[1],float)
                            matrixApply(node['xformToWorld'], vert)
                            vertexScale(vert, self.px2mm)
                            if vert[0] > self.bbox[0]:
                                self.bbox[0] = vert[0]

                            if vert[1] > self.bbox[1]:
                                self.bbox[1] = vert[1]
                                
                        # 3b.) sort output by color
                        hexcolor = node['stroke']
                        if hexcolor in self.boundarys:
                            self.boundarys[hexcolor].append(path)
                        else:
                            self.boundarys[hexcolor] = [path]

                # 4. any lasertags (cut settings)?
                if node.has_key('lasertags'):
                    self.lasertags.extend(node['lasertags'])
            
                # recursive call
                self.parse_children(child, node)





# if __name__ == "__main__":
#     # do something here when used directly
