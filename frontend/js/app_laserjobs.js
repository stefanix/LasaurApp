$(document).ready(function(){

  // populate queue from queue directory
  $.getJSON("/queue/list", function(data) {
    $.each(data, function(index, name) {
      add_to_job_queue(name);
    });
  });
    
  // populate library from library directory
  $.getJSON("/library/list", function(data) {
    $.each(data, function(index, name) {
      $('#gcode_library').prepend('<li><a href="#">'+ name +'</a></li>');
    });
  	$('#gcode_library li a').click(function(){
  	  var name = $(this).text();
      $.get("/library/get/" + name, function(gdata) {
        load_into_gcode_widget(gdata, name);
      });
  	});  	
  });
  // .success(function() { alert("second success"); })
  // .error(function() { alert("error"); })
  // .complete(function() { alert("complete"); });
 
  


  $("#progressbar").hide();  
  $("#gcode_submit").click(function(e) {
  	// send gcode string to server via POST
  	var gcode = $('#gcode_program').val();
    // $().uxmessage('notice', gcode.replace(/\n/g, '<br>'));
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


  $("#gcode_bbox").click(function(e) {
    $().uxmessage('notice', "bbox not yet implemented");
    var gcodedata = $('#gcode_program').val();
    //var gcode_bbox = 
  });

  $("#gcode_save_to_queue").click(function(e) {
    save_and_add_to_job_queue($.trim($('#gcode_name').val()), $('#gcode_program').val());
  });


  // G-Code Canvas Preview
  //
  var canvas = new Canvas('#preview_canvas');
  canvas.background('#ffffff');

  $('#gcode_program').blur(function() {
    var gcodedata = $('#gcode_program').val();
    canvas.background('#ffffff'); 
  	GcodeReader.draw(canvas, gcodedata, 0.25, '#000000');	
  });

});  // ready
