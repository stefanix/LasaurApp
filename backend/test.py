
import os
import time
import random
import unittest
import json
import threading

import web
import lasersaur
from config import conf


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


def setUpModule():
    web.start(threaded=True, debug=False)
    time.sleep(0.5)
    lasersaur.local()

def tearDownModule():
    web.stop()



class TestLowLevel(unittest.TestCase):

    def test_config(self):
        # test if we can get a sound config dict
        c = lasersaur.config()
        self.assertIsInstance(c, dict)
        self.assertIn('appname', c.keys())
        self.assertIn('version', c.keys())

    def test_status(self):
        s = lasersaur.status()
        self.assertIsInstance(s, dict)
        self.assertIn('appver', s.keys())
        self.assertIn('firmver', s.keys())

    def test_feedrate_intensity(self):
        new_rate = 4500.1
        new_intens = 210
        lasersaur.feedrate(new_rate)
        lasersaur.intensity(new_intens)
        time.sleep(1)
        s = lasersaur.status()
        self.assertAlmostEqual(s['feedrate'], new_rate, DEC)
        self.assertAlmostEqual(s['intensity'], new_intens, DEC)

    def test_move(self):
        lasersaur.absolute()
        pos = lasersaur.status()['pos']
        self.assertAlmostEqual(pos[0], stepX(0), DEC)
        self.assertAlmostEqual(pos[1], stepY(0), DEC)
        self.assertAlmostEqual(pos[2], stepZ(0), DEC)
        lasersaur.move(3,4,5)
        time.sleep(2)
        pos = lasersaur.status()['pos']
        self.assertAlmostEqual(pos[0], stepX(3), DEC)
        self.assertAlmostEqual(pos[1], stepY(4), DEC)
        self.assertAlmostEqual(pos[2], stepZ(5), DEC)
        #relative
        lasersaur.relative()
        lasersaur.move(2,2,2)
        time.sleep(2)
        pos = lasersaur.status()['pos']
        self.assertAlmostEqual(pos[0], stepX(5), DEC)
        self.assertAlmostEqual(pos[1], stepY(6), DEC)
        self.assertAlmostEqual(pos[2], stepZ(7), DEC)
        # absolute after relative
        lasersaur.absolute()
        lasersaur.move(0,0,0)
        time.sleep(2)
        pos = lasersaur.status()['pos']
        self.assertAlmostEqual(pos[0], stepX(0), DEC)
        self.assertAlmostEqual(pos[1], stepY(0), DEC)
        self.assertAlmostEqual(pos[2], stepZ(0), DEC)

    def test_offset(self):
        lasersaur.absolute()
        lasersaur.move(15.123,15.123,15.123)
        time.sleep(2)
        pos = lasersaur.status()['pos']
        self.assertAlmostEqual(pos[0], stepX(15.123), DEC)
        self.assertAlmostEqual(pos[1], stepY(15.123), DEC)
        self.assertAlmostEqual(pos[2], stepZ(15.123), DEC)
        lasersaur.offset(4,4,4)
        time.sleep(1)
        off = lasersaur.status()['offset']
        self.assertAlmostEqual(off[0], 4, DEC)
        self.assertAlmostEqual(off[1], 4, DEC)
        self.assertAlmostEqual(off[2], 4, DEC)
        # pos after offset change
        pos = lasersaur.status()['pos']
        self.assertAlmostEqual(pos[0], stepX(11.123, 4), DEC)
        self.assertAlmostEqual(pos[1], stepY(11.123, 4), DEC)
        self.assertAlmostEqual(pos[2], stepZ(11.123, 4), DEC)
        # move with offset
        lasersaur.move(16.543,16.543,16.543)
        time.sleep(2)
        pos = lasersaur.status()['pos']
        self.assertAlmostEqual(pos[0], stepX(16.543, 4), DEC)
        self.assertAlmostEqual(pos[1], stepY(16.543, 4), DEC)
        self.assertAlmostEqual(pos[2], stepZ(16.543, 4), DEC)
        # clear offset
        lasersaur.clear_offset()
        time.sleep(1)
        off = lasersaur.status()['offset']
        self.assertAlmostEqual(off[0], 0, DEC)
        self.assertAlmostEqual(off[1], 0, DEC)
        self.assertAlmostEqual(off[2], 0, DEC)
        # pos after clear offset
        pos = lasersaur.status()['pos']
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

    def test_queue_library(self):
        # empty job queue
        lasersaur.clear()
        jobs = lasersaur.listing('unstarred')
        self.assertIsInstance(jobs, list)
        self.assertListEqual(jobs, [])
        starred = lasersaur.listing('starred')
        self.assertIsInstance(starred, list)
        for job in starred:
            lasersaur.unstar(job)
        lasersaur.clear()
        jobs = lasersaur.listing()
        self.assertIsInstance(jobs, list)
        self.assertListEqual(jobs, [])
        #library
        lib = lasersaur.listing_library()
        self.assertIsInstance(lib, list)
        self.assertIn('Lasersaur', lib)
        job = lasersaur.get_library('Lasersaur')
        self.assertIsInstance(job, dict)
        lasersaur.load_library('Lasersaur')
        # queue
        jobs = lasersaur.listing()
        self.assertIsInstance(jobs, list)
        self.assertIn('Lasersaur', jobs)
        # get
        job = lasersaur.get('Lasersaur')
        self.assertIsInstance(job, dict)
        # list, starring
        jobs = lasersaur.listing('starred')
        self.assertIsInstance(jobs, list)
        self.assertListEqual(jobs, [])
        lasersaur.star('Lasersaur')
        jobs = lasersaur.listing('starred')
        self.assertIsInstance(jobs, list)
        self.assertIn('Lasersaur', jobs)
        jobs = lasersaur.listing('unstarred')
        self.assertIsInstance(jobs, list)
        self.assertListEqual(jobs, [])
        lasersaur.unstar('Lasersaur')
        jobs = lasersaur.listing('starred')
        self.assertIsInstance(jobs, list)
        self.assertListEqual(jobs, [])
        jobs = lasersaur.listing('unstarred')
        self.assertIsInstance(jobs, list)
        self.assertIn('Lasersaur', jobs)
        jobs = lasersaur.listing()
        self.assertIsInstance(jobs, list)
        self.assertIn('Lasersaur', jobs)
        #del
        lasersaur.remove('Lasersaur')
        jobs = lasersaur.listing()
        self.assertIsInstance(jobs, list)
        self.assertListEqual(jobs, [])
        #delete of starred file
        lasersaur.load_library('Lasersaur')
        lasersaur.star('Lasersaur')
        lasersaur.remove('Lasersaur')
        jobs = lasersaur.listing()
        self.assertListEqual(jobs, [])
        #constant job nums on add
        for i in range(conf['max_jobs_in_list'] + 3):
            lasersaur.load_library('Lasersaur')
        jobs = lasersaur.listing()
        self.assertEqual(len(jobs), conf['max_jobs_in_list'])
        print jobs
        lasersaur.clear()
        jobs = lasersaur.listing()
        self.assertListEqual(jobs, [])



class TestJobs(unittest.TestCase):

    def testLoad(self):
        jobfile = os.path.join(thislocation,'testjobs','full-bed.svg')
        job = lasersaur.open_file(jobfile)
        if 'vector' in job:
            job['vector']['passes'] = [{
                    "paths":[0],
                    "feedrate":4000,
                    "intensity":53
                }]
        jobname = lasersaur.load(job)
        self.assertIn(jobname, lasersaur.listing())
        lasersaur.run(jobname, progress=True)
        print "done!"


if __name__ == '__main__':
    unittest.main()

    # for partial test run like this:
    # python test.py Class
    # E.g:
    # python test.py TestQueue
