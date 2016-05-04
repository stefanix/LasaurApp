from filereaders import read_svg, SVGReader

with open("path/to/test.svg") as f:
    svgstring = f.read()
    svgReader = SVGReader(0.08, [1220,610])
    parseResults = svgReader.parse(svgstring)
    pass
