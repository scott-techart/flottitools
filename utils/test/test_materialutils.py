import flottitools.test as mayatest
import flottitools.utils.materialutils as materialutils


class MayaMaterialTestCase(mayatest.MayaTestCase):
    def create_material(self, mat_type=None):
        mat_type = mat_type or 'lambert'
        mat, shading_group = materialutils.create_material('test_mat', mat_type)
        self.scene_nodes.append(mat)
        self.scene_nodes.append(shading_group)
        return mat, shading_group


class TestGetAllMaterialsInScene(MayaMaterialTestCase):
    def setUp(self):
        super(TestGetAllMaterialsInScene, self).setUp()
        default_mat_names = ['lambert1', 'particleCloud1', 'standardSurface1']
        self.default_mats = [self.pm.PyNode(m) for m in default_mat_names]

    def test_get_all_mats_from_empty_scene(self):
        result = materialutils.get_all_materials_in_scene()
        result.sort()
        self.default_mats.sort()
        self.assertListEqual(self.default_mats, result)

    def test_one_new_mat_in_empty_scene(self):
        new_mat, _ = self.create_material()
        result = materialutils.get_all_materials_in_scene()
        result.sort()
        expected = self.default_mats + [new_mat]
        expected.sort()
        self.assertListEqual(expected, result)


class TestGetUsedMaterialsInScene(MayaMaterialTestCase):
    def test_no_used_mats(self):
        used_mats = materialutils.get_used_materials_in_scene()
        self.assertListEqual([], used_mats)

    def test_one_used_mat(self):
        new_mat, shading_group = self.create_material()
        cube = self.create_cube()
        materialutils.assign_material(cube, new_mat)
        used_mats = materialutils.get_used_materials_in_scene()
        self.assertListEqual([new_mat], used_mats)

    def test_new_unused_mat(self):
        new_mat, shading_group = self.create_material()
        used_mats = materialutils.get_used_materials_in_scene()
        self.assertListEqual([], used_mats)

    def test_one_mesh_two_used_mats(self):
        new_mat, shading_group = self.create_material()
        new_mat2, shading_group2 = self.create_material()
        cube = self.create_cube()
        materialutils.assign_material(cube, new_mat)
        materialutils.assign_material(cube.f[0], new_mat2)
        used_mats = materialutils.get_used_materials_in_scene()
        expected = [new_mat, new_mat2]
        expected.sort()
        used_mats.sort()
        self.assertListEqual(expected, used_mats)

    def test_two_meshes_two_used_mats(self):
        new_mat, shading_group = self.create_material()
        new_mat2, shading_group2 = self.create_material()
        cube = self.create_cube()
        cube2 = self.create_cube()
        materialutils.assign_material(cube, new_mat)
        materialutils.assign_material(cube2, new_mat2)
        used_mats = materialutils.get_used_materials_in_scene()
        expected = [new_mat, new_mat2]
        expected.sort()
        used_mats.sort()
        self.assertListEqual(expected, used_mats)


class TestGetShadingGroupsFromPyNode(MayaMaterialTestCase):
    def test_one_mesh_one_material(self):
        cube = self.create_cube()
        mat, shading_group = self.create_material()
        materialutils.assign_material(cube, mat)
        result = materialutils.get_shading_groups_from_pynode(cube)
        self.assertListEqual([shading_group], result)

    def test_get_from_material(self):
        cube = self.create_cube()
        mat, shading_group = self.create_material()
        materialutils.assign_material(cube, mat)
        result = materialutils.get_shading_groups_from_pynode(cube)
        self.assertListEqual([shading_group], result)

    def test_two_mats_one_mesh(self):
        cube = self.create_cube()
        mat, shading_group = self.create_material()
        mat2, shading_group2 = self.create_material()
        materialutils.assign_material(cube, mat)
        materialutils.assign_material(cube.f[0], mat2)
        result = materialutils.get_shading_groups_from_pynode(cube)
        self.assertListEqual([shading_group, shading_group2], result)


class TestAssignMaterial(MayaMaterialTestCase):
    def test_one_mesh_one_mat(self):
        cube = self.create_cube()
        mat, shading_group = self.create_material()
        materialutils.assign_material(cube, mat)
        result = cube.shadingGroups()[0].surfaceShader.listConnections()[0]
        self.assertEqual(mat, result)

    def test_asserts_if_mat_or_shading_group_missing(self):
        cube = self.create_cube()
        self.create_material()
        self.assertRaises(AssertionError, lambda: materialutils.assign_material(cube))

    def test_one_mesh_one_shading_group(self):
        cube = self.create_cube()
        mat, shading_group = self.create_material()
        materialutils.assign_material(cube, shading_group)
        result = cube.shadingGroups()[0].surfaceShader.listConnections()[0]
        self.assertEqual(mat, result)

    def test_one_mesh_both_mat_and_sg(self):
        cube = self.create_cube()
        mat, shading_group = self.create_material()
        materialutils.assign_material(cube, mat, shading_group)
        result = cube.shadingGroups()[0].surfaceShader.listConnections()[0]
        self.assertEqual(mat, result)

    def test_assign_to_face(self):
        cube = self.create_cube()
        mat, shading_group = self.create_material()
        result = cube.shadingGroups()
        self.assertEqual(1, len(result))
        materialutils.assign_material(cube.f[0], mat, shading_group)
        result = cube.shadingGroups()
        self.assertEqual(2, len(result))


class TestCreateMaterial(mayatest.MayaTestCase):
    def test_creates_material(self):
        mat, _ = materialutils.create_material('test_mat')
        self.scene_nodes.extend([mat, _])
        mats_in_scene = self.pm.ls(type=self.pm.nt.ShadingDependNode)
        self.assertTrue(mat in mats_in_scene)

    def test_creates_shadinggroup(self):
        mat, shading_group = materialutils.create_material('test_mat')
        self.scene_nodes.extend([mat, shading_group])
        shading_groups = self.pm.ls(type=self.pm.nt.ShadingEngine)
        result = mat.shadingGroups()[0]
        self.assertEqual(shading_group, result)
        self.assertTrue(result in shading_groups)


class TestGetAttrsAndFileNodesFromMat(MayaMaterialTestCase):
    def test_get_attrs_and_file_nodes_from_mat(self):
        mat, _ = self.create_material()
        file_node = self.pm.createNode("file")
        file_node.outColor.connect(mat.color, force=True)
        file_node.fileTextureName.set('foo')
        expected = [(mat.color, file_node)]
        result = materialutils.get_attrs_and_file_nodes_from_mat(mat)
        self.assertListEqual(expected, result)