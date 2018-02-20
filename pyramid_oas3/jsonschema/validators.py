import numbers
from functools import lru_cache
import re

from pyramid_oas3.jsonschema.exceptions import (
    UnknownTypeError, ValidationErrors)
from pyramid_oas3.jsonschema._resolvers import _Resolver
from pyramid_oas3.jsonschema import _validators, formats


class _Validator(object):
    def __init__(
            self, validators, format_checker, schema, resolver=None,
            fill_by_default=False):
        self._validators = validators
        self._schema = schema
        self._fill_by_default = fill_by_default
        self._types = {
            'array': list,
            'boolean': bool,
            'integer': int,
            'null': type(None),
            'number': numbers.Number,
            'object': dict,
            'string': str,
        }
        self.format_checker = format_checker
        self.resolver = resolver
        if resolver is None:
            self.resolver = _Resolver('', schema)
        self._get_regex = lru_cache(8192)(re.compile)

    def _validate(self, instance, schema, errors):
        scope = schema.get('id')
        if scope:
            self.resolver.push_scope(scope)
        try:
            ref = schema.get('$ref')
            if ref is not None:
                schema = {'$ref': ref}
            new_instance = instance
            new_schema = {}
            for k, v in schema.items():
                validator = self._validators.get(k)
                if validator is None:
                    continue
                if ref is None and self._is_nullable_and_skip_validation(
                        instance, schema):
                    continue
                ret = validator(self, v, instance, schema, errors)
                if ret is None:
                    tmp_instance, tmp_schema = instance, v
                else:
                    tmp_instance, tmp_schema = ret
                if id(tmp_instance) != id(instance):
                    new_instance = tmp_instance
                if k == '$ref':
                    new_schema.update(tmp_schema)
                else:
                    new_schema[k] = tmp_schema
            return new_instance, new_schema
        finally:
            if scope:
                self.resolver.pop_scope()

    def _descend(self, instance, schema, errors, path=None, schema_path=None):
        err_off = len(errors)
        ret = self._validate(instance, schema, errors)
        for error in errors[err_off:]:
            if path is not None:
                error.path.appendleft(path)
            if schema_path is not None:
                error.schema_path.appendleft(schema_path)
        return ret

    def validate(self, instance, **kwargs):
        errors = []
        new, schema = self._validate(instance, self._schema, errors, **kwargs)
        if errors:
            raise ValidationErrors(errors)
        return new, schema

    def is_valid(self, instance, **kwargs):
        try:
            self.validate(instance)
            return True
        except NotImplementedError as e:
            raise
        except Exception:
            return False

    def is_type(self, instance, typ, schema):
        pytype = self._types.get(typ)
        if pytype is None:
            raise UnknownTypeError(typ, instance, schema)
        if isinstance(instance, bool) and issubclass(int, pytype):
            return False
        return isinstance(instance, pytype)

    def _is_nullable_and_skip_validation(self, instance, schema):
        if instance is not None:
            return False
        return schema.get('nullable', False)


class Draft4(_Validator):
    def __init__(self, schema, format_checker=None, **kwargs):
        if format_checker is None:
            format_checker = formats.Draft4()
        super().__init__({
            '$ref': _validators.ref,
            'type': _validators.type,
            'items': _validators.items,
            'properties': _validators.properties,
            'required': _validators.required,
            'format': _validators.format,
            'oneOf': _validators.oneOf,
            'additionalItems': _validators.additionalItems,
            'additionalProperties': _validators.additionalProperties,
            'allOf': _validators.allOf,
            'anyOf': _validators.anyOf,
            'minItems': _validators.minItems,
            'maxItems': _validators.maxItems,
            'minProperties': _validators.minProperties,
            'maxProperties': _validators.maxProperties,
            'minLength': _validators.minLength,
            'maxLength': _validators.maxLength,
            'minimum': _validators.minimum,
            'maximum': _validators.maximum,
            'enum': _validators.enum,
            'uniqueItems': _validators.uniqueItems,
            'not': _validators.not_,
            'dependencies': _validators.dependencies,
            'multipleOf': _validators.multipleOf,
            'pattern': _validators.pattern,
            'patternProperties': _validators.patternProperties,
        }, format_checker, schema, **kwargs)


class Draft5(Draft4):
    def __init__(self, schema, format_checker=None, **kwargs):
        if format_checker is None:
            format_checker = formats.Draft5()
        super().__init__(schema, format_checker=format_checker, **kwargs)


class OAS3(Draft5):
    def __init__(self, schema, format_checker=None, **kwargs):
        if format_checker is None:
            format_checker = formats.OAS3()
        super().__init__(schema, format_checker=format_checker, **kwargs)
