import os

path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'test'))
os.environ['GROW_STATIC_SERVER_POD_ROOT'] = path

from .main import app
import unittest
import webtest


class TestEndpoints(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = webtest.TestApp(app)

    def test_root(self):
        resp = self.app.get('/')
        self.assertEqual(200, resp.status_int)
        self.assertIn('Hello World', resp.body.decode())


if __name__ == '__main__':
    unittest.main()
