$(document).ready(function(){

  // G-Code Canvas Preview
  var icanvas = new Canvas('#import_canvas');
  var gcode = new Gcode();
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
  	    $().uxmessage('notice', "submitting file ...");
  	  }
  	  return ret;
  	},
  	success: function(gcodedata) {
  	  $().uxmessage('notice', "rendering G-code ...");
      $('#import_results').text(gcodedata);      
    	gcode.parse(gcodedata, 0.5);
    	gcode.draw(icanvas);
    		
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
