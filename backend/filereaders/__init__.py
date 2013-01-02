"""
File Reader Module
"""


__author__ = 'Stefan Hechenberger <stefan@nortd.com>'


from .svg_reader import SVGReader
from .path_optimizers import optimize_all


def read_svg(svg_string, target_size, tolerance, forced_dpi=None, optimize=True):
    svgReader = SVGReader(tolerance, target_size)
    boundarys = svgReader.parse(svg_string, forced_dpi)
    dpi_used = svgReader.dpi
    if optimize:
        optimize_all(boundarys, tolerance)
    return {'boundarys':boundarys, 'dpi':dpi_used}

