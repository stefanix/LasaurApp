
// module to handle job data


// {
//       "vector":                          # optional
//       {
//           "passes":
//           [
//               {
//                   "paths": [0],          # paths by index
//                   "relative": True,      # optional, default: False
//                   "seekrate": 6000,      # optional, rate to first vertex
//                   "feedrate": 2000,      # optional, rate to other verteces
//                   "intensity": 100,      # optional, default: 0 (in percent)
//                   "pierce_time": 0,      # optional, default: 0
//                   "air_assist": "pass",  # optional (feed, pass, off), default: pass
//                   "aux1_assist": "off",  # optional (feed, pass, off), default: off
//               }
//           ],
//           "paths":
//           [                              # list of paths
//               [                          # list of polylines
//                   [                      # list of verteces
//                       [0,-10, 0],        # list of coords
//                   ],
//               ],
//           ],
//           "colors": ["#FF0000"],         # color is matched to path by index
//           "noreturn": True,              # do not return to origin, default: False
//           "optimized": 0.08              # optional, tolerance to which it was optimized, default: 0 (not optimized)
//       }
//       "raster":                          # optional
//       {
//           "passes":
//           [
//               {
//                   "images": [0]
//                   "seekrate": 6000,      # optional
//                   "feedrate": 3000,
//                   "intensity": 100,
//                   "air_assist": "pass",  # optional (feed, pass, off), default: pass
//                   "aux1_assist": "off",  # optional (feed, pass, off), default: off
//               },
//           ]
//           "images":
//           [
//               {
//                   "pos": (100,50),          # pos in mm
//                   "size": (300,200),        # size in mm
//                   "data": <data in base64>
//               }
//           ]
//       }
//   }



JobHandler = {

  vector : {},
  raster : {},
  raster_base64 : {},
  stats : {},
  name : "",

  clear : function() {
    this.vector = {}
    this.raster = {}
    this.raster_base64 = {}
    this.stats = {}
    name = ""
  },

  isEmpty : function() {
    return (Object.keys(this.vector).length == 0 &&
            Object.keys(this.raster).length == 0)
  },




  // readers //////////////////////////////////

  set : function(job, name, optimize) {
    this.clear();

    this.name = name
    $('title').html("LasaurApp - " + name)

    if ('vector' in job) {
      this.vector = job.vector
      if (optimize) {
        this.segmentizeLongLines();
      }
    }

    if ('raster' in job) {
      if ('images' in job.raster) {
        this.raster = job.raster
        this.raster_base64 = job.raster
        // convert base64 to Image object
        for (var i=0; i<this.raster.images.length; i++) {
          var image = this.raster.images[i]
          var image_base64 = this.raster_base64.images[i]
          image.data = new Image()
          image.data.src = image_base64.data
          // scale to have one pixel match raster_size (beam width for raster)
          image.data.width = Math.round(image.size[0]/appconfig_main.raster_size);
          image.data.height = Math.round(image.size[1]/appconfig_main.raster_size);
        }
      }
    }

    // stats
    if ('stats' in job) {
      this.stats = job['stats']
    } else {
      this.calculateBasicStats()
    }
  },



  // writers //////////////////////////////////

  get : function() {
    return {'vector':this.vector, 'raster':this.raster_base64, 'stats':this.stat}
  },

  getJson : function() {
    return JSON.stringify(this.get());
  },




  // rendering //////////////////////////////////

  draw : function (canvas, scale, exclude_colors, exclude_rasters) {
    // draw rasters and paths
    // exclude_colors, exclude_rasters is optional
    canvas.background('#ffffff');
    canvas.noFill();
    var x_prev = 0;
    var y_prev = 0;
    // rasters
    if (exclude_rasters === undefined || exclude_rasters !== true) {
      for (var k=0; k<this.rasters.length; k++) {
        var raster = this.rasters[k];

        var x1 = raster.pos[0]*scale;
        var y1 = raster.pos[1]*scale;
        var width = raster.size_mm[0]*scale;
        var height = raster.size_mm[1]*scale;
        var image = raster.image;
        var pixwidth = image.width;
        var pixheight = image.height;
        var offset = appconfig_main.raster_offset;

        // var ppmmX = pixwidth / width;
        // var ppmmY = pixheight / height;

        // canvas.stroke('#aaaaaa');
        // canvas.line(x_prev, y_prev, x1-offset, y);
        // for (var y = y1; y < y1 + height; y++) {
        //   var line = Math.round(ppmmY * (y-y1)) * pixwidth;
        //   for (var x=x1; x < x1 + width; x++) {
        //     var pixel = Math.round(line + (x - x1) * ppmmX);
        //     // convert pixel value from extended ascii to hex: [128,255] -> [0-ff]
        //     // hexpx = ((image[pixel].charCodeAt()-128)*2).toString(16)

        //     // convert pixel value from extended ascii to hex: [33,118] -> [0-ff]
        //     hexpx = ((image[pixel].charCodeAt()-33)*3).toString(16)
        //     canvas.stroke('#'+hexpx+hexpx+hexpx);
        //     canvas.line(x, y, x+1, y);
        //   }
        //   canvas.stroke('#aaaaaa');
        //   canvas.line(x1 + width, y, x1 + width + offset, y);
        //   canvas.line(x1 - offset, y, x1, y);
        // }

        canvas.ctx.drawImage(image, x1, y1, width, height);

        x_prev = x1 + width + offset;
        y_prev = y1 + height;
      }
    }
    // paths
    for (var color in this.paths_by_color) {
      if (exclude_colors === undefined || !(color in exclude_colors)) {
        var paths = this.paths_by_color[color];
        for (var k=0; k<paths.length; k++) {
          var path = paths[k];
          if (path.length > 0) {
            var x = path[0][0]*scale;
            var y = path[0][1]*scale;
            canvas.stroke('#aaaaaa');
            canvas.line(x_prev, y_prev, x, y);
            x_prev = x;
            y_prev = y;
            canvas.stroke(color);
            for (vertex=1; vertex<path.length; vertex++) {
              var x = path[vertex][0]*scale;
              var y = path[vertex][1]*scale;
              canvas.line(x_prev, y_prev, x, y);
              x_prev = x;
              y_prev = y;
            }
          }
        }
      }
    }
  },

  draw_bboxes : function (canvas, scale) {
    // draw with bboxes by color
    // only include colors that are in passe
    var bbox_combined = [Infinity, Infinity, 0, 0];

    function drawbb(stats, obj) {
      var xmin = stats['bbox'][0]*scale;
      var ymin = stats['bbox'][1]*scale;
      var xmax = stats['bbox'][2]*scale;
      var ymax = stats['bbox'][3]*scale;
      canvas.stroke('#dddddd');
      canvas.line(xmin,ymin,xmin,ymax);
      canvas.line(xmin,ymax,xmax,ymax);
      canvas.line(xmax,ymax,xmax,ymin);
      canvas.line(xmax,ymin,xmin,ymin);
      obj.bboxExpand(bbox_combined, xmin, ymin);
      obj.bboxExpand(bbox_combined, xmax, ymax);
    }

    // rasters
    if ('rasters' in this.stats) {
      drawbb(this.stats['rasters'], this);
    }
    // for all job colors
    for (var color in this.getPassesColors()) {
      drawbb(this.stats[color], this);
    }
    // draw global bbox
    xmin = bbox_combined[0];
    ymin = bbox_combined[1];
    xmax = bbox_combined[2];
    ymax = bbox_combined[3];
    canvas.stroke('#dddddd');
    canvas.line(xmin,ymin,xmin,ymax);
    canvas.line(xmin,ymax,xmax,ymax);
    canvas.line(xmax,ymax,xmax,ymin);
    canvas.line(xmax,ymin,xmin,ymin);
  },



  // passes and colors //////////////////////////

  // setPassesFromLasertags : function(lasertags) {
  //   // lasertags come in this format
  //   // (pass_num, feedrate, units, intensity, units, color1, color2, ..., color6)
  //   // [(12, 2550, '', 100, '%', ':#fff000', ':#ababab', ':#ccc999', '', '', ''), ...]
  //   this.passes = [];
  //   for (var i=0; i<lasertags.length; i++) {
  //     var vals = lasertags[i];
  //     if (vals.length == 11) {
  //       var pass = vals[0];
  //       var feedrate = vals[1];
  //       var intensity = vals[3];
  //       if (typeof(pass) === 'number' && pass > 0) {
  //         //make sure to have enough pass widgets
  //         var passes_to_create = pass - this.passes.length
  //         if (passes_to_create >= 1) {
  //           for (var k=0; k<passes_to_create; k++) {
  //             this.passes.push({'colors':[], 'feedrate':1200, 'intensity':10})
  //           }
  //         }
  //         pass = pass-1;  // convert to zero-indexed
  //         // feedrate
  //         if (feedrate != '' && typeof(feedrate) === 'number') {
  //           this.passes[pass]['feedrate'] = feedrate;
  //         }
  //         // intensity
  //         if (intensity != '' && typeof(intensity) === 'number') {
  //           this.passes[pass]['intensity'] = intensity;
  //         }
  //         // colors
  //         for (var ii=5; ii<vals.length; ii++) {
  //           var col = vals[ii];
  //           if (col.slice(0,1) == '#') {
  //             this.passes[pass]['colors'].push(col);
  //           }
  //         }
  //       } else {
  //         $().uxmessage('error', "invalid lasertag (pass number)");
  //       }
  //     } else {
  //       $().uxmessage('error', "invalid lasertag (num of args)");
  //     }
  //   }
  // },

  // getPasses : function() {
  //   return this.passes;
  // },
  //
  // hasPasses : function() {
  //   if (this.passes.length > 0) {return true}
  //   else {return false}
  // },
  //
  // clearPasses : function() {
  //   this.passes = [];
  // },
  //
  // getPassesColors : function() {
  //   var all_colors = {};
  //   for (var i=0; i<this.passes.length; i++) {
  //     var mapping = this.passes[i];
  //     var colors = mapping['colors'];
  //     for (var c=0; c<colors.length; c++) {
  //       var color = colors[c];
  //       all_colors[color] = true;
  //     }
  //   }
  //   return all_colors;
  // },
  //
  // getAllColors : function() {
  //   // return list of colors
  //   return Object.keys(this.paths_by_color);
  // },
  //
  // getColorOrder : function() {
  //     var color_order = {};
  //     var color_count = 0;
  //     for (var color in this.paths_by_color) {
  //       color_order[color] = color_count;
  //       color_count++;
  //     }
  //     return color_order
  // },



  // stats //////////////////////////////////////

  calculateBasicStats : function() {
    // calculate bounding boxes and path lengths
    // for each path, image, and also for '_all_'
    // bbox and length only account for feed lines
    // saves results in this.stats like so:
    // {'_all_':{'bbox':[xmin,ymin,xmax,ymax], 'length':numeral},
    //  'paths':[{'bbox':[xmin,ymin,xmax,ymax], 'length':numeral}, ...],
    //  'images':[{'bbox':[xmin,ymin,xmax,ymax], 'length':numeral}, ...] }

    var length_all = 0
    var bbox_all = [Infinity, Infinity, -Infinity, -Infinity]

    // paths
    if (this.vector.paths.length) > 0 {
      this.stats.paths = []
      for (var k=0; k<this.vector.paths.length; k++) {
        var x_prev = 0
        var y_prev = 0
        var path_length = 0
        var path_bbox = [Infinity, Infinity, -Infinity, -Infinity]
        var path = this.vector.paths[k]
        if (path.length > 1) {
          var x = path[0][0]
          var y = path[0][1]
          this.bboxExpand(path_bbox, x, y)
          x_prev = x
          y_prev = y
          for (vertex=1; vertex<path.length; vertex++) {
            var x = path[vertex][0]
            var y = path[vertex][1]
            path_length +=
              Math.sqrt((x-x_prev)*(x-x_prev)+(y-y_prev)*(y-y_prev))
            this.bboxExpand(path_bbox, x, y)
            x_prev = x
            y_prev = y
          }
        }
        this.stats.paths.push({'bbox':path_bbox, 'length':path_length})
        length_all += path_length
        this.bboxExpand(bbox_all, path_bbox[0], path_bbox[1])
        this.bboxExpand(bbox_all, path_bbox[2], path_bbox[3])
      }
    }

    // images
    if (this.raster.images.length > 0) {
      this.stats.images = []
      for (var k=0; k<this.raster.images.length; k++) {
        var image = this.raster.images[k]
        var image_length = (2*appconfig_main.raster_offset + image.size[0])
                         * Math.floor(image.size[1]/appconfig_main.raster_kerf)
        var image_bbox = [image.pos[0] - appconfig_main.raster_offset,
                          image.pos[1]),
                          image.pos[0] + image.size[0] + appconfig_main.raster_offset,
                          image.pos[1] + image.size[1]
                         ]
        this.stats.images.push({'bbox':path_bbox, 'length':path_length})
        length_all += image_length
        this.bboxExpand(bbox_all, image_bbox[0], image_bbox[1])
        this.bboxExpand(bbox_all, image_bbox[2], image_bbox[3])
      }
    }

    // store in object var
    this.stats['_all_'] = {
      'bbox':bbox_all,
      'length':length_all
    }
  },


  bboxExpand : function(bbox, x, y) {
    if (x < bbox[0]) {bbox[0] = x;}
    else if (x > bbox[2]) {bbox[2] = x;}
    if (y < bbox[1]) {bbox[1] = y;}
    else if (y > bbox[3]) {bbox[3] = y;}
  },

  getJobPathLength : function() {
    var total_length = 0;
    for (var k=0; k<this.vector.passes.length; k++) {
      var

    }

    for (var color in this.getPassesColors()) {
      stat = this.stats[color];
      total_length += stat['length'];
    }
    return total_length;
  },

  getJobBbox : function() {
    var total_bbox = [Infinity, Infinity, 0, 0];
    for (var color in this.getPassesColors()) {
      stat = this.stats[color];
      this.bboxExpand(total_bbox, stat['bbox'][0], stat['bbox'][1]);
      this.bboxExpand(total_bbox, stat['bbox'][2], stat['bbox'][3]);
    }
    return total_bbox;
  },


  // path optimizations /////////////////////////

  segmentizeLongLines : function() {
    // TODO: make this also work 3D
    var x_prev = 0;
    var y_prev = 0;
    var d2 = 0;
    var length_limit = appconfig_main.max_segment_length;
    var length_limit2 = length_limit*length_limit;

    var lerp = function(x0, y0, x1, y1, t) {
      return [x0*(1-t)+x1*t, y0*(1-t)+y1*t];
    }

    var paths = this.vector.paths;
    for (var k=0; k<paths.length; k++) {
      var path = paths[k];
      if (path.length > 1) {
        var new_path = [];
        var copy_from = 0;
        var x = path[0][0];
        var y = path[0][1];
        // ignore seek lines for now
        x_prev = x;
        y_prev = y;
        for (vertex=1; vertex<path.length; vertex++) {
          var x = path[vertex][0];
          var y = path[vertex][1];
          d2 = (x-x_prev)*(x-x_prev) + (y-y_prev)*(y-y_prev);
          // check length for each feed line
          if (d2 > length_limit2) {
            // copy previous verts
            for (var n=copy_from; n<vertex; n++) {
              new_path.push(path[n]);
            }
            // add lerp verts
            var t_step = 1/(Math.sqrt(d2)/length_limit);
            for(var t=t_step; t<0.99; t+=t_step) {
              new_path.push(lerp(x_prev, y_prev, x, y, t));
            }
            copy_from = vertex;
          }
          x_prev = x;
          y_prev = y;
        }
        if (new_path.length > 0) {
          // add any rest verts from path
          for (var p=copy_from; p<path.length; p++) {
            new_path.push(path[p]);
          }
          copy_from = 0;
          paths[k] = new_path;
        }
      }
    }

  },


}
