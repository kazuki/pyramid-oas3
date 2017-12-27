# -*- coding: utf-8 -*-
import json
from urllib.parse import parse_qs, urlparse

import pyramid
from pyramid.httpexceptions import (
    HTTPBadRequest, HTTPNotAcceptable,
    HTTPUnauthorized, HTTPInternalServerError, HTTPUnprocessableEntity)

from pyramid_oas3.jsonschema import OAS3Validator, Resolver
from pyramid_oas3.resolve import resolve_refs
from pyramid_oas3.types import _convert_type, _convert_style


MIME_JSON = 'application/json'


def includeme(config):
    config.add_tween(
        "pyramid_oas3.validation_tween_factory",
        under=pyramid.tweens.EXCVIEW
    )


def validation_tween_factory(handler, registry):
    from pyramid.interfaces import IRoutesMapper
    settings = {
        k[13:]: v
        for k, v in registry.settings.items()
        if k.startswith('pyramid_oas3.')}
    validate_response = settings.get('validate_response', False)
    fill_default = settings.get('fill_by_default', False)
    raise_422 = settings.get('raise_422', False)
    schema = settings['schema']
    resolver = Resolver('', schema)
    default_security = schema.get('security', None)
    route_mapper = registry.queryUtility(IRoutesMapper)
    prefixes = list(set([
        urlparse(server['url']).path.rstrip('/')
        for server in schema.get('servers', [])]))
    if not prefixes:
        prefixes = ['/']

    # 検証を簡単にするためにパラメータの $ref をすべて解決する。
    paths = schema['paths']
    for path, path_item in paths.items():
        for method, op_obj in path_item.items():
            if method not in ('get', 'put', 'post', 'delete', 'options',
                              'head', 'patch', 'trace'):
                continue
            params = op_obj.get('parameters')
            if params:
                resolve_refs(params, resolver)

    def Validator(schema):
        return OAS3Validator(
            schema, resolver=resolver, fill_by_default=fill_default)

    def get_operation_object(path, method):
        for prefix in prefixes:
            if not path.startswith(prefix):
                continue
            path_item = paths.get(path[len(prefix):])
            if path_item:
                return path_item.get(method.lower())
        return None

    def validator_tween(request):
        route_info = route_mapper(request)
        route = route_info.get('route', None)
        if not route:  # pragma: no cover
            return handler(request)
        op_obj = get_operation_object(route.path, request.method)
        if not op_obj:  # pragma: no cover
            return handler(request)

        _check_security(default_security, request, op_obj)
        try:
            params, body = _validate_and_parse(
                Validator, request, route_info.get('match', {}), op_obj)
        except HTTPBadRequest as e:
            if raise_422:
                raise HTTPUnprocessableEntity(str(e)) from e
            raise

        def oas3_data(_):
            return params

        def oas3_body(_):
            return body

        request.set_property(oas3_data)
        request.set_property(oas3_body)
        response = handler(request)

        if validate_response:
            responses_obj = op_obj['responses']
            res_obj = responses_obj.get(
                str(response.status_code), responses_obj.get('default'))
            if res_obj is None:
                raise HTTPInternalServerError('invalid response status code')
            content_prop = res_obj.get('content')
            has_content = content_prop and len(content_prop.keys()) > 0
            if not has_content and response.has_body:
                raise HTTPInternalServerError(
                    'invalid response: body must be empty')
            if response.content_type == MIME_JSON:
                res_schema = content_prop.get(MIME_JSON, {}).get('schema')
                if res_schema:
                    res_json = json.loads(response.body.decode('utf8'))
                    try:
                        _validate(Validator, res_schema, res_json)
                    except Exception as e:
                        raise HTTPInternalServerError(str(e))
        return response
    return validator_tween


def _check_security(default_security, request, op_obj):
    requires = op_obj.get('security', default_security)
    if not requires:
        return
    if request.authenticated_userid is None:
        raise HTTPUnauthorized


def _validate_and_parse(Validator, request, path_matches, op_obj):
    params, queries = {}, {}
    if request.query_string:
        try:
            queries = parse_qs(request.query_string,
                               keep_blank_values=True, strict_parsing=True)
        except Exception:
            raise HTTPBadRequest('cannot parse query string')
    for param_obj in op_obj.get('parameters', []):
        params.update(_validate_and_parse_param(
            Validator, request, param_obj, path_matches, queries))

    body = None
    reqbody = op_obj.get('requestBody')
    if reqbody:
        accept_types = set(reqbody.get('content', {}).keys())
        if not accept_types or request.content_type not in accept_types:
            raise HTTPNotAcceptable
        media_type_obj = reqbody.get('content', {}).get(MIME_JSON)
        if media_type_obj is not None:
            required = reqbody.get('required', False)
            body = request.body
            if required and not body:
                raise HTTPBadRequest('json body is required')
            body = json.loads(body.decode('utf8'))
            json_schema = media_type_obj.get('schema')
            if json_schema:
                body = _validate(Validator, json_schema, body)
    return params, body


def _validate_and_parse_param(
        Validator, request, param_obj, path_matches, queries):
    if param_obj.get('allowEmptyValue', False):
        raise NotImplementedError  # pragma: no cover
    in_, name, schema, value = (
        param_obj['in'], param_obj['name'], param_obj.get('schema'), None)
    style = param_obj.get(
        'style', 'form' if in_ in ('query', 'cookie') else 'simple')
    explode = param_obj.get('explode', True if style == 'form' else False)
    typ = schema['type'] if schema else 'object'

    if style in ('matrix', 'label', 'spaceDelimited', 'pipeDelimited'):
        raise NotImplementedError  # pragma: no cover

    if in_ == 'path':
        value = path_matches[name]  # always successful
    elif in_ == 'query':
        if style == 'form' and typ == 'object' and explode:
            raise NotImplementedError  # pragma: no cover
        if style == 'deepObject':
            value = {}
            for k, v in queries.items():
                if k.startswith(name + '[') and k[-1] == ']':
                    value[k[len(name)+1:-1]] = v[0]
            if not value:
                value = None
        else:
            if name in queries:
                value = queries[name]
                if not (style == 'form' and explode and typ == 'array'):
                    value = value[0]
    elif in_ == 'header' and name in request.headers:
        value = request.headers[name]
    elif in_ == 'cookie':  # pragma: no cover
        raise NotImplementedError
    if param_obj.get('required', False) and value is None:
        raise HTTPBadRequest(
            'required parameter "{}" is not found in {}'.format(name, in_))
    if value is None:
        return {}

    if not isinstance(value, dict):
        try:
            value = _convert_style(style, explode, typ, value)
        except Exception as e:
            raise HTTPBadRequest(
                'invalid style of "{}": {}'.format(name, e))
    if schema:
        try:
            value = _convert_type(schema, value)
        except Exception as e:
            raise HTTPBadRequest(
                'invalid value of "{}": {}'.format(name, e))
        value = _validate(Validator, schema, value)
    return {name: value}


def _validate(Validator, schema, instance):
    validator = Validator(schema)
    try:
        new_instance, _ = validator.validate(instance)
        return new_instance
    except Exception as e:
        raise HTTPBadRequest(str(e))
