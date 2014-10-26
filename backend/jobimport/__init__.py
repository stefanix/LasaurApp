"""
File Reader Module
"""


__author__ = 'Stefan Hechenberger <stefan@nortd.com>'


from svg_reader import SVGReader
from dxf_reader import DXFReader
from ngc_reader import NGCReader
import pathoptimizer


def read_svg(svg_string, workspace, tolerance, forced_dpi=None, optimize=True):
    """Read an svg file string and convert to lsa job."""
    svgReader = SVGReader(tolerance, workspace)
    res = svgReader.parse(svg_string, forced_dpi)
    # {'boundarys':b, 'dpi':d, 'lasertags':l, 'rasters':r}

    # create an lsa job from res
    # TODO: reader should generate an lsa job to begin with
    job = {}
    if 'boundarys' in res:
        job['vector'] = {}
        vec = job['vector']
        if 'dpi' in res:
            vec['dpi'] = res['dpi']
        # format: {'#ff0000': [[[x,y], [x,y], ...], [], ..], '#0000ff':[]}
        colors = []
        paths = []
        for k,v in res['boundarys'].iteritems():
            colors.append(k)
            paths.append(v)
        if optimize:
            pathoptimizer.optimize(paths, tolerance)
        vec['paths'] = paths
        vec['colors'] = colors
        if optimize:
            vec['optimized'] = tolerance


    if 'rasters' in res:
        for raster in res['rasters']:
            # format: [(pos, size, data)]
            job['raster'] = {}
            job['raster']['images'] = []
            imgs = job['raster']['images']
            imgs.append(raster)

    if 'lasertags' in res:
        # format: [('12', '2550', '', '100', '%', ':#fff000', ':#ababab', ':#ccc999', '', '', '')]
        for tag in res['lasertags']:
            if len(tag) == 10:
                # raster pass
                if tag[5] == '_raster_' and 'raster' in job \
                        and 'images' in job['raster'] and job['raster']['images']:
                    if not 'passes' in job['raster']:
                        job['raster']['passes'] = []
                    job['raster']['passes'].append({
                        "images": [0],
                        "feedrate": tag[1],
                        "intensity": tag[3]
                    })
                    break  # currently ony supporting one raster pass
                    # TODO: we should support more than one in the future
                # vector passes
                elif 'vector' in job and 'paths' in job['vector']:
                    idxs = []
                    for colidx in range(5,10):
                        color = tag[colidx]
                        i = 0
                        for col in job['vector']['colors']:
                            if col == color:
                                idxs.append(i)
                            i += 1
                    job['vector']['passes'].append({
                        "paths": idxs,
                        "feedrate": tag[1],
                        "intensity": tag[3]
                    })                    
    return job


def read_dxf(dxf_string, tolerance, optimize=True):
    """Read an dxf file string and convert to lsa job."""
    dxfReader = DXFReader(tolerance)
    res = dxfReader.parse(dxf_string)
    # # flip y-axis
    # for color,paths in res['boundarys'].items():
    # 	for path in paths:
    # 		for vertex in path:
    # 			vertex[1] = 610-vertex[1]

    # create an lsa job from res
    # TODO: reader should generate an lsa job to begin with
    job = {}
    if 'boundarys' in res:
        job['vector'] = {}
        vec = job['vector']
        # format: {'#ff0000': [[[x,y], [x,y], ...], [], ..], '#0000ff':[]}
        # colors = []
        paths = []
        for k,v in res['boundarys']:
            # colors.append(k)
            paths.append(v)
        if optimize:
            pathoptimizer.optimize(paths, tolerance)
        vec['paths'] = paths
        # vec['colors'] = colors
        if optimize:
            vec['optimized'] = tolerance
    return job


def read_ngc(ngc_string, tolerance, optimize=False):
    """Read an gcode file string and convert to lsa job."""
    ngcReader = NGCReader(tolerance)
    res = ngcReader.parse(ngc_string)
    # create an lsa job from res
    # TODO: reader should generate an lsa job to begin with
    job = {}
    if 'boundarys' in res:
        job['vector'] = {}
        vec = job['vector']
        # format: {'#ff0000': [[[x,y], [x,y], ...], [], ..], '#0000ff':[]}
        # colors = []
        paths = []
        for k,v in res['boundarys']:
            # colors.append(k)
            paths.append(v)
        if optimize:
            pathoptimizer.optimize(paths, tolerance)
        vec['paths'] = paths
        # vec['colors'] = colors
        if optimize:
            vec['optimized'] = tolerance
    return job

