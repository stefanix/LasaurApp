$(document).ready(function(){

  $("#cutting_area").click(function(e) {

  	//var x = (e.pageX - this.offsetLeft);
  	//var y = (e.pageY - this.offsetTop);

  	var offset = $('#lasaur_widget').offset();
  	var x = (e.pageX - offset.left);
  	var y = (e.pageY - offset.top);
	
  	var pos = $(this).position();
  	var lasaur_coord_x = 4*(x - pos.left);
  	var lasaur_coord_y = 4*(y - pos.top);
  	// cap
  	if (lasaur_coord_x > 1220) { lasaur_coord_x = 1220; }
  	if (lasaur_coord_y > 620) { lasaur_coord_y = 620; }
	
  	var g0_or_g1
  	if($('#radio_g1').is(":checked")){
  		g0_or_g1 = 'G1';
  	}	else {
  		g0_or_g1 = 'G0';	
  	}
  	var feedrate = $( "#feedrate_field" ).val();
  	var gcode = 'g54\n' + g0_or_g1 + ' X' + parseInt(lasaur_coord_x) + 'Y' + parseInt(lasaur_coord_y) + 'F' + feedrate + '\n';
	
  	$().uxmessage('notice', gcode);
	
  	// send new pos to server, on success move graphics
  	$.get('/gcode/'+ gcode, function(data) {
  		if (data != "") {
  			$().uxmessage('success', "Motion request sent via g54 coordinate system.");
  			moveto(x, y);
  		} else {
  			$().uxmessage('error', "Serial not connected.");
  		}
  	});
	
  });

  $('#seek_btn').button('toggle');
  
  $('#move_type_radio').buttonset();
  $("#feedrate").slider({ min:50, max:20000, value:$('#feedrate_field').val() });
  $("#feedrate").bind( "slide", function(event, ui) {
  	$('#feedrate_field').val($('#feedrate').slider("option", "value"));
  });
  $("#feedrate").bind( "slidestop", function(event, ui) {
  	$('#feedrate_field').val($('#feedrate').slider("option", "value"));
  });

  $("#cutting_area").hover(
    function () {
  		$(this).css('border', '1px solid #ff0000');
  		$(this).css('cursor', 'crosshair');
    },
    function () {
  		$(this).css('border', '1px solid #888888');
  		$(this).css('cursor', 'pointer');			
    }
  );	

  function moveto (x, y) {
  	$('#y_cart').animate({  
  		top: y - 8.5 - 6
  	}); 	
	
  	$('#x_cart').animate({  
  		left: x - 6,  
  		top: y - 6 
  	});
  };

});  // ready
