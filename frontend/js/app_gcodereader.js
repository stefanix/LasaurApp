
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
  moves : [],

  parse : function (gcode, scale) {
  
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
  	
  	this.moves = [];
  	this.bboxClear();
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
  				this.moves.push( {'type':gnum, 'X':currentX, 'Y':currentY, 'I':currentI, 'J':currentJ, 'F':currentF } );
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
  		}
  	}
  },


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

    for (var i=0; i<this.moves.length; i++) {
      var move = this.moves[i];
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
    estimatedTime *= 5.0;
    return {'cuttingPathLength':cuttingPathLength, 'estimatedTime':estimatedTime};
  },

  	
  draw : function (canvas, color) { 
  	//// draw gcode
    // canvas.clear();
    // canvas.noStroke();
    // canvas.fill('#ffffff');
    // canvas.rect(0,0,canvas.width,canvas.height);
  	canvas.noFill();
  	var move_prev = {'type':0, 'X':0, 'Y':0, 'I':0, 'J':0 };
  	var move;
  	for (var i=0; i<this.moves.length; i++) {
  		if (i > 0) { move_prev = this.moves[i-1]; }
  		move = this.moves[i];
	
  		if (move.type == 0 || move.type == 1) {  // line seek or cut
  			if (move.type == 0) { canvas.stroke('#aaaaaa'); } else {canvas.stroke(color);}
  			canvas.line(move_prev.X, move_prev.Y, move.X, move.Y);
		
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
		
  			canvas.stroke(color);
  			canvas.arc(centerX, centerY, radius, phi_end, phi_start, ccw);			
  		}
  	}	
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
  }   
  
}



