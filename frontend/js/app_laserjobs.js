

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
        load_into_gcode_widget(name, gdata);
      });
      return false;
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
    // var gcodedata = $('#gcode_program').val();
    send_gcode(DataHandler.getBboxGcode(), "BBox G-Code sent to backend", true);
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

  $('#gcode_program').blur(function() {
    var gcodedata = $('#gcode_program').val();
  	DataHandler.draw(canvas, 0.25);
    // var stats = GcodeReader.getStats();
    // var length = stats.cuttingPathLength; 
    // var duration = stats.estimatedTime;
    // $('#previe_stats').html("~" + duration.toFixed(1) + "min");
    // $().uxmessage('notice', "Total cutting path is: " + (length/1000.0).toFixed(2) + 
    //               "m. Estimated Time: " + duration.toFixed(1) + "min");
  });

});  // ready
