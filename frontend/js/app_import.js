$(document).ready(function(){
  
  var geo_boundarys = null;
  var raw_gcode = null;
  var raw_gcode_by_color = null;
  var path_optimize = true;
  var forceSvgDpiTo = undefined;
  
  // G-Code Canvas Preview
  var icanvas = new Canvas('#import_canvas');
  icanvas.width = 610;  // HACK: for some reason the canvas can't figure this out itself
  icanvas.height = 305; // HACK: for some reason the canvas can't figure this out itself
  icanvas.background('#ffffff'); 
  
  
  // file upload form
  $('#svg_upload_file').change(function(e){
    $('#svg_import_btn').button('loading');
    $('#svg_loading_hint').show();
    var input = $('#svg_upload_file').get(0)
    var browser_supports_file_api = true;
    if (typeof window.FileReader !== 'function') {
      browser_supports_file_api = false;
      $().uxmessage('notice', "This requires a modern browser with File API support.");
    } else if (!input.files) {
      browser_supports_file_api = false;
      $().uxmessage('notice', "This browser does not support the files property.");
    }
    
    if (browser_supports_file_api) {
      if (input.files[0]) {
        var fr = new FileReader()
        fr.onload = sendToBackend
        fr.readAsText(input.files[0])
      } else {
        $().uxmessage('error', "No file was selected.");
      }
    } else {  // fallback
      // $().uxmessage('notice', "Using fallback: file form upload.");
    }
    
    // reset file input form field so change event also triggers if
    // same file is chosen again (but with different dpi)
    $('#svg_upload_file_temp').val($('#svg_upload_file').val())
    $('#svg_upload_file').val('')

  	e.preventDefault();
  });


  function sendToBackend(e) {
    var filedata = e.target.result;
    var fullpath = $('#svg_upload_file_temp').val();
    var filename = fullpath.split('\\').pop().split('/').pop();    
    $().uxmessage('notice', "parsing SVG ...");
    $.ajax({
      type: "POST",
      url: "/svg_reader",
      data: {'filename':filename,'filedata':filedata, 'dpi':forceSvgDpiTo},
      dataType: "json",
      success: function (data) {
        $().uxmessage('success', "SVG parsed."); 
        $('#dpi_import_info').html('Using <b>' + data.dpi + 'dpi</b> for converting px units.');
        // alert(JSON.stringify(data));
        geo_boundarys = data.boundarys
        generateRawGcode();
      },
      error: function (data) {
        $().uxmessage('error', "backend error.");
      },
      complete: function (data) {
        $('#svg_import_btn').button('reset');
        forceSvgDpiTo = undefined;  // reset
      }
    })
  }
      
  function generateRawGcode() {
    if (geo_boundarys) {
      raw_gcode_by_color = {};
      for (var color in geo_boundarys) {
        raw_gcode_by_color[color] = GcodeWriter.write(geo_boundarys[color], 1, 0.0, 0.0);
      }
      //// add canvas color properties
      $('#canvas_properties div.colorbtns').html('');  // reset colors
      $('#pass_1_div div.colorbtns').html('');  // reset colors
      $('#pass_2_div div.colorbtns').html('');  // reset colors
      $('#pass_3_div div.colorbtns').html('');  // reset colors
      for (var color in raw_gcode_by_color) {
				$('#canvas_properties div.colorbtns').append('<button class="preview_color active-strong btn btn-small active" style="margin:2px"><div style="width:10px; height:10px; background-color:'+color+'"><span style="display:none">'+color+'</span></div></button>');          
				$('#pass_1_div div.colorbtns').append('<button class="select_color btn btn-small" data-toggle="button" style="margin:2px"><div style="width:10px; height:10px; background-color:'+color+'"><span style="display:none">'+color+'</span></div></div></button>');        
				$('#pass_2_div div.colorbtns').append('<button class="select_color btn btn-small" data-toggle="button" style="margin:2px"><div style="width:10px; height:10px; background-color:'+color+'"><span style="display:none">'+color+'</span></div></div></button>');        
				$('#pass_3_div div.colorbtns').append('<button class="select_color btn btn-small" data-toggle="button" style="margin:2px"><div style="width:10px; height:10px; background-color:'+color+'"><span style="display:none">'+color+'</span></div></div></button>');        
      }
      $('#canvas_properties div.colorbtns').append('<div style="margin-top:10px">These color toggles affect the preview only.</div>');      
      // register redraw event
			$('button.preview_color').click(function(e){
			  // toggling manually, had problem with automatic
			  if($(this).hasClass('active')) {
			    $(this).removeClass('active');
			    $(this).removeClass('active-strong');
			  } else {
			    $(this).addClass('active');			    
			    $(this).addClass('active-strong');			    
			  }
        generatePreview();
      });
			$('button.select_color').click(function(e){
			  // increase button state visually
			  if($(this).hasClass('active')) {
			    $(this).removeClass('active-strong');
			  } else {
			    $(this).addClass('active-strong');	    
			  }
      });
      // actually redraw right now 
      generatePreview();      
    } else {
      $().uxmessage('notice', "No data loaded to write G-code.");
    }   
  }
  
  function generatePreview() {
    if (raw_gcode_by_color) {        
      var exclude_colors =  {};
      $('#canvas_properties div.colorbtns button').each(function(index) {
        if (!($(this).hasClass('active'))) {
          // alert(JSON.stringify($(this).find('div i').text()));
          exclude_colors[$(this).find('div span').text()] = 1;
        }
      });
      
      icanvas.background('#ffffff');
      // var bbox_list = [];
      var scale = 0.5;
      for (var color in raw_gcode_by_color) {
        if (!(color in exclude_colors)) {
          GcodeReader.parse(raw_gcode_by_color[color], scale);
          GcodeReader.draw(icanvas, color);
          // bbox_list.push([GcodeReader.bbox[0],GcodeReader.bbox[1],GcodeReader.bbox[2],GcodeReader.bbox[3]]);
        }
      }
      // // combine all bounding boxes and report on log
      // var overall_bbox = [0,0,0,0];
      // for (var bbidx in bbox_list) {
      //   var bbox = bbox_list[bbidx];
      //   overall_bbox = bboxExpand(overall_bbox, bbox[0], bbox[1])
      //   overall_bbox = bboxExpand(overall_bbox, bbox[2], bbox[3])
      // }
      // var bbox_width = (overall_bbox[2] - overall_bbox[0]) / scale;
      // var bbox_height = (overall_bbox[3] - overall_bbox[1]) / scale;
      // $().uxmessage('notice', "The calculated bounding box is " 
      //   + bbox_width.toFixed(1) + 'x' + bbox_height.toFixed(1) + 'mm'
      //   + ' (' + (bbox_width/25.4).toFixed(1) + 'x' + (bbox_height/25.4).toFixed(1) + 'in).');      
    } else {
      $().uxmessage('notice', "No data loaded to generate preview.");
    }       
  }

  // function bboxExpand(bbox, x,y) {
  //   var bbox_new = [bbox[0],bbox[1],bbox[2],bbox[3]];
  //   if (x < bbox[0]) {bbox_new[0] = x;}
  //   else if (x > bbox[2]) {bbox_new[2] = x;}
  //   if (y < bbox[1]) {bbox_new[1] = y;}
  //   else if (y > bbox[3]) {bbox_new[3] = y;}
  //   return bbox_new;
  // }

  // forwarding file open click
  $('#svg_import_btn').click(function(e){
    path_optimize = true;
    $('#svg_upload_file').trigger('click');
  });  
  $('#svg_import_72_btn').click(function(e){
    path_optimize = true;
    forceSvgDpiTo = 72;
    $('#svg_upload_file').trigger('click');
    return false;
  });
  $('#svg_import_90_btn').click(function(e){
    path_optimize = true;
    forceSvgDpiTo = 90;
    $('#svg_upload_file').trigger('click');
    return false;
  });
  $('#svg_import_96_btn').click(function(e){
    path_optimize = true;
    forceSvgDpiTo = 96;
    $('#svg_upload_file').trigger('click');
    return false;
  });    
  $('#svg_import_nop_btn').click(function(e){
    path_optimize = false;
    $('#svg_upload_file').trigger('click');
    return false;
  });  

    
  $('#import_feedrate_1').tooltip();
  $('#import_intensity_1').tooltip();
  $('#import_feedrate_2').tooltip();
  $('#import_intensity_2').tooltip();
  $('#import_feedrate_3').tooltip();
  $('#import_intensity_3').tooltip();
  
  // setting up add to queue button
  $("#import_to_queue").click(function(e) {            
    // assemble multiple passes
    var gcodeparts = ["%\nG21\nG90\n"];
    var feedrate;
    var intensity;
    var colors = {};
    var any_assingments = false;
    //// pass 1
    $('#pass_1_div div.colorbtns button').each(function(index) {
      if ($(this).hasClass('active')) {
        colors[$(this).find('div span').text()] = 1;
      }
    });
    if (Object.keys(colors).length > 0) { 
      any_assingments = true;
      feedrate = mapConstrainFeedrate($("#import_feedrate_1").val());
      intensity = mapConstrainIntesity($("#import_intensity_1").val());
      gcodeparts.push("S"+intensity+"\nG1 F"+feedrate+"\nG0 F10000\n");
      for (var color in raw_gcode_by_color) {
        if(color in colors) {
          gcodeparts.push(raw_gcode_by_color[color]);
        }
      }
    }
    //// pass 2
    colors = {}
    $('#pass_2_div div.colorbtns button').each(function(index) {
      if ($(this).hasClass('active')) {
        colors[$(this).find('div span').text()] = 1;
      }
    });    
    if (Object.keys(colors).length > 0) { 
      any_assingments = true;
      feedrate = mapConstrainFeedrate($("#import_feedrate_2").val());
      intensity = mapConstrainIntesity($("#import_intensity_2").val());
      gcodeparts.push("S"+intensity+"\nG1 F"+feedrate+"\nG0 F10000\n");
      for (var color in raw_gcode_by_color) {
        if(color in colors) {
          gcodeparts.push(raw_gcode_by_color[color]);
        }
      }
    }
    //// pass 3
    colors = {}
    $('#pass_3_div div.colorbtns button').each(function(index) {
      if ($(this).hasClass('active')) {
        colors[$(this).find('div span').text()] = 1;
      }
    });    
    if (Object.keys(colors).length > 0) { 
      any_assingments = true;
      feedrate = mapConstrainFeedrate($("#import_feedrate_3").val());
      intensity = mapConstrainIntesity($("#import_intensity_3").val());
      gcodeparts.push("S"+intensity+"\nG1 F"+feedrate+"\nG0 F10000\n");
      for (var color in raw_gcode_by_color) {
        if(color in colors) {
          gcodeparts.push(raw_gcode_by_color[color]);
        }
      }
    }
    if (any_assingments == true) {     
      gcodeparts.push("S0\nG00X0Y0F16000\n%");
      var gcodestring = gcodeparts.join('');
      var fullpath = $('#svg_upload_file_temp').val();
      var filename = fullpath.split('\\').pop().split('/').pop();
      save_and_add_to_job_queue(filename, gcodestring);
      load_into_gcode_widget(gcodestring, filename);
      $('#tab_jobs_button').trigger('click');
      // $().uxmessage('notice', "file added to laser job queue");
    } else {
      $().uxmessage('warning', "nothing to cut -> please assign colors to passes");
    }
  	return false;
  });

});  // ready
