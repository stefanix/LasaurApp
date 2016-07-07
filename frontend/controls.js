

function controls_ready() {

  // dropdown /////////////////////////

  $("#info_btn").tooltip({placement:'bottom', delay: {show:1000, hide:100}})
  $("#info_btn").click(function(e){
    $('#info_modal').modal('toggle')
    return false
  })

  $("#export_btn").tooltip({placement:'bottom', delay: {show:1000, hide:100}})
  $("#export_btn").click(function(e){
    if (!jobhandler.isEmpty()) {
      var filename = jobhandler.name
      if (filename.length > 4 && filename.slice(-4,-3) == '.') {
        filename = filename.slice(0,-4)+'.lsa'
      } else {
        filename = filename+'.lsa'
      }
      jobhandler.setPassesFromGUI()
      var blob = new Blob([jobhandler.getJson()], {type: "application/json;charset=utf-8"})
      saveAs(blob, filename)
      // var load_request = {'job':jobhandler.getJson()}
      // post_request({
      //   url:'/temp',
      //   data: load_request,
      //   success: function (jobname) {
      //     console.log("stashing successful")
      //     // download file
      //     window.open('/download/'+jobname+'/'+jobhandler.name+'.lsa', '_blank')
      //   },
      //   error: function (data) {
      //     $().uxmessage('error', "/temp error.")
      //     $().uxmessage('error', JSON.stringify(data), false)
      //   }
      // })
      // $('#hamburger').dropdown("toggle")
    } else {
      $().uxmessage('error', "Cannot export. No job loaded.")
    }
    $("body").trigger("click")
    return false
  })

  $("#clear_btn").tooltip({placement:'bottom', delay: {show:1000, hide:100}})
  $("#clear_btn").click(function(e){
    jobhandler.clear()
    $("body").trigger("click")
    return false
  })

  $("#queue_btn").tooltip({placement:'bottom', delay: {show:1000, hide:100}})
  $("#queue_btn").click(function(e){
    $("body").trigger("click")
    $('#queue_modal').modal('toggle')
    return false
  })

  $("#library_btn").tooltip({placement:'bottom', delay: {show:1000, hide:100}})
  $("#library_btn").click(function(e){
    $("body").trigger("click")
    $('#library_modal').modal('toggle')
    return false
  })

  $("#flash_btn").tooltip({placement:'bottom', delay: {show:1000, hide:100}})
  $("#flash_btn").click(function(e){
    get_request({
      url:'/flash',
      success: function (data) {
        status_cache.firmver = undefined
        $().uxmessage('success', "Flashing successful.")
      }
    })
    $("body").trigger("click")
    return false
  })

  $("#flash_source_btn").tooltip({placement:'bottom', delay: {show:1000, hide:100}})
  $("#flash_source_btn").click(function(e){
    get_request({
      url:'/build',
      success: function (data) {
        $().uxmessage('notice', "Firmware build successful.")
        // flash new firmware
        get_request({
          url:data.flash_url,
          success: function (data) {
            status_cache.firmver = undefined
            $().uxmessage('success', "Flashing successful.")
          }
        })
      }
    })
    $("body").trigger("click")
    return false
  })

  $("#reset_btn").tooltip({placement:'bottom', delay: {show:1000, hide:100}})
  $("#reset_btn").click(function(e){
    get_request({
      url:'/reset',
      success: function (data) {
        status_cache.firmver = undefined
        $().uxmessage('success', "Reset successful.")
      }
    })
    $("body").trigger("click")
    return false
  })



  // navbar /////////////////////////

  $("#open_btn").tooltip({placement:'bottom', delay: {show:1000, hide:100}})
  $("#open_btn").click(function(e){
    $('#open_file_fld').trigger('click')
    return false
  })

  $("#run_btn").tooltip({placement:'bottom', delay: {show:1000, hide:100}})
  $("#run_btn").click(function(e){
    jobhandler.setPassesFromGUI()
    // save job to queue, in-place
    var load_request = {
      'job':jobhandler.getJson(),
      'name':jobhandler.name,
      'optimize':false,
      'overwrite':true
    }
    post_request({
      url:'/load',
      data: load_request,
      success: function (jobname) {
        // $().uxmessage('notice', "Saved to queue: "+jobname)
        // run job
        get_request({
          url:'/run/'+jobname,
          success: function (data) {
            // $().uxmessage('success', "Running job ...")
          },
          error: function (data) {
            $().uxmessage('error', "/run error.")
          },
          complete: function (data) {

          }
        })
      },
      error: function (data) {
        $().uxmessage('error', "/load error.")
        $().uxmessage('error', JSON.stringify(data), false)
      },
      complete: function (data) {

      }
    })
    return false
  })

  $("#boundary_btn").tooltip({placement:'bottom', delay: {show:1000, hide:100}})
  $("#boundary_btn").click(function(e){
    jobhandler.setPassesFromGUI()
    var bounds = jobhandler.getActivePassesBbox()
    get_request({url:'/move/'+bounds[0].toFixed(3)+'/'+bounds[1].toFixed(3)+'/0'})
    get_request({url:'/move/'+bounds[2].toFixed(3)+'/'+bounds[1].toFixed(3)+'/0'})
    get_request({url:'/move/'+bounds[2].toFixed(3)+'/'+bounds[3].toFixed(3)+'/0'})
    get_request({url:'/move/'+bounds[0].toFixed(3)+'/'+bounds[3].toFixed(3)+'/0'})
    get_request({url:'/move/'+bounds[0].toFixed(3)+'/'+bounds[1].toFixed(3)+'/0'})
    get_request({url:'/move/0/0/0'})
    return false
  })

  $("#pause_btn").tooltip({placement:'bottom', delay: {show:1000, hide:100}})
  $("#pause_btn").click(function(e){
    if (status_cache.paused) {  // unpause
      get_request({
        url:'/unpause',
        success: function (data) {
          // $().uxmessage('notice', "Continuing...")
        }
      })
    } else {  // pause
      get_request({
        url:'/pause',
        success: function (data) {
          // $().uxmessage('notice', "Pausing in a bit...")
        }
      })
    }
    return false
  })

  $("#stop_btn").tooltip({placement:'bottom', delay: {show:1000, hide:100}})
  $("#stop_btn").click(function(e){
    get_request({
      url:'/stop',
      success: function (data) {
        setTimeout(function() {
          get_request({
            url:'/unstop',
            success: function (data) {
              get_request({
                url:'/feedrate/'+app_config_main.seekrate
              })
              get_request({
                url:'/move/0/0/0',
                success: function (data) {
                  // $().uxmessage('notice', 'Moving to Origin.')
                }
              })
            }
          })
        }, 1000)
      }
    });
    return false
  })



  // footer /////////////////////////

  $("#origin_btn").tooltip({placement:'top', delay: {show:1000, hide:100}})
  $("#origin_btn").click(function(e){
    var gcode;
    if(e.shiftKey) {
      // also reset offset
      alert("TODO: reset offset")
      reset_offset____();  // TODO
    }
    get_request({
      url:'/move/0/0/0',
      success: function (data) {
        $().uxmessage('notice', "Going to origin ...")
      }
    });
    return false
  })

  $("#homing_btn").tooltip({placement:'top', delay: {show:1000, hide:100}})
  $("#homing_btn").click(function(e){
    get_request({
      url:'/homing',
      success: function (data) {
        $().uxmessage('notice', "Homing ...")
      }
    })
    return false
  })

  $("#select_btn").tooltip({placement:'top', delay: {show:1000, hide:100}})
  $("#select_btn").click(function(e){
    alert("select")
    return false
  })

  $("#motion_btn").tooltip({placement:'top', delay: {show:1000, hide:100}})
  $("#motion_btn").click(function(e){
    alert("motion")
    return false
  })

  $("#offset_btn").tooltip({placement:'top', delay: {show:1000, hide:100}})
  $("#offset_btn").click(function(e){
    alert("offset")
    return false
  })

  $("#jog_btn").tooltip({placement:'top', delay: {show:1000, hide:100}})
  $("#jog_btn").click(function(e){
    alert("jog")
    return false
  })



  // shortcut keys /////////////////////////////////////

  Mousetrap.bind(['i'], function(e) {
      $('#info_btn').trigger('click')
      return false;
  })

  Mousetrap.bind(['e'], function(e) {
      $('#export_btn').trigger('click')
      return false;
  })

  Mousetrap.bind(['del', 'backspace'], function(e) {
      $('#clear_btn').trigger('click')
      return false;
  })

  Mousetrap.bind(['q'], function(e) {
      $('#queue_btn').trigger('click')
      return false;
  })

  Mousetrap.bind(['l'], function(e) {
      $('#library_btn').trigger('click')
      return false;
  })

  Mousetrap.bind(['c'], function(e) {
      $('#config_btn').trigger('click')
      return false;
  })

  Mousetrap.bind(['shift+l'], function(e) {
      $('#log_btn').trigger('click')
      return false;
  })

  Mousetrap.bind(['enter'], function(e) {
      $('#open_btn').trigger('click')
      return false;
  })

  Mousetrap.bind(['command+enter', 'ctrl+enter'], function(e) {
      $('#run_btn').trigger('click')
      return false;
  })

  Mousetrap.bind(['command+shift+enter', 'ctrl+shift+enter'], function(e) {
      $('#boundary_btn').trigger('click')
      return false;
  })

  Mousetrap.bind(['space'], function(e) {
      $('#pause_btn').trigger('click')
      return false;
  })

  Mousetrap.bind(['ctrl+esc', 'command+esc'], function(e) {
      $('#stop_btn').trigger('click')
      return false;
  })


  Mousetrap.bind(['0'], function(e) {
      $('#origin_btn').trigger('click')
      return false;
  })

  Mousetrap.bind(['h'], function(e) {
      $('#homing_btn').trigger('click')
      return false;
  })

  Mousetrap.bind(['s'], function(e) {
      $('#select_btn').trigger('click')
      return false;
  })

  Mousetrap.bind(['m'], function(e) {
      $('#motion_btn').trigger('click')
      return false;
  })

  Mousetrap.bind(['o'], function(e) {
      $('#offset_btn').trigger('click')
      return false;
  })

  Mousetrap.bind(['j'], function(e) {
      $('#jog_btn').trigger('click')
      return false;
  })


}
