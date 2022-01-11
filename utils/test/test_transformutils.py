import maya.api.OpenMaya as om

import flottitools.test as mayatest
import flottitools.utils.transformutils as xformutils


class TestGetWorldSpaceVector(mayatest.MayaTestCase):
    def test_simple(self):
        testcube = self.create_cube()
        self.pm.move(testcube, (1, 0, 0), absolute=True)
        result = xformutils.get_worldspace_vector(testcube)
        self.assertEqual(result, om.MVector(1, 0, 0))

    def test_returns_worldspace_when_parented(self):
        testcube = self.create_cube()
        self.pm.move(testcube, (1, 0, 0), absolute=True)
        parentcube = self.create_cube()
        self.pm.move(parentcube, (3, 0, 0), absolute=True)
        testcube.setParent(parentcube)
        result = xformutils.get_worldspace_vector(testcube)
        self.assertEqual(result, om.MVector(1, 0, 0))


class TestMoveNodeToWorldspacePosition(mayatest.MayaTestCase):
    def test_move_node_to_worldspace_position(self):
        testcube = self.create_cube()
        expected = om.MVector(1, 0, 0)
        xformutils.move_node_to_worldspace_position(testcube, expected)
        result = xformutils.get_worldspace_vector(testcube)
        self.assertEqual(expected, result)

    def test_node_has_parent_off_origin(self):
        parentcube = self.create_cube()
        childcube = self.create_cube()
        childcube.setParent(parentcube)
        self.pm.move(parentcube, (1, 0, 0), absolute=True)
        result = xformutils.get_worldspace_vector(childcube)
        self.assertEqual(om.MVector(1, 0, 0), result)
        xformutils.move_node_to_worldspace_position(childcube, (0, 0, 0))
        result = xformutils.get_worldspace_vector(childcube)
        self.assertEqual(om.MVector(0, 0, 0), result)


class TestMatchWorldspacePosition(mayatest.MayaTestCase):
    def test_match_worldspace_position(self):
        targetcube = self.create_cube()
        self.pm.move(targetcube, (1, 0, 0), absolute=True)
        expected = xformutils.get_worldspace_vector(targetcube)
        testcube = self.create_cube()
        xformutils.match_worldspace_position(testcube, targetcube)
        result = xformutils.get_worldspace_vector(testcube)
        self.assertEqual(expected, result)

    def test_target_node_in_parentspace(self):
        parent_cube = self.create_cube()
        target_cube = self.create_cube()
        test_cube = self.create_cube()
        self.pm.move(target_cube, (1, 0, 0), absolute=True)
        target_cube.setParent(parent_cube)
        self.pm.move(parent_cube, (1, 0, 0), absolute=True)
        xformutils.match_worldspace_position(test_cube, target_cube)
        result = xformutils.get_worldspace_vector(test_cube)
        self.assertEqual(om.MVector(2, 0, 0), result)

    def test_node_in_parentspace(self):
        parent_cube = self.create_cube()
        target_cube = self.create_cube()
        test_cube = self.create_cube()
        test_cube.setParent(parent_cube)
        self.pm.move(parent_cube, (1, 0, 0), absolute=True)
        self.pm.move(target_cube, (0, 1, 0), absolute=True)
        xformutils.match_worldspace_position(test_cube, target_cube)
        result = xformutils.get_worldspace_vector(test_cube)
        self.assertEqual(om.MVector(0, 1, 0), result)


class TestGetDistanceScalers(mayatest.MayaTestCase):
    def test_returns_one_for_overlapping_target(self):
        source_vector = om.MVector(0, 0, 0)
        target_vectors = [om.MVector(0, 0, 0), om.MVector(1, 0, 0)]
        expected = [1.0, 0.0]
        result = xformutils.get_distance_scalers(source_vector, target_vectors)
        self.assertListEqual(result, expected)

    def test_returns_one_for_first_overlapping_target(self):
        source_vector = om.MVector(0, 0, 0)
        target_vectors = [om.MVector(0, 0, 0), om.MVector(0, 0, 0)]
        expected = [1.0, 0.0]
        result = xformutils.get_distance_scalers(source_vector, target_vectors)
        self.assertListEqual(result, expected)

    def test_two_equidistant_targets(self):
        source_vector = om.MVector(0, 0, 0)
        target_vectors = [om.MVector(1, 0, 0), om.MVector(-1, 0, 0)]
        expected = [0.5, 0.5]
        result = xformutils.get_distance_scalers(source_vector, target_vectors)
        self.assertListEqual(result, expected)

    def test_three_equidistant_targets(self):
        source_vector = om.MVector(0, 0, 0)
        target_vectors = [om.MVector(1, 0, 0), om.MVector(0, 1, 0), om.MVector(0, 0, 1)]
        expected = [0.333, 0.333, 0.333]
        result = xformutils.get_distance_scalers(source_vector, target_vectors)
        result = [round(r, 3) for r in result]
        self.assertListEqual(result, expected)

    def test_three_targets(self):
        source_vector = om.MVector(0, 0, 0)
        target_vectors = [om.MVector(1, 0, 0), om.MVector(0, 2, 0), om.MVector(0, 0, 2)]
        expected = [0.5, 0.25, 0.25]
        result = xformutils.get_distance_scalers(source_vector, target_vectors)
        result = [round(r, 3) for r in result]
        self.assertListEqual(result, expected)


class TestGetExtraRootJointsFromSkeleton(mayatest.MayaTestCase):
    def test_returns_none_if_skeleton_has_one_root(self):
        test_joints = [self.create_joint() for _ in range(5)]
        result = xformutils.get_extra_root_joints_from_root_joint(test_joints[0])
        self.assertListEqual([], result)

    def test_returns_joint_if_not_parented_to_joint(self):
        test_joints = [self.create_joint() for _ in range(5)]
        test_node = self.create_transform_node()
        test_node.setParent(test_joints[2])
        test_joints[3].setParent(test_node)
        result = xformutils.get_extra_root_joints_from_root_joint(test_joints[0])
        self.assertEqual([test_joints[3]], result)

    def test_multiple_extra_roots(self):
        test_joints = [self.create_joint() for _ in range(10)]
        test_nodes = [self.create_transform_node() for _ in range(3)]
        test_nodes[0].setParent(test_joints[1])
        test_nodes[1].setParent(test_joints[2])
        test_nodes[2].setParent(test_joints[3])
        test_joints[9].setParent(test_joints[3])
        test_joints[7].setParent(test_nodes[0])
        test_joints[5].setParent(test_nodes[1])
        test_joints[4].setParent(test_nodes[2])
        expected = [test_joints[4], test_joints[5], test_joints[7]]
        result = xformutils.get_extra_root_joints_from_root_joint(test_joints[0])
        self.assertListEqual(expected, result)


class TestNodesAlmostMatchWorldspacePosition(mayatest.MayaTestCase):
    def test_nodes_almost_match_worldspace_position(self):
        cube1 = self.create_cube()
        cube2 = self.create_cube()
        result = xformutils.nodes_almost_match_worldspace_position(cube1, cube2)
        self.assertTrue(result)

    def test_do_not_match(self):
        cube1 = self.create_cube()
        cube2 = self.create_cube()
        self.pm.move(cube2, (1, 2, 3))
        result = xformutils.nodes_almost_match_worldspace_position(cube1, cube2)
        self.assertFalse(result)

    def test_barely_within_tolerance(self):
        cube1 = self.create_cube()
        cube2 = self.create_cube()
        self.pm.move(cube2, (.0009, 0, 0))
        result = xformutils.nodes_almost_match_worldspace_position(cube1, cube2)
        self.assertTrue(result)

    def test_barely_outside_tolerance(self):
        cube1 = self.create_cube()
        cube2 = self.create_cube()
        self.pm.move(cube2, (.001, 0, 0))
        result = xformutils.nodes_almost_match_worldspace_position(cube1, cube2)
        self.assertFalse(result)