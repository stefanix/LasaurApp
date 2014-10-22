import time
import random
import unittest
import json
import threading

import web
from config import conf 
import liblasersaur


# assertEqual(a, b)
# assertNotEqual(a, b)
# assertTrue(x)
# assertFalse(x)
# assertIsNone(x)

# assertIsInstance(a, b)
# assertNotIsInstance(a, b)

# assertAlmostEqual(a, b)
# assertNotAlmostEqual(a, b)
# assertGreater(a, b)
# assertGreaterEqual(a, b)
# assertLess(a, b)
# assertLessEqual(a, b)


# assertListEqual(a, b)
# assertIn(a, b)
# assertDictEqual(a, b)
# assertDictContainsSubset(a, b)


DEC = 1

# match these to src/config.h
X_STEPS_PER_MM = 88.88888888
Y_STEPS_PER_MM = 90.90909090
Z_STEPS_PER_MM = 33.33333333
X_ORIGIN_OFFSET = 5.0
Y_ORIGIN_OFFSET = 5.0
Z_ORIGIN_OFFSET = 0.0


class TestWebJobs(unittest.TestCase):

    def setUp(self):
        self.laser = liblasersaur.Lasersaur("127.0.0.1")

    def tearDown(self):
        pass

    def test_config(self):
        # test if we can get a sound config dict
        c = self.laser.config()
        self.assertIsInstance(c, dict)
        self.assertIn('appname', c.keys())
        self.assertIn('version', c.keys())

    def test_status(self):
        s = self.laser.status()
        self.assertIsInstance(s, dict)
        self.assertIn('appver', s.keys())
        self.assertIn('firmver', s.keys())

    def test_feedrate_intensity(self):
        new_rate = 4500.1
        new_intens = 210
        self.laser.feedrate(4500.1)
        self.laser.intensity(new_intens)
        time.sleep(0.6)
        s = self.laser.status()
        self.assertAlmostEqual(s['feedrate'], new_rate, 1)
        self.assertAlmostEqual(s['intensity'], new_intens, 1)

    def test_move(self):
        self.laser.absolute()
        pos = self.laser.pos()
        self.assertAlmostEqual(pos[0], stepX(0), DEC)
        self.assertAlmostEqual(pos[1], stepY(0), DEC)
        self.assertAlmostEqual(pos[2], stepZ(0), DEC)
        self.laser.move(3,4,5)
        time.sleep(1)
        pos = self.laser.pos()
        self.assertAlmostEqual(pos[0], stepX(3), DEC)
        self.assertAlmostEqual(pos[1], stepY(4), DEC)
        self.assertAlmostEqual(pos[2], stepZ(5), DEC)
        #relative
        self.laser.relative()
        self.laser.move(2,2,2)
        time.sleep(1)
        pos = self.laser.pos()
        self.assertAlmostEqual(pos[0], stepX(5), DEC)
        self.assertAlmostEqual(pos[1], stepY(6), DEC)
        self.assertAlmostEqual(pos[2], stepZ(7), DEC)
        # absolute after relative
        self.laser.absolute()
        self.laser.move(0,0,0)
        time.sleep(1)
        pos = self.laser.pos()
        self.assertAlmostEqual(pos[0], stepX(0), DEC)
        self.assertAlmostEqual(pos[1], stepY(0), DEC)
        self.assertAlmostEqual(pos[2], stepZ(0), DEC)

    def test_offset(self):
        self.laser.absolute()
        self.laser.move(15.123,15.123,15.123)
        time.sleep(1)
        pos = self.laser.pos()
        self.assertAlmostEqual(pos[0], stepX(15.123), DEC)
        self.assertAlmostEqual(pos[1], stepY(15.123), DEC)
        self.assertAlmostEqual(pos[2], stepZ(15.123), DEC)
        self.laser.set_offset(4,4,4)
        time.sleep(0.6)
        off = self.laser.get_offset()
        self.assertAlmostEqual(off[0], 4, DEC)
        self.assertAlmostEqual(off[1], 4, DEC)
        self.assertAlmostEqual(off[2], 4, DEC)
        # pos after offset change
        pos = self.laser.pos()
        self.assertAlmostEqual(pos[0], stepX(11.123), DEC)
        self.assertAlmostEqual(pos[1], stepY(11.123), DEC)
        self.assertAlmostEqual(pos[2], stepZ(11.123), DEC)
        # move with offset
        self.laser.move(16.543,16.543,16.543)
        time.sleep(1)
        pos = self.laser.pos()
        self.assertAlmostEqual(pos[0], stepX(16.543), DEC)
        self.assertAlmostEqual(pos[1], stepY(16.543), DEC)
        self.assertAlmostEqual(pos[2], stepZ(16.543), DEC) 
        # clear offset
        self.laser.clear_offset()
        time.sleep(0.6)
        off = self.laser.get_offset()
        self.assertAlmostEqual(off[0], 0, DEC)
        self.assertAlmostEqual(off[1], 0, DEC)
        self.assertAlmostEqual(off[2], 0, DEC)
        # pos after clear offset
        pos = self.laser.pos()
        self.assertAlmostEqual(pos[0], stepX(20.543), DEC)
        self.assertAlmostEqual(pos[1], stepY(20.543), DEC)
        self.assertAlmostEqual(pos[2], stepZ(20.543), DEC)

        # self.laser.clear_offset()



def stepX(val):
    # round val to discreet pos a stepper can be in
    return (round((val-X_ORIGIN_OFFSET)*X_STEPS_PER_MM)/X_STEPS_PER_MM)+X_ORIGIN_OFFSET
def stepY(val):
    return (round((val-Y_ORIGIN_OFFSET)*Y_STEPS_PER_MM)/Y_STEPS_PER_MM)+Y_ORIGIN_OFFSET
def stepZ(val):
    return (round((val-Z_ORIGIN_OFFSET)*Z_STEPS_PER_MM)/Z_STEPS_PER_MM)+Z_ORIGIN_OFFSET


def setUpModule():
    # start web interface
    web.start(threaded=True, debug=False)
    time.sleep(0.5)

def tearDownModule():
    # stop web interface
    web.stop()


if __name__ == '__main__':
    unittest.main()
yY