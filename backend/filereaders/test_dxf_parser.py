#!/usr/bin/python

import io

from dxf_parser import DXFParser
from path_optimizers import optimize_all

tolerance = 0.08
preColor = {}
postColor = {}

fin = open("test.dxf"); 
dxf_string = fin.read();  
fin.close() 

dxf_string = unicode(dxf_string)
dxfParser = DXFParser(0.8)
forced_unit = 0

parse_results = dxfParser.parse(dxf_string, forced_unit)

for color in parse_results['boundaries']:
    if len(parse_results['boundaries'][color]) > 0:
        thisColor = parse_results['boundaries'][color]
        preColor[color] = len(thisColor)

optimize_all(parse_results['boundaries'], tolerance)

for color in parse_results['boundaries']:
    if len(parse_results['boundaries'][color]) > 0:
        thisColor = parse_results['boundaries'][color]
        postColor[color] = len(thisColor)

print("pre/post optimization entity count")
print("color\tpre\tpost")
for color in preColor:
    print("%s\t%s\t%s" % (color, preColor[color], postColor[color]))
    

