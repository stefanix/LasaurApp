
var hardware_ready_state = false;
var has_valid_id = false;
var firmware_version_reported = false;
var lasaurapp_version_reported = false;
var progress_not_yet_done_flag = false;


(function($){
  $.fn.uxmessage = function(kind, text, max_length) {
    if (max_length == null) {
      max_length = 100;
    }

    if (text.length > max_length) {
      text = text.slice(0,max_length) + '\n...'
    }

    text = text.replace(/\n/g,'<br>')

    if (kind == 'notice') {
      $('#log_content').prepend('<div class="log_item log_notice well-sm" style="display:none">' + text + '</div>');
      $('#log_content').children('div').first().show('blind');
      if ($("#log_content").is(':hidden')) {
        $().toastmessage('showNoticeToast', text);
      }
    } else if (kind == 'success') {
      $('#log_content').prepend('<div class="log_item log_success well-sm" style="display:none;">' + text + '</div>');
      $('#log_content').children('div').first().show('blind');
      if ($("#log_content").is(':hidden')) {
        $().toastmessage('showSuccessToast', text);
      }
    } else if (kind == 'warning') {
      $('#log_content').prepend('<div class="log_item log_warning well-sm" style="display:none">' + text + '</div>');
      $('#log_content').children('div').first().show('blind');
      if ($("#log_content").is(':hidden')) {
        $().toastmessage('showWarningToast', text);
      }
    } else if (kind == 'error') {
      $('#log_content').prepend('<div class="log_item log_error well-sm" style="display:none">' + text + '</div>');
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


function send_gcode(gcode, success_msg, progress, name) {
  // if (hardware_ready_state || gcode[0] == '!' || gcode[0] == '~') {
  if (true) {
    if (typeof gcode === "string" && gcode != '') {
      // $().uxmessage('notice', gcode, Infinity);
      $.ajax({
        type: "POST",
        url: "/gcode",
        data: {'name': name, 'job_data':gcode},
        // dataType: "json",
        success: function (data) {
          if (data === "__ok__") {
            $().uxmessage('success', success_msg);
            if (progress) {
              // show progress bar, register live updates
              if ($("#progressbar").children().first().width() == 0) {
                $("#progressbar").children().first().width('5%');
                $("#progressbar").show();
                progress_not_yet_done_flag = true;
                setTimeout(update_progress, 2000);
              }
            }
          } else if (data === "no_id") {
            $().uxmessage('error', "No ID entered. Please insert your ID card.");
          } else {
            $().uxmessage('error', "Backend error: " + data);
          }
        },
        error: function (data) {
          $().uxmessage('error', "Timeout. LasaurApp server down?");
        },
        complete: function (data) {
          // future use
        }
      });
    } else {
      $().uxmessage('error', "No gcode.");
    }
  } else {
    $().uxmessage('warning', "Not ready, request ignored.");
  }
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

        poll_job_history();
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

function getDurationString(durationSeconds) {
    var hours   = Math.floor(durationSeconds / 3600);
    var minutes = Math.floor((durationSeconds - (hours * 3600)) / 60);
    var seconds = durationSeconds - (hours * 3600) - (minutes * 60);

    return hours + 'h ' + minutes + 'min ' + seconds + 's ';
}

function poll_job_history() {
  console.log("poll_job_history");

  $.getJSON('/jobs/history?limit=10', function(history) {
    $('#job_history tbody').empty();

    for (var i in history) {
      var job = history[i];
      var date = new Date(job.start.$date).format('dd.mm.yyyy hh:MM:ss');
      var duration = getDurationString(job.duration);

      var row = $('<tr title="'+date+'" data-toggle="tooltip" data-placement="right"/>');
      row.append($('<td class="name" />').append($('<span/>').text(job.name)));
      row.append($('<td/>').append($('<span/>').text(duration)));
      $('#job_history tbody').append(row);
    }

    if (history.length > 0) {
      $('#total_job_duration').text(getDurationString(history[0].total));
    }

    $('[data-toggle="tooltip"]').tooltip({ container: 'body' });
  });
}


///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////



$(document).ready(function(){

  $().uxmessage('notice', "Frontend started.");

  $('#feedrate_field').val(app_settings.max_seek_speed);
  if (!app_settings.air_assist_enabled) {
    $('#air_assist_group').hide();
  }

  $('#tab_logs_button').click(function(){
    $('#log_content').show();
    $('#tab_logs div.alert').show();
  });

  //TODO finish writing
  $('#tab_sensors_button').click(function(){
    $('#sensor_values').show();
    //$('#tab_sensors div.alert').show();
  });

  if (app_settings.custom_buttons) {
    for (var i = 0; i < app_settings.custom_buttons.length; i++) {
      var btn = app_settings.custom_buttons[i];
      var btnObj = $('<button id="custom_button_' + i + '" class="btn btn-default custom_button" type="submit" title="' + btn.title + '"></button>');
      btnObj.html('<i class="glyphicon glyphicon-' + btn.icon + '"></i>');

      if (btn.default_on) {
        btnObj.addClass('btn-success');
      }
      btnObj.data('def', btn);

      btnObj.click(function() {
        var def = $(this).data('def');
        if (def.toggle) {
          if ($(this).hasClass('btn-success')) {
            $(this).removeClass('btn-success');

            send_gcode(def.gcode_disable, def.disable_message);
          } else {
            $(this).addClass('btn-success');

            send_gcode(def.gcode_enable, def.enable_message);
          }
        } else {
          send_gcode(def.gcode_enable);
        }
      });
      $('#button_container').append(btnObj);
    }
  }


  //////// serial connect and pause button ////////
  var connect_btn_state = false;
  var connect_btn_in_hover = false;
  var pause_btn_state = false;

  function connect_btn_set_state(is_connected) {
    if (is_connected) {
      connect_btn_state = true;
      $("#connect_btn").removeClass("btn-danger");
      $("#connect_btn").removeClass("btn-warning");
      $("#connect_btn").addClass("btn-success");

      if (!connect_btn_in_hover) {
        if (has_valid_id) {
          $("#connect_btn").html("Connected");
        } else {
          $("#connect_btn").html("Card Missing");
          $("#connect_btn").addClass("btn-warning");
        }
      }
    } else {
      connect_btn_state = false
      if (!connect_btn_in_hover) {
        $("#connect_btn").html("Disconnected");
      }
      $("#connect_btn").removeClass("btn-danger");
      $("#connect_btn").removeClass("btn-success");
      $("#connect_btn").addClass("btn-warning");
    }
  }

  // get hardware status
  function poll_hardware_status() {
    $.getJSON('/status', function(data) {
      // pause status
      if (data.paused) {
        pause_btn_state = true;
        $("#pause_btn").addClass("btn-primary");
        $("#pause_btn").html('<i class="glyphicon glyphicon-play"></i>');
      } else {
        pause_btn_state = false;
        $("#pause_btn").removeClass("btn-warning");
        $("#pause_btn").removeClass("btn-primary");
        $("#pause_btn").html('<i class="glyphicon glyphicon-pause"></i>');
      }
      // serial connected
      if (data.serial_connected) {
        connect_btn_set_state(true);
      } else {
        connect_btn_set_state(false);
      }

      // ready state
      has_valid_id = data.has_valid_id;
      if (!data.has_valid_id) {
        $("#connect_btn").html("Card Missing").addClass("btn-warning");
        hardware_ready_state = false;
      } else if (data.ready) {
        hardware_ready_state = true;
        $("#connect_btn").html("Ready").removeClass("btn-warning");
      } else {
        if (data.serial_connected) {
          $("#connect_btn").html("Busy");
        }
        hardware_ready_state = false;
      }

      // door, chiller, power, limit, buffer
      if (data.serial_connected) {
        if (data.door_open) {
          $('#door_status_btn').removeClass('btn-success').addClass('btn-warning');
          // $().uxmessage('warning', "Door is open!");
        } else {
          $('#door_status_btn').removeClass('btn-warning').addClass('btn-success');
        }
        if (data.chiller_off) {
          $('#chiller_status_btn').removeClass('btn-success').addClass('btn-warning');
          // $().uxmessage('warning', "Chiller is off!");
        } else {
          $('#chiller_status_btn').removeClass('btn-warning').addClass('btn-success');
        }
        if (data.power_off) {
          $().uxmessage('error', "Power is off!");
          $().uxmessage('notice', "Turn on Lasersaur power then run homing cycle to reset.");
        }
        if (data.limit_hit) {
          $().uxmessage('error', "Limit hit!");
          $().uxmessage('notice', "Run homing cycle to reset stop mode.");
        }
        if (data.buffer_overflow) {
          $().uxmessage('error', "Rx Buffer Overflow!");
          $().uxmessage('notice', "Please report this to the author of this software.");
        }
        if (data.transmission_error) {
          $().uxmessage('error', "Transmission Error!");
          $().uxmessage('notice', "If this happens a lot tell the author of this software.");
        }
        if (data.x && data.y) {
          // only update if not manually entering at the same time
          if (!$('#x_location_field').is(":focus") &&
              !$('#y_location_field').is(":focus") &&
              !$('#location_set_btn').is(":focus") &&
              !$('#origin_set_btn').is(":focus"))
          {
            var x = parseFloat(data.x).toFixed(2) - app_settings.table_offset[0];
            $('#x_location_field').val(x.toFixed(2));
            $('#x_location_field').animate({
              opacity: 0.5
            }, 100, function() {
              $('#x_location_field').animate({
                opacity: 1.0
              }, 600, function() {});
            });
            var y = parseFloat(data.y).toFixed(2) - app_settings.table_offset[1];
            $('#y_location_field').val(y.toFixed(2));
            $('#y_location_field').animate({
              opacity: 0.5
            }, 100, function() {
              $('#y_location_field').animate({
                opacity: 1.0
              }, 600, function() {});
            });
          }
        }
        if (data.firmware_version && !firmware_version_reported) {
          $().uxmessage('notice', "Firmware v" + data.firmware_version);
          $('#firmware_version').html(data.firmware_version);
          firmware_version_reported = true;
        }
      }
      if (data.lasaurapp_version && !lasaurapp_version_reported) {
        $().uxmessage('notice', "LasaurApp v" + data.lasaurapp_version);
        $('#lasaurapp_version').html(data.lasaurapp_version);
        lasaurapp_version_reported = true;
      }
      // schedule next hardware poll
      setTimeout(function() {poll_hardware_status()}, 4000);
    }).error(function() {
      // lost connection to server
      connect_btn_set_state(false);
      // schedule next hardware poll
      setTimeout(function() {poll_hardware_status()}, 8000);
    });
  }
  // kick off hardware polling
  poll_hardware_status();

  poll_job_history();

  connect_btn_width = $("#connect_btn").width();
  $("#connect_btn").width(connect_btn_width);
  $("#connect_btn").click(function(e){
    if (connect_btn_state == true) {
      $.get('/serial/0', function(data) {
        if (data != "") {
          connect_btn_set_state(false);
        } else {
          // was already disconnected
          connect_btn_set_state(false);
        }
        $("#connect_btn").html("Disconnected");
      });
    } else {
      $("#connect_btn").html('Connecting...');
      $.get('/serial/1', function(data) {
        if (data != "") {
          connect_btn_set_state(true);
          $("#connect_btn").html("Connected");
        } else {
          // failed to connect
          connect_btn_set_state(false);
          $("#connect_btn").removeClass("btn-warning");
          $("#connect_btn").addClass("btn-danger");
        }
      });
    }
    e.preventDefault();
  });
  $("#connect_btn").hover(
    function () {
      connect_btn_in_hover = true;
      if (connect_btn_state) {
        $(this).html("Disconnect");
      } else {
        $(this).html("Connect");
      }
      $(this).width(connect_btn_width);
    },
    function () {
      connect_btn_in_hover = false;
      if (!has_valid_id) {
        $(this).html("Card Missing");
        $("#connect_btn").addClass("btn-warning");
      } else if (connect_btn_state) {
        $(this).html("Connected");
      } else {
        $(this).html("Disconnected");
      }
      $(this).width(connect_btn_width);
    }
  );

  $("#pause_btn").tooltip({placement:'bottom', delay: {show:500, hide:100}});
  $("#pause_btn").click(function(e){
    if (pause_btn_state == true) {  // unpause
      $.get('/pause/0', function(data) {
        if (data == '0') {
          pause_btn_state = false;
          $("#pause_btn").removeClass('btn-primary');
          $("#pause_btn").removeClass('btn-warning');
          $("#pause_btn").html('<i class="glyphicon glyphicon-pause"></i>');
          $().uxmessage('notice', "Continuing...");
        }
      });
    } else {  // pause
      $("#pause_btn").addClass('btn-warning');
      $.get('/pause/1', function(data) {
        if (data == "1") {
          pause_btn_state = true;
          $("#pause_btn").removeClass("btn-warning");
          $("#pause_btn").addClass('btn-primary');
          $("#pause_btn").html('<i class="glyphicon glyphicon-play"></i>');
          $().uxmessage('notice', "Pausing in a bit...");
        } else if (data == '0') {
          $("#pause_btn").removeClass("btn-warning");
          $("#pause_btn").removeClass("btn-primary");
          $().uxmessage('notice', "Not pausing...");
        }
      });
    }
    e.preventDefault();
  });
  //\\\\\\ serial connect and pause button \\\\\\\\


  $("#cancel_btn").tooltip({placement:'bottom', delay: {show:500, hide:100}});
  $("#cancel_btn").click(function(e) {
    var gcode = '!\n';  // ! is enter stop state char
    // $().uxmessage('notice', gcode.replace(/\n/g, '<br>'));
    send_gcode(gcode, "Stopping ...", false);
    var delayedresume = setTimeout(function() {
      var gcode = '~\nG90\nM81\nG0X0Y0F'+app_settings.max_seek_speed+'\n'  // ~ is resume char
      // $().uxmessage('notice', gcode.replace(/\n/g, '<br>'));
      send_gcode(gcode, "Resetting ...", false);
    }, 1000);
    e.preventDefault();
  });

  $("#homing_cycle").tooltip({placement:'bottom', delay: {show:500, hide:100}});
  $("#homing_cycle").click(function(e){
    var gcode = '!\n'  // ! is enter stop state char
    // $().uxmessage('notice', gcode.replace(/\n/g, '<br>'));
    send_gcode(gcode, "Resetting ...", false);
    var delayedresume = setTimeout(function() {
      var gcode = '~\nG30\n'  // ~ is resume char
      // $().uxmessage('notice', gcode.replace(/\n/g, '<br>'));
      send_gcode(gcode, "Homing cycle ...", false);
    }, 1000);
    e.preventDefault();

  });

  $("#go_to_origin").tooltip({placement:'bottom', delay: {show:500, hide:100}});
  $("#go_to_origin").click(function(e){
    var gcode;
    if(e.shiftKey) {
      // also reset offset
      reset_offset();
    }
    gcode = 'G90\nG0X0Y0F'+app_settings.max_seek_speed+'\n'
    // $().uxmessage('notice', gcode);
    send_gcode(gcode, "Going to origin ...", false);
    e.preventDefault();
  });

  $("#reset_atmega").click(function(e){
    $.get('/reset_atmega', function(data) {
      if (data != "") {
        $().uxmessage('success', "Atmega restarted!");
        firmware_version_reported = false;
      } else {
        $().uxmessage('error', "Atmega restart failed!");
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
    $('#go_to_origin').trigger('click');
    return false;
  });

  var cancel_modal_active = false;
  $(document).on('keyup', null, 'esc', function(e){
    if (cancel_modal_active === true) {
      $('#cancel_modal').modal('hide');
      cancel_modal_active = false;
    } else {
      $('#cancel_modal').modal('show');
      $('#really_cancel_btn').focus();
      cancel_modal_active = true;
    }
    return false;
  });

  $('#really_cancel_btn').click(function(e){
    $('#cancel_btn').trigger('click');
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

  $(document).on('keypress', null, 's', function(e){
    $('#tab_sensors_button').trigger('click');
    return false;
  });

  $('#history_modal').on('show.bs.modal', function (e) {

    $.getJSON('/jobs/history', function(history) {
      $('#history_modal tbody').empty();
      for (var i in history) {
        var job = history[i];
        var start_date = new Date(job.start.$date).format('dd.mm.yyyy hh:MM:ss');
        var end_date = new Date(job.end.$date).format('dd.mm.yyyy hh:MM:ss');
        var duration = getDurationString(job.duration);

        var row = $('<tr/>');
        row.append($('<td />').append($('<span class="cell row-1" />').text(job.name).attr('data-original-title', job.name)));
        row.append($('<td />').append($('<span class="cell row-2" />').text(job.user_id)));
        row.append($('<td />').append($('<span class="cell row-3" />').text(start_date)));
        row.append($('<td />').append($('<span class="cell row-4" />').text(end_date)));
        //row.append($('<td />').append($('<span class="cell row-5" />').text(job.lines)));
        row.append($('<td />').append($('<span class="cell row-6" />').text(duration)));
        row.data('duration', job.duration);
        $('#history_modal tbody').append(row);
      }

      if (history.length > 0) {
        $('#total_job_duration_big').text(getDurationString(history[0].total));
      }

      $('#selected_history_label').hide();

      $('#history_modal tbody span.cell').tooltip({ container: 'body' });
    });
  });

  $('#job_history_big tbody').on('click', 'tr', function() {
    $(this).toggleClass('selected');

    var selected = $('#job_history_big tbody tr.selected');
    if (selected.length <= 0) {
      $('#selected_history_label').hide();
    } else {
      $('#selected_history_label').show();

      var duration = 0;
      selected.each(function(i, row) {
        duration += $(row).data('duration');
      });

      var durationString = getDurationString(duration);
      $('#selected_history_label .badge').text(durationString);
    }
  });
});  // ready


 $('#material_modal').on('show.bs.modal', function (e) {
    $("#job_comment_input").value = "";
    $('#job_materials').val([]);
    //$('#job_services').val([]);
    //TODO: Fix hard coded default
    $('#job_services').val(20);
    //$("#job_services").val = [$("option[value='20']")];
    $('#material_selected').removeClass("btn-primary");
});

useOdoo = true;

$(document).ready(function() {
    //check if we use Odoo
    $.get('/material/get_sell_mode', function(e){
        alert(e)
        useOdoo = e;
        odoo_product = 0;
        odoo_service = 0;
        job_comment = "";

        default_cut_speed = 1500;
        default_cut_intensity = 100;
        default_engrave_speed = 4000;
        default_engrave_intensity = 30;

        if(useOdoo == 'True'){
            var comment_div = document.getElementById('job_comment');
            comment_div.innerHTML = "Comment: ";
            var comment_input = document.createElement("input");
            comment_input.setAttribute("id", "job_comment_input");
            comment_input.setAttribute("type", "text");
            comment_input.setAttribute("name", "job_comment_input");
            comment_input.setAttribute("value", "");
            comment_div.appendChild(comment_input);

            $.getJSON('/material/services', function(services) {
              var select_list = document.getElementById('job_services');
              for (var i in services) {
                  var option = document.createElement("option");
                  option.value = services[i].id;
                  option.innerHTML = services[i].name;
                  select_list.appendChild(option);
              }
              select_list.size = Math.min(services.length, select_list.size);
            });


            $.getJSON('/material/products', function(products) {
              var select_list = document.getElementById("job_materials");
              for (var i in products) {
                  var option = document.createElement("option");
                  option.value = products[i].id;
                  option.innerHTML = products[i].name;
                  select_list.appendChild(option);
              }
              select_list.size = Math.min(products.length, select_list.size);
            });
        }
    });

//    if(!useOdoo) {
//
//
//        $.get("/material/set_product/" + odoo_product, function(e){ });
//        $.get("/material/set_service/" + odoo_service, function(e){ });
//        $.get("/material/set_comment/" + job_comment, function(e){ });
//
//        return();
//    }

//    $("#material_modal").modal('hide');
//        return;
//    }
  });

var material_form_ok_clickable = false;

$('#material_form').change(function(){
    if($('#job_materials').val() != null && $('#job_services').val() != null) {
        material_form_ok_clickable = true;
        $('#material_selected').addClass("btn-primary");
    } else {
        material_form_ok_clickable = false;
        $('#material_selected').removeClass("btn-primary");
    }
});

$('#job_materials').dblclick(function(){
    $('#job_materials').trigger("click");
    if(material_form_ok_clickable)
        $("#material_selected").trigger("click");
});

default_cut_speed = 1500;
default_cut_intensity = 100;
default_engrave_speed = 4000;
default_engrave_intensity = 20;

var sensor_names = null;
var sensor_values = null;

setInterval(function(){
    str = "";
    if(sensor_names && sensor_values){
        str = "";
        for(i = 0; i < sensor_names.length; i++) {
            str += "<p>";
            str += sensor_names[i];
            str += ": ";
            str += sensor_values[i];
            str += "</p>";
        }
    }
    document.getElementById('sensor_values').innerHTML = str;

    $.getJSON("/sensors/names", function(e){sensor_names = e;})
    $.getJSON("/sensors/values", function(e){sensor_values = e;})
}, 3000);

$("#material_selected").click(function(e) {
    if(!material_form_ok_clickable)
      return;
    odoo_product = $('#job_materials').val();
    odoo_service = $('#job_services').val();
    job_comment = document.querySelector('input[name = "job_comment_input"]').value;

    $.get("/material/set_product/" + odoo_product, function(e){ });
    $.get("/material/set_service/" + odoo_service, function(e){ });
    $.get("/material/set_comment/" + job_comment, function(e){ });

    $.get("/material/getCutSpeed", function(e) {default_cut_speed = e;});
    $.get("/material/getCutIntensity", function(e) {default_cut_intensity = e;});
    $.get("/material/getEngraveSpeed", function(e) {default_engrave_speed = e;});
    $.get("/material/getEngraveIntensity", function(e) {default_engrave_intensity = e;});

    $("#material_modal").modal('hide');

    //$('#material_selected').trigger("addToQueue");
});




/// PASSES //////////////////////////////////////


function setDefaultCut(passnum){
    //$('#feedrate_'+passnum).value = 100;
    feedrate_field = document.getElementById('feedrate_' + passnum);
    feedrate_field.value = default_cut_speed;
    intensity_field = document.getElementById('intensity_' + passnum);
    intensity_field.value = default_cut_intensity;
}

function setDefaultEngrave(passnum){
    //$('#feedrate_'+passnum).value = 100;
    feedrate_field = document.getElementById('feedrate_' + passnum);
    feedrate_field.value = default_engrave_speed;
    intensity_field = document.getElementById('intensity_' + passnum);
    intensity_field.value = default_engrave_intensity;
}


jQuery.fn.shake = function(intShakes, intDistance, intDuration) {
    this.each(function() {
        $(this).css("position","relative");
        for (var x=1; x<=intShakes; x++) {
        $(this).animate({left:(intDistance*-1)}, (((intDuration/intShakes)/4)))
    .animate({left:intDistance}, ((intDuration/intShakes)/2))
    .animate({left:0}, (((intDuration/intShakes)/4)));
    }
  });
  return this;
};
