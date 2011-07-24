

function Gcode(gcode_selector) {
  this.selector = gcode_selector;
  this.moves = [];
}


Gcode.prototype.parse = function (scale) {
  
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
	
	
	// parse gcode
	//
	this.moves = [];
	var gcode =   $(this.selector).val();
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
			}
		}
	}
}


	
Gcode.prototype.draw = function (canvas) {
	function theta(x, y)	{
	  return Math.atan2(y,x);
	  var theta = Math.atan(y/Math.abs(x));
	  if (y>0) {
	    return(theta);
	  } else {
	    if (theta>0) {
	      return(Math.PI-theta);
	    } else {
	      return(-Math.PI-theta);
	    }
	  }
	}	
	
	function hypot(x, y) {
		// also see http://stackoverflow.com/questions/3764978/why-hypot-function-is-so-slow
    return Math.sqrt(x * x + y * y);	
	}
	
	canvas.clear();
	canvas.noStroke();
	canvas.fill('#ffffff');
	canvas.rect(0,0,canvas.width,canvas.height);
	canvas.noFill();
	var move_prev = {'type':0, 'X':0, 'Y':0, 'I':0, 'J':0 };
	var move;
	for (var i=0; i<this.moves.length; i++) {
		if (i > 0) { move_prev = this.moves[i-1]; }
		move = this.moves[i];
		
		if (move.type == 0 || move.type == 1) { 
			if (move.type == 0) { canvas.stroke('#aaaaaa'); } else {canvas.stroke('#ff0000');}
			canvas.line(move_prev.X, move_prev.Y, move.X, move.Y);
		} else if (move.type == 2 || move.type == 3) {
			if (move.type == 2) { canvas.stroke('#ff00ff'); } else {canvas.stroke('#00ffff');}
			canvas.line(move_prev.X, move_prev.Y, move.X, move.Y);		  
			// arc CW or CCW
			// code from grbl
			var ccw = false;
      var theta_start = theta(-move.I, -move.J);
      var theta_end = theta(move.X - move.I - move_prev.X, move.Y - move.J - move_prev.Y);
      if (theta_end < theta_start) { theta_end += 2*Math.PI; }
      if (move.type == 3) {
				// arc CCW
				ccw = true;
				var theta_end_temp = theta_end;
				theta_end = theta_start;
				theta_start = theta_end_temp;
      }
      // Find the radius
      var radius = hypot(move.I, move.J);
	    var center_x = move_prev.X-Math.sin(theta_start)*radius;
	    var center_y = move_prev.Y-Math.cos(theta_start)*radius;
			
			canvas.stroke('#aaaaaa');
			canvas.arc(center_x, center_y, radius, Math.PI, 0, true);
			canvas.stroke('#ff0000');
			canvas.arc(center_x, center_y, radius, theta_end, theta_start, ccw);
			//canvas.arc(center_x, center_y, radius, theta_start+0.5*Math.PI, theta_end+0.5*Math.PI, ccw);			

			var midX = (move_prev.X+move.X)/2.0;
			var midY = (move_prev.Y+move.Y)/2.0;
			canvas.stroke('#00ff00');			
			//canvas.line(move_prev.X, move_prev.Y, move.X, move.Y);
			canvas.line(midX, midY, (midX+move.I), (midY+move.J));
			//canvas.line(move.I, move.J, move_prev.X, move_prev.Y);
			
			canvas.stroke('#aaaaaa');			
		}
	}
}



Gcode.prototype.draw2 = function (canvas) {
		
	canvas.clear();
	canvas.noStroke();
	canvas.fill('#ffffff');
	canvas.rect(0,0,canvas.width,canvas.height);
	canvas.noFill();
	var move_prev = {'type':0, 'X':0, 'Y':0, 'I':0, 'J':0 };
	var move;
	for (var i=0; i<this.moves.length; i++) {
		if (i > 0) { move_prev = this.moves[i-1]; }
		move = this.moves[i];
		
		if (move.type == 0 || move.type == 1) {  // line seek or cut
			if (move.type == 0) { canvas.stroke('#aaaaaa'); } else {canvas.stroke('#ff0000');}
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
			
			canvas.stroke('#ff0000');
			canvas.arc(centerX, centerY, radius, phi_end, phi_start, ccw);
			
		}
	}
}

