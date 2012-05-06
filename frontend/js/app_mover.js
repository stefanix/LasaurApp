$(document).ready(function(){

  $("#cutting_area").click(function(e) {
  	var offset = $('#cutting_area').offset();
  	var x = 2*(e.pageX - offset.left);
  	var y = 2*(e.pageY - offset.top);
	
  	var g0_or_g1 = 'G0'
  	if($('#feed_btn').hasClass("active")){
  		g0_or_g1 = 'G1';
  	}
  	var feedrate = parseInt($( "#feedrate_field" ).val());
  	if (feedrate < 40) {feedrate = 40;} else if (feedrate > 30000) {feedrate = 30000;}
  	var intensity =  parseInt($( "#intensity_field" ).val());
  	if (intensity < 0) {intensity = 0;} else if (intensity > 255) {intensity = 255;}
  	var gcode = 'S'+ intensity + '\nG54\n' + g0_or_g1 + ' X' + x + 'Y' + y + 'F' + feedrate + '\nS0\n';
	
	
  	// send new pos to server, on success move graphics
    // $().uxmessage('notice', gcode);
  	send_gcode_line(gcode, "Motion request sent via g54 coordinate system.", "Serial not connected.")	
  });


  $("#cutting_area").hover(
    function () {
  		$(this).css('border', '1px dashed #ff0000');
  		$(this).css('cursor', 'crosshair');
    },
    function () {
  		$(this).css('border', '1px dashed #aaaaaa');
  		$(this).css('cursor', 'pointer');	
  		$('#coordinates_info').text('');		
    }
  );
  
  $("#cutting_area").mousemove(function (e) {
  	var offset = $(this).offset();
  	var x = 2*(e.pageX - offset.left);
  	var y = 2*(e.pageY - offset.top);    
  	var move_or_cut = 'move';
  	if($('#feed_btn').hasClass("active")){
  		move_or_cut = 'cut';
  	}
  	var feedrate = parseInt($( "#feedrate_field" ).val());
  	if (feedrate < 40) {feedrate = 40;} else if (feedrate > 30000) {feedrate = 30000;}
  	var intensity =  parseInt($( "#intensity_field" ).val());
  	if (intensity < 0) {intensity = 0;} else if (intensity > 255) {intensity = 255;}
  	var coords_text;
  	if (move_or_cut == 'cut') {
  	  coords_text = move_or_cut + ' to (' + x + ', '+ y + ') at ' + feedrate + 'mm/min and ' + intensity + ' intensity';
  	} else {
  	  coords_text = move_or_cut + ' to (' + x + ', '+ y + ') at ' + feedrate + 'mm/min'
  	}
    $('#coordinates_info').text(coords_text);
  });  

  // function moveto (x, y) {
  //  $('#y_cart').animate({  
  //    top: y - 8.5 - 6
  //  });   
  //  
  //  $('#x_cart').animate({  
  //    left: x - 6,  
  //    top: y - 6 
  //  });
  // };
  
  //// motion parameters
  $( "#intensity_field" ).val('0');
  
  $("#seek_btn").click(function(e) {
    $( "#intensity_input_div" ).hide();
  });  
  $("#feed_btn").click(function(e) {
    $( "#intensity_input_div" ).show();
  });   
  
  $("#feedrate_btn_slow").click(function(e) {
    $( "#feedrate_field" ).val("400");
  });  
  $("#feedrate_btn_medium").click(function(e) {
    $( "#feedrate_field" ).val("2000");
  });  
  $("#feedrate_btn_fast").click(function(e) {
    $( "#feedrate_field" ).val("16000");
  });  
  $("#feedrate_field").focus(function(e) {
    $("#feedrate_btn_slow").removeClass('active');
    $("#feedrate_btn_medium").removeClass('active');
    $("#feedrate_btn_fast").removeClass('active');
  }); 
  
  //// jog buttons
  $("#jog_up_btn").click(function(e) {
    var gcode = 'G91\nG0Y-10F10000\nG90\n';
    send_gcode_line(gcode, "Moving Up ...", "Serial not connected.")	
  });   
  $("#jog_left_btn").click(function(e) {
    var gcode = 'G91\nG0X-10F10000\nG90\n';
    send_gcode_line(gcode, "Moving Left ...", "Serial not connected.")	
  });   
  $("#jog_right_btn").click(function(e) {
    var gcode = 'G91\nG0X10F10000\nG90\n';
    send_gcode_line(gcode, "Moving Right ...", "Serial not connected.")	
  });
  $("#jog_down_btn").click(function(e) {
    var gcode = 'G91\nG0Y10F10000\nG90\n';
    send_gcode_line(gcode, "Moving Down ...", "Serial not connected.")	
  });
      
});  // ready
