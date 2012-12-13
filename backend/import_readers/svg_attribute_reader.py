
import math
import re
import logging



class SVGAttributeReaderClass:
    DEG_TO_RAD : Math.PI / 180,
    RAD_TO_DEG : 180 / Math.PI,

    id : function(parser, node, val) {
        node.id = val
    },   

    transform : function(parser, node, val) {
        // http://www.w3.org/TR/SVG11/coords.html#EstablishingANewUserSpace
        xforms = []
        segs = val.match(/[a-z]+\s*\([^)]*\)/ig)
        for (i=0; i<segs.length; i++) {
            kv = segs[i].split("(");
            xformKind = kv[0].strip();
            paramsTemp = kv[1].strip().slice(0,-1);
            params = paramsTemp.split(/[\s,]+/).map(parseFloat)
            // double check params
            for (j=0; j<params.length; j++) {
                if ( isNaN(params[j]) ) {
                    $().uxmessage('warning', 'transform skipped; contains non-numbers');
                    continue  // skip this transform
                }
            }
            
            // translate
            if (xformKind == 'translate') {
                if (params.length == 1) {
                    xforms.append([1, 0, 0, 1, params[0], params[0]])
                } else if (params.length == 2) {
                    xforms.append([1, 0, 0, 1, params[0], params[1]])
                } else {
                    $().uxmessage('warning', 'translate skipped; invalid num of params');
                }
            // rotate         
            } else if (xformKind == 'rotate') {
                if (params.length == 3) {
                    angle = params[0] * this.DEG_TO_RAD
                    xforms.append([1, 0, 0, 1, params[1], params[2]])
                    xforms.append([Math.cos(angle), Math.sin(angle), -Math.sin(angle), Math.cos(angle), 0, 0])
                    xforms.append([1, 0, 0, 1, -params[1], -params[2]])
                } else if (params.length == 1) {
                    angle = params[0] * this.DEG_TO_RAD
                    xforms.append([Math.cos(angle), Math.sin(angle), -Math.sin(angle), Math.cos(angle), 0, 0])
                } else {
                    $().uxmessage('warning', 'rotate skipped; invalid num of params');
                }
            //scale       
            } else if (xformKind == 'scale') {
                if (params.length == 1) {
                    xforms.append([params[0], 0, 0, params[0], 0, 0])
                } else if (params.length == 2) {
                    xforms.append([params[0], 0, 0, params[1], 0, 0])
                } else {
                    $().uxmessage('warning', 'scale skipped; invalid num of params');
                }
            // matrix
            } else if (xformKind == 'matrix') {
                if (params.length == 6) {
                    xforms.append(params)
                }
            // skewX        
            } else if (xformKind == 'skewX') {
                if (params.length == 1) {
                    angle = params[0]*this.DEG_TO_RAD
                    xforms.append([1, 0, Math.tan(angle), 1, 0, 0])
                } else {
                    $().uxmessage('warning', 'skewX skipped; invalid num of params');
                }
            // skewY
            } else if (xformKind == 'skewY') {
                if (params.length == 1) {
                    angle = params[0]*this.DEG_TO_RAD
                    xforms.append([1, Math.tan(angle), 0, 1, 0, 0])
                } else {
                    $().uxmessage('warning', 'skewY skipped; invalid num of params');
                }
            }
        }

        //calculate combined transformation matrix
        xform_combined = [1,0,0,1,0,0]
        for (i=0; i<xforms.length; i++) {
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
        segs = val.split(";")
        for (i=0; i<segs.length; i++) {
            kv = segs[i].split(":")
            k = kv[0].strip()
            if (this[k]) {
                v = kv[1].strip()
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
            a = val.slice(1).match(/../g).map(
                function(i) { return parseInt(i, 16) })
            return a

        } else if (val.search(/^rgb\(/) != -1) {
            a = val.slice(4,-1).split(",")
            for (i=0; i<a.length; i++) {
                c = a[i].strip()
                if (c.charAt(c.length-1) == '%')
                    a[i] = Math.round(parseFloat(c.slice(0,-1)) * 2.55)
                else
                    a[i] = parseInt(c)
            }
            return a

        } else if (val.search(/^rgba\(/) != -1) {
            a = val.slice(5,-1).split(",")
            for (i=0; i<3; i++) {
                c = a[i].strip()
                if (c.charAt(c.length-1) == '%')
                    a[i] = Math.round(parseFloat(c.slice(0,-1)) * 2.55)
                else
                    a[i] = parseInt(c)
            }
            c = a[3].strip()
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

# singelton
svgAttributeReader = SVGAttributeReaderClass()


