
var hardware_ready_state = false;

(function($){
	$.fn.uxmessage = function(kind, text) {
	  if (text.length > 80) {
	    text = text.slice(0,100) + '\n...'
	  }
	  
  	if (kind == 'notice') {
  		$('#log_content').prepend('<div class="log_item log_notice well" style="display:none">' + text + '</div>');
  		$('#log_content').children('div').first().show('blind');
  		if ($("#log_content").is(':hidden')) {
    		$().toastmessage('showNoticeToast', text);
    	}
  	} else if (kind == 'success') {
  		$('#log_content').prepend('<div class="log_item log_success well" style="display:none">' + text + '</div>');
  		$('#log_content').children('div').first().show('blind');
  		if ($("#log_content").is(':hidden')) {
    		$().toastmessage('showSuccessToast', text);		
      }
  	} else if (kind == 'warning') {
  		$('#log_content').prepend('<div class="log_item log_warning well" style="display:none">' + text + '</div>');
  		$('#log_content').children('div').first().show('blind');
  		if ($("#log_content").is(':hidden')) {
    		$().toastmessage('showWarningToast', text);		
    	}
  	} else if (kind == 'error') {
  		$('#log_content').prepend('<div class="log_item log_error well" style="display:none">' + text + '</div>');
  		$('#log_content').children('div').first().show('blind');
  		if ($("#log_content").is(':hidden')) {
    		$().toastmessage('showErrorToast', text);		
    	}
  	}

  	while ($('#log_content').children('div').length > 200) {
  	  $('#log_content').children('div').last().remove();
  	}

	};
})(jQuery); 


function send_gcode(gcode, success_msg, progress) {
  if (hardware_ready_state || gcode[0] == '!' || gcode[0] == '~') {
    if (typeof gcode === "string" && gcode != '') {
      $.ajax({
        type: "POST",
        url: "/gcode",
        data: {'gcode_program':gcode},
        // dataType: "json",
        success: function (data) {
          if (data == "__ok__") {
            $().uxmessage('success', success_msg);
            if (progress = true) {
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
            }
          } else {
            $().uxmessage('error', "Backend error: " + data);
          }
        },
        error: function (data) {
          $().uxmessage('error', "Timeout. LasaurApp server down?");
        },
        complete: function (data) {
          // future use
        }
      });
    } else {
      $().uxmessage('error', "No gcode.");
    }
  } else {
    $().uxmessage('warning', "Not ready, request ignored.");
  }
}


var queue_num_index = 1;
function save_and_add_to_job_queue(name, gcode) {  
  if ((typeof(name) == 'undefined') || ($.trim(name) == '')) {
    var date = new Date();
    name = date.toDateString() +' - '+ queue_num_index
  }
  //// store gcode - on success add to queue
	$.post("/queue/save", { 'gcode_name':name, 'gcode_program':gcode }, function(data) {
		if (data == "1") {
		  queue_num_index += 1;
      add_to_job_queue(name);
    } else if (data == "file_exists") {
      // try again with numeral appendix
      $().uxmessage('notice', "File already exists. Appending numeral.");
      save_and_add_to_job_queue(name+' - '+ queue_num_index, gcode);
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
      if (num_non_starred > 7) {
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
    $.get("/queue/get/" + name, function(gdata) {
      if (name.slice(-8) == '.starred') {
        name = name.slice(0,-8);
      }      
      load_into_gcode_widget(gdata, name);
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

function add_to_library_queue(gcode, name) {
  if ((typeof(name) == 'undefined') || ($.trim(name) == '')) {
    var date = new Date();
    name = date.toDateString() +' - '+ queue_num_index
  }
	$('#gcode_library').prepend('<li><a href="#"><span>'+ name +'</span><i class="icon-star pull-right"></i><div style="display:none">'+ gcode +'</div></a></li>')
	
	$('#gcode_library li a').click(function(){
	  load_into_gcode_widget($(this).next().text(), $(this).text())
	});

	$('#gcode_library li a i').click(function(){
	  $().uxmessage('success', "star ...");
	});
}


function load_into_gcode_widget(gcode, name) {
	$('#gcode_name').val(name);
	$('#gcode_program').val(gcode);
	// make sure preview refreshes
	$('#gcode_program').trigger('blur');
}


function mapConstrainFeedrate(rate) {
  rate = parseInt(rate);
  if (rate < .1) {
    rate = .1;
    $().uxmessage('warning', "Feedrate constrained to 0.1");
  } else if (rate > 24000) {
    rate = 24000;
    $().uxmessage('warning', "Feedrate constrained to 24000");
  }
  return rate.toString();
}
  
function mapConstrainIntesity(intens) {
  intens = parseInt(intens);
  if (intens < 0) {
    intens = 0;
    $().uxmessage('warning', "Intensity constrained to 0");
  } else if (intens > 100) {
    intens = 100;
    $().uxmessage('warning', "Intensity constrained to 100");
  }
  //map to 255 for now until we change the backend
  return Math.round(intens * 2.55).toString();
}






$(document).ready(function(){
  
  $().uxmessage('notice', "app frontend started");
  
  $('#tab_logs_button').click(function(){
    $('#log_content').show()
    $('#tab_logs div.alert').show()
  })

  //////// serial connect and pause button ////////
  var connect_btn_state = false;
  var connect_btn_in_hover = false;
  var pause_btn_state = false;

  function connect_btn_set_state(is_connected) {
    if (is_connected) {
      connect_btn_state = true
      if (!connect_btn_in_hover) {
        $("#connect_btn").html("Connected");
      }
      $("#connect_btn").removeClass("btn-danger");
      $("#connect_btn").removeClass("btn-warning");
      $("#connect_btn").addClass("btn-success");      
    } else {
  		connect_btn_state = false
      if (!connect_btn_in_hover) {
        $("#connect_btn").html("Disconnected");
      }		
      $("#connect_btn").removeClass("btn-danger");
  	  $("#connect_btn").removeClass("btn-success");
  	  $("#connect_btn").addClass("btn-warning");     
    }
  }
    
  // get hardware status
  function poll_hardware_status() {
    $.getJSON('/status', function(data) {
      // pause status
      if (data.paused) {
        pause_btn_state = true;
        $("#pause_btn").addClass("btn-primary");
        $("#pause_btn").html('<i class="icon-play"></i>');
      } else {
        pause_btn_state = false;
        $("#pause_btn").removeClass("btn-warning");
        $("#pause_btn").removeClass("btn-primary");
        $("#pause_btn").html('<i class="icon-pause"></i>');
      }
      // serial connected
      if (data.serial_connected) {
        connect_btn_set_state(true);
      } else {
        connect_btn_set_state(false);
      }

      // ready state
      if (data.ready) {
        hardware_ready_state = true;
        $("#connect_btn").html("Ready");
      } else {
        if (data.serial_connected) {
          $("#connect_btn").html("Busy");
        }
        hardware_ready_state = false;
      }

      // door, chiller, power, limit, buffer
      if (data.serial_connected) {
        if (data.door_open) {
          $('#door_status_btn').removeClass('btn-success')
          $('#door_status_btn').addClass('btn-warning') 
          // $().uxmessage('warning', "Door is open!");
        } else {
          $('#door_status_btn').removeClass('btn-warning')
          $('#door_status_btn').addClass('btn-success')         
        }
        if (data.chiller_off) {
          $('#chiller_status_btn').removeClass('btn-success')
          $('#chiller_status_btn').addClass('btn-warning')           
          // $().uxmessage('warning', "Chiller is off!"); 
        } else {
          $('#chiller_status_btn').removeClass('btn-warning')
          $('#chiller_status_btn').addClass('btn-success')
        }
        if (data.power_off) {
          $().uxmessage('error', "Power is off!"); 
          $().uxmessage('notice', "Turn on Lasersaur power then run homing cycle to reset.");          
        }
        if (data.limit_hit) {
          $().uxmessage('error', "Limit hit!");
          $().uxmessage('notice', "Run homing cycle to reset stop mode.");
        }
        if (data.buffer_overflow) {
          $().uxmessage('error', "Rx Buffer Overflow!");
          $().uxmessage('notice', "Please report this to the author of this software.");
        }        
        if (data.transmission_error) {
          $().uxmessage('error', "Transmission Error!");
          $().uxmessage('notice', "If this happens a lot tell the author of this software.");
        }    
        if (data.firmware_version && !firmware_version_reported) {
          $().uxmessage('notice', "LasaurGrbl " + data.firmware_version);
          firmware_version_reported = true
        }
      }
    }).error(function() {
      // lost connection to server
      connect_btn_set_state(false); 
    });
  }
  // call once, to get immediate status
    poll_hardware_status();
  // register with timed callback
  var firmware_version_reported = false
  var connectiontimer = setInterval(function() {
    poll_hardware_status();
  }, 4000);

  connect_btn_width = $("#connect_btn").innerWidth();
  $("#connect_btn").width(connect_btn_width);
  $("#connect_btn").click(function(e){	
  	if (connect_btn_state == true) {
  		$.get('/serial/0', function(data) {
  			if (data != "") {
  				connect_btn_set_state(false);   
  			} else {
  			  // was already disconnected
  			  connect_btn_set_state(false);
  			}
  			$("#connect_btn").html("Disconnected");
  		});
  	}	else {
  	  $("#connect_btn").html('Connecting...');
  		$.get('/serial/1', function(data) {
  			if (data != "") {
  			  connect_btn_set_state(true);
  			  $("#connect_btn").html("Connected");		  
  			} else {
  			  // failed to connect
  			  connect_btn_set_state(false);
		  	  $("#connect_btn").removeClass("btn-warning");
      	  $("#connect_btn").addClass("btn-danger");  
  			}		
  		});
  	}	
  	e.preventDefault();		
  });	
  $("#connect_btn").hover(
    function () {
      connect_btn_in_hover = true;
      if (connect_btn_state) {
        $(this).html("Disconnect");
      } else {
        $(this).html("Connect");
      }
      $(this).width(connect_btn_width);
    }, 
    function () {
      connect_btn_in_hover = false;
      if (connect_btn_state) {
        $(this).html("Connected");
      } else {
        $(this).html("Disconnected");
      }
      $(this).width(connect_btn_width);      
    }
  );

  $("#pause_btn").tooltip({placement:'bottom', delay: {show:500, hide:100}});
  $("#pause_btn").click(function(e){  
    if (pause_btn_state == true) {  // unpause
      $.get('/pause/0', function(data) {
        if (data != "") {
          pause_btn_state = false;
          $("#pause_btn").removeClass('btn-primary');
          $("#pause_btn").removeClass('btn-warning');
          $("#pause_btn").html('<i class="icon-pause"></i>');
        }
      });
    } else {  // pause
      $("#pause_btn").addClass('btn-warning');
      $.get('/pause/1', function(data) {
        if (data != "") {
          pause_btn_state = true;
          $("#pause_btn").removeClass("btn-warning");
          $("#pause_btn").addClass('btn-primary');
          $("#pause_btn").html('<i class="icon-play"></i>');
          $().uxmessage('notice', "Pausing (after finishing hardware buffer)");
        } else {
          // failed to pause, nothing processing?
          $("#pause_btn").removeClass("btn-warning");
        }   
      });
    } 
    e.preventDefault();   
  }); 
  //\\\\\\ serial connect and pause button \\\\\\\\
  
  
  $("#cancel_btn").tooltip({placement:'bottom', delay: {show:500, hide:100}});
  $("#cancel_btn").click(function(e){
  	var gcode = '!\n'  // ! is enter stop state char
  	$().uxmessage('notice', gcode.replace(/\n/g, '<br>'));
  	send_gcode(gcode, "Stopping ...", false);	
	  var delayedresume = setTimeout(function() {
    	var gcode = '~\nG90\nM81\nG0X0Y0F20000\n'  // ~ is resume char
    	$().uxmessage('notice', gcode.replace(/\n/g, '<br>'));
    	send_gcode(gcode, "Resetting ...", false);
	  }, 1000);
  	e.preventDefault();		
  });
  
  $("#homing_cycle").tooltip({placement:'bottom', delay: {show:500, hide:100}});
  $("#homing_cycle").click(function(e){
    var gcode = '!\n'  // ! is enter stop state char
    $().uxmessage('notice', gcode.replace(/\n/g, '<br>'));
    send_gcode(gcode, "Resetting ...", false); 
    var delayedresume = setTimeout(function() {
      var gcode = '~\nG30\n'  // ~ is resume char
      $().uxmessage('notice', gcode.replace(/\n/g, '<br>'));
      send_gcode(gcode, "Homing cycle ...", false);
    }, 1000);
    e.preventDefault(); 

  });

  $("#go_to_origin").tooltip({placement:'bottom', delay: {show:500, hide:100}});
  $("#go_to_origin").click(function(e){
    var gcode;
    if(e.shiftKey) {
    	// also reset offset
    	reset_offset();
    }
    gcode = 'G90\nG0X0Y0F16000\n'
    // $().uxmessage('notice', gcode);  
  	send_gcode(gcode, "Going to origin ...", false);
  	e.preventDefault();		
  });  

  $("#reset_atmega").click(function(e){
    $.get('/reset_atmega', function(data) {
      if (data != "") {
        $().uxmessage('success', "Atmega restarted!");
      } else {
        $().uxmessage('error', "Atmega restart failed!");
      }   
    });
    e.preventDefault();   
  });
  
});  // ready
