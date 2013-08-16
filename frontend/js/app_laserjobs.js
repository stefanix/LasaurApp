

$(document).ready(function(){

  // empty job_name on reload
  $("#job_name").val("");  

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
      $('#job_library').prepend('<li><a href="#">'+ name +'</a></li>');
    });
    $('#job_library li a').click(function(){
      var name = $(this).text();
      $.get("/library/get/" + name, function(jobdata) {
        load_into_job_widget(name, jobdata);
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
    DataHandler.setByJson($('#job_data').val());
    send_gcode(DataHandler.getGcode(), "G-Code sent to backend.", true);
    return false;
  });


  $('#gcode_bbox_submit').tooltip();
  $("#gcode_bbox_submit").click(function(e) {
    DataHandler.setByJson($('#job_data').val());
    send_gcode(DataHandler.getBboxGcode(), "BBox G-Code sent to backend", true);
    return false;
  });

  $('#gcode_save_to_queue').tooltip();
  $("#gcode_save_to_queue").click(function(e) {
    save_and_add_to_job_queue($.trim($('#job_name').val()), $('#job_data').val());
    return false;
  });


  // G-Code Canvas Preview
  //
  var canvas = new Canvas('#preview_canvas');

  $('#job_data').blur(function() {
    DataHandler.setByJson($('#job_data').val());
    DataHandler.draw(canvas, 0.5);
    // var stats = GcodeReader.getStats();
    // var length = stats.cuttingPathLength; 
    // var duration = stats.estimatedTime;
    // $('#previe_stats').html("~" + duration.toFixed(1) + "min");
    // $().uxmessage('notice', "Total cutting path is: " + (length/1000.0).toFixed(2) + 
    //               "m. Estimated Time: " + duration.toFixed(1) + "min");
  });

});  // ready
