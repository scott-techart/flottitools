import pymel.core as pm

import flottitools.test as mayatest
import flottitools.utils.namespaceutils as namespaceutils


class TestMoveNodesToNamespace(mayatest.MayaTestCase):
    def test_move_one_node(self):
        pm.namespace(set=':')
        ns = self.create_namespace(':foo:bar')
        test_cube = self.create_cube()
        self.assertEqual('', test_cube.namespace())
        namespaceutils.move_node_to_namespace(test_cube, ns)
        self.assertEqual(ns, test_cube.parentNamespace())

    def test_move_multiple_nodes(self):
        pm.namespace(set=':')
        test_cubes = [self.create_cube() for _ in range(5)]
        ns = self.create_namespace(':foo:bar')
        [self.assertEqual('', x.namespace()) for x in test_cubes]
        namespaceutils.move_nodes_to_namespace(test_cubes, ns)
        [self.assertEqual(ns, x.parentNamespace()) for x in test_cubes]

    def test_move_node_to_root_ns(self):
        pm.namespace(set=':')
        ns = self.create_namespace(':foo:bar')
        test_cube = self.create_cube()
        test_cube.rename(':foo:bar:pCube1')
        self.assertEqual('foo:bar:', test_cube.namespace())
        namespaceutils.move_node_to_namespace(test_cube, ':')
        self.assertEqual('', test_cube.namespace())


class TestPreserveNamespace(mayatest.MayaTestCase):
    def test_return_to_root(self):
        pm.namespace(set=':')
        ns = self.create_namespace(':foo')
        with namespaceutils.preserve_namespace():
            pm.namespace(set=':foo')
            test_cube = self.create_cube()
        self.assertEqual(ns, test_cube.parentNamespace())
        self.assertEqual(':', self.pm.namespaceInfo(currentNamespace=True))

    def test_return_to_not_root(self):
        pm.namespace(set=':')
        ns = self.create_namespace(':foo')
        ns2 = self.create_namespace(':bar')
        pm.namespace(set=ns2)
        with namespaceutils.preserve_namespace(ns):
            test_cube = self.create_cube()
        self.assertEqual(ns, test_cube.parentNamespace())
        self.assertEqual(ns2, self.pm.namespaceInfo(currentNamespace=True))

    def test_same_ns_as_current(self):
        pm.namespace(set=':')
        ns = self.create_namespace(':foo')
        pm.namespace(set=ns)
        with namespaceutils.preserve_namespace(ns):
            test_cube = self.create_cube()
        self.assertEqual(ns, test_cube.parentNamespace())
        self.assertEqual(ns, self.pm.namespaceInfo(currentNamespace=True))


class TestSetNamespace(mayatest.MayaTestCase):
    def test_set_from_root_with_colon_prefix(self):
        pm.namespace(set=':')
        ns = self.create_namespace(':foo')
        namespaceutils.set_namespace(':foo')
        current_ns = pm.namespaceInfo(currentNamespace=True)
        self.assertEqual(ns, current_ns)

    def test_set_from_root_without_colon_prefix(self):
        pm.namespace(set=':')
        ns = self.create_namespace(':foo')
        namespaceutils.set_namespace('foo')
        current_ns = pm.namespaceInfo(currentNamespace=True)
        self.assertEqual(ns, current_ns)

    def test_searches_all_namespaces_if_ns_not_in_current(self):
        pm.namespace(set=':')
        ns = self.create_namespace(':foo')
        ns2 = self.create_namespace(':bar')
        pm.namespace(set=ns2)
        namespaceutils.set_namespace('foo')
        current_ns = pm.namespaceInfo(currentNamespace=True)
        self.assertEqual(ns, current_ns)

    def test_if_multiple_matching_ns_take_first_nested_first(self):
        pm.namespace(set=':')
        ns_foo = self.create_namespace(':foo')
        ns_bar = self.create_namespace(':bar')
        ns_bar_foo = self.create_namespace(':bar:foo')
        ns_bar_foo_spam_foo = self.create_namespace(':bar:foo:spam:foo')
        pm.namespace(set=ns_bar)
        namespaceutils.set_namespace('foo')
        current_ns = pm.namespaceInfo(currentNamespace=True)
        self.assertEqual(ns_bar_foo, current_ns)

    def test_start_at_root_true(self):
        pm.namespace(set=':')
        ns_foo = self.create_namespace(':foo')
        ns_bar = self.create_namespace(':bar')
        ns_bar_foo = self.create_namespace(':bar:foo')
        ns_bar_foo_spam_foo = self.create_namespace(':bar:foo:spam:foo')
        pm.namespace(set=ns_bar)
        namespaceutils.set_namespace('foo', start_at_root=True)
        current_ns = pm.namespaceInfo(currentNamespace=True)
        self.assertEqual(ns_foo, current_ns)


class TestAddNamespaceToRoot(mayatest.MayaTestCase):
    def test_root_current_namespace(self):
        pm.namespace(set=':')
        ns = namespaceutils.add_namespace_to_root('foo')
        expected = [ns]
        result = pm.listNamespaces(recursive=True)
        self.assertListEqual(expected, result)

    def test_not_root_and_no_leading_colon(self):
        pm.namespace(set=':')
        ns_bar = self.create_namespace('bar')
        pm.namespace(set=':bar')
        ns = namespaceutils.add_namespace_to_root('foo')
        expected = [':bar', ':foo']
        result = [str(x) for x in pm.listNamespaces(recursive=True)]
        self.assertListEqual(expected, result)

    def test_not_root_with_leading_colon(self):
        pm.namespace(set=':')
        ns_bar = self.create_namespace('bar')
        pm.namespace(set=':bar')
        ns = namespaceutils.add_namespace_to_root(':foo')
        expected = [':bar', ':foo']
        result = [str(x) for x in pm.listNamespaces(recursive=True)]
        self.assertListEqual(expected, result)

    def test_noop_if_namespace_already_exists(self):
        pm.namespace(set=':')
        ns_foo = self.create_namespace('foo')
        namespaceutils.add_namespace_to_root('foo')
        expected = [ns_foo]
        result = pm.listNamespaces(recursive=True)
        self.assertListEqual(expected, result)


class TestDuplicateToNamespace(mayatest.MayaTestCase):
    def test_basic(self):
        test_cube = self.create_cube()
        dups = namespaceutils.duplicate_to_namespace([test_cube])
        self.assertEqual(len(dups), 1)
        result = dups[0].nodeName()
        expected = 'pCube' + str(int(test_cube.nodeName().split('pCube')[1])+1)
        self.assertEqual(expected, result)

    def test_dup_to_namespace(self):
        test_cube = self.create_cube()
        pm.namespace(add='foo')
        dups = namespaceutils.duplicate_to_namespace([test_cube], dup_namespace='foo')
        self.assertEqual(len(dups), 1)
        result = dups[0].name()
        expected = 'foo:' + test_cube.nodeName()
        self.assertEqual(expected, result)

    def test_dup_to_parent_node(self):
        test_cube = self.create_cube()
        parent = self.create_transform_node()
        dups = namespaceutils.duplicate_to_namespace([test_cube], dup_parent=parent)
        self.assertEqual(len(dups), 1)
        self.assertEqual(parent, dups[0].getParent())
        self.assertEqual(test_cube.nodeName(), dups[0].nodeName())

    def test_parent_to_world(self):
        parent = self.create_transform_node()
        test_cube = self.create_cube()
        test_cube.setParent(parent)
        dups = namespaceutils.duplicate_to_namespace([test_cube], dup_parent=namespaceutils.PARENT_WORLD)
        self.assertEqual(len(dups), 1)
        self.assertIsNone(dups[0].getParent())
        self.assertEqual(test_cube.nodeName(), dups[0].nodeName())

    def test_dup_to_both(self):
        parents = [self.create_transform_node() for x in range(2)]
        test_cube = self.create_cube()
        test_cube.setParent(parents[0])
        pm.namespace(add='foo')
        dups = namespaceutils.duplicate_to_namespace([test_cube], dup_namespace='foo', dup_parent=parents[1])
        self.assertEqual(len(dups), 1)
        self.assertEqual(parents[1], dups[0].getParent())
        self.assertEqual(test_cube.nodeName(), dups[0].nodeName(stripNamespace=True))
        self.assertEqual(dups[0].parentNamespace(), 'foo')

    def test_multiple_nodes(self):
        test_cubes = [self.create_cube() for _ in range(5)]
        dups = namespaceutils.duplicate_to_namespace(test_cubes)
        self.assertEqual(len(test_cubes), len(dups))

    def test_all_the_things(self):
        parents = [self.create_transform_node() for x in range(2)]
        test_cubes = [self.create_cube() for _ in range(5)]
        [x.setParent(parents[0]) for x in test_cubes]
        pm.namespace(add='foo')
        dups = namespaceutils.duplicate_to_namespace(test_cubes, dup_namespace='foo', dup_parent=parents[1])
        self.assertEqual(len(test_cubes), len(dups))
        [self.assertEqual(parents[1], dup.getParent()) for dup in dups]
        [self.assertEqual(tc.nodeName(), dup.nodeName(stripNamespace=True)) for tc, dup in zip(test_cubes, dups)]
        [self.assertEqual(dup.parentNamespace(), 'foo') for dup in dups]

    def test_passing_one_node(self):
        test_cube = self.create_cube()
        dups = namespaceutils.duplicate_to_namespace(test_cube)
        self.assertEqual(1, len(dups))
        self.assertEqual(dups[0].type(), 'transform')
        self.assertTrue(dups[0].getShape())


class TestGetNamespacePynode(mayatest.MayaTestCase):
    def test_simple(self):
        pm.namespace(add='foo')
        expected = pm.Namespace('foo')
        result = namespaceutils.get_namespace_as_pynode('foo')
        self.assertEqual(expected, result)

    def test_nested(self):
        pm.namespace(add=':foo:bar:spam:eggs')
        expected = pm.Namespace(':foo:bar:spam')
        result = namespaceutils.get_namespace_as_pynode('spam')
        self.assertEqual(expected, result)

    def test_returns_first_nested(self):
        pm.namespace(add=':foo:bar:spam:eggs:spam')
        expected = pm.Namespace(':foo:bar:spam')
        result = namespaceutils.get_namespace_as_pynode('spam')
        self.assertEqual(expected, result)

    def test_returns_first_nested_alphabetical_if_same_depth(self):
        pm.namespace(add=':foo:bar:spam:eggs')
        pm.namespace(add=':goo:car:spam:eggs')
        expected = pm.Namespace(':foo:bar:spam')
        result = namespaceutils.get_namespace_as_pynode('spam')
        self.assertEqual(expected, result)

    def test_raises_value_error_if_ns_does_not_exist(self):
        self.assertRaises(ValueError, namespaceutils.get_namespace_as_pynode, 'foo')


class TestGetNamespaceFromNode(mayatest.MayaTestCase):
    def test_returns_first_ns(self):
        test_ns = self.create_namespace('foo')
        pm.namespace(set=test_ns)
        test_cube_a = self.create_cube()
        pm.namespace(set=':')
        result = namespaceutils.get_first_namespace_from_node(test_cube_a)
        self.assertEqual(result, test_ns)

    def test_returns_first_ns_when_node_is_in_nested_ns(self):
        test_ns = self.create_namespace('foo')
        test_ns2 = self.create_namespace('foo:bar')
        pm.namespace(set=test_ns2)
        test_cube_a = self.create_cube()
        pm.namespace(set=':')
        result = namespaceutils.get_first_namespace_from_node(test_cube_a)
        self.assertEqual(result, test_ns)

    def test_reteurns_none_if_root_namespace(self):
        test_ns = self.create_namespace('foo')
        test_ns2 = self.create_namespace('foo:bar')
        pm.namespace(set=':')
        test_cube_a = self.create_cube()
        result = namespaceutils.get_first_namespace_from_node(test_cube_a)
        self.assertIsNone(result)