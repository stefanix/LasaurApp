
import math
import re
import logging



class SVGTagReaderClass:
    
    def __init__(self):
        pass

    def svg(self, tag, node, target_size):
        dpi = None
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
                dpi = 2.54
            elif re.search('mm$', w, re.IGNORECASE):
                logging.info("Page size in 'mm' -> setting up dpi to treat px (and no) units as 'mm'.")
                dpi = 25.4
            elif re.search('pt$', w, re.IGNORECASE):
                logging.info("Page size in 'pt' -> setting up dpi to treat px (and no) units as 'pt'.")
                dpi = 1.25
            elif re.search('pc$', w, re.IGNORECASE):
                logging.info("Page size in 'pc' -> setting up dpi to treat px (and no) units as 'pc'.")
                dpi = 15.0
            elif re.search('in$', w, re.IGNORECASE):
                logging.info("Page size in 'in' -> setting up dpi to treat px (and no) units as 'in'.")
                dpi = 1.0
            else:
                # calculate scaling (dpi) from page size under the assumption the it equals the target size.
                try:
                    w = float(w.strip())
                    h = float(h.strip())
                    dpi = round(25.4*w/target_size[0])  # round, assume integer dpi
                except ValueError:
                    logging.error("Invalid w, h numerals when trying to deduce dpi from target size.") 
        return dpi  
    
    
    def g(self, parser, tag, node):
        # http://www.w3.org/TR/SVG11/struct.html#Groups
        # has transform and style attributes
        pass


    def polygon(self, parser, tag, node):
        # http://www.w3.org/TR/SVG11/shapes.html#PolygonElement
        # has transform and style attributes
        d = self._getPolyPath(tag)
        d.append('z')
        parser.addPath(d, node)      


    def polyline(self, parser, tag, node):
        # http://www.w3.org/TR/SVG11/shapes.html#PolylineElement
        # has transform and style attributes
        d = this._getPolyPath(tag)
        parser.addPath(d, node)

    
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

    def rect(self, parser, tag, node):
        # http://www.w3.org/TR/SVG11/shapes.html#RectElement
        # has transform and style attributes      
        w = parser.parseUnit(tag.getAttribute('width')) || 0
        h = parser.parseUnit(tag.getAttribute('height')) || 0
        x = parser.parseUnit(tag.getAttribute('x')) || 0
        y = parser.parseUnit(tag.getAttribute('y')) || 0
        rx = parser.parseUnit(tag.getAttribute('rx'))
        ry = parser.parseUnit(tag.getAttribute('ry'))
        
        if(rx == null || ry == null) {  # no rounded corners
            d = ['M', x, y, 'h', w, 'v', h, 'h', -w, 'z'];
            parser.addPath(d, node)
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
            parser.addPath(d, node)        
        }


    def line(self, parser, tag, node):
        # http://www.w3.org/TR/SVG11/shapes.html#LineElement
        # has transform and style attributes
        x1 = parser.parseUnit(tag.getAttribute('x1')) || 0
        y1 = parser.parseUnit(tag.getAttribute('y1')) || 0
        x2 = parser.parseUnit(tag.getAttribute('x2')) || 0
        y2 = parser.parseUnit(tag.getAttribute('y2')) || 0      
        d = ['M', x1, y1, 'L', x2, y2]
        parser.addPath(d, node)        


    def circle(self, parser, tag, node):
        # http://www.w3.org/TR/SVG11/shapes.html#CircleElement
        # has transform and style attributes      
        r = parser.parseUnit(tag.getAttribute('r'))
        cx = parser.parseUnit(tag.getAttribute('cx')) || 0
        cy = parser.parseUnit(tag.getAttribute('cy')) || 0
        
        if (r > 0.0) {
            d = ['M', cx-r, cy,                  
                             'A', r, r, 0, 0, 0, cx, cy+r,
                             'A', r, r, 0, 0, 0, cx+r, cy,
                             'A', r, r, 0, 0, 0, cx, cy-r,
                             'A', r, r, 0, 0, 0, cx-r, cy,
                             'Z'];
            parser.addPath(d, node);
        }
    },


    def ellipse(self, parser, tag, node):
        # has transform and style attributes
        rx = parser.parseUnit(tag.getAttribute('rx'))
        ry = parser.parseUnit(tag.getAttribute('ry'))
        cx = parser.parseUnit(tag.getAttribute('cx')) || 0
        cy = parser.parseUnit(tag.getAttribute('cy')) || 0
        
        if (rx > 0.0 && ry > 0.0) {    
            d = ['M', cx-rx, cy,                  
                             'A', rx, ry, 0, 0, 0, cx, cy+ry,
                             'A', rx, ry, 0, 0, 0, cx+rx, cy,
                             'A', rx, ry, 0, 0, 0, cx, cy-ry,
                             'A', rx, ry, 0, 0, 0, cx-rx, cy,
                             'Z'];          
            parser.addPath(d, node);
        }

    
    def path(self, parser, tag, node):
        # http://www.w3.org/TR/SVG11/paths.html
        # has transform and style attributes
        d = tag.getAttribute("d")
        parser.addPath(d, node) 
    
    def image(self, parser, tag, node):
        # not supported
        # has transform and style attributes
        pass
    
    def defs(self, parser, tag, node):
        # not supported
        # http://www.w3.org/TR/SVG11/struct.html#Head
        # has transform and style attributes      
        pass    

    def style(self, parser, tag, node):
        # not supported: embedded style sheets
        # http://www.w3.org/TR/SVG11/styling.html#StyleElement
        # instead presentation attributes and the 'style' attribute 
        pass            



# singelton
svgTagReader = SVGTagReaderClass()