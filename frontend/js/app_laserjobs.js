

var minNumPassWidgets = 3;
var maxNumPassWidgets = 32;



function load_into_job_widget(name, jobdata) {
  // create some empty pass widgets
  $('#passes').html('');
  DataHandler.setByJson(jobdata);
  addPasses(minNumPassWidgets);
  writePassesWidget();
  $('#passes_info').show();

  $('#job_name').val(name);
  $('#job_data').val(jobdata);
  // make sure preview refreshes
  $('#job_data').trigger('blur');
  // scroll to top
  $('html, body').animate({scrollTop:0}, 400);
}


/// QUEUE/LIBRARY ///////////////////////////////

var queue_num_index = 1;
function save_and_add_to_job_queue(name, jobdata) { 
  if ((typeof(name) == 'undefined') || ($.trim(name) == '')) {
    var date = new Date();
    name = date.toDateString() +' - '+ queue_num_index
  }
  //// store jobdata - on success add to queue
  $.post("/queue/save", { 'job_name':name, 'job_data':jobdata }, function(data) {
    if (data == "1") {
      queue_num_index += 1;
      add_to_job_queue(name);
    } else if (data == "file_exists") {
      // try again with numeral appendix
      $().uxmessage('notice', "File already exists. Appending numeral.");
      save_and_add_to_job_queue(name+' - '+ queue_num_index, jobdata);
    } else {
      $().uxmessage('error', "Failed to store G-code.");
    }
  });
}

function add_to_job_queue(name) {
  //// delete excessive queue items
  var num_non_starred = 0;
  $.each($('#gcode_queue li'), function(index, li_item) {
    if ($(li_item).find('a span.icon-star-empty').length > 0) {
      num_non_starred++;
      if (num_non_starred > app_settings.max_num_queue_items-1) {
        remove_queue_item(li_item);
      }          
    }
  });
  //// add list item to page
  var star_class = 'icon-star-empty';
  if (name.slice(-8) == '.starred') {
    name = name.slice(0,-8);
    star_class = 'icon-star';
  }
  $('#gcode_queue').prepend('<li><a href="#"><span>'+ name +'</span><span class="starwidget '+ star_class +' pull-right" title=" star to keep in queue"></span></a></li>')
  $('span.starwidget').tooltip({delay:{ show: 1500, hide: 100}})  
  //// action for loading gcode
  $('#gcode_queue li:first a').click(function(){
    var name = $(this).children('span:first').text();
    if ($(this).find('span.icon-star').length > 0) {
      name = name + '.starred'
    }
    $.get("/queue/get/" + name, function(jobdata) {
      if (name.slice(-8) == '.starred') {
        name = name.slice(0,-8);
      }      
      load_into_job_widget(name, jobdata);
    }).error(function() {
      $().uxmessage('error', "File not found: " + name);
    });
    return false;   
  });   
  //// action for star
  $('#gcode_queue li:first a span.starwidget').click(function() {
    if ($(this).hasClass('icon-star')) {
      //// unstar
      $(this).removeClass('icon-star');
      $(this).addClass('icon-star-empty');
      $.get("/queue/unstar/" + name, function(data) {
        // ui already cahnged
        if (data != "1") {
          // on failure revert ui
          $(this).removeClass('icon-star-empty');
          $(this).addClass('icon-star');        
        }      
      }).error(function() {
        // on failure revert ui
        $(this).removeClass('icon-star-empty');
        $(this).addClass('icon-star');  
      });       
    } else {
      //// star
      $(this).removeClass('icon-star-empty');
      $(this).addClass('icon-star');
      $.get("/queue/star/" + name, function(data) {
        // ui already cahnged
        if (data != "1") {
          // on failure revert ui
          $(this).removeClass('icon-star');
          $(this).addClass('icon-star-empty');         
        }
      }).error(function() {
        // on failure revert ui
        $(this).removeClass('icon-star');
        $(this).addClass('icon-star-empty');  
      });        
    }
    return false;
  });
}


function remove_queue_item(li_item) {
  // request a delete
  name = $(li_item).find('a span:first').text();
  $.get("/queue/rm/" + name, function(data) {
    if (data == "1") {
      $(li_item).remove()
    } else {
      $().uxmessage('error', "Failed to delete queue item: " + name);
    }
  });  
}

function add_to_library_queue(jobdata, name) {
  if ((typeof(name) == 'undefined') || ($.trim(name) == '')) {
    var date = new Date();
    name = date.toDateString() +' - '+ queue_num_index
  }
  $('#job_library').prepend('<li><a href="#"><span>'+ name +'</span><i class="icon-star pull-right"></i><div style="display:none">'+ jobdata +'</div></a></li>')
  
  $('#job_library li a').click(function(){
    load_into_job_widget($(this).text(), $(this).next().text())
  });

  $('#job_library li a i').click(function(){
    $().uxmessage('success', "star ...");
  });
}



/// PASSES //////////////////////////////////////

function addPasses(num) {
  var pass_num_offset = getNumPasses() + 1;
  var buttons = ''
  for (var color in DataHandler.getColorOrder()) {
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
  // alert(JSON.stringify(passes))
  if (passes.length > 0) {
    for (var i=0; i<passes.length; i++) {
      var pass = passes[i];
      num = i+1;
      // alert(JSON.stringify([i, maxNumPassWidgets]))
      if (num <= maxNumPassWidgets) {
        //make sure to have enough pass widgets
        var passes_to_create = num - getNumPasses()
        if (passes_to_create >= 1) {
          addPasses(passes_to_create);
        }
        // feedrate
        $('#passes > div:nth-child('+num+') .feedrate').val(pass['feedrate']);
        // intensity
        $('#passes > div:nth-child('+num+') .intensity').val(pass['intensity']);
        // colors
        var colors = pass['colors'];
        for (var ii=0; ii<colors.length; ii++) {
          var col = colors[ii];
          var color_order = DataHandler.getColorOrder();
          if (col in color_order) {
            $('#passes > div:nth-child('+num+') .colorbtns button:eq('+color_order[col]+')').addClass('active active-strong')
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



///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////



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
  $("#job_submit").click(function(e) {
    // send gcode string to server via POST
    DataHandler.setByJson($('#job_data').val());
    if (readPassesWidget()) {
      send_gcode(DataHandler.getGcode(), "G-Code sent to backend.", true);
    } else {
      $().uxmessage('warning', "nothing to cut -> please assign colors to passes");
    }
    return false;
  });


  $('#job_bbox_submit').tooltip();
  $("#job_bbox_submit").click(function(e) {
    DataHandler.setByJson($('#job_data').val());
    if (readPassesWidget()) {
      send_gcode(DataHandler.getBboxGcode(), "BBox G-Code sent to backend", true);
    } else {
      $().uxmessage('warning', "nothing to cut -> please assign colors to passes");
    }
    return false;
  });

  $('#job_save_to_queue').tooltip();
  $("#job_save_to_queue").click(function(e) {
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
