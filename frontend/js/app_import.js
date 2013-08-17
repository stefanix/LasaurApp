


///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////



$(document).ready(function(){
  
  var path_optimize = 1;
  var forceSvgDpiTo = undefined;
  
  // G-Code Canvas Preview
  var icanvas = new Canvas('#import_canvas');
  icanvas.width = 610;  // HACK: for some reason the canvas can't figure this out itself
  icanvas.height = 305; // HACK: for some reason the canvas can't figure this out itself
  icanvas.background('#ffffff'); 

  resetTap();
  
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
    $('#import_name').val($('#svg_upload_file').val().split('\\').pop().split('/').pop());
    $('#svg_upload_file').val('');

  	e.preventDefault();
  });


  function sendToBackend(e) {
    var filedata = e.target.result;
    var filename = $('#import_name').val()
    var ext = filename.slice(-4);
    if (ext == '.svg' || ext == '.SVG') {
      $().uxmessage('notice', "parsing SVG ...");
    } else if (ext == '.dxf' || ext == '.DXF') {
      $().uxmessage('notice', "parsing DXF ...");
      $().uxmessage('warning', "DXF import is limited to R14, lines, arcs, lwpolylines, and mm units");
    }
    if (filedata.length > 102400) {
      $().uxmessage('notice', "Importing large files may take a few minutes.");
    }
    $.ajax({
      type: "POST",
      url: "/svg_reader",
      data: {'filename':filename,'filedata':filedata, 'dpi':forceSvgDpiTo, 'optimize':path_optimize},
      dataType: "json",
      success: function (data) {
        if (ext == '.svg' || ext == '.SVG') {
          $().uxmessage('success', "SVG parsed."); 
          $('#dpi_import_info').html('Using <b>' + data.dpi + 'dpi</b> for converting px units.');
        } else if (ext == '.dxf' || ext == '.DXF') {
          $().uxmessage('success', "DXF parsed."); 
          $('#dpi_import_info').html('Assuming mm units in DXF file.');
        } else {
          $().uxmessage('warning', "File extension not supported. Import DXF or SVG files."); 
        }
        // alert(JSON.stringify(data));
        handleParsedGeometry(data);
      },
      error: function (data) {
        $().uxmessage('error', "backend error.");
      },
      complete: function (data) {
        $('#svg_import_btn').button('reset');
        forceSvgDpiTo = undefined;  // reset
      }
    });
  }
      
  function handleParsedGeometry(data) {
    // data is a dict with the following keys [boundarys, dpi, lasertags]
    var boundarys = data.boundarys;
    if (boundarys) {
      DataHandler.setByPaths(boundarys);
      resetTap();

      // add preview color buttons, show info, register events
      for (var color in DataHandler.getColorOrder()) {
        $('#canvas_properties .colorbtns').append('<button class="preview_color active-strong active btn btn-small" style="margin:2px"><div style="width:10px; height:10px; background-color:'+color+'"><span style="display:none">'+color+'</span></div></button>');
      }
      $('button.preview_color').click(function(e){
        // toggling manually because automatic toggling 
        // would happen after generatPreview()
        if($(this).hasClass('active')) {
          $(this).removeClass('active');
          $(this).removeClass('active-strong');
        } else {
          $(this).addClass('active');         
          $(this).addClass('active-strong');          
        }
        generatePreview();
      });

      // default selections for pass widgets, lasertags handling
      if (data.lasertags) {
        $().uxmessage('notice', "lasertags -> applying defaults");
        DataHandler.setPassesFromLasertags(data.lasertags);
      }
      // actually redraw right now 
      generatePreview();      
    } else {
      $().uxmessage('notice', "No data loaded to write G-code.");
    }   
  }


  function generatePreview() {
    if (!DataHandler.isEmpty()) {
      DataHandler.draw(icanvas, 0.5, getDeselectedColors());
    } else {
      $().uxmessage('notice', "No data loaded to generate preview.");
    }       
  }


  function getDeselectedColors() {
    var exclude_colors = {}       
    $('#canvas_properties .colorbtns button').each(function(index) {
      if (!($(this).hasClass('active'))) {
        exclude_colors[$(this).find('div span').text()] = true;
      }
    });
    return exclude_colors;
  }


  // forwarding file open click
  $('#svg_import_btn').click(function(e){
    path_optimize = 1;
    $('#svg_upload_file').trigger('click');
  });  
  $('#svg_import_72_btn').click(function(e){
    path_optimize = 1;
    forceSvgDpiTo = 72;
    $('#svg_upload_file').trigger('click');
    return false;
  });
  $('#svg_import_90_btn').click(function(e){
    path_optimize = 1;
    forceSvgDpiTo = 90;
    $('#svg_upload_file').trigger('click');
    return false;
  });
  $('#svg_import_96_btn').click(function(e){
    path_optimize = 1;
    forceSvgDpiTo = 96;
    $('#svg_upload_file').trigger('click');
    return false;
  });    
  $('#svg_import_nop_btn').click(function(e){
    path_optimize = 0;
    $('#svg_upload_file').trigger('click');
    return false;
  });  

  
  // setting up add to queue button
  $("#import_to_queue").click(function(e) {
    if (!(DataHandler.isEmpty())) {     
      var jobdata = DataHandler.getJson(getDeselectedColors());
      var filename = $('#import_name').val();
      save_and_add_to_job_queue(filename, jobdata);
      load_into_job_widget(filename, jobdata);
      $('#tab_jobs_button').trigger('click');
      resetTap();
      $('#import_name').val('');
    } else {
      $().uxmessage('warning', "no data");
    }
  	return false;
  });


  function resetTap() {
    $('#canvas_properties .colorbtns').html('');  // reset colors
    icanvas.background('#ffffff');
    $('#dpi_import_info').html('Supported file formats are: <b>SVG</b>, <b>DXF</b> (<a href="http://labs.nortd.com/lasersaur/manual/dxf_import">subset</a>)');
  }


});  // ready
