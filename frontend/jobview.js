
var jobview_mm2px = 1.0

function jobview_resize() {
  var job_info_width = 200
  var win_width = $(window).width()
  var win_height = $(window).height()
  var nav_height = $('#main-navbar').outerHeight(true)
  var footer_height = $('#main-footer').outerHeight(true)
  var containter_height = win_height-nav_height-footer_height
  $("#main-container").height(containter_height)
  $("#job-canvas").width(win_width-job_info_width)
  $("#job-info").width(job_info_width)
  $("#job-info").height(containter_height)
  var width = $('#job-canvas').innerWidth()
  var height = $('#job-canvas').innerHeight()

  // calculate jobview_mm2px
  // used to scale mm geometry to be displayed on canvas
  if (appconfig_main !== undefined) {
    var wk_width = appconfig_main.workspace[0]
    var wk_height = appconfig_main.workspace[1]
    var aspect_workspace = wk_width/wk_height
    var aspect_canvas = width/height
    jobview_mm2px = width/wk_width  // default for same aspect
    var p_bound = new paper.Path()
    p_bound.fillColor = '#eeeeee'
    p_bound.closed = true
    if (aspect_canvas > aspect_workspace) {
      // canvas wider, fit by height
      jobview_mm2px = height/wk_height
      // indicate border, only on one side necessary
      var w_scaled = wk_width*jobview_mm2px
      p_bound.add([w_scaled,0],[width,0],[width,height],[w_scaled,height])
    } else if (aspect_workspace > aspect_canvas) {
      // canvas taller, fit by width
      var h_scaled = wk_height*jobview_mm2px
      p_bound.add([0,h_scaled],[width,h_scaled],[width,height],[0,height])
    } else {
      // excact fit
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

  // calc/set canvas size
  jobview_resize()
  // setup paper with job-canvas
  var canvas = document.getElementById('job-canvas')
  paper.setup(canvas)

  // paper.view.onResize = function(event) {
  //   setTimeout(function() {
  //     // var w_canvas = $('#job-canvas').innerWidth()
  //     // var h_canvas = $('#job-canvas').innerHeight()
  //     // var resize_scale = w_canvas/jobview_width
  //     // console.log(w_canvas)
  //     // console.log(jobview_width)
  //     // console.log(resize_scale)
  //     // if (resize_scale > 0.01 && resize_scale < 10) {
  //     //   jobview_width = w_canvas
  //     //   jobview_height = h_canvas

  //     //   for (var i=0; i<paper.project.layers.length; i++) {
  //     //     var layer = paper.project.layers[i]
  //     //     for (var j=0; j<layer.children.length; j++) {
  //     //       var child = layer.children[j]
  //     //       child.scale(resize_scale, child.bounds.topLeft)
  //     //     }
  //     //   }

  //     //   paper.view.draw()
  //     // }
  //   }, 300);
  // }

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

  tool_pass = new paper.Tool();
  tool_pass.onMouseDown = function(event) {
    console.log(paper.project.hitTest())
    paper.project.activeLayer.selected = false;
    if (event.item) {
      event.item.selected = true;
    }
  }

  // tool1.activate()
  // tool2.activate()
  tool_pass.activate()


  // some test paths
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

  paper.view.draw()

}