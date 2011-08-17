
import math

X = 0
Y = 1

# repetitive point deletion
###########################
# Any point that is within this distance from the
# last used point is ignored.
# This also has the effect of merging geometry made from
# short lines into one segment.
# TODO: include angles into the deletion check
DELETION_EPSILON_SQUARED = 0.1**2

def write_GCODE(boundarys, feedrate, laser_intensity, scale=1.0, xoff=0.0, yoff=0.0):
    feed = 2000.0
    glist = []
    glist.append("%\n")
    glist.append("G21\nG90\n") # mm and absolute positioning
    glist.append("S%0.0f\n"%laser_intensity)
    glist.append("G1 F%0.0f\n"%feedrate)
    glist.append("G0 F10000\n")
    nsegment = 0
    x_prev = 0.0
    y_prev = 0.0
    for layer in range((len(boundarys)-1),-1,-1):
        path = boundarys[layer]
        for segment in range(len(path)):
            segment = path[segment]
            if len(segment) > 0:
                vertex = 0
                x = segment[vertex][X]*scale + xoff
                y = segment[vertex][Y]*scale + yoff
                if ((x_prev-x)**2 + (y_prev-y)**2) > DELETION_EPSILON_SQUARED:
                    glist.append("G00X%0.3f"%x+"Y%0.3f"%y+"\n")
                    nsegment += 1
                    x_prev,y_prev = x,y
                numVerts = len(segment)
                for vertex in range(1,numVerts):
                    x = segment[vertex][X]*scale + xoff
                    y = segment[vertex][Y]*scale + yoff
                    if ((x_prev-x)**2 + (y_prev-y)**2) > DELETION_EPSILON_SQUARED \
                    or vertex == numVerts-1:
                        glist.append("G01X%0.3f"%x+"Y%0.3f"%y+"\n")
                        x_prev,y_prev = x,y                
    glist.append("S0\n") # reset laser intensity
    glist.append("G00X0Y0F15000\n") # reset laser intensity
    glist.append("%\n")
    print "wrote",nsegment-1,"G code toolpath segments"
    return ''.join(glist)

  
