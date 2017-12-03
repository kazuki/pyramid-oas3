from base64 import b64decode
import pickle
import unittest

from common import create_webapp


class BodyTests(unittest.TestCase):
    def setUp(self):
        self.app = create_webapp(
            'test_body', [
                '/test_simple',
                '/test_binary',
            ])

    def _post(self, url, body, **kwargs):
        ret = self.app.post_json(url, params=body, **kwargs)
        if ret.status_code // 100 == 2:
            return pickle.loads(b64decode(ret.body))[1]

    def test_simple(self):
        m = {'foo': 'bar', 'hoge': 123}
        self.assertEqual(m, self._post('/test_simple', m, status=200))
        self._post('/test_simple', {'foo': 'bar'}, status=400)
        self._post('/test_simple', {'foo': 'hoge', 'hoge': 123}, status=400)
        self._post('/test_simple', {'foo': 'bar', 'hoge': 'piyo'}, status=400)
        self.app.post('/test_simple', status=406)
        self.app.post(
            '/test_simple', content_type='application/json', status=400)

    def test_binary(self):
        self._post('/test_binary', {'foo': 'bar'}, status=406)
        self.app.post('/test_binary', upload_files=[
            ('hoge', 'dummy', b'hello world')
        ])
