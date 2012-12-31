
import math
import logging

"""
Optimizations of polylines (path) and sets of polylines (paths).

The format of a path is:
[[x1,y1],[x2,y2],...]

The format of paths are:
[path1, path2, ...] 

"""

log = logging.getLogger("svg_reader")


def join_segments(paths, epsilon2):
    """
    Join paths with congruent end/start points.

    This is Useful to optimize pseudo-polylines made from line segments.
    """
    join_count = 0
    nPaths = []
    for path in paths:
		if nPaths:
			lastpath = nPaths[-1:][0]
			endpoint = lastpath[-1:][0]
			d2 = (endpoint[0]-path[0][0])**2 + (endpoint[1]-path[0][1])**2
			if d2 < epsilon2:
				lastpath.extend(path[1:])
				join_count += 1
			else:
				nPaths.append(path)
		else:
			nPaths.append(path)
    # report pseudo-polyline joining operations
    if join_count > 100:
        log.info("joined many line segments: " + str(join_count))

    return nPaths



def simplify(path, tolerance2):
    """
    Douglas-Peucker polyline simplification.

    path ... [[x1,y1],[x2,y2],...] polyline
    tolerance2  ... approximation tolerance squared
    ===============================================
    Copyright 2002, softSurfer (www.softsurfer.com)
    This code may be freely used and modified for any purpose
    providing that this copyright notice is included with it.
    SoftSurfer makes no warranty for this code, and cannot be held
    liable for any real or imagined damage resulting from its use.
    Users of this code must verify correctness for their application.
    http://softsurfer.com/Archive/algorithm_0205/algorithm_0205.htm
    """
    def sum(u,v): return [u[0]+v[0], u[1]+v[1]]
    def diff(u,v): return [u[0]-v[0], u[1]-v[1]]
    def prod(u,v): return [u[0]*v[0], u[1]*v[1]]
    def dot(u,v): return u[0]*v[0] + u[1]*v[1]
    def norm2(v): return v[0]*v[0] + v[1]*v[1]
    def norm(v): return math.sqrt(norm2(v))
    def d2(u,v): return norm2(diff(u,v))
    def d(u,v): return norm(diff(u,v))
    
    def simplifyDP(tol2, v, j, k, mk):
        #  This is the Douglas-Peucker recursive simplification routine
        #  It just marks vertices that are part of the simplified polyline
        #  for approximating the polyline subchain v[j] to v[k].
        #  mk[] ... array of markers matching vertex array v[]
        if k <= j+1:  # there is nothing to simplify
            return
        # check for adequate approximation by segment S from v[j] to v[k]
        maxi = j           # index of vertex farthest from S
        maxd2 = 0          # distance squared of farthest vertex
        S = [v[j], v[k]]   # segment from v[j] to v[k]
        u = diff(S[1], S[0])    # segment direction vector
        cu = norm2(u)      # segment length squared
        # test each vertex v[i] for max distance from S
        # compute using the Feb 2001 Algorithm's dist_Point_to_Segment()
        # Note: this works in any dimension (2D, 3D, ...)
        w = None           # vector
        Pb = None          # point, base of perpendicular from v[i] to S
        b = None
        cw = None
        dv2 = None         # dv2 = distance v[i] to S squared
        for i in xrange(j+1, k):
            # compute distance squared
            w = diff(v[i], S[0])
            cw = dot(w,u)
            if cw <= 0:
                dv2 = d2(v[i], S[0])
            elif cu <= cw:
                dv2 = d2(v[i], S[1])
            else:
                b = cw / cu
                Pb = [S[0][0]+b*u[0], S[0][1]+b*u[1]]
                dv2 = d2(v[i], Pb)
            # test with current max distance squared
            if dv2 <= maxd2:
                continue
            # v[i] is a new max vertex
            maxi = i
            maxd2 = dv2
        if maxd2 > tol2:       # error is worse than the tolerance
            # split the polyline at the farthest vertex from S
            mk[maxi] = 1       # mark v[maxi] for the simplified polyline
            # recursively simplify the two subpolylines at v[maxi]
            simplifyDP(tol2, v, j, maxi, mk)  # polyline v[j] to v[maxi]
            simplifyDP(tol2, v, maxi, k, mk)  # polyline v[maxi] to v[k]
        # else the approximation is OK, so ignore intermediate vertices
        return
    
    n = len(path)
    if n == 0:
        return []
    sPath = []
    tPath = []                   # vertex buffer, points

    # STAGE 1.  Vertex Reduction within tolerance of prior vertex cluster
    tPath.append(path[0])        # start at the beginning
    k = 1
    pv = 0
    for i in xrange(1, n):
        if d2(path[i], path[pv]) < tolerance2:
            continue
        tPath.append(path[i])
        k += 1
        pv = i
    if pv < n-1:
        tPath.append(path[n-1])  # finish at the end
        k += 1

    # STAGE 2.  Douglas-Peucker polyline simplification
    mk = [None for i in xrange(k)]    # marker buffer, ints
    mk[0] = mk[k-1] = 1;              # mark the first and last vertices
    simplifyDP(tolerance2, tPath, 0, k-1, mk)

    # copy marked vertices to the output simplified polyline
    for i in xrange(k):
        if mk[i]:
            sPath.append(tPath[i])
    return sPath



def simplify_all(paths, tolerance2):
    totalverts = 0
    optiverts = 0
    for u in xrange(len(paths)):
        totalverts += len(paths[u])
        paths[u] = simplify(paths[u], tolerance2)
    optiverts += len(paths[u])
    # report polyline optimizations    
    difflength = totalverts - optiverts
    diffpct = (100*difflength/totalverts)
    if diffpct > 10:  # if diff more than 10%
        log.info("polylines optimized by " + str(int(diffpct)) + '%')



def sort_by_seektime(paths, start=[0.0, 0.0]):
    # sort paths to optimize seek distances in between
    endpoint = start
    for i in xrange(len(paths)):
        if i > 0:
            endpoint = paths[i-1][len(paths[i-1])-1]
        # search the rest of array for closest path start point
        d2_hash = {}  # distance2:index pairs
        for j in xrange(i,len(paths)):
            startpoint = paths[j][0]
            d2_hash[ (endpoint[0]-startpoint[0])**2 + (endpoint[1]-startpoint[1])**2 ] = j
        d2min = 9999999999999999.9
        d2minIndex = None
        for d2 in d2_hash:
            if d2 < d2min:
                d2min = d2 
                d2minIndex = d2_hash[d2]
        # make closest subpath next item
        if d2minIndex != i:
            tempItem = paths[i]
            paths[i] = paths[d2minIndex]
            paths[d2minIndex] = tempItem

