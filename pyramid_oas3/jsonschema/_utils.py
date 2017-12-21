def ensure_list(thing):
    if not isinstance(thing, list):
        return [thing]
    return thing


def merge_instance(base, other):
    if isinstance(base, dict):
        output = dict(base)
        for k, v in other.items():
            if k not in output:
                output[k] = v
            else:
                output[k] = merge_instance(output[k], v)
    elif isinstance(base, list):
        output = list(base)
        for i, v in enumerate(other):
            output[i] = merge_instance(output[i], v)
    else:
        if not isinstance(other, str):
            return other
        return base
    return output


def merge_instances(others):
    if not isinstance(others, list):
        raise ValueError
    base = type(others[0])(others[0])
    for o in others[1:]:
        base = merge_instance(base, o)
    return base


def is_uniq(array):
    def unbool(e, true=object(), false=object()):
        if e is True:
            return true
        elif e is False:
            return false
        return e
    try:
        return len(set(unbool(a) for a in array)) == len(array)
    except Exception:
        seen = []
        for e in array:
            e = unbool(e)
            if e in seen:
                return False
            seen.append(e)
        return True
