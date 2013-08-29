



def _intersect_line2_line2(A, B):
  d = B.v.y * A.v.x - B.v.x * A.v.y
  if d == 0:
    return None

  dy = A.p.y - B.p.y
  dx = A.p.x - B.p.x
  ua = (B.v.x * dy - B.v.y * dx) / d
  if not A._u_in(ua):
    return None
  ub = (A.v.x * dy - A.v.y * dx) / d
  if not B._u_in(ub):
    return None

  return Point2(A.p.x + ua * A.v.x,
          A.p.y + ua * A.v.y)


function intersect_line_to_segment(Lp, Lv, Sp1, Sp2) {
  //Line defined by point Lp, vector Lv
  //LineSegment defined by point Sp1, vector Sp2

  Bv = [Sp2.x-Sp1.x, Sp2.y-Sp1.y]
  d = Bv.y * Lv.x - Bv.x * Lv.y
  if d == 0:
    return None

  dy = Lp.y - Bp.y
  dx = Lp.x - Bp.x
  ua = (Bv.x * dy - Bv.y * dx) / d
  // no range checking, assuming infinite line
  // if (!A._u_in(ua)) {
  //     return null
  // }
  ub = (Lv.x * dy - Lv.y * dx) / d
  if (!(ub >= 0.0 && ub <= 1.0)) {
    return null
  }

  return Point2(Lp.x + ua * Lv.x,
          Lp.y + ua * Lv.y)
}



function intersect_fill(paths, d_y, d_accel, d_decel) {
  // paths: list of paths with 2d points
  // d_y: spacing between raster lines
  // d_accel: horizontal offset of start point (of any raster line)
  // d_decel: horizontal offset of end point (of any raster line)
  // returns: List of raster lines. Each raster line contains 2d points.
  //          and "engraveTo" should be assigned for every odd point
  //          with the exception of the starting point

  // find vertical bounds
  var y_max = -9e9;
  var y_min = 9e9;
  for (var i=0; i < paths.length; i++) {
    var path = paths[i];
    for (var k=0; k < path.length; k++) {
      var y = path[k][1];
      if (y > y_max) { y_max = y; }
      if (y < y_min) { y_min = y; }
    }
  }

  var raster_lines = [];
  // loop throught y-levels of raster lines
  for (var Lp_y=y_min; Lp_y<=y_max; Lp_y+=d_y) {
    // intersect with path segments
    var rline = [[0,0]];  // holds intersection points, placeholder start
    for (var i=0; i < paths.length; i++) {
      var path = path[i];
      for (var k=1; k<path.length; k++) {
        var inter = intersect_line_to_segment([0.0,Lp_y], [0.0,1.0], path[k-1], path[k]);
        if (inter) {
          rline.push(inter);
        }
      }
    }
    if (rline.length > 1) {  //1 since we always have one placeholder
      if (rline.length % 2 == 0) {  // point num should always be even
        // add accel/decel points
        rline[0][0] -= d_accel;  // offset x
        rline.push([rline[rline.length-1][0]+d_decel,rline[rline.length-1][1]]);  // offset x
        // sort by x
        var rline_sorted = rline.sort(function(a,b) {return a[0] - b[0];});
        raster_lines.push(rline_sorted);
      } else {
        // odd number of points
        // something went wrong
      }
    }
  }

  return raster_lines;
}