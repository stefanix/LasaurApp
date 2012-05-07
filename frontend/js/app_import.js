$(document).ready(function(){
  
  var geo_boundarys = null;
  var raw_gcode = null;
  var raw_gcode_by_color = null;
  
  // G-Code Canvas Preview
  var icanvas = new Canvas('#import_canvas');
  icanvas.width = 610;  // HACK: for some reason the canvas can't figure this out herself
  icanvas.height = 305; // HACK: for some reason the canvas can't figure this out herself
  icanvas.background('#ffffff'); 
  
  
  // file upload form
  $('#svg_upload_file').change(function(e){
    $('#svg_open_button').button('loading');
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
        fr.onload = parseSvgDataFromFileAPI
        fr.readAsText(input.files[0])
      } else {
        $().uxmessage('error', "No file was selected.");
      }
    } else {  // fallback
      // $().uxmessage('notice', "Using fallback: file form upload.");
    }
    
  	e.preventDefault();		
  });


  function parseSvgDataFromFileAPI(e) {
    parseSvgData(e.target.result);
  }

  function parseSvgData(svgdata) {
    $().uxmessage('notice', "parsing SVG ...");
    geo_boundarys = SVGReader.parse(svgdata, {})
    //alert(geo_boundarys.toSource());
    //alert(JSON.stringify(geo_boundarys));
    //$().uxmessage('notice', JSON.stringify(geo_boundarys));
    generateRawGcode();
    $('#svg_open_button').button('reset');
  }
      
  function generateRawGcode() {
    if (geo_boundarys) {
      var dpi = parseFloat($('#svg_dpi_value').val());
      if (!isNaN(dpi)) {
        var px2mm = 25.4*(1.0/dpi);
        
        raw_gcode_by_color = {};
        for (var color in geo_boundarys) {
          raw_gcode_by_color[color] = GcodeWriter.write(geo_boundarys[color], px2mm, 0.0, 0.0);
        }
        //// add canvas color properties
        $('#canvas_properties div.colorbtns').html('');  // reset colors
        $('#pass_1_div div.colorbtns').html('');  // reset colors
        $('#pass_2_div div.colorbtns').html('');  // reset colors
        $('#pass_3_div div.colorbtns').html('');  // reset colors
        for (var color in raw_gcode_by_color) {
  				$('#canvas_properties div.colorbtns').append('<button class="preview_color btn btn-small active" style="margin:3px"><div style="width:10px; height:10px; background-color:'+color+'"><span style="display:none">'+color+'</span></div></button>');          
  				$('#pass_1_div div.colorbtns').append('<button class="btn btn-small" data-toggle="button" style="margin:3px"><div style="width:10px; height:10px; background-color:'+color+'"><span style="display:none">'+color+'</span></div></div></button>');        
  				$('#pass_2_div div.colorbtns').append('<button class="btn btn-small" data-toggle="button" style="margin:3px"><div style="width:10px; height:10px; background-color:'+color+'"><span style="display:none">'+color+'</span></div></div></button>');        
  				$('#pass_3_div div.colorbtns').append('<button class="btn btn-small" data-toggle="button" style="margin:3px"><div style="width:10px; height:10px; background-color:'+color+'"><span style="display:none">'+color+'</span></div></div></button>');        
        }
        // register redraw event
  			$('button.preview_color').click(function(e){
  			  // toggling manually, had problem with automatic
  			  if($(this).hasClass('active')) {
  			    $(this).removeClass('active')
  			  } else {
  			    $(this).addClass('active')			    
  			  }
          generatePreview();
        });
        // actually redraw right now 
        generatePreview();
      } else {
        $().uxmessage('error', "Invalid DPI setting.");
      }        
    } else {
      $().uxmessage('notice', "No data loaded to write G-code from.");
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
      for (var color in raw_gcode_by_color) {
        if (!(color in exclude_colors)) {
          GcodeReader.draw(icanvas, raw_gcode_by_color[color], 0.5, color);
        }
      }
    } else {
      $().uxmessage('notice', "No data loaded to write G-code from.");
    }       
  }
  
  function wrapGcode(gcode, feedrate, intensity) {
    var header = "%\nG21\nG90\nS"+intensity+"\nG1 F"+feedrate+"\nG0 F10000\n"
    var footer = "S0\nG00X0Y0F15000\n%"
    return header + gcode + footer;
  }

  // forwarding file open click
  $('#svg_open_button').click(function(e){
    $('#svg_upload_file').trigger('click');
  });  


  // setting up dpi selector
  $('#svg_dpi72_btn').click(function(e){
    $('#svg_dpi_value').val('72');
    generateRawGcode();
  });
  $('#svg_dpi90_btn').click(function(e){
    $('#svg_dpi_value').val('90');
    generateRawGcode();
  });
  $('#svg_dpi90_btn').trigger('click');
    
  $('#svg_dpi72_btn').tooltip()    
  $('#svg_dpi90_btn').tooltip()        
  $('#import_feedrate_0').tooltip()    
  $('#import_intensity_0').tooltip()    
  $('#import_feedrate_1').tooltip()    
  $('#import_intensity_1').tooltip()
  $('#import_feedrate_2').tooltip()    
  $('#import_intensity_2').tooltip()  
  
  // setting up add to queue button
  $("#import_to_queue").click(function(e) {            
    // assemble multiple passes
    var gcodeparts = ["%\nG21\nG90\n"];
    var feedrate;
    var intensity;
    var colors = {};
    //// pass 1
    $('#pass_1_div div.colorbtns button').each(function(index) {
      if ($(this).hasClass('active')) {
        colors[$(this).find('div span').text()] = 1;
      }
    });
    if (Object.keys(colors).length > 0) { 
      feedrate = $("#import_feedrate_1").val();
      intensity = $("#import_intensity_1").val();
      gcodeparts.push("S"+intensity+"\nG1 F"+feedrate+"\nG0 F16000\n");
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
      feedrate = $("#import_feedrate_2").val();
      intensity = $("#import_intensity_2").val();
      gcodeparts.push("S"+intensity+"\nG1 F"+feedrate+"\nG0 F16000\n");
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
      feedrate = $("#import_feedrate_3").val();
      intensity = $("#import_intensity_3").val();
      gcodeparts.push("S"+intensity+"\nG1 F"+feedrate+"\nG0 F16000\n");
      for (var color in raw_gcode_by_color) {
        if(color in colors) {
          gcodeparts.push(raw_gcode_by_color[color]);
        }
      }
    }       
    gcodeparts.push("S0\nG00X0Y0F16000\n%");
    var gcodestring = gcodeparts.join('');
    var fullpath = $('#svg_upload_file').val();
    var filename = fullpath.split('\\').pop().split('/').pop();
    save_and_add_to_job_queue(filename, gcodestring);
    load_into_gcode_widget(gcodestring, filename);
    $('#tab_jobs_button').trigger('click');
    // $().uxmessage('notice', "file added to laser job queue");
  	//$( "#tabs_main" ).tabs({selected: 0 });	// switch to jobs tab  // TODO
  	return false;
  });

});  // ready
