import json
import unittest

from nose2.tools import params
from pyramid.response import Response

from .common import create_webapp


class ResponseTests(unittest.TestCase):
    def setUp(self):
        def test(request):
            return Response(json.dumps(request.json_body),
                            content_type='application/json; charset=utf8')

        def empty(request):
            return Response(status=204)

        def plaintext(request):
            return Response('hello world', status=200,
                            content_type='text/plain; charset=utf8')

        def setup(config):
            entries = [
                ('/test_simple', test),
                ('/test_default', test),
                ('/test_not_json', plaintext),
                ('/test_empty', empty),
                ('/test_empty2', plaintext),
                ('/test_invalid_status_code', empty),
            ]
            for i, (path, handler) in enumerate(entries):
                name = 'test{}'.format(i)
                config.add_route(name, path)
                config.add_view(handler, route_name=name)

        self.app = create_webapp('test_response', [], func=setup, settings={
            'pyramid_oas3.validate_response': True
        })

    def _post(self, url, body, **kwargs):
        self.app.post_json(url, params=body, **kwargs)

    @params('simple', 'default')
    def test_simple(self, typ):
        path = '/test_{}'.format(typ)
        self._post(path, {'num': 123, 'str': 'hoge'}, status=200)
        self._post(path, {'num': 123, 'str': 'test'}, status=500)
        self._post(path, {'num': 'test'}, status=500)

    def test_not_json(self):
        self.app.get('/test_not_json', status=200)

    def test_empty(self):
        self.app.get('/test_empty', status=204)
        self.app.get('/test_empty2', status=500)

    def test_invalid_status_code(self):
        self.app.get('/test_invalid_status_code', status=500)
