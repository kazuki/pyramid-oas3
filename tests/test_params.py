import base64
import datetime
import pickle
import unittest
from urllib.parse import quote_plus, quote_from_bytes

from .common import create_webapp


class ParameterTests(unittest.TestCase):
    def setUp(self):
        self.app = create_webapp(
            'test_params', [
                '/test_type_convert',
                '/test_required',
                '/path_test/{d0}/{d1}/{d2}/{d3}/{d4}',
                '/test_invalid',
                '/test_fill',
            ], settings={'pyramid_oas3.fill_by_default': True})

    def _get(self, url, **kwargs):
        return pickle.loads(base64.b64decode(
            self.app.get(url, **kwargs).body))[0]

    def test_type_convert(self):
        expected = {
            'p0': 'v0',
            'p1': 1,
            'p2': 0,
            'p3': 2,
            'p4': 3.141,
            'p5': 2.718,
            'p6': b'\x00Hello\x00',
            'p8': True,
            'p9': datetime.date(2017, 12, 1),
            'p10': datetime.datetime(
                2017, 12, 1, 6, 12, 34, 56789, datetime.timezone.utc),
            'p11': {
                'num': 123,
                'str': 'hoge',
                'foo': 3.14
            },
            'p12': [False, True],
            'p13': [1, 2, 3],
            'p14': {
                'foo': 321,
                'bar': False,
            }
        }
        q = {k: str(v) for k, v in expected.items()}
        q['p6'] = base64.b64encode(expected['p6'])
        q['p9'] = expected['p9'].isoformat()
        q['p10'] = expected['p10'].isoformat()
        del q['p11']
        del q['p13']
        q.update({
            'p11[{}]'.format(quote_plus(k)): quote_plus(str(v))
            for k, v in expected['p11'].items()
        })
        q['p12'] = ','.join([str(v).lower() for v in expected['p12']])
        q['p14'] = ','.join([
            '{},{}'.format(k, v) for k, v in expected['p14'].items()])
        qs = []
        for k, v in q.items():
            qs.append('{}={}'.format(
                quote_plus(k),
                quote_plus(v) if isinstance(v, str) else quote_from_bytes(v)))
        for v in expected['p13']:
            qs.append('p13={}'.format(v))
        res = self._get('/test_type_convert?' + '&'.join(qs), status=200)
        self.assertEqual(res, expected)
        self.assertEqual(self._get('/test_type_convert', status=200), {})

    def test_required(self):
        res = self._get('/test_required?p1=A', status=200)
        self.assertEqual(res, {'p1': 'A'})
        res = self._get('/test_required?p0=A&p1=B', status=200)
        self.assertEqual(res, {'p0': 'A', 'p1': 'B'})
        self.app.get('/test_required?p0=A', status=400)

    def test_ignore_unknown_query(self):
        res = self._get('/test_required?p1=A&unknown=B', status=200)
        self.assertEqual(res, {'p1': 'A'})

    def test_path(self):
        path = '/path_test/foo/123/a,b,c/R,255,G,255,B,255/R=255,G=255,B=255'
        res = self._get(path, status=200)
        self.assertEqual(res, {
            'd0': 'foo',
            'd1': 123,
            'd2': ['a', 'b', 'c'],
            'd3': {'R': 255, 'G': 255, 'B': 255},
            'd4': {'R': 255, 'G': 255, 'B': 255},
        })

    def test_invalid_value(self):
        def _200(n, v):
            self.app.get('/test_invalid?{}={}'.format(
                n, quote_plus(v)), status=200)

        def _400(n, v):
            self.app.get('/test_invalid?{}={}'.format(
                n, quote_plus(v)), status=400)

        _200('p0', '2147483647')
        _200('p0', '-2147483648')
        _400('p0', '2147483648')
        _400('p0', '-2147483649')
        _400('p0', 'hoge')
        _200('p1', '9223372036854775807')
        _200('p1', '-9223372036854775808')
        _400('p1', '9223372036854775808')
        _400('p1', '-9223372036854775809')
        _400('p1', 'hoge')
        _200('p2', 'TRUE')
        _200('p2', 'FALSE')
        _200('p2', 'True')
        _200('p2', 'False')
        _400('p2', 'yes')
        _400('p2', 'no')
        _200('p3', '3.14')
        _200('p3', '314e-2')
        _200('p3', '0.314e+1')
        _200('p3', '1')
        _400('p3', 'hoge')
        _200('p4', '2017-12-01')
        _400('p4', '2017/12/01')
        _400('p4', 'hoge')
        _200('p5', '1997-07-16T19:20:30+01:00')
        _200('p5', '1997-07-16T19:20:30.45+01:00')
        _200('p5', '1997-07-16T19:20:30-01:00')
        _200('p5', '1997-07-16T19:20:30.45-01:00')
        _200('p5', '1997-07-16T19:20:30Z')
        _200('p5', '1997-07-16T19:20:30.45Z')
        _400('p5', '1997-07-16T19:20:30')
        _400('p5', '1997-07-16T19:20:30.45')
        _400('p5', '1997/07/16 19:20:30')
        _400('p6', 'R,255,G,255,B')
        _200('p7', 'foo')
        _400('p7', 'hoge')
        _400('&', '')  # query-string parse error

    def test_fill(self):
        expected = {
            'p0': 1, 'p1': 'hello', 'p2': datetime.date(2018, 1, 1),
            'p3': datetime.datetime(
                2018, 1, 2, 3, 4, 5, tzinfo=datetime.timezone.utc),
            'p4': False}
        actual = self._get('/test_fill', status=200)
        # TODO: PyYAMLがdate-timeのパース時にtzinfoを考慮しない
        actual.pop('p3')
        expected.pop('p3')
        self.assertEqual(actual, expected)
