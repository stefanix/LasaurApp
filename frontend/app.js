
var app_config_main = undefined
var app_run_btn = undefined
var app_visibility = true


// toast messages, install jquery plugin
;(function($){
  $.fn.uxmessage = function(kind, text, max_length) {
    if (max_length == undefined) {
        max_length = 100
    }

    if (max_length !== false && text.length > max_length) {
      text = text.slice(0,max_length) + '\n...'
    }

    text = text.replace(/\n/g,'<br>')

    if (kind == 'notice') {
      $('#log_content').prepend('<div class="log_item log_notice well" style="display:none">' + text + '</div>')
      $('#log_content').children('div').first().show('blind')
      if ($("#log_content").is(':hidden')) {
        $().toastmessage('showToast',
          {text: text, sticky: false, position: 'top-left', type: 'notice'}
        )
      }
    } else if (kind == 'success') {
      $('#log_content').prepend('<div class="log_item log_success well" style="display:none">' + text + '</div>')
      $('#log_content').children('div').first().show('blind')
      if ($("#log_content").is(':hidden')) {
        $().toastmessage('showToast',
          {text: text, sticky: false, position: 'top-left', type: 'success'}
        )
      }
    } else if (kind == 'warning') {
      $('#log_content').prepend('<div class="log_item log_warning well" style="display:none">' + text + '</div>')
      $('#log_content').children('div').first().show('blind')
      if ($("#log_content").is(':hidden')) {
        $().toastmessage('showToast',
          {text: text, sticky: false, position: 'top-left', type: 'warning'}
        )
      }
    } else if (kind == 'error') {
      $('#log_content').prepend('<div class="log_item log_error well" style="display:none">' + text + '</div>')
      $('#log_content').children('div').first().show('blind');
      if ($("#log_content").is(':hidden')) {
        $().toastmessage('showToast',
          {text: text, sticky: false, position: 'top-left', type: 'error'}
        )
      }
    }

    while ($('#log_content').children('div').length > 200) {
      $('#log_content').children('div').last().remove()
    }

  };
})(jQuery)


///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////

$(document).ready(function(){
  // $().uxmessage('notice', "Frontend started.")
  // modern browser check
  if(!Object.hasOwnProperty('keys')) {
    alert("Error: Browser may be too old/non-standard.")
  }

  // unblur button after pressing
  $(".btn").mouseup(function(){
      $(this).blur()
  })

  // run_btn, make a ladda progress spinner button
  // http://msurguy.github.io/ladda-bootstrap/
  app_run_btn = Ladda.create($("#run_btn")[0])

  // page visibility events
  window.onfocus = function() {
    app_visibility = true
    if (status_websocket && status_websocket.readyState == 1) {
      if ('ready' in status_cache && status_cache.ready) {
        status_websocket.send('{"status_every":3}')
      } else {
        status_websocket.send('{"status_every":1}')
      }
    }
  }
  window.onblur = function() {
    app_visibility = false
    if (status_websocket && status_websocket.readyState == 1) {
      status_websocket.send('{"status_every":10}')
    }
  }

  // get appconfig from server
  request_get({
    url:'/config',
    success: function (data) {
      // $().uxmessage('success', "App config received.")
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

  // connect to status channel via websocket
  // connect and also continuously check connection and reconnect if closed
  app_status_connect()
  setInterval(function () {
      if (!status_websocket || status_websocket.readyState == 3) {
        app_status_connect()
      }
    }, 8000)
}


function app_status_connect() {
  var url = "ws://"+location.hostname+":"+app_config_main.websocket_port+"/"
  status_websocket = new WebSocket(url)
  status_websocket.onopen = function(e) {
    status_handlers.server({'server':true})
  }
  status_websocket.onclose = function(e) {
    status_handlers.server({'server':false, 'serial':false})
  }
  status_websocket.onerror = function(e) {
    if (status_websocket.readyState != 3) {
      $().uxmessage('error', "Server")
    }
  }
  status_websocket.onmessage = function(e) {
    // pulsate
    $("#status_glyph").animate({"opacity": 1.0},50).animate({"opacity": 0.5},200)

    // handle data
    var data = JSON.parse(e.data)
    // console.log(data)

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

    // call handlers, only when status changes
    status_handle_message(data)

  }  // status_websocket.onmessage
}  // start_status_channel
