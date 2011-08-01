

(function($){
	$.fn.uxmessage = function(kind, text) {
	  var div_opener = '<div class="log_item log_notice ui-corner-all" style="display:none">'
  	if (kind == 'notice') {
  		$('#log_content').prepend('<div class="log_item log_notice ui-corner-all" style="display:none">' + text + '</div>');
  		$('#log_content').children('div').first().show('blind');
  		if ($("#log_content").is(':hidden')) {
    		$().toastmessage('showNoticeToast', text.slice(0,100));
    	}
  	} else if (kind == 'success') {
  		$('#log_content').prepend('<div class="log_item log_success ui-corner-all" style="display:none">' + text + '</div>');
  		$('#log_content').children('div').first().show('blind');
  		if ($("#log_content").is(':hidden')) {
    		$().toastmessage('showSuccessToast', text.slice(0,100));		
      }
  	} else if (kind == 'warning') {
  		$('#log_content').prepend('<div class="log_item log_warning ui-corner-all" style="display:none">' + text + '</div>');
  		$('#log_content').children('div').first().show('blind');
  		if ($("#log_content").is(':hidden')) {
    		$().toastmessage('showWarningToast', text.slice(0,100));		
    	}
  	} else if (kind == 'error') {
  		$('#log_content').prepend('<div class="log_item log_error ui-corner-all" style="display:none">' + text + '</div>');
  		$('#log_content').children('div').first().show('blind');
  		if ($("#log_content").is(':hidden')) {
    		$().toastmessage('showErrorToast', text.slice(0,100));		
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



$(document).ready(function(){

  $(function() {
  	$( "#tabs-main" ).tabs({
  		selected: 0
  	});
  });


  $('#log_toggle').toggle(function() {
    $("#log_content").fadeIn('slow');
  	$("#log_toggle").html("hide log");
  }, function() {
    $("#log_content").fadeOut('slow');
  	$("#log_toggle").html("show log");
  });


  // connect to serial button
  //	
  $("#serial_connection").button();
  // get serial state
  $.get('/serial/2', function(data) {
  	if (data != "") {
  		$().uxmessage('notice', "Serial is Connected");		
  		$("#serial_connection").val('1');
  		$("#serial_connection").button('option', 'label', 'Disconnect');		
  	} else {
  		$().uxmessage('notice', "Serial is Disconnected");
  		$("#serial_connection").val('0');
  		$("#serial_connection").button('option', 'label', 'Connect');
  	}		
  });
  $("#serial_connection").click(function(e){	
  	if ($("#serial_connection").val() == '1') {
  		$.get('/serial/0', function(data) {
  			if (data != "") {
  				$().uxmessage('success', "Serial Disconnected");
  			} else {
  				$().uxmessage('success', "Serial was already disonnected.");
  			}
  			$("#serial_connection").val('0');
  			$("#serial_connection").button('option', 'label', 'Connect');	
  		});
  	}	else {
  		$.get('/serial/1', function(data) {
  			if (data != "") {
  				$().uxmessage('success', "Serial Connected");
  				$().uxmessage('notice', data);				
  				$("#serial_connection").val('1');
  				$("#serial_connection").button('option', 'label', 'Disconnect');
  			} else {
  				$().uxmessage('error', "Failed to Connect");
  			}		
  		});
  	}	
  	e.preventDefault();		
  });	

  //$("#find_home").button();
  $("#find_home").click(function(e){
  	var gcode = 'G30\n'
  	$().uxmessage('notice', gcode);	
  	$.get('/gcode/'+ gcode, function(data) {
  		if (data != "") {
  			$().uxmessage('success', "G-Code sent to serial.");
  		} else {
  			$().uxmessage('error', "Serial not connected.");
  		}
  	});
  	e.preventDefault();		
  });

  //$("#go_home").button();
  $("#go_home").click(function(e){
  	var gcode = 'G0X0Y0F20000\n'
  	$().uxmessage('notice', gcode);	
  	$.get('/gcode/'+ gcode, function(data) {
  		if (data != "") {
  			$().uxmessage('success', "G-Code sent to serial.");
  		} else {
  			$().uxmessage('error', "Serial not connected.");
  		}
  	});
  	e.preventDefault();		
  });

  $("#escape_fire").button();
  $("#escape_fire").click(function(e){
  	var gcode = 'M112X0Y0F20000\n'
  	$().uxmessage('notice', gcode.replace(/\n/g, '<br>'));	
  	$.get('/gcode/'+ gcode, function(data) {
  		if (data != "") {
  			$().uxmessage('success', "G-Code sent to serial.");
  		} else {
  			$().uxmessage('error', "Serial not connected.");
  		}
  	});
  	e.preventDefault();		
  });

});  // ready
