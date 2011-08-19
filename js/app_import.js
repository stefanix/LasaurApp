$(document).ready(function(){

  // G-Code Canvas Preview
  var icanvas = new Canvas('#import_canvas');
  var gcodereader = new GcodeReader();
  icanvas.background('ffffff'); 
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
      $().uxmessage('notice', "rendering G-code ...");
      $('#import_results').text(gcodedata);
      
      
      
	  
  	  
  	  $().uxmessage('notice', "rendering SVG with cakejs ...");
      //$('#import_results').text(svgdata);
            
      var svgroot = $.parseXML(svgdata).documentElement
  		var boundarys = SVGReader.parse(svgroot, {
  		    width: 610,
  		    height: 310				
  		})
  		
  		var gcode = GcodeWriter.write(boundarys)
  		
      gcodereader.parse(gcode, 0.5);
      gcodereader.draw(icanvas);    		
  		
  		//alert(JSON.stringify(svgNode));
  		alert(svgNode.toSource())
    		
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
