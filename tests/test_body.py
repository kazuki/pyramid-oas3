from base64 import b64decode
from datetime import date, datetime, timezone
import pickle
import unittest

from pyramid_oas3 import ValidationErrors
from .common import create_webapp, get_last_exception


class BodyTests(unittest.TestCase):
    def setUp(self):
        self.app = create_webapp(
            'test_body', [
                '/test_simple',
                '/test_array',
                '/test_fill_default',
                '/test_fill_default_oneOf',
                '/test_binary',
                '/test_fill_ref',
                '/test_fill_dict_ref',
                '/test_oneOf_error',
                '/test_not0',
                '/test_not1',
                '/test_content_type',
                '/test_content_type2',
                '/test_content_type3',
                '/test_empty0',
                '/test_empty1',
                '/test_empty2',
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
        self.app.post('/test_simple', status=400)
        self.app.post(
            '/test_simple', content_type='application/json', status=400)

    def test_array(self):
        self._post('/test_array', {'foo': 'bar'}, status=400)
        self._post('/test_array', 'str', status=400)
        self._post('/test_array', [], status=200)
        self._post('/test_array', [1, 2, 3], status=200)
        self._post('/test_array', ['str'], status=400)

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
        m0, m1 = {}, {
            'foo': 'bar', 'hoge': 'hoge-default-value',
            'hoge2': 'hoge2-value'}
        self.assertEqual(m1, self._post(
            '/test_fill_ref', m0, status=200))

    def test_fill_dict_ref(self):
        tmp = {'foo': 'bar', 'hoge': 'hoge-default-value'}
        m0, m1 = {'required': {}}, {'required': tmp, 'filled': tmp}
        self.assertEqual(m1, self._post(
            '/test_fill_dict_ref', m0, status=200))

    def test_oneOf_error(self):
        self._post('/test_oneOf_error', 123, status=400)
        exc = get_last_exception()
        self.assertIsInstance(exc, ValidationErrors)
        self.assertIsInstance(exc.errors, list)
        self.assertEqual(len(exc.errors), 1)
        messages = sorted([str(e) for e in exc.errors[0].context])
        self.assertIn('not of type array', messages[0])
        self.assertIn('not of type object', messages[1])

    def test_not(self):
        self._post('/test_not0', 123)
        self._post('/test_not0', 'hello', status=400)
        self._post('/test_not1', 'ok')
        self._post('/test_not1', 'hello', status=400)
        self._post('/test_not1', 123, status=400)
        self._post('/test_not1', {}, status=400)

    def test_content_type(self):
        self.app.post('/test_content_type', '{}',
                      [('Content-Type', 'application/json')], status=200)
        self.app.post('/test_content_type', 'ok',
                      [('Content-Type', 'text/plain')], status=200)
        self.app.post('/test_content_type', b'foo',
                      [('Content-Type', 'hoge/foo')], status=200)
        self.app.post('/test_content_type', b'bar',
                      [('Content-Type', 'hoge/bar')], status=200)
        self.app.post('/test_content_type', b'bar',
                      [('Content-Type', 'image/png')], status=406)
        self.app.post('/test_content_type2', b'PNG',
                      [('Content-Type', 'image/png')], status=200)
        self.app.post('/test_content_type3', b'PNG',
                      [('Content-Type', 'image/png')], status=200)

    def test_empty(self):
        self.app.post('/test_empty0', '{}',
                      [('Content-Type', 'application/json')], status=200)
        self.app.post('/test_empty1', '{}',
                      [('Content-Type', 'application/json')], status=200)
        self.app.post('/test_empty2', '{"hoge": "hello"}',
                      [('Content-Type', 'application/json')], status=200)
        self.app.post('/test_empty1', '', [], status=400)
        self.app.post('/test_empty2', '{}',
                      [('Content-Type', 'application/json')], status=400)
        self.app.post('/test_empty0', '', [], status=200)
