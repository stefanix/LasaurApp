

import os
import cProfile as profile
# import cProfile as profile
import timeit
import pstats
import argparse

from filereaders import read_svg

### Setup Argument Parser
argparser = argparse.ArgumentParser(description='Run LasaurApp.', prog='lasaurapp')
argparser.add_argument('svg_file', metavar='svg_file', nargs='?', default=False,
                       help='svg file to parse')
argparser.add_argument('-p', '--profile', dest='profile', action='store_true',
                    default=False, help='run with profiling')  
argparser.add_argument('-t', '--timeit', dest='timeit', action='store_true',
                    default=False, help='run with timing')      
argparser.add_argument('-o', '--optimize', dest='optimize', action='store_true',
                    default=False, help='optimize by loading c extensions')   
argparser.add_argument('-d', '--debug', dest='debug', action='store_true',
                    default=False, help='verbose debug info')                                  
args = argparser.parse_args()


thislocation = os.path.dirname(os.path.realpath(__file__))
svgpath = os.path.join(thislocation, 'test_svgs')

def main():
    # svgstring = open(os.path.join(svgpath, "full-bed.svg")).read()
    svgstring = open(os.path.join(svgpath, "rocket_full.svg")).read()
    # svgstring = open(os.path.join(svgpath, "rosetta.svg")).read()
    boundarys = read_svg(svgstring, [1220,610], 0.08)


if args.profile:
    profile.run("main()", 'profile.tmp')
    p = pstats.Stats('profile.tmp')
    p.sort_stats('cumulative').print_stats(30)
    os.remove('profile.tmp')
elif args.timeit:
    t = timeit.Timer("main()", "from __main__ import main")
    print t.timeit(1)
    # print t.timeit(3)
else:
    main()