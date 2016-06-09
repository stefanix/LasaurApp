

function controls_ready() {

  // dropdown /////////////////////////

  $("#info_btn").tooltip({placement:'bottom', delay: {show:1000, hide:100}})
  $("#info_btn").click(function(e){
    alert("info")
    return false
  })

  $("#export_btn").tooltip({placement:'bottom', delay: {show:1000, hide:100}})
  $("#export_btn").click(function(e){
    alert("export")
    return false
  })

  $("#clear_btn").tooltip({placement:'bottom', delay: {show:1000, hide:100}})
  $("#clear_btn").click(function(e){
    alert("clear")
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
    alert("flash")
    return false
  })

  $("#flash_source_btn").tooltip({placement:'bottom', delay: {show:1000, hide:100}})
  $("#flash_source_btn").click(function(e){
    alert("flash source")
    return false
  })

  $("#reset_btn").tooltip({placement:'bottom', delay: {show:1000, hide:100}})
  $("#reset_btn").click(function(e){
    alert("reset")
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
    alert("run")
    return false
  })

  $("#boundary_btn").tooltip({placement:'bottom', delay: {show:1000, hide:100}})
  $("#boundary_btn").click(function(e){
    alert("boundary")
    return false
  })

  $("#pause_btn").tooltip({placement:'bottom', delay: {show:1000, hide:100}})
  $("#pause_btn").click(function(e){
    alert("pause")
    return false
  })

  $("#stop_btn").tooltip({placement:'bottom', delay: {show:1000, hide:100}})
  $("#stop_btn").click(function(e){
    alert("stop")
    return false
  })



  // footer /////////////////////////

  $("#origin_btn").tooltip({placement:'bottom', delay: {show:1000, hide:100}})
  $("#origin_btn").click(function(e){
    alert("origin")
    return false
  })

  $("#homing_btn").tooltip({placement:'bottom', delay: {show:1000, hide:100}})
  $("#homing_btn").click(function(e){
    alert("homing")
    return false
  })

  $("#motion_btn").tooltip({placement:'bottom', delay: {show:1000, hide:100}})
  $("#motion_btn").click(function(e){
    alert("motion")
    return false
  })

  $("#offset_btn").tooltip({placement:'bottom', delay: {show:1000, hide:100}})
  $("#offset_btn").click(function(e){
    alert("offset")
    return false
  })

  $("#jog_btn").tooltip({placement:'bottom', delay: {show:1000, hide:100}})
  $("#jog_btn").click(function(e){
    alert("jog")
    return false
  })



  // shortcut keys /////////////////////////

  $(document).on('keypress', null, 'i', function(e){
    $('#info_btn').trigger('click')
    return false
  })

  $(document).on('keypress', null, 'c', function(e){
    $('#clear_btn').trigger('click')
    return false
  })

  $(document).on('keypress', null, 'q', function(e){
    $('#queue_btn').trigger('click')
    return false
  })

  $(document).on('keypress', null, 'l', function(e){
    $('#library_btn').trigger('click')
    return false
  })


}
