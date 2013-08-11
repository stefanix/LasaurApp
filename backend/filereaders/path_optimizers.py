"""
Optimizations of polylines (path) and sets of polylines (paths).

The format of a path is:
[[x1,y1],[x2,y2],...]

The format of paths is:
[path1, path2, ...] 

This module is typically used by calling the optimize_all function.
It takes a boundarys object (paths by color dictionary) and does
all the optimizations in-place.
"""

__author__ = 'Stefan Hechenberger <stefan@nortd.com>'


import math
import logging

import kdtree

log = logging.getLogger("svg_reader")



def connect_segments(paths, epsilon2):
    """
    Optimizes continuity of paths.

    This function joins path segments if either the next start point
    or end point is congruent with the current end point. In case of
    an end point join it reverse the path segment.
    """
    join_count = 0
    reverse_count = 0
    nPaths = [paths[0]]  # prime with first path
    for i in xrange(1,len(paths)):
        path = paths[i]
        lastpath = nPaths[-1]
        point = lastpath[-1]
        startpoint = path[0]
        endpoint = path[-1]

        d2_start = (point[0]-startpoint[0])**2 + (point[1]-startpoint[1])**2
        if d2_start < epsilon2:
            lastpath.extend(path[1:])
            join_count += 1
            continue

        d2_end = (point[0]-endpoint[0])**2 + (point[1]-endpoint[1])**2
        if d2_end < epsilon2:
            path.reverse()
            lastpath.extend(path[1:])
            join_count += 1
            reverse_count += 1
            continue
        
        nPaths.append(path)

    # report if excessive reverts
    if reverse_count > 100:
        log.info("reverted many paths: " + str(reverse_count))
    # report if excessive joins
    if join_count > 100:
        log.info("joined many line segments: " + str(join_count))

    return nPaths


def d2(u,v): return (u[0]-v[0])**2 + (u[1]-v[1])**2


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
    # u = diff(S[1], S[0])    # segment direction vector
    u = [S[1][0]-S[0][0], S[1][1]-S[0][1]]  # segment direction vector
    # cu = norm2(u)      # segment length squared
    cu = u[0]**2 + u[1]**2  # segment length squared
    # test each vertex v[i] for max distance from S
    # compute using the Feb 2001 Algorithm's dist_Point_to_Segment()
    # Note: this works in any dimension (2D, 3D, ...)
    w = None           # vector
    Pb = None          # point, base of perpendicular from v[i] to S
    b = 0.0
    cw = 0.0
    dv2 = 0.0         # dv2 = distance v[i] to S squared
    for i in xrange(j+1, k):
        # compute distance squared
        # w = diff(v[i], S[0])
        w = [v[i][0]-S[0][0], v[i][1]-S[0][1]]  # diff
        # cw = dot(w,u)
        cw = w[0]*u[0] + w[1]*u[1]  # dot product
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



def sort_by_seektime_old(paths, start=[0.0, 0.0]):
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



def sort_by_seektime_brute(paths, startpoint=[0.0, 0.0], okdist=20):
    """Optimize for short distance between path.

    Uses a brute force approach with some smart optimizations.
    - most of the time the next path is satisfyingly closest
    - stop searching when a satisfyingly close path has been found

    """
    print len(paths)
    end = startpoint
    okdist2 = okdist**2
    d2_hash = {}  # distance2:index
    i_next = None

    # for every position find closest path to last end point
    for i in xrange(len(paths)):
        d2_hash.clear()
        i_next = None
        # search in remaining paths
        for j in xrange(i,len(paths)):
            start = paths[j][0]
            d2 = (end[0]-start[0])**2 + (end[1]-start[1])**2
            if d2 < okdist2:
                # satisfying next path found
                i_next = j
                break
            d2_hash[d2] = j  # don't care about duplicates

        if i_next is None:
            i_next = d2_hash[min(d2_hash)]

        # swap path to front
        path_temp = paths[i]
        paths[i] = paths[i_next]
        paths[i_next] = path_temp

        # endpoint for next iteration
        end = paths[i][-1]


# def sort_by_seektime_test(paths, start=[0.0, 0.0], bucket_size=30):
#     bucket_size = float(bucket_size)
#     # calculate bbox of start points
#     bbox = [9e9,9e9,0,0]  #xmin, ymin, xmax, ymin
#     for path in paths:
#         x = path[0][0]
#         y = path[0][1]
#         if x < bbox[0]:
#             bbox[0] = x
#         elif x > bbox[2]:
#             bbox[2] = x
#         if y < bbox[1]:
#             bbox[1] = y
#         elif y > bbox[3]:
#             bbox[3] = y

#     # sort paths by start/end points into square buckets
#     xnum = int(math.ceil((bbox[2]-bbox[0])/bucket_size))
#     ynum = int(math.ceil((bbox[3]-bbox[1])/bucket_size))
#     buckets_start = [[] for x in xrange(xnum*ynum)]  # empty buckets
#     buckets_end = [[] for x in xrange(xnum*ynum)]  # empty buckets
#     for path in paths:
#         # sort by start point
#         start = path[0]
#         xidx = int(math.floor(start[0]/bucket_size))
#         yidx = int(math.floor(start[1]/bucket_size))
#         buckets_start[xidx*yidx+yidx].append(path)  # column-first
#         # sort by end point
#         end = path[-1]
#         xidx = int(math.floor(end[0]/bucket_size))
#         yidx = int(math.floor(end[1]/bucket_size))
#         buckets_end[xidx*yidx+yidx].append(path)  # column-first

#     # sort within each bucket


#     paths_by_start = {}
#     for path in paths:
#         vertkey = str(int(path[0][0]))+str(int(path[0][1]))
#         try:
#             paths_by_start[vertkey].append(path)
#         except KeyError:
#             paths_by_start[vertkey] = [path]


def sort_by_seektime(paths, start=[0.0, 0.0]):
    paths_sorted = []
    tree = kdtree.Tree(2)
    
    # populate kdtree
    # for path in paths:
    for i in xrange(len(paths)):
        tree.insert(paths[i][0], i)  # startpoint, data

    # tree.insert( ((paths[i][0],i) for i in xrange(len(paths))) )

    # sort by proximity, greedy
    endpoint = start
    for p in paths:
        # print endpoint[0], endpoint[1]
        # i = tree.nearest(endpoint[0], endpoint[1])
        node, distsq = tree.nearest(endpoint, checkempty=True)
        i = node.data
        node.data = None
        # print i
        # i = tree.nearest(0.0, 0.0)
        paths_sorted.append(paths[i])
        endpoint = paths[i][-1]  # prime for next iteration

    return paths_sorted



def optimize_all(boundarys, tolerance):
    tolerance2 = tolerance**2
    epsilon2 = (0.1*tolerance)**2
    for color in boundarys:
        boundarys[color] = connect_segments(boundarys[color], epsilon2)
        simplify_all(boundarys[color], tolerance2)
        boundarys[color] = sort_by_seektime(boundarys[color])
        # sort_by_seektime_old(boundarys[color])
        # sort_by_seektime_brute(boundarys[color])
