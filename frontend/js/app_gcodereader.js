
//TODO: 
// bbox account for arcs (G2, G3)
// not an issue for svg import but
// is gcode with arcs is copy&pasted

GcodeReader = {

  // x1,y1
  //   +-------------+ 
  //   |             |
  //   |             |
  //   +-------------+
  //               x2,y2
  //bbox : [x1, y1, x2, y2],
  bbox : undefined,
  moves_by_color : {},
  exclude_colors : {},
  canvas : null,


  ///////////////////////////////////////////////
  // Parsing

  addParse : function (gcode, scale) {
  
    function parseGArgs(str) {
      var ret = {};
      var pos;
      pos = str.indexOf('X');
      if (pos != -1) {
        ret.X = parseFloat(str.slice(pos+1));
      }
      pos = str.indexOf('Y');
      if (pos != -1) {
        ret.Y = parseFloat(str.slice(pos+1));
      }
      pos = str.indexOf('I');
      if (pos != -1) {
        ret.I = parseFloat(str.slice(pos+1));
      }
      pos = str.indexOf('J');
      if (pos != -1) {
        ret.J = parseFloat(str.slice(pos+1));
      }
      pos = str.indexOf('F');
      if (pos != -1) {
        ret.F = parseFloat(str.slice(pos+1));
      }
      return ret;
    };
  
  
    //// parse gcode
    var moves = this.moves_by_color['000000'];
    var lastG0 = undefined;
    var lines = gcode.split("\n");
    var currentX = 0.0;
    var currentY = 0.0;
    var currentI = 0.0;
    var currentJ = 0.0;
    var currentF = 0.0;
    for (var i=0; i<lines.length; i++) {
      var line = lines[i];
      line.replace(' ', '');  // throw out any spaces
      if (line[0] == 'G') {
        var gnum = parseFloat(line.slice(1));
        if (gnum == 0 || gnum == 1 || gnum  == 2 || gnum == 3) { 
          // we have a move line
          var args = parseGArgs(line.slice(2));
          if ('X' in args) { currentX = args.X*scale; }
          if ('Y' in args) { currentY = args.Y*scale; }
          if ('I' in args) { currentI = args.I*scale; }
          if ('J' in args) { currentJ = args.J*scale; }
          if ('F' in args) { currentF = args.F; } else { currentF = null; }
          moves.push( {'type':gnum, 'X':currentX, 'Y':currentY, 'I':currentI, 'J':currentJ, 'F':currentF } );
          //// bbox
          if (gnum == 0 && ('X' in args || 'Y' in args)) {
            lastG0 = [currentX, currentY];
          } else if (gnum == 1  && ('X' in args || 'Y' in args)) {
            if (typeof(lastG0) != 'undefined') {
              // add a G0 only when followed by a G1
              this.bboxExpand(lastG0[0], lastG0[1]);
              lastG0 = undefined;
            }
            this.bboxExpand(currentX, currentY);
          }
        }
      } else if (line[0] == 'T') {  // e.g: T1 P#ffffff
        var rest = line.slice(1);
        // parse P param
        pos = rest.indexOf('P');
        if (pos != -1) {
          hexcolor = rest.slice(pos+2, pos+8);
          if (hexcolor.length == 6) {
            if (!(hexcolor in this.moves_by_color)) {
              this.moves_by_color[hexcolor] = [];
            }
            moves = this.moves_by_color[hexcolor];
          } 
        }
      }
    }

    // cleanup default color if nothing is in it
    if (this.moves_by_color['000000'].length == 0) {
      delete this.moves_by_color['000000'];
    } else {
    }
  },

  clear : function(){
    this.moves_by_color = {};
    this.moves_by_color['000000'] = [];  // default color
    this.bboxClear();
  },

  isEmpty : function() {
    for(var prop in this.moves_by_color) {
      if (Object.prototype.hasOwnProperty.call(this.moves_by_color, prop)) {
        return false;
      }
    }
    return true;
  },

  parse : function (gcode, scale) {
    this.clear();
    this.addParse(gcode, scale);
  },

  parseBycolor : function(gcode_by_color, scale) {
    this.clear();
    for (var color in gcode_by_color) {
      this.addParse(gcode_by_color[color], scale);
    }
  },

  setPathsByColor : function(paths_by_color, scale) {
    this.clear();
    delete this.moves_by_color['000000'];

    for (var color in paths_by_color) {
      var paths = paths_by_color[color];
      this.moves_by_color[color] = [];
      var targetMoves = this.moves_by_color[color];
      for (var i=0; i<paths.length; i++) {
        var path = paths[i];
        if (path.length > 0) {
          targetMoves.push({'type':0, 'X':path[0][0]*scale, 'Y':path[0][1]*scale})
          for (var p=1; p<path.length; p++) {
            targetMoves.push({'type':1, 'X':path[p][0]*scale, 'Y':path[p][1]*scale})
          }
        }
      }
    }
  },

  setExcludeColors : function(colors) {
    this.exclude_colors = colors;
  },



  ///////////////////////////////////////////////
  // Stats

  getStats : function() {
    // Only adds up G1 lines, no arcs, which we should not need.
    var cuttingPathLength = 0.0  // in mm
    var estimatedTime = 0.0      // in min
    var lastX = 0.0;
    var lastY = 0.0;
    var length = 0.0;
    var currentF_seek = 0.0;
    var currentF_feed = 0.0;
    // var acc = 1800000; //mm/min^2, same as defined in LasaurGrbl config.h
    var accelCompFactor = 1.0;

    for (var color in this.moves_by_color) {
      var moves = this.moves_by_color[color];
      for (var i=0; i<moves.length; i++) {
        var move = moves[i];
        if (move.type == 0) {
          if (move.F) {
            // make sure we only get feed rate, no seek rate
            currentF_seek = move.F;
          }
          lastX = move.X;
          lastY = move.Y;
        } else if (move.type == 1) {
          if (move.F) {
            // make sure we only get feed rate, no seek rate
            currentF_feed = move.F;
          }
          length = Math.sqrt(Math.pow(move.X-lastX,2) + Math.pow(move.Y-lastY,2));
          cuttingPathLength += length;
          if (currentF_feed > 0.0 && length > 0.0) {
            // very rough estimation
            // var dist_for_accel_decel = 2*(currentF_feed*currentF_feed/(2*acc));
            // var ratio = length/dist_for_accel_decel
            // var feedrateComp = Math.max(0.1, Math.min(1.0, 0.25*ratio));          
            // estimatedTime += length/(currentF_feed*feedrateComp);]

            // accelCompFactor = 1.0;
            // if (length < 1) {accelCompFactor = 1+currentF_feed/600.0;}
            // else if (length < 5) {accelCompFactor = 1+currentF_feed/1000.0;}
            // else if (length < 10) {accelCompFactor = 1+currentF_feed/2000.0;}
            // else if (length < 50) {accelCompFactor = 1+currentF_feed/3000.0;}
            // else if (length < 100) {accelCompFactor = 1+currentF_feed/6000.0;}
            // accelCompFactor = 1+currentF_feed/(length*60)
            // estimatedTime += (length/currentF_feed)*accelCompFactor*2.0;
            // alert(length/currentF_feed + "->" + estimatedTime);
            estimatedTime += (length/currentF_feed);
          }
          lastX = move.X;
          lastY = move.Y;
        }
      }
    }
    estimatedTime *= 5.0;
    return {'cuttingPathLength':cuttingPathLength, 'estimatedTime':estimatedTime};
  },

  bboxClear : function() {
    this.bbox = [99999,99999,0,0];
  },

  bboxExpand : function(x,y) {
    if (x < this.bbox[0]) {this.bbox[0] = x;}
    else if (x > this.bbox[2]) {this.bbox[2] = x;}
    if (y < this.bbox[1]) {this.bbox[1] = y;}
    else if (y > this.bbox[3]) {this.bbox[3] = y;}
  },
  
  getBboxGcode : function() {
    var glist = [];
    glist.push("G00X"+this.bbox[0].toFixed(3)+"Y"+this.bbox[1].toFixed(3)+"\n");
    glist.push("G00X"+this.bbox[2].toFixed(3)+"Y"+this.bbox[1].toFixed(3)+"\n");
    glist.push("G00X"+this.bbox[2].toFixed(3)+"Y"+this.bbox[3].toFixed(3)+"\n");
    glist.push("G00X"+this.bbox[0].toFixed(3)+"Y"+this.bbox[3].toFixed(3)+"\n");
    glist.push("G00X"+this.bbox[0].toFixed(3)+"Y"+this.bbox[1].toFixed(3)+"\n");
    return glist.join('');
  },


  ///////////////////////////////////////////////
  // Writing

  NDIGITS : 2,

  write : function(colors) {
    var glist = [];
    

    for (var color in this.moves_by_color) {
      if ((colors == null) || (color in colors)) {
        glist.push("T0 P"+color+"\n");  // color information as tool code
        var moves = this.moves_by_color[color];
        for (var i=0; i<moves.length; i++) {
          if (i > 0) { move_prev = moves[i-1]; }
          var move = moves[i];
          if (move.type == 0 || move.type == 1) {
            if (move.type == 0) {
              glist.push("G00");
            } else {
              glist.push("G01");
            }
            if (move.X != null) {
              glist.push("X"+move.X.toFixed(this.NDIGITS));
            }
            if (move.Y != null) {
              glist.push("Y"+move.Y.toFixed(this.NDIGITS));
            }
            if (move.F != null) {
              glist.push("F"+move.F.toFixed(this.NDIGITS));
            }
            glist.push("\n")
          } else if (move.type == 2 || move.type == 3) { 
            if (move.type == 2){
              glist.push("G02");
            } else {
              glist.push("G03");
            }
            if (move.X != null) {
              glist.push("X"+move.X.toFixed(this.NDIGITS));
            }
            if (move.Y != null) {
              glist.push("Y"+move.Y.toFixed(this.NDIGITS));
            }
            if (move.I != null) {
              glist.push("I"+move.I.toFixed(this.NDIGITS));
            }
            if (move.J != null) {
              glist.push("J"+move.J.toFixed(this.NDIGITS));
            }
            if (move.F != null) {
              glist.push("F"+move.F.toFixed(this.NDIGITS));
            }
            glist.push("\n")
          }
        }
      }
    }
    return glist.join('');
  },




  ///////////////////////////////////////////////
  // Drawing

  setCanvas : function(canvas) {
    this.canvas = canvas;
  },


  draw : function () { 
    //// draw gcode
    // this.canvas.clear();
    // this.canvas.noStroke();
    // this.canvas.fill('#ffffff');
    // this.canvas.rect(0,0,this.canvas.width,this.canvas.height);
    this.canvas.background('#ffffff');
    this.canvas.noFill();
    for (var color in this.moves_by_color) {
      if (!(color in this.exclude_colors)) {
        var moves = this.moves_by_color[color];
        var move_prev = {'type':0, 'X':0, 'Y':0, 'I':0, 'J':0 };
        for (var i=0; i<moves.length; i++) {
          if (i > 0) { move_prev = moves[i-1]; }
          var move = moves[i];
      
          if (move.type == 0 || move.type == 1) {  // line seek or cut
            if (move.type == 0) { this.canvas.stroke('#aaaaaa'); } else {this.canvas.stroke(color);}
            this.canvas.line(move_prev.X, move_prev.Y, move.X, move.Y);
        
          } else if (move.type == 2 || move.type == 3) {  // arc CW or CCW
            var ccw = false;
            if (move.type == 3) { ccw = true;}
        
            var centerX = move_prev.X+move.I;
            var centerY = move_prev.Y+move.J;
        
            var centerToStartX = move_prev.X-centerX;
            var centerToStartY = move_prev.Y-centerY;

            var centerToEndX = move.X-centerX;
            var centerToEndY = move.Y-centerY;
        
            var phi_start = Math.atan2(centerToStartY, centerToStartX);
            var phi_end = Math.atan2(centerToEndY, centerToEndX);
        
            var radius = Math.sqrt(centerToStartX*centerToStartX + centerToStartY*centerToStartY);
        
            this.canvas.stroke(color);
            this.canvas.arc(centerX, centerY, radius, phi_end, phi_start, ccw);      
          }
        }
      }
    }
  },

  // draw : function () { 
  //   var x_prev;
  //   var y_prev;
  //   this.canvas.background('#ffffff');
  //   this.canvas.noFill();
  //   for (var color in this.moves_by_color) {
  //     if (!(color in this.exclude_colors)) {
  //       var paths = this.moves_by_color[color];
  //       for (var i=0; i<paths.length; i++) {
  //         var path = paths[i];
  //         if (path.length > 0) {
  //           var vertex = 0;
  //           var x = path[vertex][0];
  //           var y = path[vertex][1];
  //           this.canvas.stroke('#aaaaaa');
  //           this.canvas.line(x_prev, y_prev, x, y);
  //           x_prev = x;
  //           y_prev = y;
  //           this.canvas.stroke(color);
  //           for (vertex=1; vertex<path.length; vertex++) {
  //             var x = path[vertex][0];
  //             var y = path[vertex][1];
  //             this.canvas.line(x_prev, y_prev, x, y);
  //             x_prev = x;
  //             y_prev = y;
  //           }
  //         }      
  //       }
  //     }
  //   }
  // },
  

}





///////////////////////////////////////////////
// Pan Zoom



function init_pan_zoom(canvas_selector){   
    var canvas = $(canvas_selector)[0];  
    var ctx = canvas.getContext('2d');
    trackTransforms(ctx);  // augment ctx with tracking functions

    // Clear the entire canvas
    var p1 = ctx.transformedPoint(0,0);
    var p2 = ctx.transformedPoint(canvas.width,canvas.height);
    ctx.clearRect(p1.x,p1.y,p2.x-p1.x,p2.y-p1.y);
    GcodeReader.draw();
    
    var lastX=canvas.width/2, lastY=canvas.height/2;
    var dragStart,dragged;
    canvas.addEventListener('mousedown',function(evt){
        document.body.style.mozUserSelect = document.body.style.webkitUserSelect = document.body.style.userSelect = 'none';
        lastX = evt.offsetX || (evt.pageX - canvas.offsetLeft);
        lastY = evt.offsetY || (evt.pageY - canvas.offsetTop);
        dragStart = ctx.transformedPoint(lastX,lastY);
        dragged = false;
    },false);
    canvas.addEventListener('mousemove',function(evt){
        lastX = evt.offsetX || (evt.pageX - canvas.offsetLeft);
        lastY = evt.offsetY || (evt.pageY - canvas.offsetTop);
        dragged = true;
        if (dragStart){
            var pt = ctx.transformedPoint(lastX,lastY);
            ctx.translate(pt.x-dragStart.x,pt.y-dragStart.y);
            // Clear the entire canvas
            var p1 = ctx.transformedPoint(0,0);
            var p2 = ctx.transformedPoint(canvas.width,canvas.height);
            ctx.clearRect(p1.x,p1.y,p2.x-p1.x,p2.y-p1.y);
            GcodeReader.draw();
        }
    },false);
    canvas.addEventListener('mouseup',function(evt){
        dragStart = null;
        if (!dragged) zoom(evt.shiftKey ? -1 : 1 );
    },false);

    var scaleFactor = 1.1;
    var zoom = function(clicks){
        var pt = ctx.transformedPoint(lastX,lastY);
        ctx.translate(pt.x,pt.y);
        var factor = Math.pow(scaleFactor,clicks);
        ctx.scale(factor,factor);
        ctx.translate(-pt.x,-pt.y);
        // Clear the entire canvas
        var p1 = ctx.transformedPoint(0,0);
        var p2 = ctx.transformedPoint(canvas.width,canvas.height);
        ctx.clearRect(p1.x,p1.y,p2.x-p1.x,p2.y-p1.y);
        GcodeReader.draw();
    }

    var handleScroll = function(evt){
        var delta = evt.wheelDelta ? evt.wheelDelta/40 : evt.detail ? -evt.detail : 0;
        if (delta) zoom(delta);
        return evt.preventDefault() && false;
    };
    canvas.addEventListener('DOMMouseScroll',handleScroll,false);
    canvas.addEventListener('mousewheel',handleScroll,false);
};

// Adds ctx.getTransform() - returns an SVGMatrix
// Adds ctx.transformedPoint(x,y) - returns an SVGPoint
function trackTransforms(ctx){
    var svg = document.createElementNS("http://www.w3.org/2000/svg",'svg');
    var xform = svg.createSVGMatrix();
    ctx.getTransform = function(){ return xform; };
    
    var savedTransforms = [];
    var save = ctx.save;
    ctx.save = function(){
        savedTransforms.push(xform.translate(0,0));
        return save.call(ctx);
    };
    var restore = ctx.restore;
    ctx.restore = function(){
        xform = savedTransforms.pop();
        return restore.call(ctx);
    };

    var scale = ctx.scale;
    ctx.scale = function(sx,sy){
        xform = xform.scaleNonUniform(sx,sy);
        return scale.call(ctx,sx,sy);
    };
    var rotate = ctx.rotate;
    ctx.rotate = function(radians){
        xform = xform.rotate(radians*180/Math.PI);
        return rotate.call(ctx,radians);
    };
    var translate = ctx.translate;
    ctx.translate = function(dx,dy){
        xform = xform.translate(dx,dy);
        return translate.call(ctx,dx,dy);
    };
    var transform = ctx.transform;
    ctx.transform = function(a,b,c,d,e,f){
        var m2 = svg.createSVGMatrix();
        m2.a=a; m2.b=b; m2.c=c; m2.d=d; m2.e=e; m2.f=f;
        xform = xform.multiply(m2);
        return transform.call(ctx,a,b,c,d,e,f);
    };
    var setTransform = ctx.setTransform;
    ctx.setTransform = function(a,b,c,d,e,f){
        xform.a = a;
        xform.b = b;
        xform.c = c;
        xform.d = d;
        xform.e = e;
        xform.f = f;
        return setTransform.call(ctx,a,b,c,d,e,f);
    };
    var pt  = svg.createSVGPoint();
    ctx.transformedPoint = function(x,y){
        pt.x=x; pt.y=y;
        return pt.matrixTransform(xform.inverse());
    }
}

