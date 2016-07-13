
var status_websocket = undefined
var status_server_cache = false
var status_cache = {}

function status_init() {
  status_cache = {
    //// always
    'serial': false,                // is serial connected
    'ready': false,                 // is hardware idle (and not stop mode)
    //// when hardware connected
    'appver': undefined,
    'firmver': undefined,
    'paused': false,
    'pos':[0.0, 0.0, 0.0],
    'underruns': 0,          // how many times machine is waiting for serial data
    'stackclear': Infinity,  // minimal stack clearance (must stay above 0)
    'progress': 1.0,

    //// stop conditions
    // indicated when key present
    'stops': {'dirty':true},
    // possible keys:
    // x1, x2, y1, y2, z1, z2,
    // requested, buffer, marker, data, command, parameter, transmission

    'info':{'dirty':true},
    // possible keys: door, chiller

    //// only when hardware idle
    'offset': [0.0, 0.0, 0.0],
    'feedrate': 0.0,
    'intensity': 0.0,
    'duration': 0.0,
    'pixelwidth': 0.0
  }
}



function status_handle_message(status) {
  // call handlers for data points, only when a change occurs
  for (var k in status_cache) {
    if (k in status) {
      if (status_check_new(status_cache[k], status[k])) {
        status_handlers[k](status)   // call handler
        status_cache[k] = status[k]  // update cache
      }
    }
  }
}

function status_check_new(data1, data2) {
  // compare strings, numbers bools, and arrays, maps by value
  var flag = false
  if (Array.isArray(data1)) {
    // check array values
    for (var i = 0; i < data1.length; i++) {
      if (data1[i] !== data2[i]) {
        flag = true
      }
    }
  } else if (typeof(data1) == 'string'
          || typeof(data1) == 'number'
          || typeof(data1) == 'boolean') {
    if (data1 !== data2) {
      flag = true
    }
  } else if (typeof(data1) == 'object') {
    for(var k in data1) {
      if (data1[k] !== data2[k]) {
        flag = true
      }
    }
  } else {
    flag = false
  }
  return flag
}


function status_set_main_button(status) {
  if (!status_websocket || (status_websocket.readyState == 3)) {  // disconnected
    $("#status_btn").removeClass("btn-warning btn-success").addClass("btn-danger")
  } else {  // connected
    if (!$.isEmptyObject(status.stops) || !status.serial) {  // connected but stops, serial down
      $("#status_btn").removeClass("btn-warning btn-success").addClass("btn-danger")
    } else {
      if (!$.isEmptyObject(status.info)) {  // connected, no stops, serial up, warnings
        $("#status_btn").removeClass("btn-danger btn-success").addClass("btn-warning")
      } else {  // connected, no stops, serial up, no warnings
        $("#status_btn").removeClass("btn-danger btn-warning").addClass("btn-success")
      }
    }
  }
}


///////////////////////////////////////////////////////////////////////////////
// these functions are called when the various data points change /////////////

var status_handlers = {
  //// always, evn when no hardware connected
  'server': function (status) {
    if (status.server) {  // server connected
      $().uxmessage('success', "Server says HELLO!")
      $("#status_server").removeClass("label-danger").addClass("label-success")
      status_init()
      status_server_cache = true
    } else {  // server disconnected
      if (status_server_cache) {
        status_server_cache = false
        $().uxmessage('warning', "Server LOST.")
        $("#status_server").removeClass("label-success").addClass("label-danger")
        // gray-out all dependant indicators
        $('#status_serial').removeClass("label-danger label-success").addClass("label-default")
        $(".status_hw").removeClass("label-success label-danger label-warning").addClass("label-default")
      }
    }
    status_set_main_button(status)
  },
  'serial': function (status) {
    if (status.serial) {  // serial up
      $('#status_serial').removeClass("label-default label-danger").addClass("label-success")
    } else {  // serial down
      $('#status_serial').removeClass("label-default label-success").addClass("label-danger")
      // gray-out all hardware indicators
      $(".status_hw").removeClass("label-success label-danger label-warning").addClass("label-default")
    }
    status_set_main_button(status)
  },
  'ready': function (status) {
    // hardware sends this when idle but not in a "stop mode" (e.g. error)
    if (status.ready) {
      app_run_btn.stop()
      $('#boundary_btn').prop('disabled', false)
      $('#origin_btn').prop('disabled', false)
      $('#homing_btn').prop('disabled', false)
      // reduce status refresh rate
      if (status_websocket && status_websocket.readyState == 1) {
        status_websocket.send('{"status_every":2}')
      }
    } else {
      app_run_btn.start()
      $('#boundary_btn').prop('disabled', true)
      $('#origin_btn').prop('disabled', true)
      $('#homing_btn').prop('disabled', true)
      // increase status refresh rate
      if (status_websocket && status_websocket.readyState == 1) {
        status_websocket.send('{"status_every":1}')
      }
    }
  },
  //// when hardware connected
  'appver': function (status) {
    if (status.appver) {
      $().uxmessage('notice', "LasaurApp v" + status.appver)
      $('#app_version').html(data.appver)
    } else {
      $('#app_version').html('&lt;not received&gt;')
    }
  },
  'firmver': function (status) {
    if (status.firmver) {
      $().uxmessage('notice', "Firmware v" + status.firmver)
      $('#firm_version').html(data.firmver)
    } else {
      $('#firm_version').html('&lt;not received&gt;')
    }
  },
  'paused': function (status) {
    if (status.paused) {
      // pause button
      $("#pause_btn").removeClass("btn-default").addClass("btn-primary")
      $("#pause_glyph").hide()
      $("#play_glyph").show()
      // run button
      $('#run_btn span.ladda-spinner').hide()
    } else {
      // pause button
      $("#pause_btn").removeClass("btn-primary").addClass("btn-default")
      $("#play_glyph").hide()
      $("#pause_glyph").show()
      // run button
      $('#run_btn span.ladda-spinner').show()
    }
  },
  'pos':function (status) {
    // jobview_head_move(status.pos)
    $("#head_position").animate({
      left: Math.round(status.pos[0]*jobview_scale),
      top: Math.round(status.pos[1]*jobview_scale),
    }, 500, 'linear' )
    // // head position
    // if (data.pos) {
    //   // only update if not manually entering at the same time
    //   if (!$('#x_location_field').is(":focus") &&
    //       !$('#y_location_field').is(":focus") &&
    //       !$('#location_set_btn').is(":focus") &&
    //       !$('#origin_set_btn').is(":focus"))
    //   {
    //     var x = data.pos[0] - app_settings.table_offset[0];
    //     $('#x_location_field').val(x.toFixed(2));
    //     // $('#x_location_field').animate({
    //     //   opacity: 0.5
    //     // }, 100, function() {
    //     //   $('#x_location_field').animate({
    //     //     opacity: 1.0
    //     //   }, 600, function() {});
    //     // });
    //     var y = data.pos[1] - app_settings.table_offset[1];
    //     $('#y_location_field').val(y.toFixed(2));
    //     // $('#y_location_field').animate({
    //     //   opacity: 0.5
    //     // }, 100, function() {
    //     //   $('#y_location_field').animate({
    //     //     opacity: 1.0
    //     //   }, 600, function() {});
    //     // });
        // $("#head_position").animate({
        //   left: Math.round(status.pos[0]*jobview_scale),
        //   top: Math.round(status.pos[1]*jobview_scale),
        // }, 500, 'linear' );
    //   }
    // }
  },
  'underruns': function (status) {},
  'stackclear': function (status) {
    if (typeof(status.stackclear) == 'number') {
      if (status.stackclear < 200) {
        $().uxmessage('warn', "Drive hardware low on memory.")
      } else if (status.stackclear < 100) {
        $().uxmessage('error', "Drive hardware low on memory. Stopping!")
        $('#stop_btn').trigger('click')
      }
    }
  },
  'progress': function (status) {
    app_run_btn.setProgress(status.progress)
  },
  //// stop conditions
  'stops': function (status) {
    // reset all stop error indicators
    $(".status_hw").removeClass("label-default")
    $('#status_limit_x1').removeClass("label-danger").addClass("label-success")
    $('#status_limit_x2').removeClass("label-danger").addClass("label-success")
    $('#status_limit_y1').removeClass("label-danger").addClass("label-success")
    $('#status_limit_y2').removeClass("label-danger").addClass("label-success")
    $('#status_limit_z1').removeClass("label-danger").addClass("label-success")
    $('#status_limit_z2').removeClass("label-danger").addClass("label-success")
    $('#status_requested').removeClass("label-danger").addClass("label-success")
    $('#status_buffer').removeClass("label-danger").addClass("label-success")
    $('#status_marker').removeClass("label-danger").addClass("label-success")
    $('#status_data').removeClass("label-danger").addClass("label-success")
    $('#status_command').removeClass("label-danger").addClass("label-success")
    $('#status_parameter').removeClass("label-danger").addClass("label-success")
    $('#status_transmission').removeClass("label-danger").addClass("label-success")
    // set stop error indicators
    if ('stops' in status) {
      if (status.stops.x1) {$('#status_limit_x1').removeClass("label-success").addClass("label-danger")}
      if (status.stops.x2) {$('#status_limit_x1').removeClass("label-success").addClass("label-danger")}
      if (status.stops.y1) {$('#status_limit_x1').removeClass("label-success").addClass("label-danger")}
      if (status.stops.y2) {$('#status_limit_x1').removeClass("label-success").addClass("label-danger")}
      if (status.stops.z1) {$('#status_limit_x1').removeClass("label-success").addClass("label-danger")}
      if (status.stops.z2) {$('#status_limit_x1').removeClass("label-success").addClass("label-danger")}
      if (status.stops.requested) {$('#status_requested').removeClass("label-success").addClass("label-danger")}
      if (status.stops.buffer) {$('#status_buffer').removeClass("label-success").addClass("label-danger")}
      if (status.stops.marker) {$('#status_marker').removeClass("label-success").addClass("label-danger")}
      if (status.stops.data) {$('#status_data').removeClass("label-success").addClass("label-danger")}
      if (status.stops.command) {$('#status_command').removeClass("label-success").addClass("label-danger")}
      if (status.stops.parameter) {$('#status_parameter').removeClass("label-success").addClass("label-danger")}
      if (status.stops.transmission) {$('#status_transmission').removeClass("label-success").addClass("label-danger")}
    }
    status_set_main_button(status)
  },
  'info': function (status) {
    // reset all info indicators
    $(".status_hw").removeClass("label-default")
    $('#status_door').removeClass("label-warning").addClass("label-success")
    $('#status_chiller').removeClass("label-warning").addClass("label-success")
    // set info indicators
    if ('info' in status) {
      if (status.info.door) {$('#status_door').removeClass("label-success").addClass("label-warning")}
      if (status.info.chiller) {$('#status_chiller').removeClass("label-success").addClass("label-warning")}
    }
    status_set_main_button(status)
  },
  //// only when hardware idle
  'offset': function (status) {},
  'feedrate': function (status) {},
  'intensity': function (status) {},
  'duration': function (status) {},
  'pixelwidth': function (status) {}
}
