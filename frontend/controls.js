

function controls_ready() {

  // dropdown /////////////////////////

  $("#info_btn").tooltip({placement:'bottom', delay: {show:1000, hide:100}})
  $("#info_btn").click(function(e){
    $('#info_modal').modal('toggle');
    return false
  })

  $("#export_btn").tooltip({placement:'bottom', delay: {show:1000, hide:100}})
  $("#export_btn").click(function(e){
    var blob = new Blob([jobhandler.getJson()], {type: "text/plain;charset=utf-8"});
    saveAs(blob, jobhandler.name+'.lsa');
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
    alert("queue")
    return false
  })

  $("#library_btn").tooltip({placement:'bottom', delay: {show:1000, hide:100}})
  $("#library_btn").click(function(e){
    alert("library")
    return false
  })

  $("#flash_btn").tooltip({placement:'bottom', delay: {show:1000, hide:100}})
  $("#flash_btn").click(function(e){
    get_request({
      url:'/flash',
      success: function (data) {
        $().uxmessage('success', "Flashing successful.");
      }
    });
    $("body").trigger("click")
    return false
  })

  // $("#flash_source_btn").tooltip({placement:'bottom', delay: {show:1000, hide:100}})
  // $("#flash_source_btn").click(function(e){
  //   get_request({
  //     url:'/reset',
  //     success: function (data) {
  //       app_firmware_version_flag = false;
  //       $().uxmessage('notice', "Firmware reset successful.");
  //     }
  //   });
  //   $('#hamburger').dropdown("hide")
  //   $("body").trigger("click")
  //   return false
  // })

  $("#reset_btn").tooltip({placement:'bottom', delay: {show:1000, hide:100}})
  $("#reset_btn").click(function(e){
    get_request({
      url:'/reset',
      success: function (data) {
        app_firmware_version_flag = false;
        $().uxmessage('success', "Reset successful.");
      }
    });
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
    return false
  })

  $("#boundary_btn").tooltip({placement:'bottom', delay: {show:1000, hide:100}})
  $("#boundary_btn").click(function(e){
    alert("boundary")
    return false
  })

  $("#pause_btn").tooltip({placement:'bottom', delay: {show:1000, hide:100}})
  $("#pause_btn").click(function(e){
    if (app_pause_state == true) {  // unpause
      get_request({
        url:'/unpause',
        success: function (data) {
          app_pause_state = false;
          $("#pause_btn").removeClass('btn-primary');
          $("#pause_btn").html('<i class="icon-pause"></i>');
          $().uxmessage('notice', "Continuing...");
        }
      });
    } else {  // pause
      get_request({
        url:'/pause',
        success: function (data) {
          app_pause_state = true;
          $("#pause_btn").addClass('btn-primary');
          $("#pause_btn").html('<i class="icon-play"></i>');
          $().uxmessage('notice', "Pausing in a bit...");
        }
      });
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
                url:'/move/0/0/0',
                success: function (data) {
                  $().uxmessage('notice', 'Moving to Origin.');
                }
              });
            }
          });
        }, 1000);
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
        $().uxmessage('notice', "Going to origin ...");
      }
    });
    return false
  })

  $("#homing_btn").tooltip({placement:'top', delay: {show:1000, hide:100}})
  $("#homing_btn").click(function(e){
    get_request({
      url:'/homing',
      success: function (data) {
        $().uxmessage('notice', "Homing ...");
      }
    });
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
