
var import_name = ""


///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////


$(document).ready(function(){
  passes_add(1500, 100, ['#ff00ff', '#889933'])
  passes_add(1500, 100, ['#837362'])
  passes_add(1500, 100, [])
  passes_add_widget()

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
    var file_fld = $('#open_file_fld').val()
    file_fld = file_fld.slice(file_fld.lastIndexOf('\\')+1) || file_fld  // drop unix path
    file_fld = file_fld.slice(file_fld.lastIndexOf('/')+1) || file_fld   // drop windows path
    import_name = file_fld.slice(0, file_fld.lastIndexOf('.')) || file_fld  // drop extension
    $('#open_file_fld').val('')
  })



  function sendToBackend(e) {
    var job = e.target.result

    // notify parsing started
    $().uxmessage('notice', "parsing "+import_name+" ...")
    // large file note
    if (job.length > 102400) {
      $().uxmessage('notice', "Big file! May take a few minutes.")
    }

    // send to backend
    var load_request = {'job':job, 'name':import_name, 'optimize':true}
    post_request({
      url:'/load',
      data: load_request,
      success: function (jobname) {
        $().uxmessage('notice', "Parsed "+jobname+".")
        queue_update()
        import_open(jobname)
      },
      error: function (data) {
        $().uxmessage('error', "/load error.")
        $().uxmessage('error', JSON.stringify(data), false)
      },
      complete: function (data) {
        $('#open_btn').button('reset')
      }
    })

  }

})  // ready



function import_open(jobname, from_library) {
  from_library = typeof from_library !== 'undefined' ? from_library : false  // default to false
  // get job in lsa format
  var url = '/get/'+jobname
  if (from_library === true) {
    url = '/get_library/'+jobname
  }
  get_request({
    url: url,
    success: function (job) {
      // alert(JSON.stringify(data))
      // $().uxmessage('notice', data)
      jobhandler.set(job, jobname, true)
      jobhandler.render()
      jobhandler.draw()

      // debug, show image, stats
      // if ('rasters' in job) {
        // for (var i=0; i<job.rasters.length; i++) {
        //   var raster = job.rasters[i];
        //   // convert base64 to Image object
        //   var imgid = 'rasterimg' + i;
        //   $('#tab_import').append('<img id="'+imgid+'" src="'+raster['image']+'">');
        //   var img = document.getElementById(imgid);
        //
        //   // stats
        //   raster_stats = {'pos':raster['pos'],
        //                   'size_mm':raster['size_mm'],
        //                   'size_px':[img.width, img.height],
        //                   'len':raster['image'].length}
        //   $('#tab_import').append('<p>'+JSON.stringify(raster_stats)+'</p>');
        // }
      // }
    },
    error: function (data) {
      $().uxmessage('error', "/get error.")
      $().uxmessage('error', JSON.stringify(data), false)
    }
  })
}
