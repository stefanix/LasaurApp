"""
SVGReader
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




# from .decoder import JSONDecoder
# from .encoder import JSONEncoder

# _default_encoder = JSONEncoder(
#     skipkeys=False,
#     ensure_ascii=True,
#     check_circular=True,
#     allow_nan=True,
#     indent=None,
#     separators=None,
#     encoding='utf-8',
#     default=None,
# )

# def dump(obj, fp, skipkeys=False, ensure_ascii=True, check_circular=True,
#         allow_nan=True, cls=None, indent=None, separators=None,
#         encoding='utf-8', default=None, **kw):
#     """Serialize ``obj`` as a JSON formatted stream to ``fp`` (a
#     ``.write()``-supporting file-like object).

