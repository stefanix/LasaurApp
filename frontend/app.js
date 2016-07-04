
var app_config_main = undefined
var app_hardware_ready_flag = false
var app_firmware_version_flag = false
var app_lasaurapp_version_flag = false
var app_ready_state = false
var app_pause_state = false
var app_run_btn = undefined



///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////


$(document).ready(function(){
  $().uxmessage('notice', "Frontend started.")
  // modern browser check
  if(!Object.hasOwnProperty('keys')) {
    alert("Error: Browser may be too old/non-standard.")
  }

  // unblur button after pressing
  $(".btn").mouseup(function(){
      $(this).blur()
  })

  // run_btn, make a ladda progress spinner button
  app_run_btn = Ladda.create($("#run_btn")[0])

  // get appconfig from server
  get_request({
    url:'/config',
    success: function (data) {
      $().uxmessage('success', "App config received.")
      app_config_main = data
      config_received()
    },
    error: function (data) {
      $().uxmessage('error', "Failed to receive app config.")
    },
    complete: function (data) {}
  })
});



function config_received() {
  // show in config modal
  var html = ''
  var keys_sorted = Object.keys(app_config_main).sort()
  for (var i=0; i<keys_sorted.length; i++) {
    html += keys_sorted[i] + " : " + app_config_main[keys_sorted[i]] + "<br>"
  }
  $('#config_content').html(html)
  // about modal
  $('#app_version').html(app_config_main.version)
  // $('#firmware_version').html(app_config_main.)

  // call 'ready' of jobview
  jobview_ready()
  // call 'ready' of controls
  controls_ready()
  // call 'ready' of queue
  queue_ready()
  // call 'ready' of library
  library_ready()

  start_status_channel()
}


function start_status_channel() {
  // status by websocket
  websocket = new WebSocket("ws://"+location.hostname+":4411/")
  websocket.onopen = function(e) {
    $().uxmessage('success', "status channel OPEN")
  }
  websocket.onclose = function(e) {
    $().uxmessage('warning', "status channel CLOSED")
    // setTimeout(function() {status_connect()}, 8000)
  }
  websocket.onerror = function(e) {
    $().uxmessage('error', "status channel")
  }
  websocket.onmessage = function(e) {
    // {"info": {"chiller": true}, "feedrate": 8000.0, "intensity": 0.0, "pos": [-0.005, 0.005, 0.0], "stops": {}, "stackclear": 572.0, "paused": false, "duration": 0.0, "appver": "15.00-beta1", "firmver": "15.0", "underruns": 1.0, "pixelwidth": 0.0, "offset": [0.0, 0.0, 0.0], "ready": true, "progress": 1.0, "serial": true}
    var data = JSON.parse(e.data)
    // $().uxmessage('notice', e.data, Infinity)

    // show in config modal
    var html = ''
    var keys_sorted = Object.keys(data).sort()
    for (var i=0; i<keys_sorted.length; i++) {
      var val = data[keys_sorted[i]]
      if (typeof(val) === 'object' && val !== null) {
        html += keys_sorted[i]+"<br>"
        // iterate over sub-asso-array
        var subkeys_sorted = Object.keys(val).sort()
        for (var j = 0; j < subkeys_sorted.length; j++) {
          html += "--"+subkeys_sorted[j] + ": " + val[subkeys_sorted[j]] + "<br>"
        }
      } else  {
        html += keys_sorted[i] + " : " + data[keys_sorted[i]] + "<br>"
      }
    }
    $('#status_content').html(html)

    // ready status
    if (data.ready) {
      if (!app_ready_state) {
        // ready - event
        app_ready_state = true
        $("#status_btn").removeClass("btn-danger")
        if (data.info.door || data.info.chiller) {
          $("#status_btn").addClass("btn-warning")
        } else {
          $("#status_btn").addClass("btn-success")
        }
      }
    } else {
      if (app_ready_state) {
        // not ready - event
        app_ready_state = false
        $("#status_btn").removeClass("btn-warning")
        $("#status_btn").removeClass("btn-success")
        $("#status_btn").addClass("btn-danger")
      }
    }

    // stop and info status
    status_label_update(data.stops.x1, '#status_limit_x1', "label-danger")
    status_label_update(data.stops.x2, '#status_limit_x2', "label-danger")
    status_label_update(data.stops.y1, '#status_limit_y1', "label-danger")
    status_label_update(data.stops.y2, '#status_limit_y2', "label-danger")
    status_label_update(data.stops.z1, '#status_limit_z1', "label-danger")
    status_label_update(data.stops.z2, '#status_limit_z2', "label-danger")
    status_label_update(data.info.door, '#status_door', "label-warning")
    status_label_update(data.info.chiller, '#status_chiller', "label-warning")
    status_label_update(data.stops.requested, '#status_stop', "label-danger")
    status_txerror_update(data, "#status_error")


    // pause status
    if (data.paused) {
      if (!app_pause_state) {
        // pause - event
        app_pause_state = true
        // pause button
        $("#pause_btn").removeClass("btn-default")
        $("#pause_btn").addClass("btn-primary")
        $("#pause_glyph").hide()
        $("#play_glyph").show()
        // run button
        $('#run_btn span.ladda-spinner').hide()
      }
    } else {
      if (app_pause_state) {
        // unpause - event
        app_pause_state = false
        // pause button
        $("#pause_btn").removeClass("btn-primary")
        $("#pause_btn").addClass("btn-default")
        $("#play_glyph").hide()
        $("#pause_glyph").show()
        // run button
        $('#run_btn span.ladda-spinner').show()
      }
    }

    // progress
    if (data.progress < 1) {
      if (app_run_btn.isLoading()) {
        app_run_btn.setProgress(data.progress)
      } else {
        // job processing starts - event
        app_run_btn.start()
        $('#boundary_btn').prop('disabled', true)
        $('#origin_btn').prop('disabled', true)
        $('#homing_btn').prop('disabled', true)
      }
    } else {
      if (app_run_btn.isLoading()) {
        // job processing ends - event
        app_run_btn.stop()
        $('#boundary_btn').prop('disabled', false)
        $('#origin_btn').prop('disabled', false)
        $('#homing_btn').prop('disabled', false)
      }
    }

    /////// DEBUG
    return

    // serial connected
    if (data.serial) {
      // ready state
      if (data.ready) {
        app_hardware_ready_flag = true;
        $("#connect_btn").removeClass("btn-danger");
        $("#connect_btn").removeClass("btn-warning");
        $("#connect_btn").addClass("btn-success");
      } else {
        app_hardware_ready_flag = false;
        $("#connect_btn").removeClass("btn-danger");
        $("#connect_btn").removeClass("btn-success");
        $("#connect_btn").addClass("btn-warning");
      }
    } else {
      $("#connect_btn").removeClass("btn-success");
      $("#connect_btn").removeClass("btn-warning");
      $("#connect_btn").addClass("btn-danger");
      app_hardware_ready_flag = false;
    }

    // door, chiller, power, limit, buffer
    if (data.serial) {
      if ('door' in data.info) {
        $('#door_status_btn').removeClass('btn-success')
        $('#door_status_btn').addClass('btn-warning')
        // $().uxmessage('warning', "Door is open!");
      } else {
        $('#door_status_btn').removeClass('btn-warning')
        $('#door_status_btn').addClass('btn-success')
      }
      if ('chiller' in data.info) {
        $('#chiller_status_btn').removeClass('btn-success')
        $('#chiller_status_btn').addClass('btn-warning')
        // $().uxmessage('warning', "Chiller is off!");
      } else {
        $('#chiller_status_btn').removeClass('btn-warning')
        $('#chiller_status_btn').addClass('btn-success')
      }
      // stop conditions
      var handle_stop = function(errortext) {
          $().uxmessage('error', errortext);
          $().uxmessage('notice', "Run homing cycle to reset stop mode.");
      }
      if (Object.keys(data.stops).length !== 0) {
        if ('x1' in data.stops) {
          handle_stop("Limit x1 hit!")
        }
        if ('x2' in data.stops) {
          handle_stop("Limit x2 hit!")
        }
        if ('y1' in data.stops) {
          handle_stop("Limit y1 hit!")
        }
        if ('y2' in data.stops) {
          handle_stop("Limit y2 hit!")
        }
        if ('z1' in data.stops) {
          handle_stop("Limit z1 hit!")
        }
        if ('z2' in data.stops) {
          handle_stop("Limit z2 hit!")
        }
        // if ('byrequest' in data.stops) {
        //   $().uxmessage('notice', "Stop by request!");
        //   $().uxmessage('notice', "Run homing cycle to reset stop mode.");
        // }
        if ('buffer' in data.stops) {
          handle_stop("Buffer Overflow!")
        }
        if ('marker' in data.stops) {
          handle_stop("Invalid marker!")
        }
        if ('command' in data.stops) {
          handle_stop("Invalid command!")
        }
        if ('parameter' in data.stops) {
          handle_stop("Invalid parameter!")
        }
        if ('transmission' in data.stops) {
          handle_stop("Transmission Error!")
        }
      }
      // head position
      if (data.pos) {
        // only update if not manually entering at the same time
        if (!$('#x_location_field').is(":focus") &&
            !$('#y_location_field').is(":focus") &&
            !$('#location_set_btn').is(":focus") &&
            !$('#origin_set_btn').is(":focus"))
        {
          var x = data.pos[0] - app_settings.table_offset[0];
          $('#x_location_field').val(x.toFixed(2));
          // $('#x_location_field').animate({
          //   opacity: 0.5
          // }, 100, function() {
          //   $('#x_location_field').animate({
          //     opacity: 1.0
          //   }, 600, function() {});
          // });
          var y = data.pos[1] - app_settings.table_offset[1];
          $('#y_location_field').val(y.toFixed(2));
          // $('#y_location_field').animate({
          //   opacity: 0.5
          // }, 100, function() {
          //   $('#y_location_field').animate({
          //     opacity: 1.0
          //   }, 600, function() {});
          // });
          $("#head_position").animate({
            left: Math.round(x),
            top: Math.round(y),
          }, 500, 'linear' );
        }
      }
      if (data.firmver && !app_firmware_version_flag) {
        $().uxmessage('notice', "Firmware v" + data.firmver);
        $('#firmware_version').html(data.firmver);
        app_firmware_version_flag = true;
      }
    }
    if (data.appver && !app_lasaurapp_version_flag) {
      $().uxmessage('notice', "LasaurApp v" + data.appver);
      $('#lasaurapp_version').html(data.appver);
      app_lasaurapp_version_flag = true;
    }

  }  // websocket.onmessage
}  // start_status_channel
