import maya.api.OpenMaya as om

import flottitools.utils.transformutils as xformutils
import flottitools.test as flottitest


class TestGetWorldSpaceVector(flottitest.MayaTestCase):
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


class TestGetDistanceScalers(flottitest.MayaTestCase):
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