
var appconfig_main = undefined
var hardware_ready_state = false
var firmware_version_reported = false
var lasaurapp_version_reported = false
var progress_not_yet_done_flag = false;



///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////


$(document).ready(function(){
  $().uxmessage('notice', "Frontend started.")
  // modern browser check
  if(!Object.hasOwnProperty('keys')) {
    alert("Error: Browser may be too old/non-standard.")
  }
  // get appconfig from server
  get_request({
    url:'/config',
    success: function (data) {
      $().uxmessage('success', "App config received.")
      appconfig_main = data
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
  var keys_sorted = Object.keys(appconfig_main).sort()
  for (var i=0; i<keys_sorted.length; i++) {
    html += keys_sorted[i] + " : " + appconfig_main[keys_sorted[i]] + "<br>"
  }
  $('#config_content').html(html)

  // call 'ready' of jobview
  jobview_ready()

}


function config_received_next() {

  $('#feedrate_field').val(appconfig_main.feedrate);

  //////// serial connect and pause button ////////
  var pause_btn_state = false;

  // status by websocket
  function status_connect(){
    websocket = new WebSocket("ws://"+location.hostname+":4411/");
    websocket.onopen = function(e) {
      $().uxmessage('success', "status channel OPEN");
    };
    websocket.onclose = function(e) {
      $().uxmessage('warning', "status channel CLOSED");
      // setTimeout(function() {status_connect()}, 8000);
    };
    websocket.onerror = function(e) {
      $().uxmessage('error', "status channel");
    };
    websocket.onmessage = function(e) {
      // {"info": {"chiller": true}, "feedrate": 8000.0, "intensity": 0.0, "pos": [-0.005, 0.005, 0.0], "stops": {}, "stackclear": 572.0, "paused": false, "duration": 0.0, "appver": "15.00-beta1", "firmver": "15.0", "underruns": 1.0, "pulses_per_mm": 0.0, "offset": [0.0, 0.0, 0.0], "ready": true, "progress": 1.0, "serial": true}
      var data = JSON.parse(e.data);
      // $().uxmessage('notice', e.data, Infinity);

      // pause status
      if (data.paused) {
        pause_btn_state = true;
        $("#pause_btn").addClass("btn-primary");
        $("#pause_btn").html('<i class="icon-play"></i>');
      } else {
        pause_btn_state = false;
        $("#pause_btn").removeClass("btn-warning");
        $("#pause_btn").removeClass("btn-primary");
        $("#pause_btn").html('<i class="icon-pause"></i>');
      }

      // serial connected
      if (data.serial) {
        // ready state
        if (data.ready) {
          hardware_ready_state = true;
          $("#connect_btn").removeClass("btn-danger");
          $("#connect_btn").removeClass("btn-warning");
          $("#connect_btn").addClass("btn-success");
        } else {
          hardware_ready_state = false;
          $("#connect_btn").removeClass("btn-danger");
          $("#connect_btn").removeClass("btn-success");
          $("#connect_btn").addClass("btn-warning");
        }
      } else {
        $("#connect_btn").removeClass("btn-success");
        $("#connect_btn").removeClass("btn-warning");
        $("#connect_btn").addClass("btn-danger");
        hardware_ready_state = false;
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
            var x = parseFloat(data.pos[0]).toFixed(2) - app_settings.table_offset[0];
            $('#x_location_field').val(x.toFixed(2));
            // $('#x_location_field').animate({
            //   opacity: 0.5
            // }, 100, function() {
            //   $('#x_location_field').animate({
            //     opacity: 1.0
            //   }, 600, function() {});
            // });
            var y = parseFloat(data.pos[1]).toFixed(2) - app_settings.table_offset[1];
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
        if (data.firmver && !firmware_version_reported) {
          $().uxmessage('notice', "Firmware v" + data.firmver);
          $('#firmware_version').html(data.firmver);
          firmware_version_reported = true;
        }
      }
      if (data.appver && !lasaurapp_version_reported) {
        $().uxmessage('notice', "LasaurApp v" + data.appver);
        $('#lasaurapp_version').html(data.appver);
        lasaurapp_version_reported = true;
      }


    };
  }

  // kick off status channel
  status_connect();



  $("#pause_btn").tooltip({placement:'bottom', delay: {show:500, hide:100}});
  $("#pause_btn").click(function(e){
    if (pause_btn_state == true) {  // unpause
      get_request({
        url:'/unpause',
        success: function (data) {
          pause_btn_state = false;
          $("#pause_btn").removeClass('btn-primary');
          $("#pause_btn").html('<i class="icon-pause"></i>');
          $().uxmessage('notice', "Continuing...");
        }
      });
    } else {  // pause
      get_request({
        url:'/pause',
        success: function (data) {
          pause_btn_state = true;
          $("#pause_btn").addClass('btn-primary');
          $("#pause_btn").html('<i class="icon-play"></i>');
          $().uxmessage('notice', "Pausing in a bit...");
        }
      });
    }
    e.preventDefault();
  });
  //\\\\\\ serial connect and pause button \\\\\\\\


  $("#stop_btn").tooltip({placement:'bottom', delay: {show:500, hide:100}});
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
                  $().uxmessage('notice', 'Resetting ...');
                }
              });
            }
          });
        }, 1000);
      }
    });
    e.preventDefault();
  });


  $("#homing_btn").tooltip({placement:'bottom', delay: {show:500, hide:100}});
  $("#homing_btn").click(function(e){
    get_request({
      url:'/homing',
      success: function (data) {
        $().uxmessage('notice', "Homing ...");
      }
    });
    e.preventDefault();
  });


  $("#origin_btn").tooltip({placement:'bottom', delay: {show:500, hide:100}});
  $("#origin_btn").click(function(e){
    var gcode;
    if(e.shiftKey) {
      // also reset offset
      reset_offset();
    }
    get_request({
      url:'/move/0/0/0',
      success: function (data) {
        $().uxmessage('notice', "Going to origin ...");
      }
    });
    e.preventDefault();
  });


  $("#reset_btn").click(function(e){
    get_request({
      url:'/reset',
      success: function (data) {
        firmware_version_reported = false;
        $().uxmessage('notice', "Firmware reset successful.");
      }
    });
    e.preventDefault();
  });


  /// tab shortcut keys /////////////////////////
  $(document).on('keypress', null, 'p', function(e){
    $('#pause_btn').trigger('click');
    return false;
  });

  $(document).on('keypress', null, '0', function(e){
    $('#origin_btn').trigger('click');
    return false;
  });

  var cancel_modal_active = false;
  $(document).on('keyup', null, 'esc', function(e){
    if (cancel_modal_active === true) {
      $('#cancel_modal').modal('hide');
      cancel_modal_active = false;
    } else {
      $('#cancel_modal').modal('show');
      $('#really_stop_btn').focus();
      cancel_modal_active = true;
    }
    return false;
  });

  $('#really_stop_btn').click(function(e){
    $('#stop_btn').trigger('click');
    $('#cancel_modal').modal('hide');
    cancel_modal_active = false;
  });



  /// tab shortcut keys /////////////////////////

  $(document).on('keypress', null, 'j', function(e){
    $('#tab_jobs_button').trigger('click');
    return false;
  });

  $(document).on('keypress', null, 'i', function(e){
    $('#tab_import_button').trigger('click');
    return false;
  });

  $(document).on('keypress', null, 'm', function(e){
    $('#tab_mover_button').trigger('click');
    return false;
  });

  $(document).on('keypress', null, 'l', function(e){
    $('#tab_logs_button').trigger('click');
    return false;
  });

}  // ready_2
