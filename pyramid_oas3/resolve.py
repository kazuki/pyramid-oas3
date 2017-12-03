def resolve_refs(schema):
    cache = {}

    def _resolver(n):
        print('resolve: {}'.format(n))
        if not n.startswith('#/'):
            raise NotImplementedError(
                'cannot resolve external reference')  # pragma: no cover
        node = cache.get(n)
        if node:
            return node
        path = n[2:].split('/')
        node = schema
        for n in path:
            node = node[n]
        cache[n] = node
        return node
    while resolve_refs_(schema, _resolver) > 0:
        pass


def resolve_refs_(node, resolver):
    cnt = 0
    if isinstance(node, list):
        for v in node:
            cnt += resolve_refs_(v, resolver)
        return cnt
    if not isinstance(node, dict):
        return cnt
    resolved = None
    for k in node:
        if k == '$ref':
            if resolved is None:
                resolved = {}
            resolved.update(resolver(node[k]))
            cnt += 1
            continue
        v = node[k]
        if isinstance(v, (dict, list)):
            cnt += resolve_refs_(v, resolver)
    if resolved:
        del node['$ref']
        for k, v in resolved.items():
            if k not in node:
                node[k] = v
    return cnt
