from base64 import b64decode
import pickle
import unittest

from .common import create_webapp


class NullableTests(unittest.TestCase):
    def setUp(self):
        self.app = create_webapp(
            'test_nullable', [
                '/test_00',
            ], settings={'pyramid_oas3.fill_by_default': True})

    def _post(self, url, body, **kwargs):
        ret = self.app.post_json(url, params=body, **kwargs)
        if ret.status_code // 100 == 2:
            return pickle.loads(b64decode(ret.body))[1]

    def test_00(self):
        expected = {'int-array?': [None, 1, 2, 3]}
        self.assertEqual(expected, self._post('/test_00', {}, status=200))
        self.assertEqual(expected, self._post('/test_00', {'int-array?': None},
                                              status=200))
