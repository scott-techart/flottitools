import os
import tempfile
import shutil

import pymel.core as pm

import flottitools.test as mayatest
import flottitools.skintools.skinio as skinio
import flottitools.utils.skinutils as skinutils


class TestExportSkinWeights(mayatest.MayaTestCase):
    def test_create_weight_file(self):
        test_cube, test_joints, test_skincluster = self.create_skinned_cube()
        with tempfile.TemporaryDirectory() as tempdir_name:
            dest_filename = os.path.join(tempdir_name, 'test_weights.ma')
            skinio.export_skinned_mesh(test_cube, dest_filename)
            self.assertTrue(os.path.exists(dest_filename))

    def test_exports_skinned_mesh_and_skeleton(self):
        test_cube, test_joints, test_skincluster = self.create_skinned_cube()
        with tempfile.TemporaryDirectory() as tempdir_name:
            dest_filename = os.path.join(tempdir_name, 'test_weights.ma')
            skinio.export_skinned_mesh(test_cube, dest_filename)
            pm.openFile(dest_filename, force=True)
            result_cube = skinutils.get_skinned_meshes_from_scene()[0]
            result_skincl = skinutils.get_skincluster(result_cube)
            result_joints =result_skincl.influenceObjects()
            self.assertEqual(len(test_joints), len(result_joints))

    def test_does_not_export_extra_stuff(self):
        test_cube, test_joints, test_skincluster = self.create_skinned_cube()
        second_cube = self.create_cube()
        skinutils.bind_mesh_to_joints(second_cube, test_joints)
        sms = skinutils.get_skinned_meshes_from_scene()
        self.assertEqual(2, len(sms))
        fake_rig_controller = self.create_transform_node()
        pm.parentConstraint(fake_rig_controller, test_joints[0])
        with tempfile.TemporaryDirectory() as tempdir_name:
            dest_filename = os.path.join(tempdir_name, 'test_weights.ma')
            skinio.export_skinned_mesh(test_cube, dest_filename)
            pm.openFile(dest_filename, force=True)
            result_cube = skinutils.get_skinned_meshes_from_scene()
            self.assertEqual(1, len(result_cube))
            default_trash = [x.getParent() for x in pm.ls(cameras=True)]
            default_trash.extend(pm.ls(type='joint'))
            stuff = [x for x in pm.ls(type='transform') if x not in default_trash]
            # [x for x in pm.ls(type='transform') if x not in pm.ls(defaultNodes=True, cameras=True)]
            self.assertEqual(1, len(stuff))
            constraints = pm.ls(type='parentConstraint')
            self.assertEqual(0, len(constraints))

    def test_export_referenced_mesh(self):
        ref_cube, ref_joints, ref_skincluster = self.create_skinned_cube()
        ref_cube_name = ref_cube.nodeName()
        pm.skinPercent(ref_skincluster, ref_cube.vtx, transformValue=(ref_joints[2], 1.0))
        with tempfile.TemporaryDirectory() as tempdir_name:
            # skin a cube and export it to a separate file
            ref_filename = os.path.join(tempdir_name, 'ref_test.ma')
            stuff = [ref_cube] + ref_joints
            pm.select(stuff, r=True)
            pm.exportSelected(ref_filename, type='mayaAscii', constructionHistory=True, force=True)
            # clean scene then reference in the file just exported
            self._clean_scene()
            file_reference = pm.createReference(ref_filename)
            ref_nodes = file_reference.nodes()
            ref_cube = [r for r in ref_nodes if r.nodeName().endswith(ref_cube_name)][0]
            # export the skin weights
            dest_filename = os.path.join(tempdir_name, 'test_weights.ma')
            skinio.export_skinned_mesh(ref_cube, dest_filename)
            # open the exported skin file
            pm.openFile(dest_filename, force=True)
            result_cube = skinutils.get_skinned_meshes_from_scene()[0]
            result_skincl = skinutils.get_skincluster(result_cube)
            result_joints =result_skincl.influenceObjects()
            result = skinutils.get_weighted_influences(result_cube.vtx[0])
            expected = {result_joints[2]: 1.0}
            self.assertEqual(expected, result)


class TestGetSkinnedMeshFromImport(mayatest.MayaTestCase):
    def test_one_skinned_mesh(self):
        test_cube, test_joints, test_skincluster = self.create_skinned_cube()
        result = skinio._get_skinned_mesh_from_import([test_cube, test_skincluster], 'foo')
        self.assertEqual(test_cube, result)

    def test_raises_missing_skinned_mesh(self):
        test_cube = self.create_cube()
        test_joints = [self.create_joint() for _ in range(5)]
        stuff = [test_cube] + test_joints
        self.assertRaises(
            skinio.MissingSkinnedMesh, skinio._get_skinned_mesh_from_import, stuff, 'foo')

    def test_matches_name_when_more_than_one_skinned_mesh(self):
        meshes, joints, skincls = zip(*[self.create_skinned_cube() for _ in range(4)])
        stuff = meshes + skincls
        result = skinio._get_skinned_mesh_from_import(stuff, 'foo', meshes[2].nodeName())
        self.assertEqual(meshes[2], result)

    def test_returns_first_mesh_if_no_name_matches(self):
        meshes, joints, skincls = zip(*[self.create_skinned_cube() for _ in range(4)])
        stuff = meshes + skincls
        result = skinio._get_skinned_mesh_from_import(stuff, 'foo', 'foo')
        self.assertEqual(meshes[0], result)


class TestImportSkinning(mayatest.MayaTestCase):
    def setUp(self):
        super(TestImportSkinning, self).setUp()
        self.tmp_dir = tempfile.mkdtemp()
        self._create_tmp_skindata()

    def tearDown(self):
        super(TestImportSkinning, self).tearDown()
        shutil.rmtree(self.tmp_dir)

    def _create_tmp_skindata(self):
        test_cube, test_joints, test_skincluster = self.create_skinned_cube()
        pm.skinPercent(test_skincluster, test_cube.vtx[:4], transformValue=(test_joints[2], 1.0))
        pm.skinPercent(test_skincluster, test_cube.vtx[4:], transformValue=(test_joints[1], 1.0))
        self.skin_path = os.path.join(self.tmp_dir, 'test_skinning.ma')
        skinio.export_skinned_mesh(test_cube, self.skin_path)
        pm.delete(self.scene_nodes)

    def test_copies_weights(self):
        test_cube, test_joints, test_skincluster = self.create_skinned_cube()
        skinio.import_skinning(test_cube, self.skin_path)
        result = skinutils.get_weighted_influences(test_cube.vtx[0])
        expected = {test_joints[2]: 1.0}
        self.assertEqual(expected, result)

    def test_best_guess_same_vert_order_different_positions_uses_vert_order(self):
        test_cube = self.create_cube()
        test_cube.scale.set(2, 2, 2)
        pm.makeIdentity(test_cube, apply=True, scale=True, translate=True, rotate=True)
        test_cube, test_joints, test_skincluster = self.create_skinned_cube(test_cube=test_cube)
        skinio.import_skinning(test_cube, self.skin_path, copy_weights_method=skinio.SKINNING_METHOD_BEST_GUESS)
        result = skinutils.get_weighted_influences(test_cube.vtx[0])
        expected = {test_joints[2]: 1.0}
        self.assertEqual(expected, result)
        result = skinutils.get_weighted_influences(test_cube.vtx[4])
        expected = {test_joints[1]: 1.0}
        self.assertEqual(expected, result)

    def test_best_guess_same_vert_count_different_vert_order(self):
        # if we find a better way to compare vert order that doesn't depend on vert position
        # this test's expected values should be updated
        # Currently the copy method is expected to be worldspace.
        # But with an ideal vert order check it would use vert order copy method.
        test_cube = self.create_cube()
        test_cube.scaleZ.set(-1)
        pm.makeIdentity(test_cube, apply=True, scale=True, translate=True, rotate=True)
        test_cube, test_joints, test_skincluster = self.create_skinned_cube(test_cube=test_cube)
        skinio.import_skinning(test_cube, self.skin_path, copy_weights_method=skinio.SKINNING_METHOD_BEST_GUESS)
        result = skinutils.get_weighted_influences(test_cube.vtx[0])
        expected = {test_joints[2]: 1.0}
        self.assertEqual(expected, result)
        result = skinutils.get_weighted_influences(test_cube.vtx[4])
        expected = {test_joints[1]: 1.0}
        self.assertEqual(expected, result)

    def test_best_guess_world_space(self):
        test_cube = self.create_cube()
        pm.polyMergeVertex(test_cube.vtx[2:5], d=100, am=1, ch=1)
        pm.select(clear=True)
        test_cube, test_joints, test_skincluster = self.create_skinned_cube(test_cube=test_cube)
        skinio.import_skinning(test_cube, self.skin_path, copy_weights_method=skinio.SKINNING_METHOD_BEST_GUESS)
        result = skinutils.get_weighted_influences(test_cube.vtx[0])
        expected = {test_joints[2]: 1.0}
        self.assertEqual(expected, result)
        result = skinutils.get_weighted_influences(test_cube.vtx[2])
        expected = {test_joints[1]: 0.5,
                    test_joints[2]: 0.5}
        self.assertEqual(expected, result)

    def test_cleans_up_after(self):
        test_cube, test_joints, test_skincluster = self.create_skinned_cube()
        expected_nodes = pm.ls(dagObjects=True)
        expected_namespaces = pm.listNamespaces()
        skinio.import_skinning(test_cube, self.skin_path)
        result_nodes = pm.ls(dagObjects=True)
        result_namespaces = pm.listNamespaces()
        self.assertListEqual(expected_nodes, result_nodes)
        self.assertListEqual(expected_namespaces, result_namespaces)

    def test_imports_on_unskinned_meshes(self):
        test_cube = self.create_cube()
        test_joints = [self.create_joint(position=(i, i, i), absolute=True) for i in range(5)]
        skinio.import_skinning_on_meshes_in_scene(self.skin_path, bind_unskinned=True)
        result = skinutils.get_skincluster(test_cube)
        self.assertIsNotNone(result)

    def test_matching_joint_names_only(self):
        test_cube = self.create_cube()
        test_joints = [self.create_joint(position=(i, i, i), absolute=True) for i in range(7)]
        skinio.import_skinning_on_meshes_in_scene(self.skin_path, bind_unskinned=True)
        skin_cluster = skinutils.get_skincluster(test_cube)
        result = skin_cluster.getInfluence()
        expected = test_joints[:5]
        self.assertListEqual(result, expected)


class TestGetSkinDataPath(mayatest.MayaTestCase):
    def test_if_mesh_referenced_path_to_referenced_file_dir(self):
        pass

    def test_if_saved_file_path_to_same_dir(self):
        pass

    def test_if_new_scene_path_to_tmp_dir(self):
        pass
