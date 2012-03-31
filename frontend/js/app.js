

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
  $.get('/serial/2', function(data) {
  	if (data != "") {
  		$().uxmessage('notice', "Serial is Connected");		
  		$("#connection_btn").val('1');
  		$("#connection_btn").button('option', 'label', 'Disconnect');		
  	} else {
  		$().uxmessage('notice', "Serial is Disconnected");
  		$("#connection_btn").val('0');
  		$("#connection_btn").button('option', 'label', 'Connect');
  	}		
  });
  $("#connection_btn").click(function(e){	
  	if ($("#connection_btn").val() == '1') {
  		$.get('/serial/0', function(data) {
  			if (data != "") {
  				$().uxmessage('success', "Serial Disconnected");
  			} else {
  				$().uxmessage('success', "Serial was already disonnected.");
  			}
  			$("#connection_btn").val('0');
  			$("#connection_btn").button('option', 'label', 'Connect');	
  		});
  	}	else {
  		$.get('/serial/1', function(data) {
  			if (data != "") {
  				$().uxmessage('success', "Serial Connected");
  				$().uxmessage('notice', data);				
  				$("#connection_btn").val('1');
  				$("#connection_btn").button('option', 'label', 'Disconnect');
  			} else {
  				$().uxmessage('error', "Failed to Connect");
  			}		
  		});
  	}	
  	e.preventDefault();		
  });	

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
