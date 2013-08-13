

// create new canvas like this:
// var canvas = new Canvas('#canvas_id');

function Canvas(canvas_selector) {
  this.cx = $(canvas_selector)[0].getContext("2d");
  this.width = $(canvas_selector).width();
  this.height = $(canvas_selector).height();
  
  this.bFill = true;
  this.vFill = "#ffffff";
  this.cx.fillStyle = this.vFill;
  
  this.bStroke = true;
  this.vStroke = "#000000";
  this.cx.strokeStyle = this.vStroke;

  // content geometry
  this.path_by_color = {};
  this.colors2exclude = {};
}

Canvas.prototype.setGeo = function(paths_by_color) {
  // geo data is a hash by color
  // each color entry has a list of paths
  this.path_by_color = paths_by_color;
}

Canvas.prototype.setColorsToExclude = function(colors) {
  // geo data is a hash by color
  // each color entry has a list of paths
  this.colors2exclude = colors;
}

Canvas.prototype.redraw = function() {
  // redraw from geodata

  // this.clear();
  // this.noStroke();
  // this.fill('#ffffff');
  // this.rect(0,0,this.width,this.height);
  this.noFill();
  var move_prev = {'type':0, 'X':0, 'Y':0, 'I':0, 'J':0 };
  var move;
  for (var i=0; i<this.moves.length; i++) {
    if (i > 0) { move_prev = this.moves[i-1]; }
    move = this.moves[i];

    if (move.type == 0 || move.type == 1) {  // line seek or cut
      if (move.type == 0) { this.stroke('#aaaaaa'); } else {this.stroke(color);}
      this.line(move_prev.X, move_prev.Y, move.X, move.Y);
  
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
  
      this.stroke(color);
      this.arc(centerX, centerY, radius, phi_end, phi_start, ccw);      
    }
  } 
}


Canvas.prototype.fill = function (hexcolorval) {
  this.bFill = true;
  this.vFill = hexcolorval;
  this.cx.fillStyle = this.vFill;  
}
Canvas.prototype.noFill = function () {
  this.bFill = false;
}

Canvas.prototype.stroke = function (hexcolorval) {
  this.bStroke = true;
  this.vStroke = hexcolorval;
  this.cx.strokeStyle = this.vStroke;  
}
Canvas.prototype.noStroke = function () {
  this.bStroke = false;
}

Canvas.prototype.line = function (x1, y1, x2, y2) {
  this.cx.beginPath();
  this.cx.moveTo(x1, y1);
  this.cx.lineTo(x2, y2);
  if (this.bFill) { this.cx.fill(); }
  if (this.bStroke) { this.cx.stroke(); }
  this.cx.closePath();
}

Canvas.prototype.rect = function (x, y, w, h) {
  this.cx.beginPath();
  this.cx.rect(x, y, w, h);
  if (this.bFill) { this.cx.fill(); }
  if (this.bStroke) { this.cx.stroke(); }
  this.cx.closePath();
}

Canvas.prototype.circle = function (x, y, r) {
  this.cx.beginPath();
  this.cx.arc(x, y, r, 0, Math.PI*2, true);
  if (this.bFill) { this.cx.fill(); }
  if (this.bStroke) { this.cx.stroke(); }
  this.cx.closePath();
};

Canvas.prototype.arc = function (x, y, r, startang, endang, ccw) {
  this.cx.beginPath();
  this.cx.arc(x, y, r, startang, endang, ccw);
  if (this.bFill) { this.cx.fill(); }
  if (this.bStroke) { this.cx.stroke(); }
  this.cx.closePath();
};
// there is also a cx.arcTo(x1, y1, x2, y2, radius)

Canvas.prototype.background = function (color) {
  this.noStroke();
  this.fill(color);
  this.rect(0, 0, this.width, this.height);
}

Canvas.prototype.clear = function () {
  this.cx.clearRect(0, 0, this.width, this.height);
}

Canvas.prototype.draw = function () {
  this.clear();
  this.circle(x, y, 10);

  x += 2;
  y += 4;
}


///////////////////////////////////////////////
// G-Code Drawer

Canvas.prototype.drawGcode = function (gcode) {

}



///////////////////////////////////////////////
// Pan Zoom

var canvas = document.getElementsByTagName('canvas')[0];
canvas.width = 800; canvas.height = 600;

var gkhead = new Image;
var ball   = new Image;
gkhead.src = 'http://phrogz.net/tmp/gkhead.jpg';
ball.src   = 'http://phrogz.net/tmp/alphaball.png';

function init_pan_zoom(){     
    var ctx = canvas.getContext('2d');
    trackTransforms(ctx);  // augment ctx with tracking functions
    function redraw(){
        // Clear the entire canvas
        var p1 = ctx.transformedPoint(0,0);
        var p2 = ctx.transformedPoint(canvas.width,canvas.height);
        ctx.clearRect(p1.x,p1.y,p2.x-p1.x,p2.y-p1.y);

        // Alternatively:
        // ctx.save();
        // ctx.setTransform(1,0,0,1,0,0);
        // ctx.clearRect(0,0,canvas.width,canvas.height);
        // ctx.restore();

        ctx.drawImage(gkhead,200,50);

        ctx.beginPath();
        ctx.lineWidth = 6;
        ctx.moveTo(399,250);
        ctx.lineTo(474,256);
        ctx.stroke();

        ctx.save();
        ctx.translate(4,2);
        ctx.beginPath();
        ctx.lineWidth = 1;
        ctx.moveTo(436,253);
        ctx.lineTo(437.5,233);
        ctx.stroke();

        ctx.save();
        ctx.translate(438.5,223);
        ctx.strokeStyle = '#06c';
        ctx.beginPath();
        ctx.lineWidth = 0.05;
        for (var i=0;i<60;++i){
            ctx.rotate(6*i*Math.PI/180);
            ctx.moveTo(9,0);
            ctx.lineTo(10,0);
            ctx.rotate(-6*i*Math.PI/180);
        }
        ctx.stroke();
        ctx.restore();

        ctx.beginPath();
        ctx.lineWidth = 0.2;
        ctx.arc(438.5,223,10,0,Math.PI*2);
        ctx.stroke();
        ctx.restore();
        
        ctx.drawImage(ball,379,233,40,40);
        ctx.drawImage(ball,454,239,40,40);
        ctx.drawImage(ball,310,295,20,20);
        ctx.drawImage(ball,314.5,296.5,5,5);
        ctx.drawImage(ball,319,297.2,5,5);
    }
    redraw();
    
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
            redraw();
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
        redraw();
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