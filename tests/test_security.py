import unittest
from nose2.tools import params

from .common import create_webapp


def _setup_auth(config):
    from pyramid.authorization import ACLAuthorizationPolicy
    config.set_authorization_policy(ACLAuthorizationPolicy())
    config.set_authentication_policy(DummyAuth(['hoge']))


class SecurityTests(unittest.TestCase):
    @params('test_security_1', 'test_security_2')
    def test_auth(self, schema_name):
        app = create_webapp(
            schema_name, [
                '/',
                '/auth_required',
            ], _setup_auth)
        app.get('/', status=200)
        app.get('/auth_required', status=401)
        app.get('/auth_required', headers={'X-Auth-Token': 'hoge'}, status=200)
        app.get('/auth_required', headers={'X-Auth-Token': 'foo'}, status=401)


class DummyAuth(object):
    def __init__(self, users, header_name='X-Auth-Token'):
        self._header_name = header_name
        self._users = set(users)

    def unauthenticated_userid(self, request):
        return request.headers.get(self._header_name)

    def authenticated_userid(self, request):
        uid = self.unauthenticated_userid(request)
        if uid in self._users:
            return uid
        return None
