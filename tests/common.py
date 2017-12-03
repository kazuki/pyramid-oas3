from base64 import b64encode
import os
import pickle

from pyramid.config import Configurator
from pyramid.response import Response
from webtest import TestApp


def create_webapp(schema_name, patterns):
    import yaml
    settings = {
        'pyramid.includes': 'pyramid_oas3',
        'pyramid_oas3.schema': yaml.load(open(os.path.join(
            os.path.dirname(__file__), '{}.yaml'.format(schema_name))).read()),
    }

    def test(request):
        return Response(b64encode(pickle.dumps(request.oas3_data)))

    with Configurator(settings=settings) as config:
        for i, p in enumerate(patterns):
            name = 'test{}'.format(i)
            config.add_route(name, p)
            config.add_view(test, route_name=name)
        return TestApp(config.make_wsgi_app())
