$(document).ready(function(){

  // G-Code Canvas Preview
  
  icanvas = new Canvas($('#import_canvas').get(0), {width:610, height:310})     
  
  
  //var icanvas = new Canvas('#import_canvas');
  
  var gcode = new Gcode();
  //icanvas.background('ffffff');  
  // file upload form
  $('#svg_upload_button').button();
  $('#svg_upload_file').button();
  $('#svg_upload_form').ajaxForm({
  	beforeSubmit: function() {
  	  var ret = true;
  	  var fullpath = $('#svg_upload_file').val();
  	  if (fullpath.lastIndexOf(".svg") == -1) {
  	    $().uxmessage('notice', "unsupported file type");
  	    ret = false;
  	  } else {
  	    $().uxmessage('notice', "opening file ...");
  	  }
  	  return ret;
  	},
  	success: function(svgdata) {
  	  $().uxmessage('notice', "rendering SVG with cakejs ...");
      //$('#import_results').text(svgdata);
            
      
  		var svgNode = SVGParser.parse($.parseXML(svgdata), {
  		    width: 610,
  		    height: 310				
  		})
  	  $().uxmessage('notice', "adding SVG to canvas ...");
  		icanvas.append(svgNode);  
  		
      var circle = new Circle(100, {
        id: 'myCircle',
        x: icanvas.width / 2,
        y: icanvas.height / 2,
        stroke: 'cyan',
        strokeWidth: 20,
        endAngle: Math.PI*1.8
      })
  
    	icanvas.append(circle);   		    
    	
    	//gcode.draw(icanvas);
    		
    }
  });


  $("#import_to_queue").button();  
  $("#import_to_queue").click(function(e) {
    var gcodedata = $('#import_results').text();
    var fullpath = $('#svg_upload_file').val();
    var filename = fullpath.split('\\').pop().split('/').pop();
    add_to_job_queue(gcodedata, filename);
	  $().uxmessage('notice', "file added to laser job queue");    
  	return false;
  });


});  // ready
