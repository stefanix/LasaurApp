
import os
import time
import random
import unittest

import web
import lasersaur


thislocation = os.path.dirname(os.path.realpath(__file__))


def setUpModule():
    web.start()
    lasersaur.local()

def tearDownModule():
    web.stop()


class TestJobs(unittest.TestCase):

    def testLoad(self):
        jobfile = os.path.join(thislocation,'testjobs','full-bed.svg')
        # jobfile = os.path.join(thislocation,'testjobs','key.svg')
        job = lasersaur.open_file(jobfile)
        if 'vector' in job:
            job['vector']['passes'] = [{
                    "paths":[0],
                    "feedrate":2000,
                    "intensity":53
                }]
        jobname = lasersaur.load(job)
        self.assertIn(jobname, lasersaur.listing())
        lasersaur.run(jobname, progress=True)


if __name__ == '__main__':
    unittest.main()

    # for partial test run like this:
    # python test.py Class
    # E.g:
    # python test.py TestQueue
