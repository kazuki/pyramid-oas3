from base64 import b64encode
import os
import pickle

from pyramid.config import Configurator
from pyramid.response import Response
from webtest import TestApp


def create_webapp(schema_name, patterns, func=None, settings=None):
    import yaml
    temp = settings
    settings = {
        'pyramid.includes': 'pyramid_oas3',
        'pyramid_oas3.schema': yaml.load(open(os.path.join(
            os.path.dirname(__file__), '{}.yaml'.format(schema_name))).read()),
    }
    if temp:
        settings.update(temp)

    def test(request):
        return Response(b64encode(pickle.dumps(
            (request.oas3_data, request.oas3_body))))

    with Configurator(settings=settings) as config:
        for i, p in enumerate(patterns):
            name = 'test{}'.format(i)
            config.add_route(name, p)
            config.add_view(test, route_name=name)
        if func:
            func(config)
        return TestApp(config.make_wsgi_app())
