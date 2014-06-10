
__author__ = 'Stefan Hechenberger <stefan@nortd.com>'


import math
import sys
import re
import os.path
import StringIO




class NGCReader:
    """Parse subset of G-Code.
    TODO!!
    """

    def __init__(self, tolerance):
        # tolerance settings, used in tessalation, path simplification, etc         
        self.tolerance = tolerance
        self.tolerance2 = tolerance**2

        # parsed path data, paths by color
        # {'#ff0000': [[path0, path1, ..], [path0, ..], ..]}
        # Each path is a list of vertices which is a list of two floats.        
        self.boundarys = {'#000000':[]}
        self.black_boundarys = self.boundarys['#000000']


    def parse(self, ngcstring):
        """This is a total super quick HACK!!!!
            Pretty much only parses the old example files.
        """

        paths = []
        current_path = []
        re_findall_attribs = re.compile('(S|F|X|Y|Z)(-?[0-9]+\.?[0-9]*(?:e-?[0-9]*)?)').findall

        intensity = 0.0
        feedrate = 1000.0
        target = [0.0, 0.0, 0.0]
        prev_motion_was_seek = True


        lines = ngcstring.split('\n')
        for line in lines:
            line = line.replace(' ', '')
            if line.startswith('G0'):
                attribs = re_findall_attribs(line[2:])
                for attr in attribs:
                    if attr[0] == 'X':
                        target[0] = float(attr[1])
                        prev_motion_was_seek = True
                    elif attr[0] == 'Y':
                        target[1] = float(attr[1])
                        prev_motion_was_seek = True
                    elif attr[0] == 'Z':
                        target[2] = float(attr[1])
                        prev_motion_was_seek = True
            elif line.startswith('G1'):
                if prev_motion_was_seek:
                    # new path
                    paths.append([[target[0], target[1], target[2]]])
                    current_path = paths[-1]
                    prev_motion_was_seek = False
                # new target
                attribs = re_findall_attribs(line[2:])
                for attr in attribs:
                    if attr[0] == 'X':
                        target[0] = float(attr[1])
                    elif attr[0] == 'Y':
                        target[1] = float(attr[1])
                    elif attr[0] == 'Z':
                        target[2] = float(attr[1])
                    elif attr[0] == 'S':
                        intensity = float(attr[1])
                    elif attr[0] == 'F':
                        feedrate = float(attr[1])
                current_path.append([target[0], target[1], target[2]])
            elif line.startswith('S'):
                attribs = re_findall_attribs(line)
                for attr in attribs:
                    if attr[0] == 'S':
                        intensity = float(attr[1])
            else:
                print "Warning: Unsupported Gcode"

        print "Done!"
        self.boundarys = {'#000000':paths}
        pass_ = ['1', feedrate, '', intensity, '', '#000000']
        return {'boundarys':self.boundarys}
