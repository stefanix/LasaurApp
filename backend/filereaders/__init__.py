"""
SVGReader
"""



__author__ = 'Stefan Hechenberger <stefan@nortd.com>'


from .svg_reader import SVGReader
from .path_optimizers import join_segments, simplify_all, sort_by_seektime


def read_svg(svg_string, target_size, tolerance, forced_dpi=None, optimize=True):
    svgReader = SVGReader(tolerance, target_size)
    boundarys = svgReader.parse(svg_string, forced_dpi)
    dpi_used = svgReader.dpi

    if optimize:
        tolerance2 = tolerance**2
        epsilon2 = (0.1*tolerance)**2
        # for col in boundarys:
            # boundarys[col] = join_segments(boundarys[col], epsilon2)
            # boundarys[col] = simplify_all(boundarys[col], tolerance2)
            # sort_by_seektime(boundarys[col])

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

