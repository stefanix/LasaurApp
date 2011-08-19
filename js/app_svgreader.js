

/**
  SVG parser for simple documents. Converts SVG DOM to CAKE scenegraph.
  Emphasis on graphical images, not on the "HTML-killer" features of SVG.

  var svgNode = SVGReader.parse(
    svgRootElement, filename, containerWidth, containerHeight, fontSize
  )

  Features:
    * <svg> width and height, viewBox clipping.
    * Clipping (objectBoundingBox clipping too)
    * Paths, rectangles, ellipses, circles, lines, polylines and polygons
    * Simple untransformed text using HTML
    * Nested transforms
    * Transform lists (transform="rotate(30) translate(2,2) scale(4)")
    * Gradient and pattern transforms
    * Strokes with miter, joins and caps
    * Flat fills and gradient fills, ditto for strokes
    * Parsing simple stylesheets (tag, class or id)
    * Images
    * Non-pixel units (cm, mm, in, pt, pc, em, ex, %)
    * <use>-tags
    * preserveAspectRatio
    * Dynamic gradient sizes (objectBoundingBox, etc.)
    * Markers (though buggy)

  Some of the several missing features:
    * Masks
    * Patterns
    * viewBox clipping for elements other than <marker> and <svg>
    * Text styling
    * tspan, tref, textPath, many things text
    * Fancy style rules (tag .class + #foo > bob#alice { ... })
    * Filters
    * Animation
    * Dashed strokes
  */
SVGReader = {
  
  /**
    Parses an SVG DOM into CAKE scenegraph.

    Config hash parameters:
      filename: Filename for the SVG document. Used for parsing image paths.
      width: Width of the bounding box to fit the SVG in.
      height: Height of the bounding box to fit the SVG in.
      fontSize: Default font size for the SVG document.
      currentColor: HTML text color of the containing element.

    @param svgstring a string representing a SVG document.
    @param config The config hash.
    @returns the boundarys of all the shapes.
    */
  
  node : {},  // node currently parsing
    
  parse : function(svgstring, config) {
    
    // parse xml
    var svgRootElement;
		if (window.DOMParser) {
			var parser = new DOMParser();
			svgRootElement = parser.parseFromString(svgstring, 'text/xml').documentElement;
		}
		else {
			xml = xml.replace(/<!DOCTYPE svg[^>]*>/, '');
			var xmlDoc = new ActiveXObject('Microsoft.XMLDOM');
			xmlDoc.async = 'false';
			xmlDoc.loadXML(svgstring); 
			svgRootElement = xmlDoc.documentElement;
		}
    
    var defs = {}
    var style = { ids : {}, classes : {}, tags : {} }
    this.parseChildren(svgRootElement, defs, style)
    n.defs = defs
    n.style = style
    return n
  },
  
  
  parseChildren : function(dom_node) {
    var childNodes = []
    for (var i=0; i<dom_node.childNodes.length; i++) {
      var c = dom_node.childNodes[i]
      if (c.childNodes) {
        if (c.tagName) {
          // we are looping here through 
          // all nodes with child nodes
          
          var node = {}
          
          if (c.attributes) {
            for (var j=0; j<c.attributes.length; j++) {
              var attr = c.attributes[j]
              if (this.SVGMapping[attr.nodeName])
                this.SVGMapping[attr.nodeName].call(attr.nodeValue)
            }
          }
                    
          if (this.SVGTagMapping[c.tagName]) {
            this.SVGTagMapping[c.tagName].call(this, c)
          }
          
          this.state.tagName = c.tagName
          this.applySVGTransform(c.getAttribute("transform"))  //FIX
          this.applySVGStyle(c.getAttribute("style"))          //FIX
        }
        
        // recursive call
        this.parseChildren(c, defs, style)
      }
    }
  },
  


  ///////////////////////////
  // recognized svg elements
  
  SVGTagMapping : {
    svg : function(c) {
      this.node.width = 0
      this.node.height = 0
      this.node.fill = 'black'
      this.node.stroke = 'none'
      
      
      var vb = c.getAttribute('viewBox')
      var w = c.getAttribute('width')
      var h = c.getAttribute('height')
      if (!w) w = h
      else if (!h) h = w
      if (w) {
        var wpx = this.parseUnit(w, cn, 'x')
        var hpx = this.parseUnit(h, cn, 'y')
      }
      if (vb) {
        xywh = vb.match(/[-+]?\d+/g).map(parseFloat)
        this.node.cx = xywh[0]
        this.node.cy = xywh[1]
        this.node.width = xywh[2]
        this.node.height = xywh[3]
        var iw = cn.innerWidth = this.node.width
        var ih = cn.innerHeight = this.node.height
        cn.innerSize = Math.sqrt(iw*iw + ih*ih) / Math.sqrt(2)
        if (c.getAttribute('overflow') != 'visible')
          this.node.clip = true
      }
      if (w) {
        if (vb) { // nuts, let's parse the alignment :|
          var aspect = c.getAttribute('preserveAspectRatio')
          var align = this.parsePreserveAspectRatio(aspect,
            wpx, hpx,
            this.node.width, this.node.height)
          this.node.cx -= align.x / align.w
          this.node.cy -= align.y / align.h
          this.node.width = wpx / align.w
          this.node.height = hpx / align.h
          this.node.x += align.x
          this.node.y += align.y
          this.node.scale = [align.w, align.h]
        }
        // wrong place!
        cn.docWidth = wpx
        cn.docHeight = hpx
      }
      return p
    },
    
    title : function(c) {
      this.node.title = c.textContent
    },

    desc : function(c) {
      this.node.description = c.textContent
    },

    metadata : function(c) {
      this.node.metadata = c
    },

    path : function(c) {
      this.node.path =  new Path(c.getAttribute("d"))
    },

    polygon : function(c) {
      this.node.path = new Polygon(c.getAttribute("points").toString().strip()
                          .split(/[\s,]+/).map(parseFloat))
    },

    polyline : function(c) {
      this.node.path = new Polygon(c.getAttribute("points").toString().strip()
                          .split(/[\s,]+/).map(parseFloat), {closePath:false})
    },

    rect : function(c, cn) {
      var p = new Rectangle(
        this.parseUnit(c.getAttribute('width'), cn, 'x'),
        this.parseUnit(c.getAttribute('height'), cn, 'y')
      )
      this.node.cx = this.parseUnit(c.getAttribute('x'), cn, 'x') || 0
      this.node.cy = this.parseUnit(c.getAttribute('y'), cn, 'y') || 0
      this.node.rx = this.parseUnit(c.getAttribute('rx'), cn, 'x') || 0
      this.node.ry = this.parseUnit(c.getAttribute('ry'), cn, 'y') || 0
      return p
    },

    line : function(c, cn) {
      var x1 = this.parseUnit(c.getAttribute('x1'), cn, 'x') || 0
      var y1 = this.parseUnit(c.getAttribute('y1'), cn, 'y') || 0
      var x2 = this.parseUnit(c.getAttribute('x2'), cn, 'x') || 0
      var y2 = this.parseUnit(c.getAttribute('y2'), cn, 'y') || 0
      var p = new Line(x1,y1, x2,y2)
      return p
    },

    circle : function(c, cn) {
      var p = new Circle(this.parseUnit(c.getAttribute('r'), cn) || 0)
      this.node.cx = this.parseUnit(c.getAttribute('cx'), cn, 'x') || 0
      this.node.cy = this.parseUnit(c.getAttribute('cy'), cn, 'y') || 0
      return p
    },

    ellipse : function(c, cn) {
      var p = new Ellipse(
        this.parseUnit(c.getAttribute('rx'), cn, 'x') || 0,
        this.parseUnit(c.getAttribute('ry'), cn, 'y') || 0
      )
      this.node.cx = this.parseUnit(c.getAttribute('cx'), cn, 'x') || 0
      this.node.cy = this.parseUnit(c.getAttribute('cy'), cn, 'y') || 0
      return p
    },

    text : function(c, cn) {
      if (false) {
        var p = new TextNode(c.textContent.strip())
        this.node.setAsPath(true)
        this.node.cx = this.parseUnit(c.getAttribute('x'),cn, 'x') || 0
        this.node.cy = this.parseUnit(c.getAttribute('y'),cn, 'y') || 0
        return p
      } else {
        var e = E('div', c.textContent.strip())
        e.style.marginTop = '-1em'
        e.style.whiteSpace = 'nowrap'
        var p = new ElementNode(e)
        this.node.xOffset = this.parseUnit(c.getAttribute('x'),cn, 'x') || 0
        this.node.yOffset = this.parseUnit(c.getAttribute('y'),cn, 'y') || 0
        return p
      }
    },

    style : function(c, cn, defs, style) {
      this.parseStyle(c, style)
    },

    defs : function(c, cn, defs, style) {
      return new CanvasNode({visible: false})
    }
  },

  // recognized svg elements
  ///////////////////////////



  /////////////////////////////
  // recognized svg attributes
  
  SVGMapping : {
    DEG_TO_RAD_FACTOR : Math.PI / 180,
    RAD_TO_DEG_FACTOR : 180 / Math.PI,

    parseUnit : function(v, cn, dir) {
      return SVGReader.parseUnit(v, cn, dir)
    },

    "class" : function(node, v) {
      node.className = v
    },

    "clip-path" : function(node, v, defs) {
      SVGReader.getDef(defs, v.replace(/^url\(#|\)$/g, ''), function(g) {
        node.clipPath = g
      })
    },

    id : function(node, v) {
      node.id = v
    },

    translate : function(node, v) {
      var xy = v.split(/[\s,]+/).map(parseFloat)
      node.transformList.push(['translate', [xy[0], xy[1] || 0]])
    },

    rotate : function(node, v) {
      if (v == 'auto' || v == 'auto-reverse') return
      var rot = v.split(/[\s,]+/).map(parseFloat)
      var angle = rot[0] * this.DEG_TO_RAD_FACTOR
      if (rot.length > 1)
        node.transformList.push(['rotate', [angle, rot[1], rot[2] || 0]])
      else
        node.transformList.push(['rotate', [angle]])
    },

    scale : function(node, v) {
      var xy = v.split(/[\s,]+/).map(parseFloat)
      var trans = ['scale']
      if (xy.length > 1)
        trans[1] = [xy[0], xy[1]]
      else
        trans[1] = [xy[0], xy[0]]
      node.transformList.push(trans)
    },

    matrix : function(node, v) {
      var mat = v.split(/[\s,]+/).map(parseFloat)
      node.transformList.push(['matrix', mat])
    },

    skewX : function(node, v) {
      var angle = parseFloat(v)*this.DEG_TO_RAD_FACTOR
      node.transformList.push(['skewX', [angle]])
    },

    skewY : function(node, v) {
      var angle = parseFloat(v)*this.DEG_TO_RAD_FACTOR
      node.transformList.push(['skewY', [angle]])
    },

    opacity : function(node, v) {
      node.opacity = parseFloat(v)
    },

    display : function (node, v) {
      node.display = v
    },

    visibility : function (node, v) {
      node.visibility = v
    },

    'stroke-miterlimit' : function(node, v) {
      node.miterLimit = parseFloat(v)
    },

    'stroke-linecap' : function(node, v) {
      node.lineCap = v
    },

    'stroke-linejoin' : function(node, v) {
      node.lineJoin = v
    },

    'stroke-width' : function(node, v) {
      node.strokeWidth = this.parseUnit(v, node)
    },

    fill : function(node, v, defs, style) {
      node.fill = this.__parseStyle(v, node.fill, defs, node.color)
    },

    stroke : function(node, v, defs, style) {
      node.stroke = this.__parseStyle(v, node.stroke, defs, node.color)
    },

    color : function(node, v, defs, style) {
      if (v == 'inherit') return
      node.color = this.__parseStyle(v, false, defs, node.color)
    },

    'stop-color' : function(node, v, defs, style) {
      if (v == 'none') {
        node[1] = [0,0,0,0]
      } else {
        node[1] = this.__parseStyle(v, node[1], defs, node.color)
      }
    },

    'fill-opacity' : function(node, v) {
      node.fillOpacity = Math.min(1,Math.max(0,parseFloat(v)))
    },

    'stroke-opacity' : function(node, v) {
      node.strokeOpacity = Math.min(1,Math.max(0,parseFloat(v)))
    },

    'stop-opacity' : function(node, v) {
      node[1] = node[1] || [0,0,0]
      node[1][3] = Math.min(1,Math.max(0,parseFloat(v)))
    },

    'text-anchor' : function(node, v) {
      node.textAnchor = v
      if (node.setAlign) {
        if (v == 'middle')
          node.setAlign('center')
        else
          node.setAlign(v)
      }
    },

    'font-family' : function(node, v) {
      node.fontFamily = v
    },

    'font-size' : function(node, v) {
      node.fontSize = this.parseUnit(v, node)
    },

    __parseStyle : function(v, currentStyle, defs, currentColor) {

      if (v.charAt(0) == '#') {
        if (v.length == 4)
          v = v.replace(/([^#])/g, '$1$1')
        var a = v.slice(1).match(/../g).map(
          function(i) { return parseInt(i, 16) })
        return a

      } else if (v.search(/^rgb\(/) != -1) {
        var a = v.slice(4,-1).split(",")
        for (var i=0; i<a.length; i++) {
          var c = a[i].strip()
          if (c.charAt(c.length-1) == '%')
            a[i] = Math.round(parseFloat(c.slice(0,-1)) * 2.55)
          else
            a[i] = parseInt(c)
        }
        return a

      } else if (v.search(/^rgba\(/) != -1) {
        var a = v.slice(5,-1).split(",")
        for (var i=0; i<3; i++) {
          var c = a[i].strip()
          if (c.charAt(c.length-1) == '%')
            a[i] = Math.round(parseFloat(c.slice(0,-1)) * 2.55)
          else
            a[i] = parseInt(c)
        }
        var c = a[3].strip()
        if (c.charAt(c.length-1) == '%')
          a[3] = Math.round(parseFloat(c.slice(0,-1)) * 0.01)
        else
          a[3] = Math.max(0, Math.min(1, parseFloat(c)))
        return a

      } else if (v.search(/^url\(/) != -1) {
        var id = v.match(/\([^)]+\)/)[0].slice(1,-1).replace(/^#/, '')
        if (defs[id]) {
          return defs[id]
        } else { // missing defs, let's make it known that we're screwed
          return 'rgba(255,0,255,1)'
        }

      } else if (v == 'currentColor') {
        return currentColor

      } else if (v == 'none') {
        return 'none'

      } else if (v == 'freeze') { // SMIL is evil, but so are we
        return null

      } else if (v == 'remove') {
        return null

      } else { // unknown value, maybe it's an ICC color
        return v
      }
    }
  },
  
  // recognized svg attributes
  /////////////////////////////
  


  parseStyle : function(node, style) {
    var text = node.textContent
    var segs = text.split(/\}/m)
    for (var i=0; i<segs.length; i++) {
      var seg = segs[i]
      var kv = seg.split(/\{/m)
      if (kv.length < 2) continue
      var key = kv[0].strip()
      var value = kv[1].strip()
      switch (key.charAt(0)) {
        case '.':
          style.classes[key.slice(1)] = value
          break;
        case '#':
          style.ids[key.slice(1)] = value
          break;
        default:
          style.tags[key] = value
          break;
      }
    }
  },

  parseStops : function(g, node, defs, style) {
    var href = node.getAttribute('xlink:href')
    g.colorStops = []
    if (href) {
      href = href.replace(/^#/,'')
      this.getDef(defs, href, function(g2) {
        if (g.colorStops.length == 0)
          g.colorStops = g2.colorStops
      })
    }
    var stops = []
    for (var i=0; i<node.childNodes.length; i++) {
      var c = node.childNodes[i]
      if (c.tagName == 'stop') {
        var offset = parseFloat(c.getAttribute('offset'))
        if (c.getAttribute('offset').search(/%/) != -1)
          offset *= 0.01
        var stop = [offset]
        stop.color = g.color
        for (var j=0; j<c.attributes.length; j++) {
          var attr = c.attributes[j]
          if (this.SVGMapping[attr.nodeName])
            this.SVGMapping[attr.nodeName](stop, attr.nodeValue, defs, style)
        }
        this.applySVGStyle(stop, c.getAttribute('style'), defs, style)
        var id = c.getAttribute('id')
        if (id) this.setDef(defs, id, stop)
        stops.push(stop)
      }
    }
    if (stops.length > 0)
      g.colorStops = stops
  },

  applySVGTransform : function(node, transform, defs, style) {
    if (!transform) return
    node.transformList = []
    var segs = transform.match(/[a-z]+\s*\([^)]*\)/ig)
    for (var i=0; i<segs.length; i++) {
      var kv = segs[i].split("(")
      var k = kv[0].strip()
      if (this.SVGMapping[k]) {
        var v = kv[1].strip().slice(0,-1)
        this.SVGMapping[k](node, v, defs, style)
      }
    }
    this.breakDownTransformList(node)
  },

  breakDownTransformList : function(node) {
    var tl = node.transformList
    if (node.transformList.length == 1) {
      var tr = tl[0]
      if (tr[0] == 'translate') {
        node.x = tr[1][0]
        node.y = tr[1][1]
      } else if (tr[0] == 'scale') {
        node.scale = tr[1]
      } else if (tr[0] == 'rotate') {
        node.rotation = tr[1]
      } else if (tr[0] == 'matrix') {
        node.matrix = tr[1]
      } else if (tr[0] == 'skewX') {
        node.skewX = tr[1][0]
      } else if (tr[0] == 'skewY') {
        node.skewY = tr[1][0]
      } else {
        return
      }
      node.transformList = null
    }
  },

  applySVGStyle : function(style, defs, st) {
    if (!style) return
    var segs = style.split(";")
    for (var i=0; i<segs.length; i++) {
      var kv = segs[i].split(":")
      var k = kv[0].strip()
      if (this.SVGMapping[k]) {
        var v = kv[1].strip()
        this.SVGMapping[k].call(v, defs, st)
      }
    }
  },

  getDef : function(defs, id, f) {
    if (defs[id] && defs[id] instanceof Array) {
      defs[id].push(f)
    } else if (defs[id]) {
      f(defs[id])
    } else {
      defs[id] = [f]
    }
  },

  setDef : function(defs, id, obj) {
    if (defs[id] && defs[id] instanceof Array) {
      for (var i=0; i<defs[id].length; i++) {
        defs[id][i](obj)
      }
    }
    // should here be an "else"? /stefan
    defs[id] = obj
  },

  parseUnit : function(v, parent, dir) {
    if (v == null) {
      return null
    } else {
      return this.parseUnitMultiplier(v, parent, dir) * parseFloat(v.strip())
    }
  },

  parseUnitMultiplier : function(str, parent, dir) {
    var cm = this.getCmInPixels()
    if (str.search(/cm$/i) != -1)
      return cm
    else if (str.search(/mm$/i) != -1)
      return 0.1 * cm
    else if (str.search(/pt$/i) != -1)
      return 0.0352777778 * cm
    else if (str.search(/pc$/i) != -1)
      return 0.4233333333 * cm
    else if (str.search(/in$/i) != -1)
      return 2.54 * cm
    else if (str.search(/em$/i) != -1)
      return parent.fontSize
    else if (str.search(/ex$/i) != -1)
      return parent.fontSize / 2
    else if (str.search(/%$/i) != -1)
      if (dir == 'x')
        return parent.root.innerWidth * 0.01
      else if (dir == 'y')
        return parent.root.innerHeight * 0.01
      else
        return parent.root.innerSize * 0.01
    else
      return 1
  },

  getCmInPixels : function() {
    if (!this.cmInPixels) {
      var e = E('div',{ style: {
        margin: '0px',
        padding: '0px',
        width: '1cm',
        height: '1cm',
        position: 'absolute',
        visibility: 'hidden'
      }})
      document.body.appendChild(e)
      var cm = e.offsetWidth
      document.body.removeChild(e)
      this.cmInPixels = cm || 38
    }
    return this.cmInPixels
  },

  getEmInPixels : function() {
    if (!this.emInPixels) {
      var e = E('div',{ style: {
        margin: '0px',
        padding: '0px',
        width: '1em',
        height: '1em',
        position: 'absolute',
        visibility: 'hidden'
      }})
      document.body.appendChild(e)
      var em = e.offsetWidth
      document.body.removeChild(e)
      this.emInPixels = em || 12
    }
    return this.emInPixels
  },

  getExInPixels : function() {
    if (!this.exInPixels) {
      var e = E('div',{ style: {
        margin: '0px',
        padding: '0px',
        width: '1ex',
        height: '1ex',
        position: 'absolute',
        visibility: 'hidden'
      }})
      document.body.appendChild(e)
      var ex = e.offsetWidth
      document.body.removeChild(e)
      this.exInPixels = ex || 6
    }
    return this.exInPixels
  },
  
  
  parsePreserveAspectRatio : function(aspect, w, h, vpw, vph) {
    var aspect = aspect || ""
    var aspa = aspect.split(/\s+/)
    var defer = (aspa[0] == 'defer')
    if (defer) aspa.shift()
    var align = (aspa[0] || 'xMidYMid')
    var meet = (aspa[1] || 'meet')
    var wf = w / vpw
    var hf = h / vph
    var xywh = {x:0, y:0, w:wf, h:hf}
    if (align == 'none') return xywh
    xywh.w = xywh.h = (meet == 'meet' ? Math.min : Math.max)(wf, hf)
    var xa = align.slice(1, 4).toLowerCase()
    var ya = align.slice(5, 8).toLowerCase()
    var xf = (this.SVGAlignMap[xa] || 0)
    var yf = (this.SVGAlignMap[ya] || 0)
    xywh.x = xf * (w-vpw*xywh.w)
    xywh.y = yf * (h-vph*xywh.h)
    return xywh
  },

  SVGAlignMap : {
    min : 0,
    mid : 0.5,
    max : 1
  }

}





/**
  Path is used for creating custom paths.

  Attributes: segments, closePath.

    var path = new Path([
      ['moveTo', [-50, -60]],
      ['lineTo', [30, 50],
      ['lineTo', [-50, 50]],
      ['bezierCurveTo', [-50, 100, -50, 100, 0, 100]],
      ['quadraticCurveTo', [0, 120, -20, 130]],
      ['quadraticCurveTo', [0, 140, 0, 160]],
      ['bezierCurveTo', [-10, 160, -20, 170, -30, 180]],
      ['quadraticCurveTo', [10, 230, -50, 260]]
    ])

  The path segments are used as [methodName, arguments] on the canvas
  drawing context, so the possible path segments are:

    ['moveTo', [x, y]]
    ['lineTo', [x, y]]
    ['quadraticCurveTo', [control_point_x, control_point_y, x, y]]
    ['bezierCurveTo', [cp1x, cp1y, cp2x, cp2y, x, y]]
    ['arc', [x, y, radius, startAngle, endAngle, drawClockwise]]
    ['arcTo', [x1, y1, x2, y2, radius]]
    ['rect', [x, y, width, height]]

  You can also pass an SVG path string as segments.

    var path = new Path("M 100 100 L 300 100 L 200 300 z", {
      stroke: true, strokeStyle: 'blue',
      fill: true, fillStyle: 'red',
      lineWidth: 3
    })

  @param segments The path segments.
  @param config Optional config hash.
  */
Path = {
  segments : [],
  closePath : false,

  /**
    Creates a path on the given drawing context.

    For each path segment, calls the context method named in the first element
    of the segment with the rest of the segment elements as arguments.

    SVG paths are parsed and executed.

    Closes the path if closePath is true.

    @param ctx Canvas drawing context.
    */
  drawGeometry : function(ctx) {
    var segments = this.getSegments()
    for (var i=0; i<segments.length; i++) {
      var seg = segments[i]
      ctx[seg[0]].apply(ctx, seg[1])
    }
    if (this.closePath)
      ctx.closePath()
  },

  /**
    Returns true if the point x,y is inside the path's bounding rectangle.

    The x,y point is in user-space coordinates, meaning that e.g. the point
    5,5 will always be inside the rectangle [0, 0, 10, 10], regardless of the
    transform on the rectangle.

    @param px X-coordinate of the point.
    @param py Y-coordinate of the point.
    @return Whether the point is inside the path's bounding rectangle.
    @type boolean
    */
  isPointInPath : function(px,py) {
    var bbox = this.getBoundingBox()
    return (px >= bbox[0] && px <= bbox[0]+bbox[2] &&
            py >= bbox[1] && py <= bbox[1]+bbox[3])
  },

  getBoundingBox : function() {
    if (!(this.compiled && this.compiledBoundingBox)) {
      var minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity
      var segments = this.getSegments()
      for (var i=0; i<segments.length; i++) {
        var seg = segments[i][1]
        for (var j=0; j<seg.length; j+=2) {
          var x = seg[j], y = seg[j+1]
          if (x < minX) minX = x
          if (x > maxX) maxX = x
          if (y < minY) minY = y
          if (y > maxY) maxY = y
        }
      }
      this.compiledBoundingBox = [minX, minY, maxX-minX, maxY-minY]
    }
    return this.compiledBoundingBox
  },

  getStartPoint : function() {
    var segs = this.getSegments()
    if (!segs || !segs[0]) return {point: [0,0], angle: 0}
    var fs = segs[0]
    var c = fs[1]
    var point = [c[c.length-2], c[c.length-1]]
    var ss = segs[1]
    var angle = 0
    if (ss) {
      c2 = ss[1]
      angle = Curves.lineAngle(point, [c2[c2.length-2], c2[c2.length-1]])
    }
    return {
      point: point,
      angle: angle
    }
  },

  getEndPoint : function() {
    var segs = this.getSegments()
    if (!segs || !segs[0]) return {point: [0,0], angle: 0}
    var fs = segs[segs.length-1]
    var c = fs[1]
    var point = [c[c.length-2], c[c.length-1]]
    var ss = segs[segs.length-2]
    var angle = 0
    if (ss) {
      c2 = ss[1]
      angle = Curves.lineAngle([c2[c2.length-2], c2[c2.length-1]], point)
    }
    return {
      point: point,
      angle: angle
    }
  },

  getMidPoints : function() {
    var segs = this.getSegments()
    if (this.vertices)
      return this.vertices.slice(1,-1)
    var verts = []
    for (var i=1; i<segs.length-1; i++) {
      var b = segs[i-1][1].slice(-2)
      var c = segs[i][1].slice(0,2)
      if (segs[i-1].length > 2) {
        var a = segs[i-1][1].slice(-4,-2)
        var t = 0.5 * (Curves.lineAngle(a,b) + Curves.lineAngle(b,c))
      } else {
        var t = Curves.lineAngle(b,c)
      }
      verts.push(
        {point: b, angle: t}
      )
      var id = segs[i][2]
      if (id != null) {
        i++
        while (segs[i] && segs[i][2] == id) i++
        i--
      }
    }
    return verts
  },

  getSegments : function() {
    if (typeof(this.segments) == 'string') {
      if (!this.compiled || this.segments != this.compiledSegments) {
        this.compiled = this.compileSVGPath(this.segments)
        this.compiledSegments = this.segments
      }
    } else if (!this.compiled) {
      this.compiled = Object.clone(this.segments)
    }
    return this.compiled
  },

  /**
    Compiles an SVG path string into an array of canvas context method calls.

    Returns an array of [methodName, [arg1, arg2, ...]] method call arrays.
    */
  compileSVGPath : function(svgPath) {
    var segs = svgPath.split(/(?=[a-z])/i)
    var x = 0
    var y = 0
    var px,py
    var pc
    var commands = []
    for (var i=0; i<segs.length; i++) {
      var seg = segs[i]
      var cmd = seg.match(/[a-z]/i)
      if (!cmd) return [];
      cmd = cmd[0];
      var coords = seg.match(/[+-]?\d+(\.\d+(e\d+(\.\d+)?)?)?/gi)
      if (coords) coords = coords.map(parseFloat)
      switch(cmd) {
        case 'M':
          x = coords[0]
          y = coords[1]
          px = py = null
          commands.push(['moveTo', [x, y]])
          break
        case 'm':
          x += coords[0]
          y += coords[1]
          px = py = null
          commands.push(['moveTo', [x, y]])
          break

        case 'L':
          x = coords[0]
          y = coords[1]
          px = py = null
          commands.push(['lineTo', [x, y]])
          break
        case 'l':
          x += coords[0]
          y += coords[1]
          px = py = null
          commands.push(['lineTo', [x, y]])
          break
        case 'H':
          x = coords[0]
          px = py = null
          commands.push(['lineTo', [x, y]])
          break
        case 'h':
          x += coords[0]
          px = py = null
          commands.push(['lineTo', [x,y]])
          break
        case 'V':
          y = coords[0]
          px = py = null
          commands.push(['lineTo', [x,y]])
          break
        case 'v':
          y += coords[0]
          px = py = null
          commands.push(['lineTo', [x,y]])
          break

        case 'C':
          x = coords[4]
          y = coords[5]
          px = coords[2]
          py = coords[3]
          commands.push(['bezierCurveTo', coords])
          break
        case 'c':
          commands.push(['bezierCurveTo',[
            coords[0] + x, coords[1] + y,
            coords[2] + x, coords[3] + y,
            coords[4] + x, coords[5] + y
          ]])
          px = x + coords[2]
          py = y + coords[3]
          x += coords[4]
          y += coords[5]
          break

        case 'S':
          if (px == null || !pc.match(/[sc]/i)) {
            px = x
            py = y
          }
          commands.push(['bezierCurveTo',[
            x-(px-x), y-(py-y),
            coords[0], coords[1],
            coords[2], coords[3]
          ]])
          px = coords[0]
          py = coords[1]
          x = coords[2]
          y = coords[3]
          break
        case 's':
          if (px == null || !pc.match(/[sc]/i)) {
            px = x
            py = y
          }
          commands.push(['bezierCurveTo',[
            x-(px-x), y-(py-y),
            x + coords[0], y + coords[1],
            x + coords[2], y + coords[3]
          ]])
          px = x + coords[0]
          py = y + coords[1]
          x += coords[2]
          y += coords[3]
          break

        case 'Q':
          px = coords[0]
          py = coords[1]
          x = coords[2]
          y = coords[3]
          commands.push(['quadraticCurveTo', coords])
          break
        case 'q':
          commands.push(['quadraticCurveTo',[
            coords[0] + x, coords[1] + y,
            coords[2] + x, coords[3] + y
          ]])
          px = x + coords[0]
          py = y + coords[1]
          x += coords[2]
          y += coords[3]
          break

        case 'T':
          if (px == null || !pc.match(/[qt]/i)) {
            px = x
            py = y
          } else {
            px = x-(px-x)
            py = y-(py-y)
          }
          commands.push(['quadraticCurveTo',[
            px, py,
            coords[0], coords[1]
          ]])
          px = x-(px-x)
          py = y-(py-y)
          x = coords[0]
          y = coords[1]
          break
        case 't':
          if (px == null || !pc.match(/[qt]/i)) {
            px = x
            py = y
          } else {
            px = x-(px-x)
            py = y-(py-y)
          }
          commands.push(['quadraticCurveTo',[
            px, py,
            x + coords[0], y + coords[1]
          ]])
          x += coords[0]
          y += coords[1]
          break

        case 'A':
          var arc_segs = this.solveArc(x,y, coords)
          for (var l=0; l<arc_segs.length; l++) arc_segs[l][2] = i
          commands.push.apply(commands, arc_segs)
          x = coords[5]
          y = coords[6]
          break
        case 'a':
          coords[5] += x
          coords[6] += y
          var arc_segs = this.solveArc(x,y, coords)
          for (var l=0; l<arc_segs.length; l++) arc_segs[l][2] = i
          commands.push.apply(commands, arc_segs)
          x = coords[5]
          y = coords[6]
          break

        case 'Z':
          commands.push(['closePath', []])
          break
        case 'z':
          commands.push(['closePath', []])
          break
      }
      pc = cmd
    }
    return commands
  },

  solveArc : function(x, y, coords) {
    var rx = coords[0]
    var ry = coords[1]
    var rot = coords[2]
    var large = coords[3]
    var sweep = coords[4]
    var ex = coords[5]
    var ey = coords[6]
    var segs = this.arcToSegments(ex, ey, rx, ry, large, sweep, rot, x, y)
    var retval = []
    for (var i=0; i<segs.length; i++) {
      retval.push(['bezierCurveTo', this.segmentToBezier.apply(this, segs[i])])
    }
    return retval
  },


  // Copied from Inkscape svgtopdf, thanks!
  arcToSegments : function(x, y, rx, ry, large, sweep, rotateX, ox, oy) {
    var th = rotateX * (Math.PI/180)
    var sin_th = Math.sin(th)
    var cos_th = Math.cos(th)
    rx = Math.abs(rx)
    ry = Math.abs(ry)
    var px = cos_th * (ox - x) * 0.5 + sin_th * (oy - y) * 0.5
    var py = cos_th * (oy - y) * 0.5 - sin_th * (ox - x) * 0.5
    var pl = (px*px) / (rx*rx) + (py*py) / (ry*ry)
    if (pl > 1) {
      pl = Math.sqrt(pl)
      rx *= pl
      ry *= pl
    }

    var a00 = cos_th / rx
    var a01 = sin_th / rx
    var a10 = (-sin_th) / ry
    var a11 = (cos_th) / ry
    var x0 = a00 * ox + a01 * oy
    var y0 = a10 * ox + a11 * oy
    var x1 = a00 * x + a01 * y
    var y1 = a10 * x + a11 * y

    var d = (x1-x0) * (x1-x0) + (y1-y0) * (y1-y0)
    var sfactor_sq = 1 / d - 0.25
    if (sfactor_sq < 0) sfactor_sq = 0
    var sfactor = Math.sqrt(sfactor_sq)
    if (sweep == large) sfactor = -sfactor
    var xc = 0.5 * (x0 + x1) - sfactor * (y1-y0)
    var yc = 0.5 * (y0 + y1) + sfactor * (x1-x0)

    var th0 = Math.atan2(y0-yc, x0-xc)
    var th1 = Math.atan2(y1-yc, x1-xc)

    var th_arc = th1-th0
    if (th_arc < 0 && sweep == 1){
      th_arc += 2*Math.PI
    } else if (th_arc > 0 && sweep == 0) {
      th_arc -= 2 * Math.PI
    }

    var segments = Math.ceil(Math.abs(th_arc / (Math.PI * 0.5 + 0.001)))
    var result = []
    for (var i=0; i<segments; i++) {
      var th2 = th0 + i * th_arc / segments
      var th3 = th0 + (i+1) * th_arc / segments
      result[i] = [xc, yc, th2, th3, rx, ry, sin_th, cos_th]
    }

    return result
  },

  segmentToBezier : function(cx, cy, th0, th1, rx, ry, sin_th, cos_th) {
    var a00 = cos_th * rx
    var a01 = -sin_th * ry
    var a10 = sin_th * rx
    var a11 = cos_th * ry

    var th_half = 0.5 * (th1 - th0)
    var t = (8/3) * Math.sin(th_half * 0.5) * Math.sin(th_half * 0.5) / Math.sin(th_half)
    var x1 = cx + Math.cos(th0) - t * Math.sin(th0)
    var y1 = cy + Math.sin(th0) + t * Math.cos(th0)
    var x3 = cx + Math.cos(th1)
    var y3 = cy + Math.sin(th1)
    var x2 = x3 + t * Math.sin(th1)
    var y2 = y3 - t * Math.cos(th1)
    return [
      a00 * x1 + a01 * y1,      a10 * x1 + a11 * y1,
      a00 * x2 + a01 * y2,      a10 * x2 + a11 * y2,
      a00 * x3 + a01 * y3,      a10 * x3 + a11 * y3
    ]
  },

  getLength : function() {
    var segs = this.getSegments()
    if (segs.arcLength == null) {
      segs.arcLength = 0
      var x=0, y=0
      for (var i=0; i<segs.length; i++) {
        var args = segs[i][1]
        if (args.length < 2) continue
        switch(segs[i][0]) {
          case 'bezierCurveTo':
            segs[i][3] = Curves.cubicLength(
              [x, y], [args[0], args[1]], [args[2], args[3]], [args[4], args[5]])
            break
          case 'quadraticCurveTo':
            segs[i][3] = Curves.quadraticLength(
              [x, y], [args[0], args[1]], [args[2], args[3]])
            break
          case 'lineTo':
            segs[i][3] = Curves.lineLength(
              [x, y], [args[0], args[1]])
            break
        }
        if (segs[i][3])
          segs.arcLength += segs[i][3]
        x = args[args.length-2]
        y = args[args.length-1]
      }
    }
    return segs.arcLength
  },

  pointAngleAt : function(t, config) {
    var segments = []
    var segs = this.getSegments()
    var length = this.getLength()
    var x = 0, y = 0
    for (var i=0; i<segs.length; i++) {
      var seg = segs[i]
      if (seg[1].length < 2) continue
      if (seg[0] != 'moveTo') {
        segments.push([x, y, seg])
      }
      x = seg[1][seg[1].length-2]
      y = seg[1][seg[1].length-1]
    }
    if (segments.length < 1)
      return {point: [x, y], angle: 0 }
    if (t >= 1) {
      var rt = 1
      var seg = segments[segments.length-1]
    } else if (config && config.discrete) {
      var idx = Math.floor(t * segments.length)
      var seg = segments[idx]
      var rt = 0
    } else if (config && config.linear) {
      var idx = t * segments.length
      var rt = idx - Math.floor(idx)
      var seg = segments[Math.floor(idx)]
    } else {
      var len = t * length
      var rlen = 0, idx, rt
      for (var i=0; i<segments.length; i++) {
        if (rlen + segments[i][2][3] > len) {
          idx = i
          rt = (len - rlen) / segments[i][2][3]
          break
        }
        rlen += segments[i][2][3]
      }
      var seg = segments[idx]
    }
    var angle = 0
    var cmd = seg[2][0]
    var args = seg[2][1]
    switch (cmd) {
      case 'bezierCurveTo':
        return Curves.cubicLengthPointAngle([seg[0], seg[1]], [args[0], args[1]], [args[2], args[3]], [args[4], args[5]], rt)
        break
      case 'quadraticCurveTo':
        return Curves.quadraticLengthPointAngle([seg[0], seg[1]], [args[0], args[1]], [args[2], args[3]], rt)
        break
      case 'lineTo':
        x = Curves.linearValue(seg[0], args[0], rt)
        y = Curves.linearValue(seg[1], args[1], rt)
        angle = Curves.lineAngle([seg[0], seg[1]], [args[0], args[1]], rt)
        break
    }
    return {point: [x, y], angle: angle }
  }

})
