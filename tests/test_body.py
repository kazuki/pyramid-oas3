from base64 import b64decode
from datetime import date, datetime, timezone
import pickle
import unittest

from .common import create_webapp


class BodyTests(unittest.TestCase):
    def setUp(self):
        self.app = create_webapp(
            'test_body', [
                '/test_simple',
                '/test_fill_default',
                '/test_fill_default_oneOf',
                '/test_binary',
                '/test_fill_ref',
                '/test_fill_dict_ref',
            ], settings={'pyramid_oas3.fill_by_default': True})

    def _post(self, url, body, **kwargs):
        ret = self.app.post_json(url, params=body, **kwargs)
        if ret.status_code // 100 == 2:
            return pickle.loads(b64decode(ret.body))[1]

    def test_simple(self):
        now = datetime.now(timezone.utc)
        m = {'foo': 'bar', 'hoge': 123, 'created': now.isoformat()}
        m2 = dict(m)
        m2['created'] = now
        self.assertEqual(m2, self._post('/test_simple', m, status=200))
        self._post('/test_simple', {'foo': 'bar'}, status=400)
        self._post('/test_simple', {'foo': 'hoge', 'hoge': 123}, status=400)
        self._post('/test_simple', {'foo': 'bar', 'hoge': 'piyo'}, status=400)
        self._post('/test_simple', {
            'foo': 'bar', 'hoge': 123,
            'created': '2017-12-21 00:00:00+00:00'}, status=400)
        self.app.post('/test_simple', status=406)
        self.app.post(
            '/test_simple', content_type='application/json', status=400)

    def test_fill_default(self):
        m = {'foo': 'bar', 'hoge': 123, 'created': date(2017, 7, 26)}
        m2 = {'foo': 'bar', 'hoge': 123, 'created': date(2017, 7, 26),
              'nested': {'hoge': 'piyo', 'foo': 3.14}}
        self.assertEqual(m, self._post('/test_fill_default', {}, status=200))
        self.assertEqual(m2, self._post(
            '/test_fill_default', {'nested': {}}, status=200))

    def test_fill_default_oneOf(self):
        m0, m1 = {'hoge': 'x'}, {'hoge': 'x', 'created': date(2017, 7, 26)}
        m2, m3 = {'foo': 123}, {'foo': 123, 'bar': 3.14}
        self.assertEqual(m1, self._post(
            '/test_fill_default_oneOf', m0, status=200))
        self.assertEqual(m3, self._post(
            '/test_fill_default_oneOf', m2, status=200))

    def test_binary(self):
        self._post('/test_binary', {'foo': 'bar'}, status=406)
        self.app.post('/test_binary', upload_files=[
            ('hoge', 'dummy', b'hello world')
        ])

    def test_fill_ref(self):
        m0, m1 = {}, {'foo': 'bar', 'hoge': 'hoge-default-value'}
        self.assertEqual(m1, self._post(
            '/test_fill_ref', m0, status=200))

    def test_fill_dict_ref(self):
        tmp = {'foo': 'bar', 'hoge': 'hoge-default-value'}
        m0, m1 = {'required': {}}, {'required': tmp, 'filled': tmp}
        self.assertEqual(m1, self._post(
            '/test_fill_dict_ref', m0, status=200))
