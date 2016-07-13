var jobview_width = 0
var jobview_height = 0
var jobview_mm2px = 1.0

var jobview_gridLayer = undefined
var jobview_boundsLayer = undefined
var jobview_seekLayer = undefined
var jobview_feedLayer = undefined
var jobview_headLayer = undefined

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
  jobview_boundsLayer.remove()
  jobview_boundsLayer = new paper.Layer()
  jobview_seekLayer.remove()
  jobview_seekLayer = new paper.Layer()
  jobview_feedLayer.remove()
  jobview_feedLayer = new paper.Layer()
  paper.view.draw()
  jobview_color_selected = undefined
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

  // feed/seek lines layer
  jobview_boundsLayer = new paper.Layer();
  jobview_feedLayer = paper.project.activeLayer
  jobview_seekLayer = new paper.Layer();
  jobview_feedLayer.activate()
  // bounds layer

  // tools
  var path;
  jobview_tselect_init()
  jobview_toffset_init()
  jobview_tmove_init()
  jobview_tjog_init()
  jobview_tselect.activate()


  // grid
  jobview_grid()

  // head
  jobview_head()

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
  jobview_toffset = new paper.Tool()
  jobview_toffset.onMouseDown = function(event) {
    var x = Math.ceil(event.point.x / jobview_mm2px)
    var y = Math.ceil(event.point.y / jobview_mm2px)
    console.log(x + ',' + y)
  }
  jobview_toffset.onMouseMove = function(event) {
    // Use the arcTo command to draw cloudy lines
    // path.arcTo(event.point)
  }
}

function jobview_tmove_init() {
  jobview_tmove = new paper.Tool()
  jobview_tmove.minDistance = 20
  jobview_tmove.onMouseDown = function(event) {
    path = new paper.Path()
    path.strokeColor = 'black'
    path.add(event.point)
  }
  jobview_tmove.onMouseDrag = function(event) {
    // Use the arcTo command to draw cloudy lines
    path.arcTo(event.point)
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

function jobview_head_move(pos) {
  jobview_headLayer.position = new paper.Point(pos[0]*jobview_scale, pos[1]*jobview_scale)
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
