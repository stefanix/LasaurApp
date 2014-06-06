"""
File Reader Module
"""


__author__ = 'Stefan Hechenberger <stefan@nortd.com>'


from .svg_reader import SVGReader
from .dxf_reader import DXFReader
from .ngc_reader import NGCReader
from .path_optimizers import optimize_all


def read_svg(svg_string, target_size, tolerance, forced_dpi=None, optimize=True):
    svgReader = SVGReader(tolerance, target_size)
    parse_results = svgReader.parse(svg_string, forced_dpi)
    if optimize:
        optimize_all(parse_results['boundarys'], tolerance)
    # {'boundarys':b, 'dpi':d, 'lasertags':l}
    return parse_results


def read_dxf(dxf_string, tolerance, optimize=True):
    dxfReader = DXFReader(tolerance)
    parse_results = dxfReader.parse(dxf_string)
    if optimize:
        optimize_all(parse_results['boundarys'], tolerance)
    # # flip y-axis
    # for color,paths in parse_results['boundarys'].items():
    # 	for path in paths:
    # 		for vertex in path:
    # 			vertex[1] = 610-vertex[1]
    return parse_results


def read_ngc(ngc_string, tolerance, optimize=True):
    ngcReader = NGCReader(tolerance)
    parse_results = ngcReader.parse(ngc_string)
    # if optimize:
    #     optimize_all(parse_results['boundarys'], tolerance)
    return parse_results

