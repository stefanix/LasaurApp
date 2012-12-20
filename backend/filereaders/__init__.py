"""
SVGReader
"""



__author__ = 'Stefan Hechenberger <stefan@nortd.com>'


from .svg_reader import SVGReader
# from .path_optimizers import join_segments, simplify_all, sort_by_seektime


def read_svg(svg_string, target_size, tolerance, forced_dpi=None, optimize=True):
    svgReader = SVGReader(tolerance, target_size)
    paths_by_color = svgReader.parse(svg_string, forced_dpi)
    dpi_used = svgReader.dpi

    # if optimize:
    #     tolerance2 = tolerance**2
    #     epsilon2 = (0.1*tolerance)**2
    #     for col,paths in paths_by_color:
    #         paths = join_segments(paths, epsilon2)
    #         paths = simplify_all(paths, tolerance2)
    #         sort_by_seektime(paths)

    return {'boundarys':paths_by_color, 'dpi':dpi_used}




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

