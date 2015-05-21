
__author__ = 'Stefan Hechenberger <stefan@nortd.com>'

import re
import math
import logging

from .webcolors import hex_to_rgb, rgb_to_hex
from .utilities import matrixMult, matrixApply, matrixApplyScale
from .utilities import vertexScale, parseFloats, parseScalar
from .svg_tag_reader import SVGTagReader


logging.basicConfig()
log = logging.getLogger("svg_reader")
log.setLevel(logging.DEBUG)
# log.setLevel(logging.INFO)
# log.setLevel(logging.WARN)


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
#   * raster images
#
# Intentinally not Supported:
#   * markers
#   * masking
#   * em, ex, % units
#   * text (needs to be converted to paths)
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

        # the conversion factor to physical dimensions
        # applied to all coordinates in the SVG
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

        self.rasters = []



    def parse(self, svgstring, force_dpi=None):
        """ Parse a SVG document.

        This traverses through the document tree and collects all path
        data and converts it to polylines of the requested tolerance.

        Path data is returned as paths by color:
        {'#ff0000': [[path0, path1, ..], [path0, ..], ..]}
        Each path is a list of vertices which is a list of two floats.

        Determining Physical Dimensions
        -------------------------------
        SVG files may use physical units (mm, in) or screen units (px).
        For obvious reason former are preferred as these take out any
        guess-work of how to interpret any coordinates.

        A good SVG authoring app writes physical dimensions to file like this:
        - the svg tag has a width, height, viewBox attribute
        - width and height contains the page dimensions and unit
        - viewBox defines a rectangle with (x, y, width, height)
        - width/viewBox:width is the factor that needs to be applied to
          any (unit-less) coordinates in the file
        - x,y is a translation that needs to be applied to any coordinates

        One issue with svg documents is that they are not always clear on
        the physical dimensions. Often they lack or use px units in the
        width/height attributes (no units implies px units in the SVG
        standard). For example, it's possible to encounter px
        units in the file even when the authoring app interprets these
        as physical units (e.g mm). This means there is an implied DPI
        conversion in the app that we need to guess/know.

        The following strategy is used to get physical dimensions:

        1. from argument (force_dpi)
        2. from units of svg width/height and viewBox
        3. from hints of (known) originating apps
        4. from ratio of page and target size
        5. defaults to 90 DPI
        """
        self.px2mm = None
        self.boundarys = {}
        self.lasertags = []
        self.rasters = []

        # parse xml
        svgRootElement = ET.fromstring(svgstring)
        tagName = self._tagReader._get_tag(svgRootElement)

        if tagName != 'svg':
            log.error("Invalid file, no 'svg' tag found.")
            return self.boundarys

        # 1. Get px2mm from argument
        if force_dpi is not None:
            self.px2mm = 25.4/force_dpi
            log.info("SVG import forced to %s dpi." % (force_dpi))

        # Get width, height, viewBox for further processing
        if not self.px2mm:
            width = None
            height = None
            vb_x = None
            vb_y = None
            vb_w = None
            vb_h = None
            unit = ''

            # get width, height, unit
            width_str = svgRootElement.attrib.get('width')
            height_str = svgRootElement.attrib.get('height')
            if width_str and height_str:
                width, width_unit = parseScalar(width_str)
                height, height_unit = parseScalar(height_str)
                if width_unit != height_unit:
                    log.error("Conflicting units found.")
                unit = width_unit
                log.info("SVG w,h (unit) is %s,%s (%s)." % (width, height, unit))

            # get viewBox
            # http://www.w3.org/TR/SVG11/coords.html#ViewBoxAttribute
            vb = svgRootElement.attrib.get('viewBox')
            if vb:
                vb_x, vb_y, vb_w, vb_h = parseFloats(vb)
                log.info("SVG viewBox (%s,%s,%s,%s)." % (vb_x, vb_y, vb_w, vb_h))

        # 2. Get px2mm from width, height, viewBox
        if not self.px2mm:
            if (width and height) or vb:
                if not (width and height):
                    # default to viewBox
                    width = vb_w
                    height = vb_h
                if not vb:
                    # default to width, height, and no offset
                    vb_x = 0.0
                    vb_y = 0.0
                    vb_w = width
                    vb_h = height

                self.px2mm = width/vb_w

                if unit == 'mm':
                    # great, the svg file already uses mm
                    pass
                    log.info("px2mm by svg mm unit")
                elif unit == 'in':
                    # prime for inch to mm conversion
                    self.px2mm *= 25.4
                    log.info("px2mm by svg inch unit")
                elif unit == 'cm':
                    # prime for cm to mm conversion
                    self.px2mm *= 10.0
                    log.info("px2mm by svg cm unit")
                elif unit == 'px' or unit == '':
                    # no physical units in file
                    # we have to interpret user (px) units
                    # 3. For some apps we can make a good guess.
                    svghead = svgstring[0:400]
                    if 'Inkscape' in svghead:
                        self.px2mm *= 25.4/90.0
                        log.info("SVG exported with Inkscape -> 90dpi.")
                    elif 'Illustrator' in svghead:
                        self.px2mm *= 25.4/72.0
                        log.info("SVG exported with Illustrator -> 72dpi.")
                    elif 'Intaglio' in svghead:
                        self.px2mm *= 25.4/72.0
                        log.info("SVG exported with Intaglio -> 72dpi.")
                    elif 'CorelDraw' in svghead:
                        self.px2mm *= 25.4/96.0
                        log.info("SVG exported with CorelDraw -> 96dpi.")
                    elif 'Qt' in svghead:
                        self.px2mm *= 25.4/90.0
                        log.info("SVG exported with Qt lib -> 90dpi.")
                    else:
                        # give up in this step
                        self.px2mm = None
                else:
                    log.error("SVG with unsupported unit.")
                    self.px2mm = None

        # 4. Get px2mm by the ratio of svg size to target size
        if not self.px2mm and (width and height):
            self.px2mm = self._target_size[0]/width
            log.info("px2mm by target_size/page_size ratio")


        # 5. Fall back on px unit DPIs default value
        if not self.px2mm:
            log.warn("Failed to determin physical dimensions -> defaulting to 90dpi.")
            self.px2mm = 25.4/90.0

        # adjust tolerances to px units
        self.tolerance2_px = (self.tolerance/self.px2mm)*(self.tolerance/self.px2mm)

        # translation from viewbox
        if vb_x:
            tx = vb_x
        else:
            tx = 0.0
        if vb_y:
            ty = vb_y
        else:
            ty = 0.0

        # let the fun begin
        # recursively parse children
        # output will be in self.boundarys
        node = {
            'xformToWorld': [1,0,0,1,tx,ty],
            'display': 'visible',
            'visibility': 'visible',
            'fill': '#000000',
            'stroke': '#000000',
            'color': '#000000',
            'fill-opacity': 1.0,
            'stroke-opacity': 1.0,
            'opacity': 1.0
        }
        self.parse_children(svgRootElement, node)

        # build result dictionary
        parse_results = {'dpi':round(25.4/self.px2mm)}

        if self.boundarys:
            parse_results['boundarys'] = self.boundarys

        if self.lasertags:
            parse_results['lasertags'] = self.lasertags

        if self.rasters:
            parse_results['rasters'] = self.rasters

        return parse_results



    def parse_children(self, domNode, parentNode):
        for child in domNode:
            # log.debug("considering tag: " + child.tag)
            if self._tagReader.has_handler(child):
                # 1. setup a new node
                # and inherit from parent
                node = {
                    'paths': [],
                    'rasters': [],
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
                        # 3b.) sort output by color
                        hexcolor = node['stroke']
                        if hexcolor in self.boundarys:
                            self.boundarys[hexcolor].append(path)
                        else:
                            self.boundarys[hexcolor] = [path]

                # 4. any lasertags (cut settings)?
                if node.has_key('lasertags'):
                    self.lasertags.extend(node['lasertags'])

                # 5. Raster Data [(x, y, size, data)]
                for raster in node['rasters']:
                    # pos to world coordinates and then to mm units
                    matrixApply(node['xformToWorld'], raster['pos'])
                    vertexScale(raster['pos'], self.px2mm)

                    # size to world scale and then to mm units
                    matrixApplyScale(node['xformToWorld'], raster['size'])
                    vertexScale(raster['size'], self.px2mm)

                    self.rasters.append(raster)

                # recursive call
                self.parse_children(child, node)





# if __name__ == "__main__":
#     # do something here when used directly
