from contextlib import contextmanager

import pymel.core as pm


PARENT_WORLD = object()


def set_namespace(namespace, start_at_root=False):
    if start_at_root:
        pm.namespace(set=':')
    try:
        pm.namespace(set=namespace)
    except RuntimeError as missing_namespace_error:
        check_name = namespace
        if not check_name.startswith(':'):
            check_name = ':{}'.format(check_name)
        current_ns = pm.namespaceInfo(currentNamespace=True)
        nested_ns = pm.listNamespaces(root=current_ns, recursive=True, internal=False)
        for ns in nested_ns:
            if ns.endswith(check_name):
                pm.namespace(set=ns)
                return ns
        all_ns = pm.listNamespaces(root=None, recursive=True, internal=False)
        for ns in all_ns:
            if ns.endswith(check_name):
                pm.namespace(set=ns)
                return ns
        raise missing_namespace_error


@contextmanager
def preserve_namespace(on_enter_namespace=None):
    current_namespace = pm.namespaceInfo(currentNamespace=True)
    if on_enter_namespace:
        set_namespace(on_enter_namespace)
    try:
        yield
    finally:
        set_namespace(current_namespace)


def move_node_to_namespace(node, namespace):
    node.rename('{0}:{1}'.format(namespace, node))


def move_nodes_to_namespace(nodes, namespace):
    [move_node_to_namespace(node, namespace) for node in nodes]


def add_namespace_to_root(namespace):
    with preserve_namespace(':'):
        try:
            ns = pm.namespace(add=namespace)
        except RuntimeError:
            # if namespace already exists return it
            ns = namespace
    return ns


def rename_preserve_namespace(node, new_name):
    ns = node.namespace()
    new_new_name = ns + new_name
    node.rename(new_new_name)
    return new_new_name


def duplicate_to_namespace(nodes, dup_namespace=None, dup_parent=None):
    dup_namespace = dup_namespace or pm.namespaceInfo(currentNamespace=True)
    with preserve_namespace(dup_namespace):
        dup_nodes = pm.duplicate(nodes)
    if dup_parent:
        try:
            len(nodes)
        except TypeError:
            nodes = [nodes]
        for node, dup_node in zip(nodes, dup_nodes):
            if dup_parent is PARENT_WORLD:
                dup_node.setParent(world=True)
            else:
                dup_node.setParent(dup_parent)
            rename_preserve_namespace(dup_node, node.nodeName())
    return dup_nodes


def get_namespace_as_pynode(namespace_string):
    namespace = None
    try:
        namespace = pm.Namespace(namespace_string)
    except ValueError:
        for ns in pm.listNamespaces(recursive=True):
            if ns.endswith(namespace_string):
                namespace = ns
                break
    if namespace:
        return namespace
    raise ValueError("Namespace '{}' does not exist.".format(namespace_string))
