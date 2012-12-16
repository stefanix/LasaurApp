
import math
import re
import logging

from .webcolors import hex_to_rgb, css3_names_to_hex
from .utilities import matrixMult, parseFloats

from svg_attribute_reader import SVGAttributeReader
from svg_path_reader import SVGPathReader


class SVGTagReader:
    
    def __init__(self, tolerance, target_size):

        self._target_size = target_size

        # init helper for attribute reading
        self._attribReader = SVGAttributeReader()
        # init helper for path handling
        self._pathReader = SVGPathReader(tolerance)

        self._handlers = {
            'svg': self.svg,
            'g': self.g,
            'path': self.path,
            'polygon': self.polygon,
            'polyline': self.polyline,
            'rect': self.rect,
            'line': self.line,
            'circle': self.circle,
            'ellipse': self.ellipse,
            'image': self.image,
            'defs': self.defs,
            'style' self.style
        }


    def readTag(self, tag, node):
        """Read a tag.

        Any tag name that is in self._handlers will be handled.
        Similarly any attribute name in self._attribReader._handlers
        will be parsed. Both tag and attribute results are stored in
        node.

        Any path data is ultimately handled by 
        self._pathReader.addPath(...). For any  geometry that is not
        already in the 'd' attribute of a 'path' tag this class 
        converts it first to this format and then delegates it to 
        addPath(...).

        """
        # parse own attributes and overwrite in node
        for attr,value in tag.attrib.items():
            self._attribReader.readAttrib(node, attr, value)
        # accumulate transformations
        node.xformToWorld = matrixMult(parentNode.xformToWorld, node.xform)
        # read tag
        tagName = self._getTag(tag)
        if tagName in self._handlers:
            self._handlers[tagName](tag, node)


    def svg(self, tag, node):
        # has style attributes
        node.fill = 'black'
        node.stroke = 'none'
        # figure out SVG's immplied dpi
        # SVGs have user units/pixel that have an implied dpi.
        # Inkscape typically uses 90dpi, Illustrator and Intaglio use 72dpi.
        # We can use the width/height and/or viewBox attributes on the svg tag
        # and map the document neatly onto the desired dimensions.
        w = tag.getAttribute('width')
        h = tag.getAttribute('height')
        if !w or !h:
            # get size from viewBox
            vb = tag.getAttribute('viewBox')
            if vb:
                vb_parts = vb.split(',')
                if vb_parts.length != 4:
                    vb_parts = vb.split(' ')
                if vb_parts.length == 4):
                    w = vb_parts[2]
                    h = vb_parts[3]
        if w and h:
            if re.search('cm$', w, re.IGNORECASE):
                logging.info("Page size in 'cm' -> setting up dpi to treat px (and no) units as 'cm'.")
                node['dpi'] = 2.54
            elif re.search('mm$', w, re.IGNORECASE):
                logging.info("Page size in 'mm' -> setting up dpi to treat px (and no) units as 'mm'.")
                node['dpi'] = 25.4
            elif re.search('pt$', w, re.IGNORECASE):
                logging.info("Page size in 'pt' -> setting up dpi to treat px (and no) units as 'pt'.")
                node['dpi'] = 1.25
            elif re.search('pc$', w, re.IGNORECASE):
                logging.info("Page size in 'pc' -> setting up dpi to treat px (and no) units as 'pc'.")
                node['dpi'] = 15.0
            elif re.search('in$', w, re.IGNORECASE):
                logging.info("Page size in 'in' -> setting up dpi to treat px (and no) units as 'in'.")
                node['dpi'] = 1.0
            else:
                # calculate scaling (dpi) from page size under the assumption the it equals the target size.
                try:
                    w = float(w.strip())
                    h = float(h.strip())
                    node['dpi'] = round(25.4*w/target_size[0])  # round, assume integer dpi
                except ValueError:
                    logging.error("Invalid w, h numerals when trying to deduce dpi from target size.") 
    
    
    def g(self, tag, node):
        # http://www.w3.org/TR/SVG11/struct.html#Groups
        # has transform and style attributes
        pass


    ###############
    # geometry tags

    def path(self, tag, node):
        # http://www.w3.org/TR/SVG11/paths.html
        # has transform and style attributes
        d = tag.getAttribute("d")
        self._svgPathReader.addPath(d, node) 


    def polygon(self, tag, node):
        # http://www.w3.org/TR/SVG11/shapes.html#PolygonElement
        # has transform and style attributes
        d = self._getPolyPath(tag)
        d.append('z')
        self._svgPathReader.addPath(d, node)      


    def polyline(self, tag, node):
        # http://www.w3.org/TR/SVG11/shapes.html#PolylineElement
        # has transform and style attributes
        d = this._getPolyPath(tag)
        self._svgPathReader.addPath(d, node)

    
    def _getPolyPath(self, tag):
        # has transform and style attributes
        subpath = []
        vertnums = tag.getAttribute("points").toString().strip().split(/[\s,]+/).map(parseFloat)
        if (vertnums.length % 2 == 0) {
            d = ['M']
            d.append(vertnums[0])
            d.append(vertnums[1])
            for (i=2; i<vertnums.length; i+=2) {
                d.append(vertnums[i])
                d.append(vertnums[i+1])
            }
            return d
        } else {
            $().uxmessage('error', "in _getPolyPath: odd number of verteces");
        }

    def rect(self, tag, node):
        # http://www.w3.org/TR/SVG11/shapes.html#RectElement
        # has transform and style attributes      
        w = self._parseUnit(tag.getAttribute('width')) || 0
        h = self._parseUnit(tag.getAttribute('height')) || 0
        x = self._parseUnit(tag.getAttribute('x')) || 0
        y = self._parseUnit(tag.getAttribute('y')) || 0
        rx = self._parseUnit(tag.getAttribute('rx'))
        ry = self._parseUnit(tag.getAttribute('ry'))
        
        if(rx == null || ry == null) {  # no rounded corners
            d = ['M', x, y, 'h', w, 'v', h, 'h', -w, 'z'];
            self._svgPathReader.addPath(d, node)
        } else {                       # rounded corners
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
            self._svgPathReader.addPath(d, node)        
        }


    def line(self, tag, node):
        # http://www.w3.org/TR/SVG11/shapes.html#LineElement
        # has transform and style attributes
        x1 = self._parseUnit(tag.getAttribute('x1')) || 0
        y1 = self._parseUnit(tag.getAttribute('y1')) || 0
        x2 = self._parseUnit(tag.getAttribute('x2')) || 0
        y2 = self._parseUnit(tag.getAttribute('y2')) || 0      
        d = ['M', x1, y1, 'L', x2, y2]
        self._svgPathReader.addPath(d, node)        


    def circle(self, tag, node):
        # http://www.w3.org/TR/SVG11/shapes.html#CircleElement
        # has transform and style attributes      
        r = self._parseUnit(tag.getAttribute('r'))
        cx = self._parseUnit(tag.getAttribute('cx')) || 0
        cy = self._parseUnit(tag.getAttribute('cy')) || 0
        
        if (r > 0.0) {
            d = ['M', cx-r, cy,                  
                             'A', r, r, 0, 0, 0, cx, cy+r,
                             'A', r, r, 0, 0, 0, cx+r, cy,
                             'A', r, r, 0, 0, 0, cx, cy-r,
                             'A', r, r, 0, 0, 0, cx-r, cy,
                             'Z'];
            self._svgPathReader.addPath(d, node);
        }
    },


    def ellipse(self, tag, node):
        # has transform and style attributes
        rx = self._parseUnit(tag.getAttribute('rx'))
        ry = self._parseUnit(tag.getAttribute('ry'))
        cx = self._parseUnit(tag.getAttribute('cx')) || 0
        cy = self._parseUnit(tag.getAttribute('cy')) || 0
        
        if (rx > 0.0 && ry > 0.0) {    
            d = ['M', cx-rx, cy,                  
                             'A', rx, ry, 0, 0, 0, cx, cy+ry,
                             'A', rx, ry, 0, 0, 0, cx+rx, cy,
                             'A', rx, ry, 0, 0, 0, cx, cy-ry,
                             'A', rx, ry, 0, 0, 0, cx-rx, cy,
                             'Z'];          
            self._svgPathReader.addPath(d, node);
        }

    
    def image(self, tag, node):
        # not supported
        # has transform and style attributes
        logging.warn("image tag is not supported")     
    
    # geometry tags
    ###############


    def defs(self, tag, node):
        # not supported
        # http://www.w3.org/TR/SVG11/struct.html#Head
        # has transform and style attributes      
        logging.warn("defs tag is not supported")     

    def style(self, tag, node):
        # not supported: embedded style sheets
        # http://www.w3.org/TR/SVG11/styling.html#StyleElement
        # instead presentation attributes and the 'style' attribute 
        logging.warn("style tag is not supported, use presentation \
                      attributes or the style attribute instead")     




    def _getTag(self, node):
        """Get tag name without possible namespace prefix."""
        tag = node.tag
        return tag[tag.rfind('}')+1:]


