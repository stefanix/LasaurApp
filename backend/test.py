
import os
import time
import random
import unittest
import json
import threading

import web
from config import conf 
import liblasersaur
import lasersaur


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


# the num of decimals, match firmware protocol
DEC = 3

# match these to src/config.h
X_STEPS_PER_MM = 88.88888888
Y_STEPS_PER_MM = 90.90909090
Z_STEPS_PER_MM = 33.33333333
X_ORIGIN_OFFSET = 5.0
Y_ORIGIN_OFFSET = 5.0
Z_ORIGIN_OFFSET = 0.0

thislocation = os.path.dirname(os.path.realpath(__file__))


class TestLowLevel(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # start web interface
        web.start(threaded=True, debug=False)
        time.sleep(0.5)
        # conf liblasersaur
        cls.laser = liblasersaur.Lasersaur("127.0.0.1")

    @classmethod
    def tearDownClass(cls):
        # stop web interface
        web.stop()

    # def setUp(self):
    #     self.laser = liblasersaur.Lasersaur("127.0.0.1")
    # def tearDown(self):
    #     pass

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
        pos = self.laser.status()['pos']
        self.assertAlmostEqual(pos[0], stepX(0), DEC)
        self.assertAlmostEqual(pos[1], stepY(0), DEC)
        self.assertAlmostEqual(pos[2], stepZ(0), DEC)
        self.laser.move(3,4,5)
        time.sleep(1)
        pos = self.laser.status()['pos']
        self.assertAlmostEqual(pos[0], stepX(3), DEC)
        self.assertAlmostEqual(pos[1], stepY(4), DEC)
        self.assertAlmostEqual(pos[2], stepZ(5), DEC)
        #relative
        self.laser.relative()
        self.laser.move(2,2,2)
        time.sleep(1)
        pos = self.laser.status()['pos']
        self.assertAlmostEqual(pos[0], stepX(5), DEC)
        self.assertAlmostEqual(pos[1], stepY(6), DEC)
        self.assertAlmostEqual(pos[2], stepZ(7), DEC)
        # absolute after relative
        self.laser.absolute()
        self.laser.move(0,0,0)
        time.sleep(1)
        pos = self.laser.status()['pos']
        self.assertAlmostEqual(pos[0], stepX(0), DEC)
        self.assertAlmostEqual(pos[1], stepY(0), DEC)
        self.assertAlmostEqual(pos[2], stepZ(0), DEC)

    def test_offset(self):
        self.laser.absolute()
        self.laser.move(15.123,15.123,15.123)
        time.sleep(1)
        pos = self.laser.status()['pos']
        self.assertAlmostEqual(pos[0], stepX(15.123), DEC)
        self.assertAlmostEqual(pos[1], stepY(15.123), DEC)
        self.assertAlmostEqual(pos[2], stepZ(15.123), DEC)
        self.laser.offset(4,4,4)
        time.sleep(0.6)
        off = self.laser.status()['offset']
        self.assertAlmostEqual(off[0], 4, DEC)
        self.assertAlmostEqual(off[1], 4, DEC)
        self.assertAlmostEqual(off[2], 4, DEC)
        # pos after offset change
        pos = self.laser.status()['pos']
        self.assertAlmostEqual(pos[0], stepX(11.123, 4), DEC)
        self.assertAlmostEqual(pos[1], stepY(11.123, 4), DEC)
        self.assertAlmostEqual(pos[2], stepZ(11.123, 4), DEC)
        # move with offset
        self.laser.move(16.543,16.543,16.543)
        time.sleep(1)
        pos = self.laser.status()['pos']
        self.assertAlmostEqual(pos[0], stepX(16.543, 4), DEC)
        self.assertAlmostEqual(pos[1], stepY(16.543, 4), DEC)
        self.assertAlmostEqual(pos[2], stepZ(16.543, 4), DEC) 
        # clear offset
        self.laser.clear_offset()
        time.sleep(0.6)
        off = self.laser.status()['offset']
        self.assertAlmostEqual(off[0], 0, DEC)
        self.assertAlmostEqual(off[1], 0, DEC)
        self.assertAlmostEqual(off[2], 0, DEC)
        # pos after clear offset
        pos = self.laser.status()['pos']
        self.assertAlmostEqual(pos[0], stepX(20.543), DEC)
        self.assertAlmostEqual(pos[1], stepY(20.543), DEC)
        self.assertAlmostEqual(pos[2], stepZ(20.543), DEC)



def stepX(val, off1=0, off2=X_ORIGIN_OFFSET):
    # round val to discreet pos a stepper can be in
    return (round((val+off1+off2)*X_STEPS_PER_MM)/X_STEPS_PER_MM)-off1-off2
def stepY(val, off1=0, off2=Y_ORIGIN_OFFSET):
    return (round((val+off1+off2)*Y_STEPS_PER_MM)/Y_STEPS_PER_MM)-off1-off2
def stepZ(val, off1=0, off2=Z_ORIGIN_OFFSET):
    return (round((val+off1+off2)*Z_STEPS_PER_MM)/Z_STEPS_PER_MM)-off1-off2





class TestQueue(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # start web interface
        web.start(threaded=True, debug=False)
        time.sleep(0.5)
        # conf liblasersaur
        cls.laser = liblasersaur.Lasersaur("127.0.0.1")

    @classmethod
    def tearDownClass(cls):
        # stop web interface
        web.stop()

    def test_queue_library(self):
        # empty job queue
        self.laser.clear()
        jobs = self.laser.list('unstarred')
        self.assertIsInstance(jobs, list)
        self.assertListEqual(jobs, [])
        starred = self.laser.list('starred')
        self.assertIsInstance(starred, list)
        for job in starred:
            self.laser.unstar(job)
        self.laser.clear()
        jobs = self.laser.list()
        self.assertIsInstance(jobs, list)
        self.assertListEqual(jobs, [])
        #library
        lib = self.laser.list_library()
        self.assertIsInstance(lib, list)
        self.assertIn('Lasersaur.lsa', lib)
        job = self.laser.get_library('Lasersaur.lsa')
        self.assertIsInstance(job, dict)
        self.laser.load_library('Lasersaur.lsa')
        # queue
        jobs = self.laser.list()
        self.assertIsInstance(jobs, list)
        self.assertIn('Lasersaur.lsa', jobs)
        # get
        job = self.laser.get('Lasersaur.lsa')
        self.assertIsInstance(job, dict)
        # list, starring
        jobs = self.laser.list('starred')
        self.assertIsInstance(jobs, list)
        self.assertListEqual(jobs, [])
        self.laser.star('Lasersaur.lsa')
        jobs = self.laser.list('starred')
        self.assertIsInstance(jobs, list)
        self.assertIn('Lasersaur.lsa', jobs)
        jobs = self.laser.list('unstarred')
        self.assertIsInstance(jobs, list)
        self.assertListEqual(jobs, [])
        self.laser.unstar('Lasersaur.lsa')
        jobs = self.laser.list('starred')
        self.assertIsInstance(jobs, list)
        self.assertListEqual(jobs, [])
        jobs = self.laser.list('unstarred')
        self.assertIsInstance(jobs, list)
        self.assertIn('Lasersaur.lsa', jobs)
        jobs = self.laser.list()
        self.assertIsInstance(jobs, list)
        self.assertIn('Lasersaur.lsa', jobs)
        #del
        self.laser.delete('Lasersaur.lsa')
        jobs = self.laser.list()
        self.assertIsInstance(jobs, list)
        self.assertListEqual(jobs, [])
        #TODO: constant job nums on add
        #TODO: delete of starred file



class TestJobs(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # start web interface
        web.start(threaded=True, debug=False)
        time.sleep(0.5)
        # conf liblasersaur
        cls.laser = liblasersaur.Lasersaur("127.0.0.1")

    @classmethod
    def tearDownClass(cls):
        # stop web interface
        web.stop()

    def testLoad(self):
        # jobname = self.laser.load(os.path.join(thislocation,'test_svgs','full-bed.svg'))
        # jobname = self.laser.load(os.path.join(thislocation,'test_svgs','Lasersaur.lsa'))
        # self.assertIn(jobname, self.laser.list())
        # self.laser.run(jobname) 
        jobs = self.laser.list()
        # self.laser.run(jobs[-1], async=False)
        self.laser.run(jobs[-1])

        s = self.laser.status()
        while not s['idle']:
            print s['pos']
            time.sleep(1)
            s = self.laser.status()
        print s['pos']




class TestSerial(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        lasersaur.connect()
        time.sleep(0.3)

    @classmethod
    def tearDownClass(cls):
        time.sleep(20)
        lasersaur.close()

    def testJob(self):
        jobfile = os.path.join(thislocation,'test_svgs','Lasersaur.lsa')
        with open(jobfile) as fp:
            job = fp.read()
        lasersaur.job(json.loads(job))



# def setUpModule():
#     # start web interface
#     web.start(threaded=True, debug=False)
#     time.sleep(0.5)

# def tearDownModule():
#     # stop web interface
#     web.stop()


if __name__ == '__main__':
    unittest.main()

    # for partial test run like this:
    # python test.py Class
    # E.g:
    # python test.py TestQueue
