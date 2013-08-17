

var minNumPassWidgets = 3;
var maxNumPassWidgets = 32;


function addPasses(num) {
  var pass_num_offset = getNumPasses() + 1;
  var buttons = ''
  for (var color in DataHandler.getAllColors()) {
    buttons +='<button class="select_color btn btn-small" style="margin:2px"><div style="width:10px; height:10px; background-color:'+color+'"><span style="display:none">'+color+'</span></div></button>'
  }
  for (var i=0; i<num; i++) {
    var passnum = pass_num_offset+i;
    var margintop = '';
    if (passnum != 1) {
      margintop = 'margin-top:6px;'
    }
    var html = '<div class="row well" style="margin:0px; '+margintop+' padding:4px; background-color:#eeeeee">' + 
                '<div class="form-inline" style="margin-bottom:0px">' +
                  '<label>Pass '+ passnum +': </label>' +
                  '<div class="input-prepend" style="margin-left:6px">' +
                    '<span class="add-on" style="margin-right:-5px;">F</span>' +
                    '<input type="text" class="feedrate" value="2000" title="feedrate 1-8000mm/min" style="width:32px" data-delay="500">' +
                  '</div>' +
                  '<div class="input-prepend" style="margin-left:6px">' +
                    '<span class="add-on" style="margin-right:-5px;">%</span>' +
                    '<input class="intensity" type="textfield" value="100" title="intensity 0-100%" style="width:26px;" data-delay="500">' +
                  '</div>' +
                  '<span class="colorbtns" style="margin-left:6px">'+buttons+'</span>' +
                '</div>' +
              '</div>';
    // $('#passes').append(html);
    var pass_elem = $(html).appendTo('#passes');
    // color pass widget toggles events registration
    pass_elem.find('.colorbtns button.select_color').click(function(e){
      // toggle manually to work the same as preview buttons
      // also need active-strong anyways
      if($(this).hasClass('active')) {
        $(this).removeClass('active');
        $(this).removeClass('active-strong');
      } else {
        $(this).addClass('active');
        $(this).addClass('active-strong');      
      }
    });
  }
}


function getNumPasses() {
  return $('#passes').children().length;
}


function readPassesWidget() {
  DataHandler.clearPasses();
  $('#passes > div').each(function(index) {
    var colors = [];
    $(this).find('.colorbtns button').each(function(index) {
      if ($(this).hasClass('active')) {
        colors.push($(this).find('div span').text());
      }
    });
    if (colors.length > 0) { 
      var feedrate = $(this).find('.feedrate').val();
      var intensity = $(this).find('.intensity').val();
      DataHandler.addPass({'colors':colors, 'feedrate':feedrate, 'intensity':intensity});
    }
  });
  return DataHandler.hasPasses();
}

function writePassesWidget() {
  var passes = DataHandler.getPasses();
  if (passes.length > 0) {
    for (var i=0; i<passes.length; i++) {
      var pass = passes[i];
      if (pass <= maxNumPassWidgets) {
        //make sure to have enough pass widgets
        var passes_to_create = i - getNumPasses()
        if (passes_to_create >= 1) {
          addPasses(passes_to_create);
        }
        // feedrate
        $('#passes > div:nth-child('+i+') .feedrate').val(pass['feedrate']);
        // intensity
        $('#passes > div:nth-child('+i+') .intensity').val(pass['intensity']);
        // colors
        var colors = pass['colors'];
        for (var ii=0; ii<colors.length; ii++) {
          var col = colors[ii];
          var color_order = DataHandler.getColorOrder();
          if (col in color_order) {
            $('#passes > div:nth-child('+i+') .colorbtns button:eq('+color_order[col]+')').addClass('active active-strong')
          }
        }
      } else {
        $().uxmessage('error', "pass number too high");
        break;
      }
    }
  } else {
    // no lasertags, if only one color -> assign to pass1
    if (DataHandler.getAllColors().length == 1) {
      $('#passes > div:nth-child(1) .colorbtns').children('button').addClass('active')
      $().uxmessage('notice', "assigned to pass1");
    }
  }
}



$(document).ready(function(){

  /// init //////////////////////////////////////

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
 

  /// button event //////////////////////////////

  $("#progressbar").hide();  
  $("#gcode_submit").click(function(e) {
    // send gcode string to server via POST
    DataHandler.setByJson($('#job_data').val());
    if (readPassesWidget()) {
      send_gcode(DataHandler.getGcode(), "G-Code sent to backend.", true);
    } else {
      $().uxmessage('warning', "nothing to cut -> please assign colors to passes");
    }
    return false;
  });


  $('#gcode_bbox_submit').tooltip();
  $("#gcode_bbox_submit").click(function(e) {
    DataHandler.setByJson($('#job_data').val());
    if (readPassesWidget()) {
      send_gcode(DataHandler.getBboxGcode(), "BBox G-Code sent to backend", true);
    } else {
      $().uxmessage('warning', "nothing to cut -> please assign colors to passes");
    }
    return false;
  });

  $('#gcode_save_to_queue').tooltip();
  $("#gcode_save_to_queue").click(function(e) {
    DataHandler.setByJson($('#job_data').val());
    readPassesWidget();
    save_and_add_to_job_queue($.trim($('#job_name').val()), DataHandler.getJson());
    return false;
  });


  // canvas preview generation
  var canvas = new Canvas('#preview_canvas');
  canvas.background('#ffffff');
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



  /// passes ////////////////////////////////////

  $('#import_feedrate_1').tooltip();
  $('#import_intensity_1').tooltip();
  $('#import_feedrate_2').tooltip();
  $('#import_intensity_2').tooltip();
  $('#import_feedrate_3').tooltip();
  $('#import_intensity_3').tooltip();


  $("#add_pass_btn").click(function(e) {
    if (getNumPasses() < maxNumPassWidgets) {
      addPasses(1);
    } else {
      $().uxmessage('error', "Max number of passes reached.");
    }
    return false;
  });  


});  // ready
