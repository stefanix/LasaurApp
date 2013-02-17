

$(document).ready(function(){

  // populate queue from queue directory
  $.getJSON("/queue/list", function(data) {
    $.each(data, function(index, name) {
      add_to_job_queue(name);
    });
  });
    
  // populate library from library directory
  $.getJSON("/library/list", function(data) {
    if (typeof(data.sort) == 'function') {
      data.sort();
    }
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
    send_gcode("G90\n" + gcode, "G-Code sent to backend.", true);
  	return false;
  });


  $('#gcode_bbox_submit').tooltip();
  $("#gcode_bbox_submit").click(function(e) {
    var gcodedata = $('#gcode_program').val();
    GcodeReader.parse(gcodedata, 1);
    var gcode_bbox = GcodeReader.getBboxGcode();
    var header = "G90\nG0F16000\n"
    var footer = "G00X0Y0F16000\n"
    // save_and_add_to_job_queue($('#gcode_name').val() + 'BBOX', header + gcode_bbox + footer);  // for debugging
    send_gcode(header + gcode_bbox + footer, "BBox G-Code sent to backend", true);
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
    var stats = GcodeReader.getStats();
    var length = stats.cuttingPathLength; 
    var duration = stats.estimatedTime;
    $('#previe_stats').html("~" + duration.toFixed(1) + "min");
    // $().uxmessage('notice', "Total cutting path is: " + (length/1000.0).toFixed(2) + 
    //               "m. Estimated Time: " + duration.toFixed(1) + "min");
  });

});  // ready
