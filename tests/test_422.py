import unittest

from common import create_webapp


class Raise422Tests(unittest.TestCase):
    def setUp(self):
        self.app = create_webapp(
            'test_body', [
                '/test_simple',
            ], settings={'pyramid_oas3.raise_422': True})

    def _post(self, url, body, **kwargs):
        self.app.post_json(url, params=body, **kwargs)

    def test(self):
        self._post('/test_simple', {'foo': 'bar'}, status=422)
