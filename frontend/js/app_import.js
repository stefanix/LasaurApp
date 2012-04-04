$(document).ready(function(){
  
  var geo_boundarys = null;
  var raw_gcode = null;
  
  // G-Code Canvas Preview
  var icanvas = new Canvas('#import_canvas');
  icanvas.background('ffffff'); 
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
  $('#svg_dpi90_btn').attr('checked', 'checked').button("refresh");
    
    
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
    var feedrate = $("#import_feedrate").val();
    var intensity = $("#import_intensity").val();
    var gcodedata = wrapGcode(raw_gcode, feedrate, intensity);
    var fullpath = $('#svg_upload_file').val();
    var filename = fullpath.split('\\').pop().split('/').pop();
    add_to_job_queue(gcodedata, filename);
    load_into_gcode_widget(gcodedata, filename);
	  $().uxmessage('notice', "file added to laser job queue");
  	//$( "#tabs_main" ).tabs({selected: 0 });	// switch to jobs tab  // TODO
  	return false;
  });

});  // ready
