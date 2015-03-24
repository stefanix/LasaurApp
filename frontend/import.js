


///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////


$(document).ready(function(){

  var path_optimize = true
  var forceSvgDpiTo = undefined
  // open button
  $('#open_btn').click(function(e){
    e.preventDefault()
    path_optimize = true
    // forceSvgDpiTo = 90;
    $('#open_file_fld').trigger('click')
  })

  // file upload form
  $('#open_file_fld').change(function(e){
    e.preventDefault()
    $('#open_btn').button('loading')
    var input = $('#open_file_fld').get(0)

    // file API check
    var browser_supports_file_api = true
    if (typeof window.FileReader !== 'function') {
      browser_supports_file_api = false
    } else if (!input.files) {
      browser_supports_file_api = false
    }

    // setup onload handler
    if (browser_supports_file_api) {
      if (input.files[0]) {
        var fr = new FileReader()
        fr.onload = sendToBackend
        fr.readAsText(input.files[0])
      } else {
        $().uxmessage('error', "No file was selected.")
      }
    } else {  // fallback
      $().uxmessage('error', "Requires browser with File API support.")
    }

    // reset file input form field so change event also triggers again
    var name = $('#open_file_fld').val().split('\\').pop().split('/').pop()
    $('title').html("LasaurApp - " + name)
    $('#open_file_fld').val('')
  });



  function sendToBackend(e) {
    var job = e.target.result
    var name = $('title').html().split(" - ")[1]
    var ext = name.slice(-4)

    // type
    var type = ''
    if (ext == '.svg' || ext == '.SVG') {
      type = 'svg';
    } else if (ext == '.dxf' || ext == '.DXF') {
      type = 'dxf'
    } else if (ext == '.ngc' || ext == '.NGC') {
      type = 'ngc'
    }
    $().uxmessage('notice', "parsing "+type+" ...")

    // large file note
    if (job.length > 102400) {
      $().uxmessage('notice', "Big file! May take a few minutes.")
    }

    // send to backend
    var load_request = {'job':job, 'name':name, 'optimize':path_optimize}
    post_request({
      url:'/load',
      data: load_request,
      success: function (data) {
        $().uxmessage('notice', "Parsed "+type+".")
        $('title').html("LasaurApp - " + data)
        // alert(JSON.stringify(data));
        // handleParsedGeometry(data);
      },
      error: function (data) {
        $().uxmessage('error', "backend error.")
        $().uxmessage('error', JSON.stringify(data), false)
      },
      complete: function (data) {
        $('#open_btn').button('reset')
        forceSvgDpiTo = undefined;  // reset
      }
    })

  }



  function handleParsedGeometry(data) {
    // data is a dict with the following keys [boundarys, dpi, lasertags, rasters]
    if ('boundarys' in data || 'rasters' in data) {

      if ('boundarys' in data) {
        DataHandler.setByPaths(data.boundarys);
        if (path_optimize) {
          DataHandler.segmentizeLongLines();
        }
      }

      if ('rasters' in data) {
        // // debug, show image, stats
        // for (var i=0; i<data.rasters.length; i++) {
        //   var raster = data.rasters[i];
        //   // convert base64 to Image object
        //   var imgid = 'rasterimg' + i;
        //   $('#tab_import').append('<img id="'+imgid+'" src="'+raster['image']+'">');
        //   var img = document.getElementById(imgid);

        //   // stats
        //   raster_stats = {'pos':raster['pos'],
        //                   'size_mm':raster['size_mm'],
        //                   'size_px':[img.width, img.height],
        //                   'len':raster['image'].length}
        //   $('#tab_import').append('<p>'+JSON.stringify(raster_stats)+'</p>');
        // }
        DataHandler.addRasters(data.rasters);
      }

      // some init
      $('#canvas_properties .colorbtns').html('');  // reset colors
      canvas.background('#ffffff');

      // add preview color buttons, show info, register events
      for (var color in DataHandler.getColorOrder()) {
        $('#canvas_properties .colorbtns').append('<button class="preview_color active-strong active btn btn-small" style="margin:2px"><div style="width:10px; height:10px; background-color:'+color+'"><span style="display:none">'+color+'</span></div></button>');
      }
      $('#canvas_properties .colorbtns').append(' <span id="num_selected_colors">0</span> colors selected for import.');
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
      DataHandler.draw(canvas, app_settings.to_canvas_scale, getDeselectedColors());
    } else {
      $().uxmessage('notice', "No data loaded to generate preview.");
    }
  }


  function getDeselectedColors() {
    var num_selected = 0;
    var exclude_colors = {};
    $('#canvas_properties .colorbtns button').each(function(index) {
      if (!($(this).hasClass('active'))) {
        exclude_colors[$(this).find('div span').text()] = true;
      } else {
        num_selected += 1;
      }
    });
    $('#num_selected_colors').html(''+num_selected);
    return exclude_colors;
  }



  // setting up add to queue button
  $("#import_to_queue").click(function(e) {
    if (!(DataHandler.isEmpty())) {
      var jobdata = DataHandler.getJson(getDeselectedColors());
      var name = $('title').html().split(" - ")[1]
      save_and_add_to_job_queue(name, jobdata);
      load_job(name, jobdata);
      $('#tab_jobs_button').trigger('click');

      // reset tap
      $('#canvas_properties .colorbtns').html('');  // reset colors
      canvas.background('#ffffff');
      $('#dpi_import_info').html('Supported file formats are: <b>SVG</b>, <b>DXF</b> (<a href="http://www.lasersaur.com/manual/dxf_import">subset</a>)');
      $('title').html('LasaurApp');
    } else {
      $().uxmessage('warning', "no data");
    }
    return false;
  });



});  // ready
