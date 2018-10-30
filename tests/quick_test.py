from webtest import TestApp
import unittest
from google.appengine.ext import testbed

import sys
sys.path.append('./main')



class AppTest(unittest.TestCase):
    def setUp(self):
        # Wrap the app with WebTest's TestApp.
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_memcache_stub()
        self.testbed.init_datastore_v3_stub()
        from main import app
        self.testapp = TestApp(app)


    def tearDown(self):
        self.testbed.deactivate()

    def testIndexHandler(self):
        response = self.testapp.get('/')
        self.assertEqual(response.status_int, 200)

    def testNonExistentHandler(self):
        response = self.testapp.get('/not-there', status=404)
        self.assertEqual(response.status_int, 404)
