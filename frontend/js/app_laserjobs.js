
function send_gcode_to_backend(gcode) {
  if (typeof gcode === "string" && gcode != '') {
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
  } else {
    $().uxmessage('error', "No gcode.");
  }
}



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
    send_gcode_to_backend(gcode);
  	return false;
  });


  $('#gcode_bbox_submit').tooltip();
  $("#gcode_bbox_submit").click(function(e) {
    var gcodedata = $('#gcode_program').val();
    GcodeReader.parse(gcodedata, 1);
    var gcode_bbox = GcodeReader.getBboxGcode();
    var header = "%\nG21\nG90\nG0F16000\n"
    var footer = "G00X0Y0F16000\n%"
    // save_and_add_to_job_queue($('#gcode_name').val() + 'BBOX', header + gcode_bbox + footer);  // for debugging
    send_gcode_to_backend(header + gcode_bbox + footer);
    return false;
  });

  $('#gcode_save_to_queue').tooltip();
  $("#gcode_save_to_queue").click(function(e) {
    save_and_add_to_job_queue($.trim($('#gcode_name').val()), $('#gcode_program').val());
    return false;
  });


  // G-Code Canvas Preview
  //
  var canvas = new Canvas('#preview_canvas');
  canvas.background('#ffffff');

  $('#gcode_program').blur(function() {
    var gcodedata = $('#gcode_program').val();
    canvas.background('#ffffff'); 
  	GcodeReader.parse(gcodedata, 0.25);
  	GcodeReader.draw(canvas, '#000000');
  });

});  // ready
