$(document).ready(function(){
  
  $('#gcode_queue').show();

  $('#library_placeholder').replaceWith($('#gcode_library'));
  $('#gcode_library').show();

  $('#gcode_library a').click(function(){		
    preview_job($(this).next().text(), $(this).text())
  });


  $('#calibration_placeholder').replaceWith($('#gcode_for_calibration'));
  $('#gcode_for_calibration').show();

  $('#gcode_for_calibration a').click(function(){
    $('#gcode_name').val( $(this).text() );
  	$('#gcode_program').val( $(this).next().text() );

  	// make sure preview refreshes
  	$('#gcode_program').trigger('blur');	
  });


  $("#progressbar").hide();  
  $("#gcode_submit").click(function(e) {
  	// send gcode string to server via POST
  	var gcode = $('#gcode_program').val();
  	$().uxmessage('notice', gcode.replace(/\n/g, '<br>'));
  	$.post("/gcode", { 'gcode_program':gcode }, function(data) {
  		if (data != "") {
  			$().uxmessage('success', "G-Code sent to serial.");	
  			// show progress bar, register live updates
  			if ($("#progressbar").children().first().width() == 0) {
  				$("#progressbar").children().first().width('5%');
  				$("#progressbar").show();
  				var progress_not_yet_done_flag = true;
  			  var progresstimer = setInterval(function() {
  					$.get('/queue_pct_done', function(data2) {
  						if (data2.length > 0) {
  							var pct = parseInt(data2);
                $("#progressbar").children().first().width(pct+'%');  							
  						} else {
  						  if (progress_not_yet_done_flag) {
    						  $("#progressbar").children().first().width('100%');
    						  $().uxmessage('notice', "Done.");
    						  progress_not_yet_done_flag = false;
    						} else {
    							$('#progressbar').hide();
    							$("#progressbar").children().first().width(0); 
    							clearInterval(progresstimer);
    						}
  						}
  					});
  			  }, 2000);
  			}
  		} else {
  			$().uxmessage('error', "Serial not connected.");
  		}
    });
  	return false;
  });


  $("#gcode_bbox").button();  
  $("#gcode_bbox").click(function(e) {
    $().uxmessage('notice', "bbox not yet implemented");
    var gcodedata = $('#gcode_program').val();
    //var gcode_bbox = 
  });

  $("#gcode_save_to_queue").button();  
  $("#gcode_save_to_queue").click(function(e) {
    add_to_job_queue($('#gcode_program').val(), $.trim($('#gcode_name').val()));
  });


  // G-Code Canvas Preview
  //
  var canvas = new Canvas('#preview_canvas');
  canvas.background('ffffff');

  $('#gcode_program').blur(function() {
    var gcodedata = $('#gcode_program').val();
  	GcodeReader.parse(gcodedata, 0.25);
  	GcodeReader.draw(canvas);	
  });

});  // ready
