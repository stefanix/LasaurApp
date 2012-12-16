
import math
import re
import logging



class SVGAttributeReader:

    def __init__(self):
        self.DEG_TO_RAD = math.pi/180
        self.RAD_TO_DEG = 180/math.pi

        self._handlers = {
            'id': self.stringAttrib,
            # xform
            'transform': self.transform,
            'viewBox': ,
            # styles
            'style': self.style,
            'opacity': self.opacityAttrib,
            'display': self.stringAttrib,
            'visibility': self.stringAttrib,
            'fill': self.colorAttrib,
            'stroke': self.colorAttrib,
            'color': self.colorAttrib,
            'fill-opacity': self.opacityAttrib,
            'stroke-opacity': self.opacityAttrib,
            # geometry
            'width': self.dimensionAttrib,
            'height': self.dimensionAttrib,
            'd'
            'points'
            'x': self.dimensionAttrib,
            'y': self.dimensionAttrib,
            'rx': self.dimensionAttrib,
            'ry': self.dimensionAttrib,
            'x1': self.dimensionAttrib,
            'y1': self.dimensionAttrib,
            'x2': self.dimensionAttrib,
            'y2': self.dimensionAttrib,
            'r': self.dimensionAttrib,
            'cx': self.dimensionAttrib,
            'cy': self.dimensionAttrib
        }


    def readAttrib(self, node, attr, value):
        if attr in self._handlers:
            self._handlers[attr](node, attr, value)


    def stringAttrib(self, node, attr, value):
        node[attr] = value

    def opacityAttrib(self, node, attr, value):
        try:
            node[attr] = min(1.0,max(0.0,float(val)))
        except ValueError:
            node[attr] = 1.0

    def dimensionAttrib(self, node, attr, value):
        node[attr] = self._parseUnit(value)

    def colorAttrib(self, node, attr, value):
        if value == 'inherit':
            return
        node[attr] = self._parseColor(value, node.get(attr))


    def transform(self, node, attr, val):
        # http://www.w3.org/TR/SVG11/coords.html#EstablishingANewUserSpace
        xforms = []
        matches = re.findall('(([a-z]+\s*)\(([^)]*)\))', val, re.IGNORECASE)
        # this parses  something like "translate(50,50), rotate(56)"" to
        # [('translate(50,50)', 'translate', '50,50'), ('rotate(56)', 'rotate', '56')]
        for match in matches:
            xformKind = match[1]
            params = parseFloats(match[2])

            # translate
            if (xformKind == 'translate') {
                if len(params) == 1:
                    xforms.append([1, 0, 0, 1, params[0], params[0]])
                elif len(params) == 2:
                    xforms.append([1, 0, 0, 1, params[0], params[1]])
                else:
                    logging.warn('translate skipped; invalid num of params')
            # rotate         
            elif xformKind == 'rotate':
                if len(params) == 3:
                    angle = params[0] * self.DEG_TO_RAD
                    xforms.append([1, 0, 0, 1, params[1], params[2]])
                    xforms.append([math.cos(angle), math.sin(angle), -math.sin(angle), math.cos(angle), 0, 0])
                    xforms.append([1, 0, 0, 1, -params[1], -params[2]])
                elif len(params) == 1:
                    angle = params[0] * self.DEG_TO_RAD
                    xforms.append([math.cos(angle), math.sin(angle), -math.sin(angle), math.cos(angle), 0, 0])
                else:
                    logging.warn('rotate skipped; invalid num of params')
            #scale       
            elif xformKind == 'scale':
                if len(params) == 1:
                    xforms.append([params[0], 0, 0, params[0], 0, 0])
                elif len(params) == 2:
                    xforms.append([params[0], 0, 0, params[1], 0, 0])
                else:
                    logging.warn('scale skipped; invalid num of params')
            # matrix
            elif xformKind == 'matrix':
                if len(params) == 6:
                    xforms.append(params)
            # skewX        
            elif xformKind == 'skewX':
                if len(params) == 1:
                    angle = params[0]*self.DEG_TO_RAD
                    xforms.append([1, 0, math.tan(angle), 1, 0, 0])
                else:
                    logging.warn('skewX skipped; invalid num of params')
            # skewY
            elif xformKind == 'skewY':
                if len(params) == 1:
                    angle = params[0]*self.DEG_TO_RAD
                    xforms.append([1, math.tan(angle), 0, 1, 0, 0])
                else:
                    logging.warn('skewY skipped; invalid num of params')

        #calculate combined transformation matrix
        xform_combined = [1,0,0,1,0,0]
        for xform in xforms:
            xform_combined = matrixMult(xform_combined, xform)
        
        # assign
        node.xform = xform_combined  


    def style(self, node, attr, val):
        # style attribute
        # http:#www.w3.org/TR/SVG11/styling.html#StyleAttribute
        # example: <rect x="200" y="100" width="600" height="300" 
        #          style="fill: red; stroke: blue; stroke-width: 3"/>
        
        # relay to parse style attributes the same as Presentation Attributes
        segs = val.split(";")
        for seg in segs:
            kv = seg.split(":")
            k = kv[0].strip()
            v = kv[1].strip()
            if k != 'style':  # prevent infinite loop
                self.readAttrib(node, k, v)
        # Also see: Presentations Attributes 
        # http://www.w3.org/TR/SVG11/styling.html#UsingPresentationAttributes
        # example: <rect x="200" y="100" width="600" height="300" 
        #          fill="red" stroke="blue" stroke-width="3"/>
    


    def _parseUnit(self, val):
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


    def _parseColor(val, currentColor):
        # http://www.w3.org/TR/2008/REC-CSS2-20080411/syndata.html#color-units
        if val[0] == '#':
            return hex_to_rgb(val)
        elif val.startswith('rgba'):
            floats = parseFloats(val[5:-1])
            if len(floats) != 4:
                logging.error("invalid color")
            else:
                logging.warn("opacity in rgba is ignored, \
                              use stroke-opacity/fill-opacity instead")
                return floats
        elif val.startswith('rgb'):
            floats = parseFloats(val[4:-1])
            if len(floats) != 3:
                logging.error("invalid color")
            else:
                return floats
        elif val.startswith('url'):
            logging.error("defs are not supported");
        elif val == 'currentColor':
            return currentColor
        elif val == 'none'
            logging.warn("color 'none' may be ignored")
            return None
        elif val == 'freeze': # SMIL is evil, but so are we
            logging.warn("color 'freeze' may be ignored")
            return None
        elif val == 'remove':
            logging.warn("color 'remove' may be ignored")
            return None
        elif css3_names_to_hex.has_key(val):  # named colors
            return hex_to_rgb(css3_names_to_hex[val])
        else:
            logging.error("invalid color")
            return None


