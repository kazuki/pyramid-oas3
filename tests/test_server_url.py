import unittest

from .common import create_webapp


class ServerUrlTest(unittest.TestCase):
    def setUp(self):
        self.app = create_webapp(
            'test_server_url', [
                '/v1/test'
            ])

    def test(self):
        self.app.get('/v1/test', status=400)
