var jobview_width = 0
var jobview_height = 0
var jobview_mm2px = 1.0

var jobview_gridLayer = undefined
var jobview_feedLayer = undefined
var jobview_seekLayer = undefined

var nav_height_init = 0
var footer_height = 0
var info_width_init = 0

var jobview_width_last = 0
var jobview_height_last = 0

var jobview_color_selected = undefined


function jobview_clear(){
  jobview_seekLayer.remove()
  jobview_seekLayer = new paper.Layer()
  jobview_feedLayer.remove()
  jobview_feedLayer = new paper.Layer()
  paper.view.draw()
  jobview_color_selected = undefined
}


function jobview_resize() {
  var win_width = $(window).innerWidth()
  var win_height = $(window).innerHeight()
  var canvas_width = win_width-info_width_init
  var canvas_height = win_height-nav_height_init-footer_height_init
  // var containter_height = win_height-nav_height_init-footer_height_init
  $("#main_container").height(canvas_height)
  $("#job_canvas").width(win_width-info_width_init)
  // $("#info_panel").width(job_info_min_width)
  $("#info_panel").height(canvas_height)
  // jobview_width = $('#job_canvas').innerWidth()
  // jobview_height = $('#job_canvas').innerHeight()

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
      $("#job_canvas").width(Math.floor(wk_width*jobview_mm2px))
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
  setTimeout(function() {
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
  }, 600);
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

  // seek lines layer
  jobview_feedLayer = paper.project.activeLayer
  jobview_seekLayer = new paper.Layer();
  jobview_feedLayer.activate()

  // tools
  var tool1, tool2, tool_pass;
  // Create two drawing tools.
  // tool1 will draw straight lines,
  // tool2 will draw clouds.

  // Both share the mouseDown event:
  var path;
  function onMouseDown(event) {
    path = new paper.Path();
    path.strokeColor = 'black';
    path.add(event.point);
  }

  tool1 = new paper.Tool();
  tool1.onMouseDown = onMouseDown;

  tool1.onMouseDrag = function(event) {
    path.add(event.point);
  }

  tool2 = new paper.Tool();
  tool2.minDistance = 20;
  tool2.onMouseDown = onMouseDown;

  tool2.onMouseDrag = function(event) {
    // Use the arcTo command to draw cloudy lines
    path.arcTo(event.point);
  }

  // Pass Tool
  tool_pass = new paper.Tool();
  tool_pass.onMouseDown = function(event) {
    // console.log(paper.project.hitTest())
    // paper.project.activeLayer.selected = false
    // if (event.item) {
    //   event.item.selected = true
    // }
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

  // tool1.activate()
  // tool2.activate()
  tool_pass.activate()


  // grid
  jobview_grid()
  // // some test paths
  // jobview_testpath()
  // commit
  paper.view.draw()
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
