# -*- coding: utf-8 -*-
from urllib.parse import parse_qsl


def _is_primitive_type(type_name):
    return (
        type_name == 'string' or
        type_name == 'integer' or
        type_name == 'number' or
        type_name == 'boolean')


def _convert_style(style, explode, typ, value):
    if _is_primitive_type(typ):
        typ = 'string'
    mapping = {
        ('simple', 'string'): 0,
        ('simple', 'array'): 1,
        ('simple', 'object', True): 2,
        ('simple', 'object', False): 3,
        ('form', 'string'): 0,
        ('form', 'array', True): 0,
        ('form', 'array', False): 1,
        ('form', 'object', False): 3,
    }
    method = mapping.get((style, typ, explode))
    if method is None:
        method = mapping.get((style, typ))
        if method is None:
            raise NotImplementedError  # pragma: no cover
    if method == 0:
        return value
    elif method == 1:
        return value.split(',')
    elif method == 2:
        tmp = value.split(',')
        value = {}
        for t in tmp:
            k, v = parse_qsl(
                t, keep_blank_values=True, strict_parsing=True)[0]
            value[k] = v
        return value
    elif method == 3:
        tmp = value.split(',')
        value = {}
        for i in range(0, len(tmp), 2):
            value[tmp[i]] = tmp[i + 1]
        return value
    raise NotImplementedError('style={}, explode={}, type={}'.format(
        style, explode, typ))  # pragma: no cover


def _convert_type(schema, value, default_type='object'):
    typ = schema.get('type', default_type)
    fmt = schema.get('format')
    if typ == 'string':
        return value
    elif typ == 'boolean':
        value = value.lower()
        if value == 'true':
            return True
        elif value == 'false':
            return False
        else:
            raise ValueError('invalid value')
    elif typ == 'integer':
        value = int(value)
        if fmt is None:
            return value
        elif fmt == 'int32':
            rang = (-2**31, 2**31 - 1)
        elif fmt == 'int64':
            rang = (-2**63, 2**63 - 1)
        else:
            raise ValueError('invalid integer format')  # pragma: no cover
        if value < rang[0] or value > rang[1]:
            raise ValueError('out of range')
        return value
    elif typ == 'number':
        return float(value)
    elif typ == 'object':
        props = schema.get('properties', {})
        for pn, ps in props.items():
            if pn in value:
                value[pn] = _convert_type(ps, value[pn])
        aprops = schema.get('additionalProperties', True)
        if isinstance(aprops, dict):
            others = set(value.keys()) - set(props.keys())
            for k in others:
                value[k] = _convert_type(aprops, value[k])
        return value
    elif typ == 'array':
        item_schema = schema['items']
        if isinstance(item_schema, dict):
            for i in range(len(value)):
                value[i] = _convert_type(item_schema, value[i])
        else:
            raise ValueError('array items is must be dict')  # pragma: no cover
        return value
    else:
        raise ValueError('invalid type')  # pragma: no cover
