from collections import deque
import pprint
import textwrap


def _dedent(x):
    return textwrap.dedent(x).strip('\n')


def _pformat_and_indent(obj, times=1):
    return textwrap.indent(pprint.pformat(obj), ' ' * (4 * times))


def _format_as_index(indices):
    if not indices:
        return ''
    return '[{}]'.format(']['.join(repr(index) for index in indices))


_unset = object()


class UnknownTypeError(Exception):
    def __init__(self, type, instance, schema):
        self.type = type
        self.instance = instance
        self.schema = schema

    def __str__(self):
        return _dedent('''
        Unknown type "{}" for validator with schema:
        {}

        While checking instance:
        {}''').format(
            self.type,
            _pformat_and_indent(self.schema),
            _pformat_and_indent(self.instance))


class _Error(Exception):
    def __init__(
            self, message, validator=_unset, path=(), cause=None, context=(),
            validator_value=_unset, instance=_unset, schema=_unset,
            schema_path=(), parent=None):
        self.message = message
        self.path = self.relative_path = deque(path)
        self.schema_path = self.relative_schema_path = deque(schema_path)
        self.context = list(context)
        self.__cause__ = cause
        self.validator = validator
        self.validator_value = validator_value
        self.instance = instance
        self.schema = schema
        self.parent = parent

        for error in context:
            error.parent = self

    def __repr__(self):
        return "<%s: %r>" % (self.__class__.__name__, self.message)

    def __str__(self):
        essential_for_verbose = (
            self.validator, self.validator_value, self.instance, self.schema,
        )
        if any(m is _unset for m in essential_for_verbose):
            return self.message

        return self.message + _dedent(
            '''
            Failed validating %r in %s%s:
            %s

            On %s%s:
            %s
            ''').format(
                self.validator,
                self._word_for_schema_in_error_message,
                _format_as_index(list(self.relative_schema_path)[:-1]),
                _pformat_and_indent(self.schema),
                self._word_for_instance_in_error_message,
                _format_as_index(self.relative_path),
                _pformat_and_indent(self.instance),
            )

    @property
    def absolute_path(self):
        parent = self.parent
        if parent is None:
            return self.relative_path

        path = deque(self.relative_path)
        path.extendleft(reversed(parent.absolute_path))
        return path

    @property
    def absolute_schema_path(self):
        parent = self.parent
        if parent is None:
            return self.relative_schema_path

        path = deque(self.relative_schema_path)
        path.extendleft(reversed(parent.absolute_schema_path))
        return path


class ValidationError(_Error):
    _word_for_schema_in_error_message = "schema"
    _word_for_instance_in_error_message = "instance"


class SchemaError(_Error):
    _word_for_schema_in_error_message = "metaschema"
    _word_for_instance_in_error_message = "schema"


class RefResolutionError(Exception):
    pass


class FormatError(Exception):
    def __init__(self, message, cause=None):
        self.message = message
        if cause:
            self.__cause__ = cause

    def __str__(self):
        return self.message


class StyleError(FormatError):
    pass


class ValidationErrors(Exception):
    def __init__(self, errors):
        if isinstance(errors, Exception):
            errors = [errors]
        self.errors = errors

    def __str__(self):
        return 'found {} validation error(s)\n{}'.format(
            len(self.errors), '\n\n'.join([str(e) for e in self.errors]))
