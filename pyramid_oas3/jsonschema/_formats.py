from base64 import b64decode
import datetime
from ipaddress import IPv4Address, IPv6Address
import re

import rfc3987


RE_HOSTNAME = re.compile(r'^[A-Za-z0-9][A-Za-z0-9\.\-]{1,255}$')


def int32(v):
    if isinstance(v, int) and (v < -2**31 or v > 2**31 - 1):
        raise ValueError('{} is out of int32 range'.format(v))
    return v


def int64(v):
    if isinstance(v, int) and (v < -2**63 or v > 2**63 - 1):
        raise ValueError('{} is out of int64 range'.format(v))
    return v


def byte(v):
    if isinstance(v, str):
        return b64decode(v)
    return v


def date(v):
    if not isinstance(v, str):
        return v
    return datetime.datetime.strptime(v, '%Y-%m-%d').date()


def date_time(v):
    if not isinstance(v, str):
        return v

    v = v.replace(':', '')
    if v[-1] == 'Z':
        v = v[0:-1] + '+0000'
    if '.' in v:
        tries = ['%Y-%m-%dT%H%M%S.%f%z', '%Y-%m-%dT%H%M%S.%f']
    else:
        tries = ['%Y-%m-%dT%H%M%S%z', '%Y-%m-%dT%H%M%S']
    for pattern in tries:
        try:
            ret = datetime.datetime.strptime(v, pattern)
            if ret.tzinfo is None:
                raise ValueError(
                    'invalid date-time format. required timezone info')
            return ret
        except Exception:
            pass
    raise ValueError('invalid date-time format')


def email(v):
    if isinstance(v, str):
        # TODO(kazuki): more strict
        if '@' not in v:
            raise ValueError('invalid email format')
    return v


def hostname(v):
    if isinstance(v, str):
        # TODO(kazuki): more strict
        if not RE_HOSTNAME.match(v):
            raise ValueError('invalid hostname format')
    return v


def ipv4(v):
    if not isinstance(v, str):
        return v
    return IPv4Address(v)


def ipv6(v):
    if not isinstance(v, str):
        return v
    return IPv6Address(v)


def uri(v):
    if isinstance(v, str):
        rfc3987.parse(v, rule='URI')
    return v


def uriref(v):
    if isinstance(v, str):
        rfc3987.parse(v, rule='URI_reference')
    return v
