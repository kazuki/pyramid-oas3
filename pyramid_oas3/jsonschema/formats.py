from pyramid_oas3.jsonschema import _formats
from pyramid_oas3.jsonschema.exceptions import FormatError


class FormatChecker(object):
    def __init__(self, formats):
        self._formats = formats

    def check(self, instance, format):
        checker = self._formats.get(format)
        if not checker:
            return instance
        try:
            return checker(instance)
        except Exception as e:
            raise FormatError('{} is not a {}'.format(
                instance, format)) from e


class Draft4(FormatChecker):
    def __init__(self):
        super().__init__({
            'date-time': _formats.date_time,
            'email': _formats.email,
            'hostname': _formats.hostname,
            'ipv4': _formats.ipv4,
            'ipv6': _formats.ipv6,
            'uri': _formats.uri,
        })


class Draft5(FormatChecker):
    def __init__(self):
        super().__init__({
            'date-time': _formats.date_time,
            'email': _formats.email,
            'hostname': _formats.hostname,
            'ipv4': _formats.ipv4,
            'ipv6': _formats.ipv6,
            'uri': _formats.uri,
            'uriref': _formats.uriref,
        })


class OAS3(FormatChecker):
    def __init__(self):
        super().__init__({
            'int32': _formats.int32,
            'int64': _formats.int64,
            'byte': _formats.byte,
            'date': _formats.date,
            'date-time': _formats.date_time,
            'email': _formats.email,
            'hostname': _formats.hostname,
            'ipv4': _formats.ipv4,
            'ipv6': _formats.ipv6,
            'uri': _formats.uri,
            'uriref': _formats.uriref,
        })
