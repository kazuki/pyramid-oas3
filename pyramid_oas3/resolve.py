def resolve_refs(node, resolver):
    if isinstance(node, list):
        for v in node:
            resolve_refs(v, resolver)
        return
    if not isinstance(node, dict):
        return
    ref_url = node.get('$ref', None)
    if ref_url is not None:
        node.clear()
        _, fragment = resolver.resolve(ref_url)
        resolve_refs(fragment, resolver)
        node.update(fragment)
        return
    for v in node.values():
        resolve_refs(v, resolver)
