import pymel.core as pm

import flottitools.test as mayatest
import flottitools.utils.deformerutils as deformerutils


class TestApplyWrapDeformer(mayatest.MayaTestCase):
    def test_creates_wrap_deformer(self):
        cube1 = self.create_cube()
        cube2 = self.create_cube()
        result_wrap, result_base = deformerutils.create_wrap_deformer(cube1, cube2)
        self.scene_nodes.extend((result_wrap, result_base))
        self.assertIsInstance(result_wrap, pm.nt.Wrap)

    def test_wrap_deforms_target_mesh(self):
        source_cube, target_cube = [self.create_cube() for _ in range(2)]
        initial_target_vert_pos = pm.pointPosition(target_cube.vtx[0])
        wrap_node, base_shape = deformerutils.create_wrap_deformer(source_cube, target_cube)
        self.scene_nodes.extend((wrap_node, base_shape))
        pm.move(source_cube.vtx[0], (1, 1, 1))
        target_vert_pos = pm.pointPosition(source_cube.vtx[0])
        result_target_vert_post = pm.pointPosition(target_cube.vtx[0])
        self.assertNotEqual(initial_target_vert_pos, result_target_vert_post)
        self.assertEqual(target_vert_pos, result_target_vert_post)


class TestGetBlendshapeAttrs(mayatest.MayaTestCase):
    def test_basic(self):
        test_cube = self.create_cube()
        target_cube = self.create_cube()
        expected = pm.blendShape(target_cube, test_cube)
        result = deformerutils.get_blendshape_nodes(test_cube)
        self.assertListEqual(expected, result)

    def test_ignores_parallel_node(self):
        test_cube = self.create_cube()
        target_cube1 = self.create_cube()
        target_cube2 = self.create_cube()
        b1 = pm.blendShape(target_cube1, test_cube, parallel=True)[0]
        b2 = pm.blendShape(target_cube2, test_cube, parallel=True)[0]
        result = deformerutils.get_blendshape_nodes(test_cube)
        self.assertListEqual([b1, b2], result)

    def test_multiple_blend_targets(self):
        test_cube = self.create_cube()
        target_cube1 = self.create_cube()
        target_cube2 = self.create_cube()
        target_cube3 = self.create_cube()
        b1 = pm.blendShape(target_cube1, test_cube)[0]
        b2 = pm.blendShape(target_cube2, test_cube)[0]
        b3 = pm.blendShape(target_cube3, test_cube)[0]
        result = deformerutils.get_blendshape_nodes(test_cube)
        result.sort()
        expected = [b1, b2, b3]
        expected.sort()
        self.assertListEqual(expected, result)

    def test_multiple_deleted_blend_targets(self):
        test_cube = self.create_cube()
        target_cube1 = self.create_cube()
        target_cube2 = self.create_cube()
        target_cube3 = self.create_cube()
        b1 = pm.blendShape(target_cube1, test_cube)[0]
        b2 = pm.blendShape(target_cube2, test_cube)[0]
        b3 = pm.blendShape(target_cube3, test_cube)[0]
        pm.delete([target_cube1, target_cube2, target_cube3])
        result = deformerutils.get_blendshape_nodes(test_cube)
        result.sort()
        expected = [b1, b2, b3]
        expected.sort()
        self.assertListEqual(expected, result)

    def test_is_blendshape_target(self):
        test_cube = self.create_cube()
        target_cube1 = self.create_cube()
        b1 = pm.blendShape(target_cube1, test_cube)[0]
        self.assertTrue(deformerutils.is_blendshape_target(b1, test_cube))

    def test_is_not_blendshape_target(self):
        test_cube = self.create_cube()
        target_cube1 = self.create_cube()
        target_cube2 = self.create_cube()
        b1 = pm.blendShape(target_cube1, test_cube, parallel=True)[0]
        b2 = pm.blendShape(target_cube2, test_cube, parallel=True)[0]
        bade_blendshape_node = pm.ls('parallelBlender')[0]
        self.assertFalse(deformerutils.is_blendshape_target(bade_blendshape_node, test_cube))

    def test_ignores_parallel_node_deleted_targets(self):
        test_cube = self.create_cube()
        target_cube1 = self.create_cube()
        target_cube2 = self.create_cube()
        b1 = pm.blendShape(target_cube1, test_cube, parallel=True)[0]
        b2 = pm.blendShape(target_cube2, test_cube, parallel=True)[0]
        pm.delete([target_cube1, target_cube2])
        result = deformerutils.get_blendshape_nodes(test_cube)
        self.assertListEqual([b1, b2], result)