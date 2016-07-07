
var app_config_main = undefined
var app_run_btn = undefined



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

  // get appconfig from server
  get_request({
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
