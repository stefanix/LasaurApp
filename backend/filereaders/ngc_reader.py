
__author__ = 'Stefan Hechenberger <stefan@nortd.com>'


import math
import sys
import os.path
import StringIO




class NGCReader:
    """Parse subset of G-Code.


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

        print "Done!"
        return {'boundarys':self.boundarys}
