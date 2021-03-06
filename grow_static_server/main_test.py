import os

path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'test'))
os.environ['GROW_STATIC_SERVER_POD_ROOT'] = path

from .main import app
from .main import StaticHandler
import unittest
import webtest


class TestEndpoints(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = webtest.TestApp(app)

    def test(self):
        # Test root.
        resp = self.app.get('/')
        self.assertEqual(200, resp.status_int)
        etag = StaticHandler.get_etag('test/build/index.html')
        self.assertEqual(etag, resp.headers['ETag'])
        self.assertIn('Hello World', resp.body.decode())
        self.assertEqual('Bar', resp.headers['X-Foo'])

        resp = self.app.get('/', headers={'If-None-Match': etag})
        self.assertEqual(304, resp.status_int)

        # Test 404.
        resp = self.app.get('/does-not-exist/', status=404)
        self.assertEqual(404, resp.status_int)

        # Test trailing slash redirect.
        resp = self.app.get('/test')
        self.assertEqual(302, resp.status_int)
        self.assertEqual('https://example.com/', resp.headers['Location'])

        # Test vanity URLs.
        resp = self.app.get('/test/foo')
        self.assertEqual(302, resp.status_int)
        self.assertEqual('https://example.com/foo', resp.headers['Location'])

        # Test trailing slash redirect.
        resp = self.app.get('/subfolder')
        self.assertEqual(302, resp.status_int)
        self.assertEqual('http://localhost/subfolder/', resp.headers['Location'])

        # Test permanent redirects.
        resp = self.app.get('/foo')
        self.assertEqual(301, resp.status_int)
        self.assertEqual('http://localhost/bar', resp.headers['Location'])


if __name__ == '__main__':
    unittest.main()
