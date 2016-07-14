var jobview_width = 0
var jobview_height = 0
var jobview_mm2px = 1.0

var jobview_gridLayer = undefined
var jobview_boundsLayer = undefined
var jobview_seekLayer = undefined
var jobview_feedLayer = undefined
var jobview_headLayer = undefined
var jobview_offsetLayer = undefined
var jobview_moveLayer = undefined
var jobview_jogLayer = undefined

var nav_height_init = 0
var footer_height = 0
var info_width_init = 0

var jobview_width_last = 0
var jobview_height_last = 0

var jobview_color_selected = undefined

var jobview_scale = 1

// tools
var jobview_tselect = undefined
var jobview_toffset = undefined
var jobview_tmove = undefined
var jobview_tjog = undefined


function jobview_clear(){
  jobview_boundsLayer.removeChildren()
  jobview_seekLayer.removeChildren()
  jobview_feedLayer.removeChildren()
  paper.view.draw()
  jobview_color_selected = undefined
}


function jobview_reset_layer(layer) {
  if (layer) {
    layer.remove()
  }
  layer = new paper.Layer()
  layer.pivot = new paper.Point(0,0)
  var x = 0
  var y = 0
  if ('offset' in status_cache) {
    var x_mm = status_cache.offset[0]
    var y_mm = status_cache.offset[1]
    x = Math.floor(x_mm*jobview_mm2px)
    y = Math.floor(y_mm*jobview_mm2px)
  }
  console.log("status_cahce.offset: "+x_mm+","+y_mm)
  layer.position = new paper.Point(x,y)
  return layer
}


function jobview_calc_scale() {
  // figure out scale
  var w_workspace = app_config_main.workspace[0]
  var h_workspace = app_config_main.workspace[1]
  var aspect_workspace = w_workspace/h_workspace
  var w_canvas = $('#job_canvas').innerWidth()
  var h_canvas = $('#job_canvas').innerHeight()
  var aspect_canvas = w_canvas/h_canvas
  jobview_scale = w_canvas/w_workspace  // default for same aspect
  if (aspect_canvas > aspect_workspace) {
    // canvas wider, fit by height
    jobview_scale = h_canvas/h_workspace
  }
  // if (aspect_canvas > aspect_workspace) {
  //   // canvas wider, fit by height
  //   jobview_scale = h_canvas/h_workspace
  //   // indicate border, only on one side necessary
  //   var w_scaled = w_workspace*scale
  //   var p_bound = new paper.Path()
  //   p_bound.fillColor = '#eeeeee'
  //   p_bound.closed = true
  //   p_bound.add([w_scaled,0],[w_canvas,0],[w_canvas,h_canvas],[w_scaled,h_canvas])
  // } else if (aspect_workspace > aspect_canvas) {
  //   var h_scaled = h_workspace*scale
  //   var p_bound = new paper.Path()
  //   p_bound.fillColor = '#eeeeee'
  //   p_bound.closed = true
  //   p_bound.add([0,h_scaled],[w_canvas,h_scaled],[w_canvas,h_canvas],[0,h_canvas])
  // }
}


function jobview_resize() {
  var win_width = $(window).innerWidth()
  var win_height = $(window).innerHeight()
  var canvas_width = win_width-info_width_init
  var canvas_height = win_height-nav_height_init-footer_height_init
  // var containter_height = win_height-nav_height_init-footer_height_init
  $("#main_container").height(canvas_height)
  $("#canvas_container").width(win_width-info_width_init)
  // $("#info_panel").width(job_info_min_width)
  $("#info_panel").height(canvas_height)

  // calculate jobview_mm2px
  // used to scale mm geometry to be displayed on canvas
  if (app_config_main !== undefined) {
    var wk_width = app_config_main.workspace[0]
    var wk_height = app_config_main.workspace[1]
    var aspect_workspace = wk_width/wk_height
    var aspect_canvas = canvas_width/canvas_height
    jobview_mm2px = canvas_width/wk_width  // default for same aspect
    if (aspect_canvas > aspect_workspace) {
      // canvas wider, fit by height
      jobview_mm2px = canvas_height/wk_height
      // indicate border, only on one side necessary
      $("#canvas_container").width(Math.floor(wk_width*jobview_mm2px))
      $("#info_panel").width(win_width-Math.ceil(wk_width*jobview_mm2px))
    } else if (aspect_workspace > aspect_canvas) {
      // canvas taller, fit by width
      var h_scaled = Math.floor(wk_height*jobview_mm2px)
      $("#info_panel").width(info_width_init)
      $("#main_container").height(h_scaled)
      $("#info_panel").height(h_scaled)
      // $('#main_footer').height(win_height-nav_height_init-h_scaled)
    } else {
      // excact fit
    }
  }
  jobview_width = $('#job_canvas').innerWidth()
  jobview_height = $('#job_canvas').innerHeight()

  // resize content
  clearTimeout(window.lastResizeTimer)
  window.lastResizeTimer = setTimeout(function() {
    var resize_scale = jobview_width/jobview_width_last
    jobview_width_last = jobview_width
    jobview_height_last = jobview_height
    for (var i=0; i<paper.project.layers.length; i++) {
      var layer = paper.project.layers[i]
      for (var j=0; j<layer.children.length; j++) {
        var child = layer.children[j]
        child.scale(resize_scale, new paper.Point(0,0))
      }
    }
    paper.view.draw()
  }, 300)
}


function jobview_deselect_all() {
  for (var i=0; i<paper.project.layers.length; i++) {
    var layer = paper.project.layers[i]
    for (var j=0; j<layer.children.length; j++) {
      var child = layer.children[j]
      child.selected = false
    }
  }
}


///////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////

$(window).resize(function() {
  jobview_resize()
  jobview_calc_scale()
})


function jobview_ready() {
  // This function is called after appconfig received.

  nav_height_init = $('#main_navbar').outerHeight(true)
  footer_height_init = $('#main_footer').outerHeight(true)
  info_width_init = $("#info_panel").outerWidth(true)

  // calc/set canvas size
  jobview_resize()
  // store inital size
  jobview_width_last = jobview_width
  jobview_height_last = jobview_height
  // setup paper with job_canvas
  var canvas = document.getElementById('job_canvas')
  paper.setup(canvas)

  // grid
  jobview_grid()

  // layers
  jobview_seekLayer = new paper.Layer()
  jobview_seekLayer.pivot = new paper.Point(0,0)
  jobview_seekLayer.transformContent = false
  jobview_feedLayer = new paper.Layer()
  jobview_feedLayer.pivot = new paper.Point(0,0)  // xforms anchor
  jobview_feedLayer.transformContent = false      // make xforms more OpenGL-like
  jobview_boundsLayer = new paper.Layer()
  jobview_boundsLayer.pivot = new paper.Point(0,0)
  jobview_boundsLayer.transformContent = false

  // head
  // jobview_head()

  // tools
  jobview_tselect_init()
  jobview_toffset_init()
  jobview_tmove_init()
  jobview_tjog_init()
  jobview_tselect.activate()

  // // some test paths
  // jobview_testpath()
  // commit
  paper.view.draw()
}



function jobview_tselect_init() {
  jobview_tselect = new paper.Tool()
  jobview_tselect.onMouseDown = function(event) {
    var hitOptions = {
      // class: paper.Group,
      segments: true,
      stroke: true,
      fill: true,
      tolerance: 10
    }
    var hitResult = jobview_feedLayer.hitTest(event.point, hitOptions)
    if (hitResult) {
      jobview_deselect_all()
      path = hitResult.item
      path.parent.selected = !path.parent.selected
      // show info on this group
      jobview_color_selected = path.strokeColor.toCSS(true)

    } else {
      jobview_deselect_all()
      jobview_color_selected = undefined
    }
  }
}

function jobview_toffset_init() {
  // create layer
  jobview_offsetLayer = new paper.Layer()
  jobview_offsetLayer.transformContent = false
  jobview_offsetLayer.pivot = new paper.Point(0,0)
  jobview_offsetLayer.visible = false
  jobview_offsetLayer.activate()
  // greate group
  var group = new paper.Group()
  var rec1 = new paper.Path.Rectangle(new paper.Point(-9999,-9999), new paper.Point(9999,0))
  group.addChild(rec1)
  var rec2 = new paper.Path.Rectangle(new paper.Point(-9999,0), new paper.Point(0,9999))
  group.addChild(rec2)
  group.fillColor = '#000000'
  rec1.opacity = 0.5
  rec2.opacity = 0.5
  // create tool
  jobview_toffset = new paper.Tool()
  jobview_toffset.onMouseDown = function(event) {
    var x = Math.ceil(event.point.x/jobview_mm2px)
    var y = Math.ceil(event.point.y/jobview_mm2px)
    request_get({
      url:'/offset/'+x+'/'+y+'/0',
      success: function (data) {
        $().uxmessage('notice', "Offset set to: "+x+","+y)
      },
      error: function (data) {
        jobview_offsetLayer.position = new paper.Point(status_cache.offset[0],status_cache.offset[1])
      }
    })
    $("#offset_reset_btn").hide()
    $('#select_btn').trigger('click')
  }
  jobview_toffset.onMouseMove = function(event) {
    if (event.point.x <= jobview_width && event.point.y <= jobview_height) {
      jobview_offsetLayer.visible = true
      jobview_offsetLayer.position = event.point
    }
  }
}


function jobview_tmove_init() {
  // create layer
  jobview_moveLayer = new paper.Layer()
  jobview_moveLayer.transformContent = false
  jobview_moveLayer.pivot = new paper.Point(0,0)
  jobview_moveLayer.visible = false
  jobview_moveLayer.activate()

  // greate group
  var group = new paper.Group()
  var line1 = new paper.Path()
  line1.add([-9999,0],[9999,0])
  group.addChild(line1)

  var line2 = new paper.Path()
  line2.add([0,-9999],[0,9999])
  group.addChild(line2)

  var circ1 = new paper.Path.Circle([0,0],10)
  group.addChild(circ1)

  group.strokeColor = '#ff0000'


  jobview_tmove = new paper.Tool()
  jobview_tmove.onMouseDown = function(event) {
    var x = Math.ceil(event.point.x/jobview_mm2px-status_cache.offset[0])
    var y = Math.ceil(event.point.y/jobview_mm2px-status_cache.offset[1])
    request_get({
      url:'/move/'+x+'/'+y+'/0',
      success: function (data) {
        $().uxmessage('notice', "Move requested: "+x+","+y)
      }
    })
    $('#select_btn').trigger('click')
    // setTimeout(function(){
    //   jobview_moveLayer.visible = false
    // },1000)
  }
  jobview_tmove.onMouseMove = function(event) {
    if (event.point.x <= jobview_width && event.point.y <= jobview_height) {
      jobview_moveLayer.visible = true
      jobview_moveLayer.position = event.point
    }
  }
}


function jobview_tjog_init() {
  jobview_tjog = new paper.Tool()
  jobview_tjog.onMouseDown = function(event) {

  }
}


function jobview_grid(){
  if (!('workspace' in app_config_main) || !('grid_mm' in app_config_main) ) {
    return
  }
  var w_mm = app_config_main.workspace[0]
  var line_every_mm = app_config_main.grid_mm
  var every_px = (jobview_width*line_every_mm)/w_mm
  jobview_gridLayer = new paper.Layer()
  jobview_gridLayer.transformContent = false
  jobview_gridLayer.pivot = new paper.Point(0,0)
  jobview_gridLayer.activate()
  var grid_group = new paper.Group()
  // vertical
  var x = every_px
  while (x < jobview_width) {
    var line = new paper.Path()
    line.add([x,0], [x,jobview_height])
    grid_group.addChild(line);
    x += every_px
  }
  // horizontal
  var y = every_px
  while (y < jobview_height) {
    var line = new paper.Path()
    line.add([0,y], [jobview_width,y])
    grid_group.addChild(line);
    y += every_px
  }
  grid_group.strokeColor = '#dddddd';
}


function jobview_head(){
  jobview_headLayer = new paper.Layer()
  jobview_headLayer.transformContent = false
  jobview_headLayer.pivot = new paper.Point(0,0)
  jobview_headLayer.activate()
  var head_group = new paper.Group()

  var line1 = new paper.Path()
  line1.add([-10,0],[10,0])
  head_group.addChild(line1)

  var line2 = new paper.Path()
  line2.add([0,-10],[0,10])
  head_group.addChild(line2)

  var circ1 = new paper.Path.Circle([0,0],5)
  head_group.addChild(circ1)

  head_group.strokeColor = '#aa0000';
}

function jobview_head_move(pos, offset) {
  var x = (pos[0]+offset[0])*jobview_mm2px
  var y = (pos[1]+offset[1])*jobview_mm2px
  jobview_headLayer.position = new paper.Point(x, y)
  paper.view.draw()
}


function jobview_testpath(){
  jobview_feedLayer.activate()
  var width = jobview_width
  var height = jobview_height
  var path = new paper.Path()
  path.strokeColor = 'red'
  path.closed = true
  path.add([1,1],[width-1,1],[width-1,height-1],[1,height-1])

  var path2 = new paper.Path()
  path2.strokeColor = 'red'
  path2.closed = true
  path2.add([60,60],[width-60,60],[width-60,height-60],[60,height-60])
}
