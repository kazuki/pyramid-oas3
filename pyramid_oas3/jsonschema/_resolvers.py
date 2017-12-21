from collections.abc import MutableMapping, Sequence
from functools import lru_cache
from urllib.parse import urljoin, urlsplit, urlunsplit, unquote


class _Resolver(object):
    def __init__(self, base_uri, referrer):
        self._scopes_stack = [base_uri]
        self._store = _URIDict()
        self._store[base_uri] = referrer
        self._urljoin = lru_cache(64)(urljoin)
        self._remote_cache = lru_cache(8192)(self.resolve_from_url)

    @property
    def resolution_scope(self):
        return self._scopes_stack[-1]

    def push_scope(self, scope):
        self._scopes_stack.append(self._urljoin(self.resolution_scope, scope))

    def pop_scope(self):
        try:
            self._scopes_stack.pop()
        except IndexError:
            raise RuntimeError

    def resolve(self, ref):
        if self.resolution_scope:
            url = self._urljoin(self.resolution_scope, ref)
        else:
            url = ref
        return url, self._remote_cache(url)

    def resolve_from_url(self, url):
        url, fragment = _urldefrag(url)
        document = self._store.get(url)
        if document is None:
            raise NotImplementedError
        return self.resolve_fragment(document, fragment)

    def resolve_fragment(self, document, fragment):
        fragment = fragment.lstrip('/')
        parts = unquote(fragment).split('/') if fragment else []
        for part in parts:
            part = part.replace('~1', '/').replace('~0', '~')
            if isinstance(document, Sequence):
                try:
                    part = int(part)
                except ValueError:
                    pass
            try:
                document = document[part]
            except (TypeError, LookupError):
                raise RuntimeError(
                    "Unresolvable JSON pointer: {}".format(fragment)
                )
        return document


class _URIDict(MutableMapping):
    def _normalize(self, uri):
        return urlsplit(uri).geturl()

    def __init__(self, *args, **kwargs):
        self._store = dict()
        self._store.update(*args, **kwargs)

    def __getitem__(self, uri):
        return self._store[self._normalize(uri)]

    def __setitem__(self, uri, value):
        self._store[self._normalize(uri)] = value

    def __delitem__(self, uri):
        del self._store[self._normalize(uri)]

    def __iter__(self):
        return iter(self._store)

    def __len__(self):
        return len(self._store)


def _urldefrag(url):
    if '#' in url:
        s, n, p, q, frag = urlsplit(url)
        defrag = urlunsplit((s, n, p, q, ''))
    else:
        defrag = url
        frag = ''
    return defrag, frag
