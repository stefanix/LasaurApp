
import os
import sys
import time
import random
import unittest
import json
import threading
import base64
import Image

import web
from config import conf 
import lasersaur
import driveboard


thislocation = os.path.dirname(os.path.realpath(__file__))

laser = None

class TestRaster(unittest.TestCase):
    def test_config(self):
        img = Image.open(os.path.join(thislocation, 'testjobs', 'bat.png'))
        # img_g = img.convert('LA')  # to grayscale
        img_g = img.convert('L')  # to grayscale
        w = 80
        h = int(img_g.size[1]*(float(w)/img_g.size[0]))
        img_s = img_g.resize((w,h), resample=Image.BICUBIC)
        # img_s.show()
        data = img_s.getdata()

        for lx in xrange(h):
            for rx in xrange(w):
                x = data[w*lx+rx]
                if x < 150:
                    sys.stdout.write('.')
                elif x < 200:
                    sys.stdout.write('o')
                else:
                    sys.stdout.write('X')
            sys.stdout.write('\n')


class TestEncode(unittest.TestCase):
    def test_encode(self):
        filein = os.path.join(thislocation, 'testjobs', 'bat.png')
        fileout = os.path.join(thislocation, 'testjobs', 'bat--.svg')
        with open(filein,"rb") as fp:
            b64 = base64.encodestring(fp.read()).decode("utf8")
        with open(fileout,"w") as fp:
            fp.write(header+b64+footer)
        # print b64



header = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<!-- Created with Inkscape (http://www.inkscape.org/) -->

<svg
   xmlns:dc="http://purl.org/dc/elements/1.1/"
   xmlns:cc="http://creativecommons.org/ns#"
   xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
   xmlns:svg="http://www.w3.org/2000/svg"
   xmlns="http://www.w3.org/2000/svg"
   xmlns:xlink="http://www.w3.org/1999/xlink"
   version="1.1"
   width="744.09448"
   height="1052.3622"
   id="svg2">
  <defs
     id="defs4" />
  <metadata
     id="metadata7">
    <rdf:RDF>
      <cc:Work
         rdf:about="">
        <dc:format>image/svg+xml</dc:format>
        <dc:type
           rdf:resource="http://purl.org/dc/dcmitype/StillImage" />
        <dc:title></dc:title>
      </cc:Work>
    </rdf:RDF>
  </metadata>
  <g
     id="layer1">
    <image
       xlink:href="data:image/png;base64,"""

footer = """"
       x="112.85717"
       y="125.21935"
       width="500"
       height="540"
       id="image3082" />
  </g>
</svg>"""


class TestLSA(unittest.TestCase):
    def test_encode(self):
        filein = os.path.join(thislocation, 'testjobs', 'bat.png')
        fileout = os.path.join(thislocation, 'testjobs', 'bat--.lsa')
        with open(filein,"rb") as fp:
            b64 = base64.encodestring(fp.read()).decode("utf8")
        with open(fileout,"w") as fp:
            fp.write(header+b64+footer)
        # print b64



def setUpModule():
    global laser
    # start web interface
    # web.start(threaded=True, debug=False)
    # time.sleep(0.5)
    laser = lasersaur.Lasersaur("127.0.0.1")

def tearDownModule():
    # stop web interface
    # web.stop()
    pass


if __name__ == '__main__':
    unittest.main()

    # for partial test run like this:
    # python test.py Class
    # E.g:
    # python test.py TestQueue
