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

