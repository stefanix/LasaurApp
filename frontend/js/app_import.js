$(document).ready(function(){
  
  var geo_boundarys = null;
  var raw_gcode = null;
  
  // G-Code Canvas Preview
  var icanvas = new Canvas('#import_canvas');
  icanvas.background('ffffff'); 
  // file upload form
  $('#svg_upload_file').change(function(e){
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
    $('#svg_loading_hint').hide();
  }
      
  function generateRawGcode() {
    if (geo_boundarys) {
      var dpi = parseFloat($('#dpi_value').val());
      if (!isNaN(dpi)) {
        var px2mm = 25.4*(1.0/dpi);
        raw_gcode = GcodeWriter.write(geo_boundarys, 2000, 255, px2mm, 0.0, 0.0);
        GcodeReader.parse(raw_gcode, 0.5);
        GcodeReader.draw(icanvas);
      } else {
        $().uxmessage('error', "Invalid DPI setting.");
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

  // setting up open button
  $('#svg_open_button').button();
  $('#svg_open_button').click(function(e){
    $('#svg_upload_file').trigger('click');
  });  


  // setting up dpi selector
  $("#dpi_radio_set").buttonset();
  $('#dpi_radio_72').click(function(e){
    $('#dpi_value').val('72');
    generateRawGcode();
  });
  $('#dpi_radio_90').click(function(e){
    $('#dpi_value').val('90');
    generateRawGcode();
  });
  $('#dpi_radio_other').click(function(e){
    $('#dpi_radio_set').hide();
    $('#dpi_value_div').show();
  });
  $('#dpi_other_back').click(function(e){
    $('#dpi_value_div').hide();
    $('#dpi_radio_set').show();
    generateRawGcode();
  });
  $('#dpi_radio_90').attr('checked', 'checked').button("refresh");
  
  
  //setting up sliders for feedrate and laser intensity
  $("#import_feedrate").slider({ min:60, max:4000, step:20, value:2000 });
  $("#import_feedrate").bind( "slide", function(event, ui) {
  	$('#feedrate_val').text($('#import_feedrate').slider("value"));
  });  
  $("#import_feedrate").bind( "slidestop", function(event, ui) {
  	$('#feedrate_val').text($('#import_feedrate').slider("value"));
  });
  $('#feedrate_val').text($('#import_feedrate').slider("value"));
  //
  $("#import_intensity").slider({ min:0, max:255, step:5, value:80 });
  $("#import_intensity").bind( "slide", function(event, ui) {
  	//$('#import_intensity_field').val($('#import_intensity').slider("option", "value"));
  	$('#intensity_val').text($('#import_intensity').slider("value"));
  });  
  $("#import_intensity").bind( "slidestop", function(event, ui) {
  	$('#intensity_val').text($('#import_intensity').slider("value"));
  });
  $('#intensity_val').text($('#import_intensity').slider("value"));
  


  // setting up add to queue button
  $("#import_to_queue").button();  
  $("#import_to_queue").click(function(e) {
    var feedrate = $("#import_feedrate").slider("value");
    var intensity = $("#import_intensity").slider("value");
    var gcodedata = wrapGcode(raw_gcode, feedrate, intensity);
    var fullpath = $('#svg_upload_file').val();
    var filename = fullpath.split('\\').pop().split('/').pop();
    add_to_job_queue(gcodedata, filename);
    preview_job(gcodedata, filename);
	  $().uxmessage('notice', "file added to laser job queue");
  	$( "#tabs-main" ).tabs({selected: 0 });	// switch to jobs tab
  	return false;
  });

});  // ready
