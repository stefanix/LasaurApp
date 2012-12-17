
import math
import re
import logging

from .webcolors import hex_to_rgb, css3_names_to_hex
from .utilities import matrixMult, parseFloats

from svg_attribute_reader import SVGAttributeReader
from svg_path_reader import SVGPathReader


class SVGTagReader:
    
    def __init__(self, tolerance):

        # init helper for attribute reading
        self._attribReader = SVGAttributeReader()
        # init helper for path handling
        self._pathReader = SVGPathReader(tolerance)

        self._handlers = {
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

    
    
    def g(self, node):
        # http://www.w3.org/TR/SVG11/struct.html#Groups
        # has transform and style attributes
        pass


    def path(self, node):
        # http://www.w3.org/TR/SVG11/paths.html
        # has transform and style attributes
        d = node.get("d")
        self._svgPathReader.addPath(d, node) 


    def polygon(self, node):
        # http://www.w3.org/TR/SVG11/shapes.html#PolygonElement
        # has transform and style attributes
        d = ['M'] + node['points'] + ['z']
        node['points'] = None
        self._svgPathReader.addPath(d, node)      


    def polyline(self, node):
        # http://www.w3.org/TR/SVG11/shapes.html#PolylineElement
        # has transform and style attributes
        d = ['M'] + node['points']
        node['points'] = None
        self._svgPathReader.addPath(d, node)  


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


