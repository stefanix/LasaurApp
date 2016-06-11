

function passes_clear() {
  $('#job_passes').html("")
}

function passes_add(feedrate, intensity, colors_assigned) {
  // multiple = typeof multiple !== 'undefined' ? multiple : 1  // default to 1
  var colors = jobhandler.getAllColors()
  var num_passes_already = $('#job_passes').children().length
  var num = num_passes_already + 1
  var html = passes_pass_html(num, feedrate, intensity, colors)
  var pass_elem = $(html).appendTo('#job_passes')

  // bind all color add buttons within dropdown
  $('.color_add_btn_'+num).click(function(e) {
    // $(this).parentsUntil().toggle();
    // $('#pass_'+num+' .pass_colselect').toggle()
    var color = $(this).children('span').text()
    // passes_add_colors(num, [color])
    // $(this).parentsUntil('ul.pass_color_dropdown').toggle()
    $('#passsel_'+num+'_'+color.slice(1)).hide()
    $('#pass_'+num+'_'+color.slice(1)).show(300)
    $('#passdp_'+num).dropdown("toggle");
    return false
  })

  // bind all color remove buttons
  $('.color_remove_btn_'+num).click(function(e) {
    var color = $(this).children('span.colmem').text()
    $('#passsel_'+num+'_'+color.slice(1)).show(0)
    $('#pass_'+num+'_'+color.slice(1)).hide(300)
    return false
  })
}


// function passes_add_colors(passnum, colors) {
//   for (var i = 0; i < colors.length; i++) {
//     var html = passes_color_html(colors[i])
//     $(html).appendTo('#pass_'+passnum+' .pass_colors')
//   }
// }


function passes_color_html(num, color) {
  var html =
  '<div id="pass_'+num+'_'+color.slice(1)+'" class="btn-group pull-left" style="margin-top:0.5em; display:none">'+
    '<button id="color_btn" class="btn btn-default btn-sm" type="submit" style="width:175px; background-color:'+color+'">'+
      '<span class="glyphicon glyphicon-eye-open"></span>'+
    '</button>'+
    '<button class="btn btn-default btn-sm color_remove_btn_'+num+'" type="submit" style="width:34px">'+
      '<span class="glyphicon glyphicon-remove"></span>'+
      '<span style="display:none" class="colmem">'+color+'</span>'+
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
  '<div id="pass_'+num+'" style="margin-bottom:20px">'+
    '<label>Pass '+num+'</label>'+
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
            'id="assign_btn_'+num+'" data-toggle="dropdown" aria-haspopup="true" aria-expanded="true">'+
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
