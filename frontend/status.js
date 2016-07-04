


function status_label_update(val, domid, classyes, classno) {
  if (val) {
    $(domid).removeClass(classno)
    $(domid).addClass(classyes)
  } else {
    $(domid).removeClass(classyes)
    $(domid).addClass(classno)
  }
}


function status_any_error(data, domid) {
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
