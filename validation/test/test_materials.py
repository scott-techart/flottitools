import os

import flottitools.test as flottitest
import flottitools.utils.materialutils as matutils
import flottitools.validation.materials as matval


class MayaMaterialTestCase(flottitest.MayaTestCase):
    def create_material(self, mat_type=None):
        mat_type = mat_type or 'lambert'
        mat, shading_group = matutils.create_material('test_mat', mat_type)
        self.scene_nodes.append(mat)
        self.scene_nodes.append(shading_group)
        return mat, shading_group


class TestGetFileNodesWithBadTexturePaths(MayaMaterialTestCase):
    def test_get_file_nodes_with_bad_texture_paths(self):
        mat, _ = self.create_material()
        file_node = self.pm.createNode("file")
        file_node.outColor.connect(mat.color, force=True)
        file_node.fileTextureName.set('foo')
        result = matval.get_file_nodes_with_bad_texture_paths(mat)
        self.assertEqual([file_node], result)

    def test_one_good_one_bad_path(self):
        mat, _ = self.create_material()
        file_node = self.pm.createNode("file")
        file_node2 = self.pm.createNode("file")
        file_node.outColor.connect(mat.color, force=True)
        file_node2.outColor.connect(mat.transparency, force=True)
        file_node.fileTextureName.set('foo')
        good_path = os.path.join('foo', 'media', 'bar')
        file_node2.fileTextureName.set(good_path)
        result = matval.get_file_nodes_with_bad_texture_paths(mat)
        self.assertEqual([file_node], result)

    def test_two_bad_paths(self):
        mat, _ = self.create_material()
        file_node = self.pm.createNode("file")
        file_node2 = self.pm.createNode("file")
        file_node.outColor.connect(mat.color, force=True)
        file_node2.outColor.connect(mat.transparency, force=True)
        file_node.fileTextureName.set('foo')
        file_node2.fileTextureName.set('bar')
        result = matval.get_file_nodes_with_bad_texture_paths(mat)
        self.assertEqual([file_node, file_node2], result)