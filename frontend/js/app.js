

(function($){
	$.fn.uxmessage = function(kind, text) {
	  if (text.length > 80) {
	    text = text.slice(0,100) + '\n...'
	  }
	  
	  var div_opener = '<div class="log_item log_notice ui-corner-all" style="display:none">'
  	if (kind == 'notice') {
  		$('#log_content').prepend('<div class="log_item log_notice ui-corner-all" style="display:none">' + text + '</div>');
  		$('#log_content').children('div').first().show('blind');
  		if ($("#log_content").is(':hidden')) {
    		$().toastmessage('showNoticeToast', text);
    	}
  	} else if (kind == 'success') {
  		$('#log_content').prepend('<div class="log_item log_success ui-corner-all" style="display:none">' + text + '</div>');
  		$('#log_content').children('div').first().show('blind');
  		if ($("#log_content").is(':hidden')) {
    		$().toastmessage('showSuccessToast', text);		
      }
  	} else if (kind == 'warning') {
  		$('#log_content').prepend('<div class="log_item log_warning ui-corner-all" style="display:none">' + text + '</div>');
  		$('#log_content').children('div').first().show('blind');
  		if ($("#log_content").is(':hidden')) {
    		$().toastmessage('showWarningToast', text);		
    	}
  	} else if (kind == 'error') {
  		$('#log_content').prepend('<div class="log_item log_error ui-corner-all" style="display:none">' + text + '</div>');
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


connect_btn_state = false;
connect_btn_in_hover = false;
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


var queue_num_index = 0;
function add_to_job_queue(gcode, name) {
	queue_num_index += 1;  
  if ((typeof(name) == 'undefined') || ($.trim(name) == '')) {
    var date = new Date();
    name = date.toDateString() +' - '+ queue_num_index
  }
	if (queue_num_index > 10) {
		// remove old items
		$('#gcode_queue').children('a').last().remove();
		$('#gcode_queue').children('div').last().remove();
	}
	$('#gcode_queue').prepend('<a href="#">'+ name +'</a>\n<div>'+ gcode +'</div>\n')
	$('#gcode_queue a').click(function(){
	  $('#gcode_name').val( $(this).text() );
		$('#gcode_program').val( $(this).next().text() );

		// make sure preview refreshes
		$('#gcode_program').trigger('blur');	
	});	
}


function preview_job(gcode, name) {
	$('#gcode_name').val(name);
	$('#gcode_program').val(gcode);
	// make sure preview refreshes
	$('#gcode_program').trigger('blur');
}



$(document).ready(function(){

  $('#log_toggle').toggle(function() {
    $("#log_content").fadeIn('slow');
  	$("#log_toggle").html("hide log");
  }, function() {
    $("#log_content").fadeOut('slow');
  	$("#log_toggle").html("show log");
  });
  //$('#log_toggle').trigger('click');  // show log, for debugging


  //// connect to serial button
  // get serial state
  var connectiontimer = setInterval(function() {
    $.ajax({
        url: '/serial/2',
        success: function( data ) {
        	if (data != "") {
        	  connect_btn_set_state(true);
        	} else {
        	  connect_btn_set_state(false);
        	}
        },
        error: function(request, status, error) {
          // lost connection to server
      		connect_btn_set_state(false); 
        }
    });
  }, 3000);
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
  
  

  $("#cancel_btn").click(function(e){
  	var gcode = '!\n'  // ! is enter stop state char
  	$().uxmessage('notice', gcode.replace(/\n/g, '<br>'));	
  	$.get('/gcode/'+ gcode, function(data) {
  		if (data != "") {
  			$().uxmessage('success', "Stopping ...");
  		} else {
  			$().uxmessage('error', "Serial not connected.");
  		}
  	});
	  var delayedresume = setTimeout(function() {
    	var gcode = '~\nG0X0Y0F20000\n'  // ~ is resume char
    	$().uxmessage('notice', gcode.replace(/\n/g, '<br>'));	
    	$.get('/gcode/'+ gcode, function(data) {
    		if (data != "") {
    			$().uxmessage('success', "Resetting ...");
    		} else {
    			$().uxmessage('error', "Serial not connected.");
    		}
    	});
	  }, 1000);
  	e.preventDefault();		
  });
  
  $("#find_home").click(function(e){
  	var gcode = '~G30\n'  // ~ is the cancel stop state char
  	$().uxmessage('notice', gcode);	
  	$.get('/gcode/'+ gcode, function(data) {
  		if (data != "") {
  			$().uxmessage('success', "Homing cycle ...");
  		} else {
  			$().uxmessage('error', "Serial not connected.");
  		}
  	});
  	e.preventDefault();		
  });

  $("#go_to_origin").click(function(e){
  	var gcode = 'G0X0Y0F20000\n'
  	$().uxmessage('notice', gcode);	
  	$.get('/gcode/'+ gcode, function(data) {
  		if (data != "") {
  			$().uxmessage('success', "Going to origin ...");
  		} else {
  			$().uxmessage('error', "Serial not connected.");
  		}
  	});
  	e.preventDefault();		
  });
  
  $("#set_custom_offset").click(function(e){
  	var gcode = 'G10L20P1\nG55\n'
  	$().uxmessage('notice', gcode);	
  	$.get('/gcode/'+ gcode, function(data) {
  		if (data != "") {
  			$().uxmessage('success', "Setting custom offset ...");
  		} else {
  			$().uxmessage('error', "Serial not connected.");
  		}
  	});
  	e.preventDefault();		
  });
  
  $("#use_table_offset").click(function(e){
  	var gcode = 'G54\n'
  	$().uxmessage('notice', gcode);	
  	$.get('/gcode/'+ gcode, function(data) {
  		if (data != "") {
  			$().uxmessage('success', "Using table offset ...");
  		} else {
  			$().uxmessage('error', "Serial not connected.");
  		}
  	});
  	e.preventDefault();		
  });
  
  
});  // ready
