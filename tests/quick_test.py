import sys
import unittest

from webtest import TestApp

sys.path.append('./main')


class AppTest(unittest.TestCase):
  def setUp(self):
    # Wrap the app with WebTest's TestApp.
    from main import app
    self.testapp = TestApp(app)

  def test_index_handler(self):
    response = self.testapp.get('/')
    self.assertEqual(response.status_int, 200)

  def test_non_existent_handler(self):
    response = self.testapp.get('/not-there', status=404)
    self.assertEqual(response.status_int, 404)
