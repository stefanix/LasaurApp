
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
  				this.moves.push( {'type':gnum, 'X':currentX, 'Y':currentY, 'I':currentI, 'J':currentJ } );
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



