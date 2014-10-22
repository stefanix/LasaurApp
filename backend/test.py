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
        self.assertAlmostEqual(pos[0], stepX(0), 3)
        self.assertAlmostEqual(pos[1], stepY(0), 3)
        self.assertAlmostEqual(pos[2], stepZ(0), 3)
        self.laser.move(3,4,5)
        time.sleep(1)
        pos = self.laser.pos()
        self.assertAlmostEqual(pos[0], stepX(3), 3)
        self.assertAlmostEqual(pos[1], stepY(4), 3)
        self.assertAlmostEqual(pos[2], stepZ(5), 3)
        #relative
        self.laser.relative()
        self.laser.move(2,2,2)
        time.sleep(1)
        pos = self.laser.pos()
        self.assertAlmostEqual(pos[0], stepX(5), 1)
        self.assertAlmostEqual(pos[1], stepY(6), 1)
        self.assertAlmostEqual(pos[2], stepZ(7), 1)
        # absolute after relative
        self.laser.absolute()
        self.laser.move(0,0,0)
        time.sleep(1)
        pos = self.laser.pos()
        self.assertAlmostEqual(pos[0], stepX(0), 1)
        self.assertAlmostEqual(pos[1], stepY(0), 1)
        self.assertAlmostEqual(pos[2], stepZ(0), 1)

    def test_offset(self):
        self.laser.absolute()
        self.laser.move(15.123,15.123,15.123)
        time.sleep(1)
        pos = self.laser.pos()
        self.assertAlmostEqual(pos[0], stepX(15.123), 3)
        self.assertAlmostEqual(pos[1], stepY(15.123), 3)
        self.assertAlmostEqual(pos[2], stepZ(15.123), 3)
        self.laser.set_offset(4,4,4)
        time.sleep(0.6)
        off = self.laser.get_offset()
        self.assertAlmostEqual(off[0], 4, 3)
        self.assertAlmostEqual(off[1], 4, 3)
        self.assertAlmostEqual(off[2], 4, 3)
        # pos after offset change
        pos = self.laser.pos()
        self.assertAlmostEqual(pos[0], stepX(11.123), 3)
        self.assertAlmostEqual(pos[1], stepY(11.123), 3)
        self.assertAlmostEqual(pos[2], stepZ(11.123), 3)
        # move with offset
        self.laser.move(16.543,16.543,16.543)
        time.sleep(1)
        pos = self.laser.pos()
        self.assertAlmostEqual(pos[0], stepX(16.543), 3)
        self.assertAlmostEqual(pos[1], stepY(16.543), 3)
        self.assertAlmostEqual(pos[2], stepZ(16.543), 3) 
        # clear offset
        self.laser.clear_offset()
        time.sleep(0.6)
        off = self.laser.get_offset()
        self.assertAlmostEqual(off[0], 0, 3)
        self.assertAlmostEqual(off[1], 0, 3)
        self.assertAlmostEqual(off[2], 0, 3)
        # pos after clear offset
        pos = self.laser.pos()
        self.assertAlmostEqual(pos[0], stepX(20.543), 3)
        self.assertAlmostEqual(pos[1], stepY(20.543), 3)
        self.assertAlmostEqual(pos[2], stepZ(20.543), 3)

        # self.laser.clear_offset()



def stepX(val):
    # round val to discreet pos a stepper can be in
    return round(val*88.88888888)/88.88888888
def stepY(val):
    return round(val*90.90909090)/90.90909090
def stepZ(val):
    return round(val*33.33333333)/33.33333333


def setUpModule():
    # start web interface
    web.start(threaded=True, debug=False)
    time.sleep(0.5)

def tearDownModule():
    # stop web interface
    web.stop()


if __name__ == '__main__':
    unittest.main()
