
$(document).ready(function(){
  
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


});