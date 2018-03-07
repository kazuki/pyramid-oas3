from pyramid_oas3.jsonschema import _utils
from pyramid_oas3.jsonschema.exceptions import ValidationError


def ref(validator, ref, instance, schema, errors):
    scope, resolved = validator.resolver.resolve(ref)
    validator.resolver.push_scope(scope)
    try:
        return validator._descend(instance, resolved, errors)
    finally:
        validator.resolver.pop_scope()


def type(validator, types, instance, schema, errors):
    types = _utils.ensure_list(types)
    if not any(validator.is_type(instance, type, schema) for type in types):
        errors.append(ValidationError('{} is not of type {}'.format(
            instance, ', '.join(types))))


def items(validator, items, instance, schema, errors):
    if not validator.is_type(instance, 'array', schema):
        return

    if validator.is_type(items, 'object', schema):
        new_instance = [None] * len(instance)
        new_schema = items
        for index, item in enumerate(instance):
            new_instance[index], new_schema = validator._descend(
                item, items, errors, path=index)
    else:
        new_instance = [None] * min(len(instance), len(items))
        new_schema = list(items)
        for (index, item), subschema in zip(enumerate(instance), items):
            new_instance[index], new_schema[index] = validator._descend(
                item, subschema, errors, path=index, schema_path=index)
    return new_instance, new_schema


def properties(validator, properties, instance, schema, errors):
    if not validator.is_type(instance, 'object', schema):
        return

    new_schema = {}
    new_instance = dict(instance)
    for property, subschema in properties.items():
        prop_value = instance.get(property)
        if prop_value is None:
            filled, default_value = _try_get_default_value(
                validator, subschema)
            if filled:
                if isinstance(default_value, (dict, list)):
                    prop_value = default_value
                else:
                    # dict/list以外の場合はformatで型が変わっている可能性があるので
                    # default値を信頼してvalidationは実施しない
                    new_instance[property] = default_value
                    new_schema[property] = subschema
                    continue
            else:
                new_schema[property] = subschema
                continue
        new_instance[property], new_schema[property] = validator._descend(
            prop_value, subschema, errors, path=property, schema_path=property)
    return new_instance, new_schema


def _try_get_default_value(validator, subschema):
    if not validator._fill_by_default or not isinstance(subschema, dict):
        return False, None
    ref_value = subschema.get('$ref')
    if ref_value:
        scope, subschema = validator.resolver.resolve(ref_value)
        validator.resolver.push_scope(scope)
    try:
        if 'default' in subschema:
            return True, subschema['default']
        if 'allOf' in subschema:
            ret = []
            for s in subschema['allOf']:
                filled, value = _try_get_default_value(validator, s)
                if filled:
                    ret.append(value)
            if len(ret) == 1:
                return True, ret[0]
    finally:
        if ref_value:
            validator.resolver.pop_scope()
    return False, None


def format(validator, format, instance, schema, errors):
    if validator.format_checker is not None:
        try:
            instance = validator.format_checker.check(instance, format)
        except Exception as e:
            errors.append(ValidationError(str(e), cause=e.__cause__))
    return instance, format


def oneOf(validator, oneOf, instance, schema, errors):
    valids = []
    all_errors = []
    for index, subschema in enumerate(oneOf):
        erroff = len(errors)
        ret = validator._descend(
            instance, subschema, errors, schema_path=index)
        if len(errors) == erroff:
            valids.append((ret, subschema))
        else:
            all_errors.extend(errors[erroff:])
            del errors[erroff:]

    if len(valids) == 1:
        return valids[0][0][0], oneOf

    if not valids:
        errors.append(ValidationError(
            '{} is not valid under any of the given schemas'.format(instance),
            context=all_errors,
        ))
    elif len(valids) > 1:
        errors.append(ValidationError(
            '{} is valid under each of {}'.format(
                instance, ', '.join(repr(schema) for _, schema in valids))))


def allOf(validator, allOf, instance, schema, errors):
    if not allOf:
        return
    ret = []
    for index, subschema in enumerate(allOf):
        tmp, _ = validator._descend(
            instance, subschema, errors, schema_path=index)
        ret.append(tmp)
    return _utils.merge_instances(ret), allOf


def anyOf(validator, anyOf, instance, schema, errors):
    valids, all_errors = [], []
    for index, subschema in enumerate(anyOf):
        erroff = len(errors)
        ret, _ = validator._descend(
            instance, subschema, errors, schema_path=index)
        if len(errors) == erroff:
            valids.append(ret)
        else:
            all_errors.extend(errors[erroff:])
            del errors[erroff:]

    if len(valids) > 0:
        return _utils.merge_instances(valids), anyOf

    errors.append(ValidationError(
        '{} is not valid under any of the given schemas'.format(instance),
        context=all_errors,
    ))


def required(validator, required, instance, schema, errors):
    if not validator.is_type(instance, 'object', schema):
        return
    for property in required:
        if property not in instance:
            errors.append(ValidationError(
                '{} is a required property'.format(property)))


def additionalItems(validator, aI, instance, schema, errors):
    if (not validator.is_type(instance, 'array', schema) or
            validator.is_type(schema.get('items', {}), 'object', schema)):
        return

    items_array = schema.get('items', [])
    if validator.is_type(aI, 'object', schema):
        new_instance = list(instance)
        for index, item in enumerate(
                instance[len(items_array):], start=len(items_array)):
            new_instance[index] = validator._descend(
                item, aI, errors, path=index)
    elif not aI and len(instance) > len(items_array):
        errors.append(ValidationError(
            'Additional items are not allowed ({} were unexpected)'.format(
                ', '.join([
                    str(x) for x in instance[len(items_array):]]))))


def additionalProperties(validator, aP, instance, schema, errors):
    if not validator.is_type(instance, 'object', schema):
        return

    extras = set()
    properties = schema.get("properties", {})
    patterns = schema.get("patternProperties", {})
    if patterns and isinstance(patterns, dict):
        patterns = validator._get_regex('|'.join(patterns))
    else:
        patterns = None
    for name in instance:
        if name not in properties:
            if patterns and patterns.search(name):
                continue
            extras.add(name)

    if validator.is_type(aP, 'object', schema):
        new_instance = dict(instance)
        for extra in extras:
            new_instance[extra], _ = validator._descend(
                instance[extra], aP, errors, path=extra)
        return new_instance, aP
    elif not aP and extras:
        if patterns:
            patterns = sorted(schema['patternProperties'])
            errors.append(ValidationError(
                '{} do not match any of the regexes: {}'.format(
                    ', '.join(map(repr, sorted(extras))),
                    ', '.join(map(repr, patterns)))))
        else:
            errors.append(ValidationError(
                'Additional properties are not allowed '
                '({} were unexpected)'.format(extras)))


def minItems(validator, minItems, instance, schema, errors):
    if (validator.is_type(instance, 'array', schema)
            and len(instance) < minItems):
        errors.append(ValidationError('{} is too short'.format(instance,)))


def maxItems(validator, maxItems, instance, schema, errors):
    if (validator.is_type(instance, 'array', schema)
            and len(instance) > maxItems):
        errors.append(ValidationError('{} is too long'.format(instance,)))


def minLength(validator, mL, instance, schema, errors):
    if (validator.is_type(instance, 'string', schema)
            and len(instance) < mL):
        errors.append(ValidationError('{} is too short'.format(instance,)))


def maxLength(validator, mL, instance, schema, errors):
    if (validator.is_type(instance, 'string', schema)
            and len(instance) > mL):
        errors.append(ValidationError('{} is too long'.format(instance,)))


def minimum(validator, minimum, instance, schema, errors):
    if not validator.is_type(instance, 'number', schema):
        return

    if schema.get('exclusiveMinimum', False):
        failed = instance <= minimum
        cmp = 'less than or equal to'
    else:
        failed = instance < minimum
        cmp = 'less than'
    if failed:
        errors.append(ValidationError(
            '{} is {} the minimum of {}'.format(instance, cmp, minimum)))


def maximum(validator, maximum, instance, schema, errors):
    if not validator.is_type(instance, 'number', schema):
        return

    if schema.get('exclusiveMaximum', False):
        failed = instance >= maximum
        cmp = 'greater than or equal to'
    else:
        failed = instance > maximum
        cmp = 'greater than'

    if failed:
        errors.append(ValidationError(
            '{} is {} the maximum of {}'.format(instance, cmp, maximum)))


def minProperties(validator, mP, instance, schema, errors):
    if validator.is_type(instance, 'object', schema) and len(instance) < mP:
        errors.append(ValidationError(
            '{} does not have enough properties'.format(instance)))


def maxProperties(validator, mP, instance, schema, errors):
    if validator.is_type(instance, 'object', schema) and len(instance) > mP:
        errors.append(ValidationError(
            '{} has too many properties'.format(instance)))


def enum(validator, enum, instance, schema, errors):
    if instance not in enum:
        errors.append(ValidationError(
            '{} is not one of {}'.format(instance, enum)))


def uniqueItems(validator, uI, instance, schema, errors):
    if (uI and validator.is_type(instance, 'array', schema) and
            not _utils.is_uniq(instance)):
        errors.append(ValidationError(
            '{} has non-unique elements'.format(instance)))


def not_(validator, not_, instance, schema, errors):
    tmp_errors = []
    validator._descend(instance, not_, tmp_errors)
    if len(tmp_errors) != 0:
        return
    errors.append(ValidationError(
        '{} is not allowed for {}'.format(not_, instance)))


def dependencies(validator, deps, instance, schema, errors):
    raise NotImplementedError


def multipleOf(validator, mO, instance, schema, errors):
    if not validator.is_type(instance, 'number', schema):
        return
    if isinstance(mO, float):
        quotient = instance / mO
        failed = int(quotient) != quotient
    else:
        failed = instance % mO
    if failed:
        errors.append(ValidationError(
            '{} is not a multiple of {}'.format(instance, mO)))


def pattern(validator, pattern, instance, schema, errors):
    if (validator.is_type(instance, 'string', schema) and
            not validator._get_regex(pattern).search(instance)):
        errors.append(ValidationError(
            '{} does not match {}'.format(instance, pattern)))


def patternProperties(validator, pP, instance, schema, errors):
    if not validator.is_type(instance, 'object', schema):
        return
    new_instance = dict(instance)
    for pattern, subschema in pP.items():
        x = validator._get_regex(pattern)
        for k, v in instance.items():
            if x.search(k):
                new_instance[k] = validator._descend(
                    v, subschema, errors, path=k, schema_path=pattern)
    return new_instance, pP
