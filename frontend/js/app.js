
var appconfig_main = undefined;
var hardware_ready_state = false;
var firmware_version_reported = false;
var lasaurapp_version_reported = false;
var progress_not_yet_done_flag = false;


(function($){
  $.fn.uxmessage = function(kind, text, max_length) {
    if (max_length == undefined) {
        max_length = 100;
    }

    if (max_length !== false && text.length > max_length) {
      text = text.slice(0,max_length) + '\n...'
    }

    text = text.replace(/\n/g,'<br>')

    if (kind == 'notice') {
      $('#log_content').prepend('<div class="log_item log_notice well" style="display:none">' + text + '</div>');
      $('#log_content').children('div').first().show('blind');
      if ($("#log_content").is(':hidden')) {
        $().toastmessage('showNoticeToast', text);
      }
    } else if (kind == 'success') {
      $('#log_content').prepend('<div class="log_item log_success well" style="display:none">' + text + '</div>');
      $('#log_content').children('div').first().show('blind');
      if ($("#log_content").is(':hidden')) {
        $().toastmessage('showSuccessToast', text);
      }
    } else if (kind == 'warning') {
      $('#log_content').prepend('<div class="log_item log_warning well" style="display:none">' + text + '</div>');
      $('#log_content').children('div').first().show('blind');
      if ($("#log_content").is(':hidden')) {
        $().toastmessage('showWarningToast', text);
      }
    } else if (kind == 'error') {
      $('#log_content').prepend('<div class="log_item log_error well" style="display:none">' + text + '</div>');
      $('#log_content').children('div').first().show('blind');
      if ($("#log_content").is(':hidden')) {
        $().toastmessage('showErrorToast', text);
      }
    }

    while ($('#log_content').children('div').length > 200) {
      $('#log_content').children('div').last().remove();
    }

  };
})(jQuery);


function get_request(args) {
  // args items: url, success, error, complete
  $.ajax({
    type: "GET",
    url: args.url,
    dataType: "json",
    username: "laser",
    password: "laser",
    statusCode: {
      400: function(s) {
        // alert(JSON.stringify(s))
        if ('responseText' in s) {
          r = s.responseText;
          var error_txt = r.slice(r.indexOf('<pre>')+5,r.lastIndexOf('</pre>'))
          $().uxmessage('error', error_txt);
        }
      },
      401: function() {
        $().uxmessage('error', "Wrong password/username.");
      }
    },
    success: function (data) {
      if ('success' in args) {
        args.success(data);
      }
    },
    error: function (data) {
      if ('error' in args) {
        args.error(data);
      }
    },
    complete: function (data) {
      if ('complete' in args) {
        args.complete(data);
      }
    }
  });
}


function send_job(job, success_msg, progress) {
  if (true) {
    if ('vector' in job || 'raster' in job) {
      // $().uxmessage('notice', JSON.stringify(job), Infinity);
      $.ajax({
        type: "POST",
        url: "/job",
        data: {'job_data':JSON.stringify(job)},
        // dataType: "json",
        success: function (data) {
          if (data == "__ok__") {
            $().uxmessage('success', success_msg);
            if (progress = true) {
              // show progress bar, register live updates
              if ($("#progressbar").children().first().width() == 0) {
                $("#progressbar").children().first().width('5%');
                $("#progressbar").show();
                progress_not_yet_done_flag = true;
                setTimeout(update_progress, 2000);
              }
            }
          } else {
            $().uxmessage('error', "Backend error: " + data);
          }
        },
        error: function (data) {
          // alert(JSON.stringify(data))
          $().uxmessage('error', "Timeout. LasaurApp server down?");
          if ("responseText" in data) {
            $().uxmessage('error', data.responseText, Infinity);
          }
        },
        complete: function (data) {
          // future use
        }
      });
    } else {
      $().uxmessage('error', "No job data.");
    }
  } else {
    $().uxmessage('warning', "Not ready, request ignored.");
  }
}
// function send_gcode(gcode, success_msg, progress) {
//   // if (hardware_ready_state || gcode[0] == '!' || gcode[0] == '~') {
//   if (true) {
//     if (typeof gcode === "string" && gcode != '') {
//       // $().uxmessage('notice', gcode, Infinity);
//       $.ajax({
//         type: "POST",
//         url: "/gcode",
//         data: {'job_data':gcode},
//         // dataType: "json",
//         success: function (data) {
//           if (data == "__ok__") {
//             $().uxmessage('success', success_msg);
//             if (progress = true) {
//               // show progress bar, register live updates
//               if ($("#progressbar").children().first().width() == 0) {
//                 $("#progressbar").children().first().width('5%');
//                 $("#progressbar").show();
//                 progress_not_yet_done_flag = true;
//                 setTimeout(update_progress, 2000);
//               }
//             }
//           } else {
//             $().uxmessage('error', "Backend error: " + data);
//           }
//         },
//         error: function (data) {
//           $().uxmessage('error', "Timeout. LasaurApp server down?");
//         },
//         complete: function (data) {
//           // future use
//         }
//       });
//     } else {
//       $().uxmessage('error', "No gcode.");
//     }
//   } else {
//     $().uxmessage('warning', "Not ready, request ignored.");
//   }
// }


function send_relative_move(x, y, z, seekrate, success_msg) {
  var job = {
    "vector":{
      "passes":[
        {
          "paths":[0],
          "relative":true,
          "seekrate":seekrate
        }
      ],
      "paths":[
        [
          [[x,y,z]]
        ]
      ],
      "noreturn": true
    }
  }
  send_job(job, success_msg, false);
}


function update_progress() {
  $.get('/queue_pct_done', function(data) {
    if (data.length > 0) {
      var pct = parseInt(data);
      $("#progressbar").children().first().width(pct+'%');
      setTimeout(update_progress, 2000);
    } else {
      if (progress_not_yet_done_flag) {
        $("#progressbar").children().first().width('100%');
        $().uxmessage('notice', "Done.");
        progress_not_yet_done_flag = false;
        setTimeout(update_progress, 2000);
      } else {
        $('#progressbar').hide();
        $("#progressbar").children().first().width(0);
      }
    }
  });
}


function open_bigcanvas(scale, deselectedColors) {
  var w = scale * app_settings.canvas_dimensions[0];
  var h = scale * app_settings.canvas_dimensions[1];
  $('#container').before('<a id="close_big_canvas" href="#"><canvas id="big_canvas" width="'+w+'px" height="'+h+'px" style="border:1px dashed #aaaaaa;"></canvas></a>');
  var mid = $('body').innerWidth()/2.0-30;
  $('#close_big_canvas').click(function(e){
    close_bigcanvas();
    return false;
  });
  $("html").on('keypress.closecanvas', function (e) {
    if ((e.which && e.which == 13) || (e.keyCode && e.keyCode == 13) ||
        (e.which && e.which == 27) || (e.keyCode && e.keyCode == 27)) {
      // on enter or escape
      close_bigcanvas();
      return false;
    } else {
      return true;
    }
  });
  // $('#big_canvas').focus();
  $('#container').hide();
  var bigcanvas = new Canvas('#big_canvas');
  // DataHandler.draw(bigcanvas, 4*app_settings.to_canvas_scale, getDeselectedColors());
  if (deselectedColors === undefined) {
    DataHandler.draw(bigcanvas, scale*app_settings.to_canvas_scale);
  } else {
    DataHandler.draw(bigcanvas, scale*app_settings.to_canvas_scale, deselectedColors);
  }
}


function close_bigcanvas() {
  $('#big_canvas').remove();
  $('#close_big_canvas').remove();
  $('html').off('keypress.closecanvas');
  delete bigcanvas;
  $('#container').show();
}


function generate_download(filename, filedata) {
  $.ajax({
    type: "POST",
    url: "/stash_download",
    data: {'filedata': filedata},
    success: function (data) {
      window.open("/download/" + data + "/" + filename, '_blank');
    },
    error: function (data) {
      $().uxmessage('error', "Timeout. LasaurApp server down?");
    },
    complete: function (data) {
      // future use
    }
  });
}



///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////



$(document).ready(function(){
  // modern browser check
  if(!Object.hasOwnProperty('keys')) {
    alert("Error: Browser may be too old/non-standard.")
  }

  $('#tab_logs_button').click(function(){
    $('#log_content').show()
    $('#tab_logs div.alert').show()
  })

  $().uxmessage('notice', "Frontend started.");

  // get config from server
  get_request({
    url:'/config',
    success: function (data) {
      $().uxmessage('success', "App config received.");
      appconfig_main = data;
    },
    error: function (data) {
      $().uxmessage('error', "No app config received");
    },
    complete: function (data) {
      ready_2();
    }
  })

});


function ready_2() {

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
      // {"info": {"chiller": true}, "feedrate": 8000.0, "intensity": 0.0, "pos": [-0.005, 0.005, 0.0], "stops": {}, "stackclear": 572.0, "paused": false, "duration": 0.0, "appver": "15.00-beta1", "firmver": "15.0", "underruns": 1.0, "pixelwidth": 0.0, "offset": [0.0, 0.0, 0.0], "ready": true, "progress": 1.0, "serial": true}
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
