
var tools_tselect = undefined
var tools_toffset = undefined
var tools_tmove = undefined
var tools_tjog = undefined


function tools_tselect_init() {
  tools_tselect = new paper.Tool()
  tools_tselect.onMouseDown = function(event) {
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


function tools_toffset_init() {
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
  tools_toffset = new paper.Tool()
  tools_toffset.onMouseDown = function(event) {
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
  tools_toffset.onMouseMove = function(event) {
    if (event.point.x <= jobview_width && event.point.y <= jobview_height) {
      jobview_offsetLayer.visible = true
      jobview_offsetLayer.position = event.point
    }
  }
}


function tools_tmove_init() {
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
  // create tool
  tools_tmove = new paper.Tool()
  tools_tmove.onMouseDown = function(event) {
    var x_mm = Math.ceil(event.point.x/jobview_mm2px-status_cache.offset[0])
    var y_mm = Math.ceil(event.point.y/jobview_mm2px-status_cache.offset[1])
    request_absolute_move(x_mm, y_mm, 0, app_config_main.seekrate, "Moving to "+x_mm+","+y_mm)
    $('#select_btn').trigger('click')
    // setTimeout(function(){
    //   jobview_moveLayer.visible = false
    // },1000)
  }
  tools_tmove.onMouseMove = function(event) {
    if (event.point.x <= jobview_width && event.point.y <= jobview_height) {
      jobview_moveLayer.visible = true
      jobview_moveLayer.position = event.point
    }
  }
}


function tools_tjog_init() {
  // create layer
  jobview_jogLayer = new paper.Layer()
  jobview_jogLayer.transformContent = false
  jobview_jogLayer.pivot = new paper.Point(0,0)
  jobview_jogLayer.visible = false
  jobview_jogLayer.activate()
  // greate group
  var group = new paper.Group()
  var ref = undefined
  // up widget
  // var rec_up = new paper.Path.Rectangle(
  //   new paper.Point(jobview_width*0.3,0),
  //   new paper.Point(jobview_width*0.7,jobview_height*0.3))
  // group.addChild(rec_up)
  var arrow_up = new paper.Path()
  ref = [0.5*jobview_width,jobview_height*0.1]
  arrow_up.add(
    ref,
    [ref[0]-30,ref[1]+30],
    [ref[0]-15,ref[1]+30],
    [ref[0]-15,ref[1]+40],
    [ref[0]+15,ref[1]+40],
    [ref[0]+15,ref[1]+30],
    [ref[0]+30,ref[1]+30],
    ref)
  group.addChild(arrow_up)
  var arrow_up_lg = new paper.Path()
  ref = [0.5*jobview_width,jobview_height*0.1+50]
  arrow_up_lg.add(
    ref,
    [ref[0]-60,ref[1]+60],
    [ref[0]-30,ref[1]+60],
    [ref[0]-30,ref[1]+80],
    [ref[0]+30,ref[1]+80],
    [ref[0]+30,ref[1]+60],
    [ref[0]+60,ref[1]+60],
    ref)
  group.addChild(arrow_up_lg)
  // down widget
  // var rec_down = new paper.Path.Rectangle(
  //   new paper.Point(jobview_width*0.3,jobview_height*0.7),
  //   new paper.Point(jobview_width*0.7,jobview_height))
  // group.addChild(rec_down)
  var arrow_down = new paper.Path()
  ref = [0.5*jobview_width,jobview_height*0.9]
  arrow_down.add(
    ref,
    [ref[0]-30,ref[1]-30],
    [ref[0]-15,ref[1]-30],
    [ref[0]-15,ref[1]-40],
    [ref[0]+15,ref[1]-40],
    [ref[0]+15,ref[1]-30],
    [ref[0]+30,ref[1]-30],
    ref)
  group.addChild(arrow_down)
  var arrow_down_lg = new paper.Path()
  ref = [0.5*jobview_width,jobview_height*0.9-50]
  arrow_down_lg.add(
    ref,
    [ref[0]-60,ref[1]-60],
    [ref[0]-30,ref[1]-60],
    [ref[0]-30,ref[1]-80],
    [ref[0]+30,ref[1]-80],
    [ref[0]+30,ref[1]-60],
    [ref[0]+60,ref[1]-60],
    ref)
  group.addChild(arrow_down_lg)
  // left widget
  // var rec_left = new paper.Path.Rectangle(
  //   new paper.Point(0,jobview_height*0.3),
  //   new paper.Point(jobview_width*0.3,jobview_height*0.7))
  // group.addChild(rec_left)
  var arrow_left = new paper.Path()
  ref = [0.1*jobview_width,0.5*jobview_height]
  arrow_left.add(
    ref,
    [ref[0]+30,ref[1]-30],
    [ref[0]+30,ref[1]-15],
    [ref[0]+40,ref[1]-15],
    [ref[0]+40,ref[1]+15],
    [ref[0]+30,ref[1]+15],
    [ref[0]+30,ref[1]+30],
    ref)
  group.addChild(arrow_left)
  var arrow_left_lg = new paper.Path()
  ref = [0.1*jobview_width+50,0.5*jobview_height]
  arrow_left_lg.add(
    ref,
    [ref[0]+60,ref[1]-60],
    [ref[0]+60,ref[1]-30],
    [ref[0]+80,ref[1]-30],
    [ref[0]+80,ref[1]+30],
    [ref[0]+60,ref[1]+30],
    [ref[0]+60,ref[1]+60],
    ref)
  group.addChild(arrow_left_lg)
  // right widget
  // var rec_right = new paper.Path.Rectangle(
  //   new paper.Point(jobview_width*0.7,jobview_height*0.3),
  //   new paper.Point(jobview_width,jobview_height*0.7))
  // group.addChild(rec_right)
  var arrow_right = new paper.Path()
  ref = [0.9*jobview_width,0.5*jobview_height]
  arrow_right.add(
    ref,
    [ref[0]-30,ref[1]-30],
    [ref[0]-30,ref[1]-15],
    [ref[0]-40,ref[1]-15],
    [ref[0]-40,ref[1]+15],
    [ref[0]-30,ref[1]+15],
    [ref[0]-30,ref[1]+30],
    ref)
  group.addChild(arrow_right)
  var arrow_right_lg = new paper.Path()
  ref = [0.9*jobview_width-50,0.5*jobview_height]
  arrow_right_lg.add(
    ref,
    [ref[0]-60,ref[1]-60],
    [ref[0]-60,ref[1]-30],
    [ref[0]-80,ref[1]-30],
    [ref[0]-80,ref[1]+30],
    [ref[0]-60,ref[1]+30],
    [ref[0]-60,ref[1]+60],
    ref)
  group.addChild(arrow_right_lg)
  // properties
  group.fillColor = '#000000'
  arrow_up.opacity = 0.7
  arrow_up_lg.opacity = 0.7
  arrow_down.opacity = 0.7
  arrow_down_lg.opacity = 0.7
  arrow_left.opacity = 0.7
  arrow_left_lg.opacity = 0.7
  arrow_right.opacity = 0.7
  arrow_right_lg.opacity = 0.7
  // create tool
  tools_tjog = new paper.Tool()
  tools_tjog.onMouseDown = function(event) {
    var hit = jobview_jogLayer.hitTest(event.point)
    if (hit) {
      if (hit.item === arrow_up) {
        request_relative_move(0, -10, 0, app_config_main.seekrate, "jogging up 10mm")
      } else if (hit.item === arrow_up_lg) {
        request_relative_move(0, -50, 0, app_config_main.seekrate, "jogging up 50mm")
      } else if (hit.item === arrow_down) {
        request_relative_move(0, 10, 0, app_config_main.seekrate, "jogging down 10mm")
      } else if (hit.item === arrow_down_lg) {
        request_relative_move(0, 50, 0, app_config_main.seekrate, "jogging down 50mm")
      } else if (hit.item === arrow_left) {
        request_relative_move(-10, 0, 0, app_config_main.seekrate, "jogging left 10mm")
      } else if (hit.item === arrow_left_lg) {
        request_relative_move(-50, 0, 0, app_config_main.seekrate, "jogging left 50mm")
      } else if (hit.item === arrow_right) {
        request_relative_move(10, 0, 0, app_config_main.seekrate, "jogging right 10mm")
      } else if (hit.item === arrow_right_lg) {
        request_relative_move(50, 0, 0, app_config_main.seekrate, "jogging right 50mm")
      }
    }
  }
  tools_tjog.onMouseMove = function(event) {
    // if (event.point.x <= jobview_width && event.point.y <= jobview_height) {
    //   jobview_jogLayer.visible = true
    //   jobview_jogLayer.position = event.point
    // }
  }
}
