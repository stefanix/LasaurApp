

var status_data_cache = {
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
  'stops': {},
  // possible keys:
  // x1, x2, y1, y2, z1, z2,
  // requested, buffer, marker, data, command, parameter, transmission

  'info':{},
  // possible keys: door, chiller

  //// only when hardware idle
  'offset': [0.0, 0.0, 0.0],
  'feedrate': 0.0,
  'intensity': 0.0,
  'duration': 0.0,
  'pixelwidth': 0.0
}


var status_handlers {
  //// always
  'serial': function () {},
  'ready': function () {},
  //// when hardware connected
  'appver': function () {},
  'firmver': function () {},
  'paused': function () {},
  'pos':function () {},
  'underruns': function () {},
  'stackclear': function () {},
  'progress': function () {},

  //// stop conditions
  // indicated when key present
  'stops': {},
  // possible keys:
  // x1, x2, y1, y2, z1, z2,
  // requested, buffer, marker, data, command, parameter, transmission

  'info':{},
  // possible keys: door, chiller

  //// only when hardware idle
  'offset': [0.0, 0.0, 0.0],
  'feedrate': 0.0,
  'intensity': 0.0,
  'duration': 0.0,
  'pixelwidth': 0.0
}

function status_handle_message(msg) {
  for (var k in status_data_cache) {
    if (k in msg) {
      if (value) {
        if (status_data_cache[k] != msg[d]) {
          // handle a value change

        }
      } else if (array) {

      } else if hash {

      }
    }
  }
}


function status_label_update(val, domid, classactive) {
  if (val) {
    $(domid).removeClass("label-success")
    $(domid).addClass(classactive)
  } else {
    $(domid).removeClass(classactive)
    $(domid).addClass("label-success")
  }
}


function status_txerror_update(data, domid) {
  var flag = false
  var label = "TxError"
  if (data.stops.buffer) {
    flag = true
    label = "TxBuffer"
  } else if (data.stops.marker) {
    flag = true
    label = "TxMarker"
  } else if (data.stops.data) {
    flag = true
    label = "TxData"
  } else if (data.stops.command) {
    flag = true
    label = "TxCommand"
  } else if (data.stops.parameter) {
    flag = true
    label = "TxParameter"
  } else if (data.stops.transmission) {
    flag = true
    label = "TxTransmission"
  }

  if (flag) {
    $(domid).removeClass("label-success")
    $(domid).addClass("label-danger")
  } else {
    $(domid).removeClass("label-danger")
    $(domid).addClass("label-success")
  }

  $(domid).html(label)
}
