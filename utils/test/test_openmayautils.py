import maya.api.OpenMaya as om
import pymel.core as pm

import flottitools.test as mayatest
import flottitools.utils.openmayautils as omutils


class TestGetDagPathOrDependNode(mayatest.MayaTestCase):
    def test_get_dag_node_from_name(self):
        test_cube = self.create_cube()
        sel_list = om.MSelectionList()
        sel_list.add(test_cube.name())
        expected = sel_list.getDagPath(0)
        result = omutils.get_dagpath_or_dependnode_from_name(test_cube.name())
        self.assertEqual(result, expected)

    def test_get_depend_node_from_name(self):
        test_depend_node = pm.ls(type='displayLayerManager')[0]
        sel_list = om.MSelectionList()
        sel_list.add(test_depend_node.name())
        expected = sel_list.getDependNode(0)
        result = omutils.get_dagpath_or_dependnode_from_name(test_depend_node.name())
        self.assertEqual(result, expected)

    def test_get_dag_node_from_node(self):
        test_cube = self.create_cube()
        sel_list = om.MSelectionList()
        sel_list.add(test_cube.name())
        expected = sel_list.getDagPath(0)
        result = omutils.get_dagpath_or_dependnode(test_cube)
        self.assertEqual(result, expected)

    def test_get_dag_node_more_than_one_object_with_same_name(self):
        test_cubes = [self.create_cube() for _ in range(3)]
        test_cubes[2].setParent(test_cubes[1])
        test_cubes[2].rename(test_cubes[0].nodeName())
        sel_list = om.MSelectionList()
        sel_list.add(test_cubes[0].name())
        expected = sel_list.getDagPath(0)
        result = omutils.get_dagpath_or_dependnode(test_cubes[0])
        self.assertEqual(test_cubes[0].nodeName(), test_cubes[2].nodeName())
        self.assertEqual(result, expected)

    def test_get_dag_namespaces(self):
        pm.namespace(set=':')
        test_cube1 = self.create_cube()
        ns = pm.namespace(add='foo')
        pm.namespace(set=ns)
        test_cube2 = self.create_cube()
        pm.namespace(set=':')
        sel_list = om.MSelectionList()
        sel_list.add(test_cube2.name())
        expected = sel_list.getDagPath(0)
        result = omutils.get_dagpath_or_dependnode(test_cube2)
        self.assertEqual(test_cube1.nodeName(stripNamespace=True), test_cube2.nodeName(stripNamespace=True))
        self.assertNotEqual(test_cube1.nodeName(), test_cube2.nodeName())
        self.assertEqual(result, expected)