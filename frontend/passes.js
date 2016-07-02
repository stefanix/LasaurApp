

function passes_clear() {
  $('#job_passes').html("")
}

function passes_add(feedrate, intensity, colors_assigned) {
  // multiple = typeof multiple !== 'undefined' ? multiple : 1  // default to 1
  var colors = jobhandler.getAllColors()
  var num_passes_already = $('#job_passes').children('.pass_widget').length
  var num = num_passes_already + 1
  var html = passes_pass_html(num, feedrate, intensity, colors)
  if ($('#pass_add_widget').length) {
    var pass_elem = $(html).insertBefore('#pass_add_widget')
  } else {
    var pass_elem = $(html).appendTo('#job_passes')
  }
  // unblur buttons after pressing
  $("#pass_add_widget > .btn").mouseup(function(){
      $(this).blur();
  })

  // assign colors
  for (var i = 0; i < colors_assigned.length; i++) {
    var col_sliced = colors_assigned[i].slice(1)
    $('#passsel_'+num+'_'+col_sliced).hide()
    $('#pass_'+num+'_'+col_sliced).show(300)
    passes_update_handler()
  }

  // bind color assign button
  $('#assign_btn_'+num).click(function(e) {
    if (jobview_color_selected !== undefined) {
      var col_sliced = jobview_color_selected.slice(1)
      $('#passsel_'+num+'_'+col_sliced).hide()
      $('#pass_'+num+'_'+col_sliced).hide()
      $('#pass_'+num+'_'+col_sliced).show(300)
      passes_update_handler()
      return false
    } else {
      return true
    }
  })

  // bind all color add buttons within dropdown
  $('.color_add_btn_'+num).click(function(e) {
    var color = $(this).children('span').text()
    $('#passsel_'+num+'_'+color.slice(1)).hide()
    $('#pass_'+num+'_'+color.slice(1)).show(300)
    $('#passdp_'+num).dropdown("toggle")
    passes_update_handler()
    return false
  })

  // bind all color remove buttons
  $('.color_remove_btn_'+num).click(function(e) {
    var color = $(this).parent().find('span.colmem').text()
    $('#passsel_'+num+'_'+color.slice(1)).show(0)
    $('#pass_'+num+'_'+color.slice(1)).hide(300)
    passes_update_handler()
    return false
  })

  // bind all color select buttons
  $('.color_select_btn_'+num).click(function(e) {
    var color = $(this).parent().find('span.colmem').text()
    jobhandler.selectColor(color)
    return false
  })

  // hotkey
  // $('#assign_btn_'+num).tooltip({placement:'bottom', delay: {show:1000, hide:100}})
  Mousetrap.bind([num.toString()], function(e) {
      $('#assign_btn_'+num).trigger('click')
      return false;
  })
}


function passes_color_html(num, color) {
  var html =
  '<div id="pass_'+num+'_'+color.slice(1)+'" class="btn-group pull-left" style="margin-top:0.5em; display:none">'+
    '<span style="display:none" class="colmem">'+color+'</span>'+
    '<button id="color_btn" class="btn btn-default btn-sm color_select_btn_'+num+'" '+
      'type="submit" style="width:175px; background-color:'+color+'">'+
      '<span class="glyphicon glyphicon-eye-open"></span>'+
    '</button>'+
    '<button class="btn btn-default btn-sm color_remove_btn_'+num+'" type="submit" style="width:34px">'+
      '<span class="glyphicon glyphicon-remove"></span>'+
    '</button>'+
  '</div>'
  return html
}


function passes_pass_html(num, feedrate, intensity, colors) {
  // add all color selectors
  var select_html = ''
  for (var i = 0; i < colors.length; i++) {
    select_html += '<li id="passsel_'+num+'_'+colors[i].slice(1)+'" style="background-color:'+colors[i]+';"">'+
    '<a href="#" class="color_add_btn_'+num+'" style="color:'+colors[i]+'">Assign<span style="display:none">'+colors[i]+'</span></a></li>'
  }
  // add all selectable colors
  var colors_html = ''
  for (var i = 0; i < colors.length; i++) {
    colors_html += passes_color_html(num, colors[i])
  }
  // html template like it's 1999
  var html =
  '<div id="pass_'+num+'" class="row pass_widget" style="margin:0; margin-bottom:20px">'+
    '<label style="color:#666666">Pass '+num+'</label>'+
    '<form class="form-inline">'+
      '<div class="form-group">'+
        '<div class="input-group" style="margin-right:4px">'+
          '<div class="input-group-addon" style="width:10px">F</div>'+
          '<input type="text" class="form-control input-sm feedrate" style="width:50px;" value="'+feedrate+'" title="feedrate">'+
        '</div>'+
        '<div class="input-group" style="margin-right:4px">'+
          '<div class="input-group-addon" style="width:10px">%</div>'+
          '<input type="text" class="form-control input-sm intensity" style="width:44px" value="'+intensity+'" title="intensity 0-100%">'+
        '</div>'+
        '<div class="dropdown input-group">'+
          '<button class="btn btn-primary btn-sm dropdown-toggle" type="button" style="width:34px" '+
            'id="assign_btn_'+num+'" data-toggle="dropdown" aria-haspopup="true" aria-expanded="true" title="['+num+']">'+
            '<span class="glyphicon glyphicon-plus"></span>'+
          '</button>'+
          '<ul id="passdp_'+num+'" class="dropdown-menu dropdown-menu-right pass_color_dropdown" aria-labelledby="assign_btn_'+num+'">'+
            select_html+
          '</ul>'+
        '</div>'+
      '</div>'+
    '</form>'+
    '<div class="pass_colors">'+colors_html+'</div>'+
  '</div>'
  return html
}


function passes_add_widget() {
  var html =
  '<div id="pass_add_widget" class="row" style="margin:0; margin-bottom:20px">'+
    '<label style="color:#666666">More Passes</label>'+
    '<div>'+
      '<button class="btn btn-default btn-sm dropdown-toggle" type="button" style="width:34px" '+
        'id="pass_add_btn" data-toggle="dropdown" aria-haspopup="true" aria-expanded="true" title="[P]">'+
        '<span class="glyphicon glyphicon-plus"></span>'+
      '</button>'+
    '</div>'+
  '</div>'
  var pass_elem = $(html).appendTo('#job_passes')

  // bind pass_add_btn
  $('#pass_add_btn').click(function(e) {
    passes_add(1500, 100, [])
    return false
  })

  // hotkey
  Mousetrap.bind(['p'], function(e) {
      $('#pass_add_btn').trigger('click')
      return false;
  })
}


function passes_get_assignments() {
  var assignments = []
  $('#job_passes').children('.pass_widget').each(function(i) { // each pass
    var feedrate = parseFloat($(this).find("input.feedrate").val()).toFixed()
    var intensity = parseFloat($(this).find("input.intensity").val()).toFixed()
    assignments.push({"colors":[], "feedrate":feedrate, "intensity":intensity})
    $(this).children('div.pass_colors').children('div').filter(':visible').each(function(k) {
      var color = $(this).find('.colmem').text()
      assignments[i].colors.push(color)
      // console.log('assign '+color+' -> '+(i+1))
    })
  })
  return assignments
}


function passes_set_assignments(job) {
  // set passes in gui from lsa job dict
  // console.log(job)
  var not_set_flag = true
  if ("vector" in job) {
    if ("passes" in job.vector && "colors" in job.vector) {
      for (var i = 0; i < job.vector.passes.length; i++) {
        var pass = job.vector.passes[i]
        not_set_flag = false
        // convert path index to color
        var colors = []
        for (var ii = 0; ii < pass.paths.length; ii++) {
          var pathidx = pass.paths[ii]
          colors.push(job.vector.colors[pathidx])
        }
        passes_add(pass.feedrate, pass.intensity, colors)
      }
    }
  }
  if (not_set_flag) {
    passes_add(1500, 100, [])
    passes_add(1500, 100, [])
    passes_add(1500, 100, [])
  }
  passes_add_widget()
}


function passes_update_handler() {
  // called whenever passes wiget changes happen (color add/remove)
  // this event handler is debounced to minimize updates
  clearTimeout(window.lastPassesUpdateTimer)
  window.lastPassesUpdateTimer = setTimeout(function() {
    jobhandler.setPassesFromGUI()
    // length
    var length = (jobhandler.getActivePassesLength()/1000.0).toFixed(1)
    $('#job_info_length').html(' | '+length+'m')
    // bounds
    jobhandler.renderBounds()
    jobhandler.draw()
  }, 2000)
}
