

X = 0
Y = 1

def write_GCODE(boundarys, feedrate, laser_intensity, scale=1.0, xoff=0.0, yoff=0.0):
    feed = 2000.0
    glist = []
    glist.append("%\n")
    glist.append("G21\nG90\n") # mm and absolute positioning
    glist.append("F%0.3f\n"%feedrate)
    glist.append("S%0.3f\n"%laser_intensity)
    nsegment = 0
    for layer in range((len(boundarys)-1),-1,-1):
        path = boundarys[layer]
        for segment in range(len(path)):
            nsegment += 1
            vertex = 0
            x = path[segment][vertex][X]*scale + xoff
            y = path[segment][vertex][Y]*scale + yoff
            glist.append("G00X%0.3f"%x+"Y%0.3f"%y+"\n")
            for vertex in range(1,len(path[segment])):
                x = path[segment][vertex][X]*scale + xoff
                y = path[segment][vertex][Y]*scale + yoff
                glist.append("G01X%0.3f"%x+"Y%0.3f"%y+"\n")
    glist.append("S0\n") # reset laser intensity
    glist.append("G00X0Y0F20000\n") # reset laser intensity
    glist.append("%\n")
    print "wrote",nsegment,"G code toolpath segments"
    return ''.join(glist)

  
