import itertools

import pymel.core as pm

import flottitools.test as mayatest
import flottitools.utils.materialutils as matutils
import flottitools.utils.skeletonutils as skelutils
import flottitools.utils.skinutils as skinutils


class TestGetSkinCluster(mayatest.MayaTestCase):
    def test_get_skin_cluster_from_cube(self):
        cube = self.create_cube()
        joint = self.create_joint()
        skin_cluster = self.pm.skinCluster(joint, cube)
        result = skinutils. get_skincluster(cube)
        self.assertEqual(result, skin_cluster)

    def test_get_from_shape_node(self):
        test_cube, test_joints, test_skincluster = self.create_skinned_cube()
        shape = test_cube.getShape()
        result = skinutils.get_skincluster(shape)
        self.assertEqual(test_skincluster, result)

    def test_returns_none_if_no_skincluster(self):
        test_cube = self.create_cube()
        self.assertIsNone(skinutils.get_skincluster(test_cube))

    def test_returns_none_if_no_shape(self):
        test_node = self.create_transform_node()
        self.assertIsNone(skinutils.get_skincluster(test_node))

    def test_get_skin_cluster_from_vert(self):
        test_cube, test_joints, test_skincluster = self.create_skinned_cube()
        test_vert = test_cube.vtx[0]
        result = skinutils.get_skincluster(test_vert)
        self.assertEqual(test_skincluster, result)

    def test_is_not_skinned(self):
        test_cube = self.create_cube()
        self.assertTrue(skinutils.is_not_skinned(test_cube))

    def test_is_not_skinned_false(self):
        test_cube, test_joints, skin_cluster = self.create_skinned_cube()
        self.assertFalse(skinutils.is_not_skinned(test_cube))


class TestGetSkinClusterWithReferences(mayatest.MayaTempDirTestCase):
    def tearDown(self):
        pm.newFile(force=True)

    def test_referenced_skeleton(self):
        [pm.joint() for _ in range(5)]
        scene_path = self.tmp_dir_root.joinpath('foo3.ma')
        pm.saveAs(scene_path, force=True)
        pm.newFile()
        pm.createReference(scene_path, returnNewNodes=True)
        test_cube = self.create_cube()
        test_joints = pm.ls(type=pm.nt.Joint)
        expected = skinutils.bind_mesh_to_joints(test_cube, test_joints)
        result = skinutils.get_skincluster(test_cube)
        self.assertEqual(result, expected)

    def test_referenced_skeleton_and_skinned_mesh(self):
        self.create_skinned_cube()
        scene_path = self.tmp_dir_root.joinpath('foo1.ma')
        pm.saveAs(scene_path, force=True)
        pm.newFile()
        ref_nodes = pm.createReference(scene_path, returnNewNodes=True)
        test_cube = [n for n in ref_nodes if n.type() == 'transform'][0]
        expected = pm.ls(type=pm.nt.SkinCluster)[0]
        result = skinutils.get_skincluster(test_cube)
        self.assertEqual(result, expected)

    def test_mesh_referenced_then_skinned(self):
        test_cube = self.create_cube()
        test_cube_name = test_cube.nodeName()
        scene_path = self.tmp_dir_root.joinpath('foo2.ma')
        pm.saveAs(scene_path, force=True)
        pm.newFile()
        ref_nodes = pm.createReference(scene_path, returnNewNodes=True)
        test_cube = [n for n in ref_nodes if n.type() == 'transform'][0]
        test_joints = [self.create_joint() for _ in range(5)]
        skin_cluster = skinutils.bind_mesh_to_joints(test_cube, test_joints)
        result = skinutils.get_skincluster(test_cube)
        self.assertEqual(result, skin_cluster)
        # test_joints = [self.create_joint(position=(i, i, i), absolute=True) for i in range(joint_count)]


class TestBindMeshToJoints(mayatest.MayaTestCase):
    def setUp(self):
        super(TestBindMeshToJoints, self).setUp()
        self.test_cube = self.create_cube()
        self.test_joints = [self.create_joint() for _ in range(5)]

    def test_returns_skincluster(self):
        skincl = skinutils.bind_mesh_to_joints(self.test_cube, self.test_joints)
        self.assertIsNotNone(skincl)

    def test_raises_with_no_mesh_to_skin(self):
        self.assertRaises(RuntimeError, lambda: skinutils.bind_mesh_to_joints(None, self.test_joints))

    def test_raises_with_no_joint(self):
        self.assertRaises(RuntimeError, lambda: skinutils.bind_mesh_to_joints(self.test_cube, None))

    def test_maintains_max_influences_default_four(self):
        skincl = skinutils.bind_mesh_to_joints(self.test_cube, self.test_joints)
        inf_values = pm.skinPercent(skincl, self.test_cube.vtx[0], q=True, value=True)
        inf_count = len([i for i in inf_values if i != 0.0])
        self.assertEqual(4, inf_count)

    def test_maintains_max_influences_five(self):
        skincl = skinutils.bind_mesh_to_joints(self.test_cube, self.test_joints, maximumInfluences=5)
        inf_values = pm.skinPercent(skincl, self.test_cube.vtx[0], q=True, value=True)
        inf_count = len([i for i in inf_values if i != 0.0])
        self.assertEqual(5, inf_count)

    def test_extra_joints_in_skeleton(self):
        skincl = skinutils.bind_mesh_to_joints(self.test_cube, self.test_joints[2:4])
        result = skincl.influenceObjects()
        self.assertListEqual(self.test_joints[2:4], result)

    def test_voxel_method(self):
        # the geodesic voxel bind method requires a GPU so the command cannot be run in Maya standalone.
        # skincl = skinutils.bind_mesh_geodesic_voxel(self.test_cube, self.test_joints, maximumInfluences=1)
        # self.assertIsNotNone(skincl)
        pass

    def test_bind_to_similar_skeleton(self):
        test_cube = self.create_cube()
        test_ns = self.create_namespace('foo')
        pm.namespace(set=test_ns)
        source_cube, source_joints, source_cluster = self.create_skinned_cube()
        pm.namespace(set=':')
        skincl = skinutils.bind_mesh_to_similar_joints(source_cube, test_cube,
                                                       source_skincluster=source_cluster, target_joints=self.test_joints)
        self.assertIsNotNone(skincl)

    def test_bind_to_similar_skeleton_get_target_joints_from_scene(self):
        test_cube = self.create_cube()
        test_ns = self.create_namespace('foo')
        pm.namespace(set=test_ns)
        source_cube, source_joints, source_cluster = self.create_skinned_cube()
        pm.namespace(set=':')
        skincl = skinutils.bind_mesh_to_similar_joints(source_cube, test_cube,
                                                       source_skincluster=source_cluster)
        self.assertIsNotNone(skincl)

    def test_bind_to_similar_skeleton_get_target_joints_from_scene_extra_target_joints(self):
        test_cube = self.create_cube()
        extra_joints = [self.create_joint() for _ in range(5)]
        test_ns = self.create_namespace('foo')
        pm.namespace(set=test_ns)
        source_cube, source_joints, source_cluster = self.create_skinned_cube()
        pm.namespace(set=':')
        skincl = skinutils.bind_mesh_to_similar_joints(source_cube, test_cube,
                                                       source_skincluster=source_cluster)
        expected = self.test_joints
        result = skincl.getInfluence()
        self.assertListEqual(expected, result)

    def test_bind_to_similar_skeleton_extra_target_joints(self):
        test_cube = self.create_cube()
        extra_joints = [self.create_joint() for _ in range(5)]
        test_ns = self.create_namespace('foo')
        pm.namespace(set=test_ns)
        source_cube, source_joints, source_cluster = self.create_skinned_cube()
        pm.namespace(set=':')
        skincl = skinutils.bind_mesh_to_similar_joints(source_cube, test_cube,
                                                       source_skincluster=source_cluster,
                                                       target_joints=self.test_joints)
        expected = self.test_joints
        result = skincl.getInfluence()
        self.assertListEqual(expected, result)



class TestGetVertsWithExceedingInfluences(mayatest.MayaTestCase):
    def test_get_verts_with_more_than_four_infs(self):
        test_cube = self.create_cube()
        test_joints = [self.create_joint() for _ in range(5)]
        skincl = skinutils.bind_mesh_to_joints(test_cube, test_joints, maximumInfluences=5)
        flagged_vert_indexes = skinutils.get_vert_indexes_with_exceeding_influences(
            test_cube, skin_cluster=skincl, max_influences=4)
        flagged_verts = [test_cube.vtx[i] for i in flagged_vert_indexes.keys()]
        flagged_verts.sort()
        expected = list(test_cube.vtx)
        expected.sort()

        self.assertListEqual(expected, flagged_verts)

    def test_no_bad_verts(self):
        test_cube = self.create_cube()
        test_joints = [self.create_joint() for _ in range(5)]
        skincl = skinutils.bind_mesh_to_joints(test_cube, test_joints, maximumInfluences=4)
        flagged_vert_indexes = skinutils.get_vert_indexes_with_exceeding_influences(
            test_cube, skin_cluster=skincl, max_influences=4)
        flagged_verts = [test_cube.vtx[i] for i in flagged_vert_indexes.keys()]

        self.assertListEqual([], flagged_verts)


class TestGetNonZeroInfluencesFromVert(mayatest.MayaTestCase):
    def test_get_non_zero_influences_from_vert(self):
        test_cube = self.create_cube()
        test_joints = [self.create_joint() for _ in range(5)]
        skincl = skinutils.bind_mesh_to_joints(test_cube, test_joints, maximumInfluences=5)
        non_zero_infs = skinutils.get_weighted_influences(test_cube.vtx[0], skincl)
        self.assertEqual(5, len(non_zero_infs))


class TestGetSkinnedMeshesFromScene(mayatest.MayaTestCase):
    def test_get_skinned_meshes_from_scene(self):
        test_skinned_cubes = [self.create_cube() for x in range(3)]
        test_cube = self.create_cube()
        test_joints = [self.create_joint() for _ in range(5)]
        skinclusters = []
        for each in test_skinned_cubes:
            skincl = skinutils.bind_mesh_to_joints(each, test_joints, maximumInfluences=5)
            skinclusters.append(skincl)

        skinned_meshes_from_scene = skinutils.get_skinned_meshes_from_scene()
        skinned_meshes_from_scene.sort()
        test_skinned_cubes.sort()
        self.assertListEqual(test_skinned_cubes, skinned_meshes_from_scene)

    def test_skinned_curve_in_scene(self):
        """
        Should only return skinned meshes in the scene. Not skinned curves.
        """
        test_skinned_cubes = [self.create_cube() for x in range(3)]
        test_curve = self.pm.curve(p=[(0, 0, 0), (3, 5, 6), (5, 6, 7), (9, 9, 9)])
        test_joints = [self.create_joint() for _ in range(5)]
        curve_skincl = skinutils.bind_mesh_to_joints(test_curve, test_joints)
        skinclusters = []
        for each in test_skinned_cubes:
            skincl = skinutils.bind_mesh_to_joints(each, test_joints, maximumInfluences=5)
            skinclusters.append(skincl)
        skinned_meshes_from_scene = skinutils.get_skinned_meshes_from_scene()
        skinned_meshes_from_scene.sort()
        test_skinned_cubes.sort()
        self.assertListEqual(test_skinned_cubes, skinned_meshes_from_scene)

    def test_multiple_mats_assigned_to_skinned_mesh(self):
        test_skinned_cube = self.create_cube()
        test_joints = [self.create_joint() for _ in range(5)]
        skincl = skinutils.bind_mesh_to_joints(test_skinned_cube, test_joints, maximumInfluences=5)
        mat1, _ = matutils.create_material('foo')
        mat2, _ = matutils.create_material('bar')
        matutils.assign_material(test_skinned_cube, mat1)
        matutils.assign_material(test_skinned_cube.f[0], mat2)
        skinned_meshes_from_scene = skinutils.get_skinned_meshes_from_scene()
        self.assertListEqual([test_skinned_cube], skinned_meshes_from_scene)



class TestGetPrunedInfluencesToWeights(mayatest.MayaTestCase):
    def test_no_op_with_four_infs(self):
        influences_to_weights = {'foo': 0.5, 'bar': 0.1, 'spam': 0.1, 'eggs': 0.3}
        result = skinutils.get_pruned_influences_to_weights(influences_to_weights)
        self.assertDictEqual(influences_to_weights, result)

    def test_max_3_influences(self):
        influences_to_weights = {'foo': 0.5, 'bar': 0.2, 'spam': 0.2, 'eggs': 0.1}
        result = skinutils.get_pruned_influences_to_weights(influences_to_weights, max_influences=3)
        expected = {'foo': 0.5, 'bar': 0.2, 'spam': 0.2, 'eggs': 0.0}
        self.assertDictEqual(expected, result)

    def test_five_influences(self):
        influences_to_weights = {'foo': 0.5, 'bar': 0.2, 'spam': 0.1, 'eggs': 0.1, 'ham': 0.05}
        result = skinutils.get_pruned_influences_to_weights(influences_to_weights)
        expected = {'foo': 0.5, 'bar': 0.2, 'spam': 0.1, 'eggs': 0.1, 'ham': 0.0}
        self.assertDictEqual(expected, result)

    def test_five_influences_with_equal_min_values(self):
        influences_to_weights = {'foo': 0.5, 'bar': 0.2, 'spam': 0.2, 'eggs': 0.05, 'ham': 0.05}
        result = skinutils.get_pruned_influences_to_weights(influences_to_weights)
        expected = {'foo': 0.5, 'bar': 0.2, 'spam': 0.2, 'eggs': 0.0, 'ham': 0.0}
        self.assertDictEqual(expected, result)

    def test_divisor_is_2(self):
        influences_to_weights = {'foo': 1.0, 'bar': 0.4, 'spam': 0.2, 'eggs': 0.2}
        result = skinutils.get_pruned_influences_to_weights(influences_to_weights, divisor=2.0)
        expected = {'foo': 0.5, 'bar': 0.2, 'spam': 0.1, 'eggs': 0.1}
        self.assertDictEqual(expected, result)

    def test_too_many_infs_all_equal(self):
        influences_to_weights = {'foo': 0.2, 'bar': 0.2, 'spam': 0.2, 'eggs': 0.2, 'ham': 0.2}
        result = skinutils.get_pruned_influences_to_weights(influences_to_weights)
        expected = {'foo': 0.2, 'bar': 0.2, 'spam': 0.0, 'eggs': 0.2, 'ham': 0.2}
        self.assertDictEqual(expected, result)

    def test_far_too_many_infs_all_equal(self):
        influences_to_weights = {'foo': 0.2, 'bar': 0.2, 'spam': 0.2, 'eggs': 0.2, 'ham': 0.2,
                                 'foo2': 0.2, 'bar2': 0.2, 'spam2': 0.2, 'eggs2': 0.2, 'ham2': 0.2}
        result = skinutils.get_pruned_influences_to_weights(influences_to_weights)
        expected = {'foo': 0.0, 'bar': 0.2, 'spam': 0.0, 'eggs': 0.2, 'ham': 0.0,
                    'foo2': 0.0, 'bar2': 0.2, 'spam2': 0.0, 'eggs2': 0.2, 'ham2': 0.0}
        self.assertDictEqual(expected, result)


class TestPruneExceedingInfluences(mayatest.MayaTestCase):
    def test_prune_exceeding_influences(self):
        test_cube = self.create_cube()
        test_joints = [self.create_joint() for _ in range(5)]
        skincl = skinutils.bind_mesh_to_joints(test_cube, test_joints, maximumInfluences=5)
        influences_to_weights = skinutils.get_weighted_influences(test_cube.vtx[0], skincl)
        skinutils.prune_exceeding_influences_vertex(test_cube.vtx[0], skincl, influences_to_weights)
        result = skinutils.get_weighted_influences(test_cube.vtx[0], skincl)
        self.assertEqual(4, len(result))


class TestGetNonNormalizedVerts(mayatest.MayaTestCase):
    def test_zero_bad_verts(self):
        test_cube = self.create_cube()
        test_joints = [self.create_joint() for _ in range(5)]
        skincl = skinutils.bind_mesh_to_joints(test_cube, test_joints, maximumInfluences=4)
        skincl.setNormalizeWeights(2)  # 2 == post normalize method
        result = skinutils.get_non_normalized_vert_indexes(test_cube.vtx, skincl)
        self.assertEqual(0, len(result))

    def test_one_bad_vert(self):
        test_cube = self.create_cube()
        test_joints = [self.create_joint() for _ in range(5)]
        skincl = skinutils.bind_mesh_to_joints(test_cube, test_joints, maximumInfluences=4)
        skincl.setNormalizeWeights(2)  # 2 == post normalize method
        pm.skinPercent(skincl, test_cube.vtx[0], transformValue=(test_joints[0], 1.5))
        result = skinutils.get_non_normalized_vert_indexes(test_cube.vtx, skincl)
        self.assertEqual(1, len(result))

    def test_returns_total(self):
        test_cube = self.create_cube()
        test_joints = [self.create_joint() for _ in range(5)]
        skincl = skinutils.bind_mesh_to_joints(test_cube, test_joints, maximumInfluences=4)
        skincl.setNormalizeWeights(2)  # 2 == post normalize method
        pm.skinPercent(skincl, test_cube.vtx[0], transformValue=(test_joints[0], 1.5))
        pm.skinPercent(skincl, test_cube.vtx[1], transformValue=(test_joints[0], 1.5))
        expected = {0: 2.25, 1: 2.25}
        result = skinutils.get_non_normalized_vert_indexes(test_cube.vtx, skincl)
        self.assertDictEqual(expected, result)


class TestMoveWeights(mayatest.MayaTestCase):
    def setUp(self):
        super(TestMoveWeights, self).setUp()
        test_cube = self.create_cube()
        test_joints = [self.create_joint() for _ in range(5)]
        self.skincl = skinutils.bind_mesh_to_joints(test_cube, test_joints, maximumInfluences=4)
        self.vert = test_cube.vtx[0]
        self.origin_inf = test_joints[0]
        self.destination_inf = test_joints[1]
        self.initial_origin_weight = self.pm.skinPercent(self.skincl, self.vert, q=True, transform=self.origin_inf)
        self.initial_destination_weight = self.pm.skinPercent(
            self.skincl, self.vert, q=True, transform=self.destination_inf)

    def test_move_weight_single_vert_expected_dest_weight(self):
        skinutils.move_weights_single_vert(self.skincl, self.vert, self.origin_inf, self.destination_inf)
        expected_dest_weight = self.initial_origin_weight + self.initial_destination_weight
        result_dest_weight = self.pm.skinPercent(self.skincl, self.vert, q=True, transform=self.destination_inf)
        self.assertEqual(expected_dest_weight, result_dest_weight)

    def test_single_vert_expected_origin_weight(self):
        skinutils.move_weights_single_vert(self.skincl, self.vert, self.origin_inf, self.destination_inf)
        expected_origin_weight = 0.0
        result_origin_weight = self.pm.skinPercent(self.skincl, self.vert, q=True, transform=self.origin_inf)
        self.assertEqual(expected_origin_weight, result_origin_weight)

    def test_get_move_weight_data_expected_dest_weight(self):
        infs_to_wts = skinutils.get_move_weights_data(self.skincl, self.vert, self.origin_inf, self.destination_inf)
        expected_dest_weight = self.initial_origin_weight + self.initial_destination_weight
        result_dest_weight = infs_to_wts.get(self.destination_inf, 0.0)
        self.assertEqual(expected_dest_weight, result_dest_weight)

    def test_get_move_weight_data_origin_weight(self):
        infs_to_wts = skinutils.get_move_weights_data(self.skincl, self.vert, self.origin_inf, self.destination_inf)
        expected_origin_weight = 0.0
        # result_origin_weight = self.pm.skinPercent(self.skincl, self.vert, q=True, transform=self.origin_inf)
        result_origin_weight = infs_to_wts.get(self.origin_inf, 0.0)
        self.assertEqual(expected_origin_weight, result_origin_weight)


class TestMaxInfluencesNormalizeWeightsDisabled(mayatest.MayaTestCase):
    def test_max_influences_normalize_weights_disabled(self):
        pass


class TestPruneExceedingSkinnedMesh(mayatest.MayaTestCase):
    def test_prune_exceeding_skinned_mesh(self):
        test_cube = self.create_cube()
        test_joints = [self.create_joint() for _ in range(5)]
        skincl = skinutils.bind_mesh_to_joints(test_cube, test_joints, maximumInfluences=5)
        initial_influences = []
        for vert in test_cube.vtx:
            initial_inf = skinutils.get_weighted_influences(vert, skincl)
            initial_influences.append(len(initial_inf))
        expected_initial = [5, 5, 5, 5, 5, 5, 5, 5]
        self.assertListEqual(expected_initial, initial_influences)
        skinutils.prune_exceeding_skinned_mesh(test_cube, skincluster=skincl)
        results = []
        for vert in test_cube.vtx:
            result = skinutils.get_weighted_influences(vert, skincl)
            results.append(len(result))
        expected = [4, 4, 4, 4, 4, 4, 4, 4]
        self.assertListEqual(expected, results)


class TestDeltaMeshSkinning(mayatest.MayaTestCase):
    def test_modifies_skinning(self):
        test_cube = self.create_cube()
        test_joints = [self.create_joint() for _ in range(5)]
        [pm.move(j, (1,0,0)) for j in test_joints]
        skinutils.bind_mesh_to_joints(test_cube, test_joints, maximumInfluences=1)
        start_infs = skinutils.get_weighted_influences(test_cube.vtx[0])
        self.assertEqual(1, len(start_infs))
        skinutils.apply_delta_mush_skinning(test_cube, cleanup=True)
        after_infs = skinutils.get_weighted_influences(test_cube.vtx[0])
        self.assertEqual(4, len(after_infs))

    def test_clean_up_mush_nodes(self):
        pass

    def test_clean_up_extra_meshes(self):
        pass


class TestApplyDeltaMush(mayatest.MayaTestCase):
    def test_creates_mush_node(self):
        test_cube = self.create_cube()
        result = skinutils.apply_delta_mush(test_cube)
        mush_nodes = pm.ls(type=pm.nt.DeltaMush)
        self.assertEqual(mush_nodes, [result])

    def test_default_settings(self):
        test_cube = self.create_cube()
        mush_node = skinutils.apply_delta_mush(test_cube)
        self.scene_nodes.append(mush_node)
        expected = {'smoothingIterations': 20,
                    'smoothingStep': 1.0,
                    'pinBorderVertices': False,
                    'envelope': 1.0,
                    'inwardConstraint': 0.0,
                    'outwardConstraint': 0.0,
                    'distanceWeight': 1.0,
                    'displacement': 1.0}
        result = {'smoothingIterations': mush_node.smoothingIterations.get(),
                  'smoothingStep': mush_node.smoothingStep.get(),
                  'pinBorderVertices': mush_node.pinBorderVertices.get(),
                  'envelope': mush_node.envelope.get(),
                  'inwardConstraint': mush_node.inwardConstraint.get(),
                  'outwardConstraint': mush_node.outwardConstraint.get(),
                  'distanceWeight': mush_node.distanceWeight.get(),
                  'displacement': mush_node.displacement.get()}
        self.assertDictEqual(expected, result)

    def test_not_default_settings(self):
        test_cube = self.create_cube()
        kwargs = {'smoothingIterations': 10,
                  'smoothingStep': 0.5,
                  'pinBorderVertices': True,
                  'envelope': 0.5,
                  'inwardConstraint': 0.5,
                  'outwardConstraint': 1.0}
        mush_node = skinutils.apply_delta_mush(test_cube, 0.0, 0.0, **kwargs)
        self.scene_nodes.append(mush_node)
        expected = {'distanceWeight': 0.0,
                    'displacement': 0.0}
        expected.update(kwargs)
        result = {'smoothingIterations': mush_node.smoothingIterations.get(),
                  'smoothingStep': mush_node.smoothingStep.get(),
                  'pinBorderVertices': mush_node.pinBorderVertices.get(),
                  'envelope': mush_node.envelope.get(),
                  'inwardConstraint': mush_node.inwardConstraint.get(),
                  'outwardConstraint': mush_node.outwardConstraint.get(),
                  'distanceWeight': mush_node.distanceWeight.get(),
                  'displacement': mush_node.displacement.get()}
        self.assertDictEqual(expected, result)


class TestBakeDeformer(mayatest.MayaTestCase):
    def test_one_skeleton(self):
        source_cube = self.create_cube()
        target_cube = self.create_cube()
        test_joints = [self.create_joint() for _ in range(5)]
        skinutils.bind_mesh_to_joints(source_cube, test_joints)
        target_skincl = skinutils.bind_mesh_to_joints(target_cube, test_joints)
        self.scene_nodes.append(skinutils.apply_delta_mush(source_cube))
        pm.skinPercent(target_skincl, target_cube.vtx, transformValue=(test_joints[-1], 1.0))
        previous_val = pm.skinPercent(target_skincl, target_cube.vtx[0], query=True, transform=test_joints[-1])
        # pm.skinPercent(skincluster, vertex, transformValue=pruned_infs_to_weights.items())
        target_skincl = skinutils.bake_deformer_to_skin(source_cube, target_cube)
        result = pm.skinPercent(target_skincl, target_cube.vtx[0], query=True, transform=test_joints[-1])
        self.assertNotEqual(previous_val, result)

    def test_two_skeletons(self):
        source_cube = self.create_cube()
        target_cube = self.create_cube()
        source_joints = [self.create_joint() for _ in range(5)]
        pm.select(clear=True)
        target_joints = [self.create_joint() for _ in range(5)]
        skinutils.bind_mesh_to_joints(source_cube, source_joints)
        target_skincl = skinutils.bind_mesh_to_joints(target_cube, target_joints)
        self.scene_nodes.append(skinutils.apply_delta_mush(source_cube))
        pm.skinPercent(target_skincl, target_cube.vtx, transformValue=(target_joints[-1], 1.0))
        previous_val = pm.skinPercent(target_skincl, target_cube.vtx[0], query=True, transform=target_joints[-1])
        # pm.skinPercent(skincluster, vertex, transformValue=pruned_infs_to_weights.items())
        target_skincl = skinutils.bake_deformer_to_skin(source_cube, target_cube, source_joints, target_joints)
        result = pm.skinPercent(target_skincl, target_cube.vtx[0], query=True, transform=target_joints[-1])
        self.assertNotEqual(previous_val, result)

    def test_respects_max_influences(self):
        source_cube = self.create_cube()
        target_cube = self.create_cube()
        test_joints = [self.create_joint() for _ in range(5)]
        skinutils.bind_mesh_to_joints(source_cube, test_joints)
        skinutils.bind_mesh_to_joints(target_cube, test_joints)
        self.scene_nodes.append(skinutils.apply_delta_mush(source_cube))
        expected = 3
        target_skincl = skinutils.bake_deformer_to_skin(source_cube, target_cube, max_influences=expected)
        result = target_skincl.getMaximumInfluences()
        self.assertEqual(expected, result)

    def test_normalizes_weights(self):
        source_cube = self.create_cube()
        target_cube = self.create_cube()
        test_joints = [self.create_joint() for _ in range(5)]
        skinutils.bind_mesh_to_joints(source_cube, test_joints)
        target_skincl = skinutils.bind_mesh_to_joints(target_cube, test_joints)
        target_skincl.setNormalizeWeights(False)
        pm.skinPercent(target_skincl, target_cube.vtx, transformValue=(test_joints[-1], 2.0))
        weights = [sum(pm.skinPercent(target_skincl, v, value=True, q=True)) for v in target_cube.vtx]
        [self.assertLess(1.0, w) for w in weights]
        self.scene_nodes.append(skinutils.apply_delta_mush(source_cube))
        target_skincl = skinutils.bake_deformer_to_skin(source_cube, target_cube, cleanup=True)
        # target_skincl.forceNormalizeWeights()
        weights = [sum(pm.skinPercent(target_skincl, v, value=True, q=True)) for v in target_cube.vtx]
        [self.assertGreaterEqual(1.0, w) for w in weights]


class CopyWeights(mayatest.MayaTestCase):
    def test_simple(self):
        source_cube = self.create_cube()
        target_cube = self.create_cube()
        source_joints = [self.create_joint() for _ in range(5)]
        [pm.move(j, (0.1, 0.1, 0.1)) for j in source_joints]
        source_skincl = skinutils.bind_mesh_to_joints(source_cube, source_joints)
        expected = [pm.skinPercent(source_skincl, v, value=True, q=True) for v in source_cube.vtx]
        pm.select(clear=True)
        target_joints = [self.create_joint() for _ in range(5)]
        [pm.move(j, (0.1, 0.1, 0.1)) for j in target_joints]
        target_skincl = skinutils.bind_mesh_to_joints(target_cube, target_joints)
        pm.skinPercent(target_skincl, target_cube.vtx, transformValue=(target_joints[-1], 1.0))
        skinutils.copy_weights(source_cube, target_cube)
        result = [pm.skinPercent(source_skincl, v, value=True, q=True) for v in source_cube.vtx]

        for e, r in zip(expected, result):
            [self.assertAlmostEqual(expected_weight, result_weight) for expected_weight, result_weight in zip(e, r)]


class TestGetRootFromSkinnedMesh(mayatest.MayaTestCase):
    def test_get_root_joint_from_skinned_mesh(self):
        test_cube = self.create_cube()
        test_joints = [self.create_joint() for _ in range(5)]
        skinutils.bind_mesh_to_joints(test_cube, test_joints)
        result = skinutils.get_root_joint_from_skinned_mesh(test_cube)
        self.assertEqual(test_joints[0], result)


class TestGetVertsToWeightedInfluences(mayatest.MayaTestCase):
    def test_get_verts_to_weighted_influences(self):
        test_cube, test_joints, skin_cluster = self.create_skinned_cube()
        expected = {}
        inf_index = 0
        for vert in test_cube.vtx:
            expected[vert.index()] = {test_joints[inf_index]: 1.0}
            pm.skinPercent(skin_cluster, vert, transformValue=expected[vert.index()].items())
            inf_index += 1
            if inf_index > 4:
                inf_index = 0
        result = skinutils.get_vert_indexes_to_weighted_influences(skin_cluster)
        self.assertDictEqual(expected, result)

    def test_multiple_influences_per_vert(self):
        test_cube, test_joints, skin_cluster = self.create_skinned_cube()
        expected = {}
        inf_index = 0
        weight_values = [0.3, 0.2, 0.4, 0.1]
        for vert in test_cube.vtx:
            inf_wts = {}
            for weight in weight_values:
                inf_wts[test_joints[inf_index]] = weight
                inf_index += 1
                if inf_index > 4:
                    inf_index = 0
            pm.skinPercent(skin_cluster, vert, transformValue=inf_wts.items())
            expected[vert.index()] = inf_wts
        result = skinutils.get_vert_indexes_to_weighted_influences(skin_cluster)
        self.assertDictEqual(expected, result)

    def test_subset_of_meshes_verts(self):
        test_cube, test_joints, skin_cluster = self.create_skinned_cube()
        expected = {}
        inf_index = 0
        weight_values = [0.3, 0.2, 0.4, 0.1]
        for vert in test_cube.vtx:
            inf_wts = {}
            for weight in weight_values:
                inf_wts[test_joints[inf_index]] = weight
                inf_index += 1
                if inf_index > 4:
                    inf_index = 0
            pm.skinPercent(skin_cluster, vert, transformValue=inf_wts.items())
            expected[vert.index()] = inf_wts
        for i in [0, 1, 7]:
            expected.pop(i)
        result = skinutils.get_vert_indexes_to_weighted_influences(skin_cluster, test_cube.vtx[2:6])
        self.assertDictEqual(expected, result)

    def test_skin_cluster_has_removed_influences(self):
        """An influence index can be greater than the length all influences in the skin_cluster"""
        test_cube = self.create_cube()
        test_joints = [self.create_joint() for _ in range(15)]
        skin_cluster = self.pm.skinCluster(test_joints, test_cube)
        for index in [13, 10, 9]:
            skin_cluster.removeInfluence(test_joints[index])
        self.scene_nodes.append(skin_cluster)
        expected = {}
        for vert in test_cube.vtx:
            expected[vert.index()] = {test_joints[-1]: 1.0}
            pm.skinPercent(skin_cluster, vert, transformValue=expected[vert.index()].items())
        result = skinutils.get_vert_indexes_to_weighted_influences(skin_cluster)
        self.assertDictEqual(expected, result)

    def test_removed_influence_had_non_zero_weights_before(self):
        test_cube = self.create_cube()
        test_joints = [self.create_joint() for _ in range(15)]
        skin_cluster = self.pm.skinCluster(test_joints, test_cube)
        test_indices = [13, 10, 9]
        for vert in test_cube.vtx:
            for index in test_indices:
                pm.skinPercent(skin_cluster, vert, transformValue=(test_joints[index], 0.5))
        for index in test_indices[1:]:
            skin_cluster.removeInfluence(test_joints[index])
        expected = {}
        for vert in test_cube.vtx:
            expected[vert.index()] = {test_joints[0]: 1.0}
            pm.skinPercent(skin_cluster, vert, transformValue=(expected[vert.index()].items()))
        self.scene_nodes.append(skin_cluster)
        result = skinutils.get_vert_indexes_to_weighted_influences(skin_cluster)
        self.assertDictEqual(expected, result)


class TestGetInfluenceIndex(mayatest.MayaTestCase):
    def test_influence_passed_as_pynode(self):
        test_cube, test_joints, skin_cluster = self.create_skinned_cube()
        expected = 3
        result = skinutils.get_influence_index(test_joints[expected], skin_cluster)
        self.assertEqual(expected, result)

    def test_influence_passed_as_string(self):
        test_cube, test_joints, skin_cluster = self.create_skinned_cube()
        expected = 3
        result = skinutils.get_influence_index(test_joints[expected].name(), skin_cluster)
        self.assertEqual(expected, result)

    def test_more_than_one_joint_with_same_name_pynode(self):
        test_cube, test_joints, skin_cluster = self.create_skinned_cube()
        dummy_joints = [self.create_joint() for _ in range(5)]
        expected = 3
        test_joints[expected].rename('foo')
        dummy_joints[expected].rename('foo')
        result = skinutils.get_influence_index(test_joints[expected], skin_cluster)
        self.assertEqual(expected, result)

    def test_more_than_one_joint_with_same_name_string(self):
        test_cube, test_joints, skin_cluster = self.create_skinned_cube()
        dummy_joints = [self.create_joint() for _ in range(5)]
        expected = 3
        test_joints[expected].rename('foo')
        dummy_joints[expected].rename('foo')
        result = skinutils.get_influence_index(test_joints[expected].nodeName(), skin_cluster)
        self.assertEqual(expected, result)


class TestMoveWeightAndRemoveInfluence(mayatest.MayaTestCase):
    def test_removes_influence(self):
        test_cube, test_joints, skin_cluster = self.create_skinned_cube()
        skinutils.move_weight_and_remove_influence(test_joints[-1], test_joints[0], skin_cluster)
        self.assertFalse(test_joints[-1] in skin_cluster.getInfluence())

    def test_moves_weights_to_parent(self):
        test_cube, test_joints, skin_cluster = self.create_skinned_cube()
        values = [0, 0.25, 0.25, 0.25, 0.25]
        infs_to_wts = dict(zip(test_joints, values))
        with skinutils.max_influences_normalize_weights_disabled(skin_cluster):
            for vertex in test_cube.vtx:
                pm.skinPercent(skin_cluster, vertex, transformValue=infs_to_wts.items())
        skinutils.move_weight_and_remove_influence(test_joints[-1], test_joints[-2], skin_cluster)
        result = skinutils.get_weighted_influences(test_cube.vtx[0], skin_cluster)
        expected_values = [0.25, 0.25, 0.5]
        expected = dict(zip(test_joints[1:-1], expected_values))
        self.assertDictEqual(expected, result)


class TestCopyWeightsVertOrder(mayatest.MayaTestCase):
    def test_simple(self):
        source_test_cube, source_test_joints, source_skin_cluster = self.create_skinned_cube()
        target_test_cube, target_test_joints, target_skin_cluster = self.create_skinned_cube()
        inf_map = dict([(sj, [tj]) for sj, tj in zip(source_test_joints, target_test_joints)])
        for vertex in source_test_cube.vtx:
            pm.skinPercent(source_skin_cluster, vertex, transformValue=(source_test_joints[0], 1.0))
        skinutils.copy_weights_vert_order(source_test_cube, target_test_cube, inf_map)
        result = skinutils.get_weighted_influences(target_test_cube.vtx[0])
        expected = {target_test_joints[0]: 1.0}
        self.assertDictEqual(expected, result)


class TestGetInfluenceMapByInfluenceIndex(mayatest.MayaTestCase):
    def test_update_inf_map_by_skincluster_index(self):
        source_cube, source_joints, source_skin_cluster = self.create_skinned_cube()
        target_cube, target_joints, target_skin_cluster = self.create_skinned_cube()
        expected_map = dict([(x, [y]) for x, y in zip(source_joints, target_joints)])
        result_map, result_remaining = skinutils.update_inf_map_by_skincluster_index(source_joints,
                                                                                     target_joints,
                                                                                     source_skin_cluster,
                                                                                     target_skin_cluster)
        self.assertDictEqual(result_map, expected_map)
        self.assertListEqual([], result_remaining)

    def test_skincluster_index_influence_lists_order_differ(self):
        source_cube, source_joints, source_skin_cluster = self.create_skinned_cube()
        target_cube, target_joints, target_skin_cluster = self.create_skinned_cube()
        expected_map = dict([(x, [y]) for x, y in zip(source_joints, target_joints)])
        target_joints.reverse()
        result_map, result_remaining = skinutils.update_inf_map_by_skincluster_index(source_joints,
                                                                                     target_joints,
                                                                                     source_skin_cluster,
                                                                                     target_skin_cluster)
        self.assertDictEqual(result_map, expected_map)
        self.assertListEqual([], result_remaining)

    def test_more_source_influences(self):
        source_cube, source_joints, source_skin_cluster = self.create_skinned_cube(joint_count=10)
        target_cube, target_joints, target_skin_cluster = self.create_skinned_cube()
        expected_map = dict([(x, [y]) for x, y in zip(source_joints, target_joints)])
        result_map, result_remaining = skinutils.update_inf_map_by_skincluster_index(source_joints,
                                                                                     target_joints,
                                                                                     source_skin_cluster,
                                                                                     target_skin_cluster)
        self.assertDictEqual(result_map, expected_map)
        self.assertListEqual([], result_remaining)

    def test_more_target_influences(self):
        source_cube, source_joints, source_skin_cluster = self.create_skinned_cube()
        target_cube, target_joints, target_skin_cluster = self.create_skinned_cube(joint_count=10)
        expected_map = dict([(x, [y]) for x, y in zip(source_joints, target_joints)])
        expected_remaining = target_joints[5:]
        result_map, result_remaining = skinutils.update_inf_map_by_skincluster_index(source_joints,
                                                                                     target_joints,
                                                                                     source_skin_cluster,
                                                                                     target_skin_cluster)
        self.assertDictEqual(result_map, expected_map)
        self.assertListEqual(expected_remaining, result_remaining)


class TestCopyWeights(mayatest.MayaTestCase):
    def test_copy_weights_vert_order_same_skeleton(self):
        source_cube, source_joints, source_skincluster = self.create_skinned_cube()
        target_cube = self.create_cube()
        target_skincluster = skinutils.bind_mesh_to_joints(target_cube, source_joints)
        transform_values = dict(itertools.zip_longest(source_joints[:4], [0.25], fillvalue=0.25))
        transform_values[source_joints[-1]] = 0.0
        pm.skinPercent(source_skincluster, source_cube.vtx[0], transformValue=transform_values.items())
        source_weightedinfs = skinutils.get_weighted_influences(target_cube.vtx[0], target_skincluster)
        transform_values = dict(itertools.zip_longest(source_joints[1:], [0.25], fillvalue=0.25))
        transform_values[source_joints[0]] = 0.0
        pm.skinPercent(target_skincluster, target_cube.vtx[0], transformValue=transform_values.items())
        target_weightedinfs = skinutils.get_weighted_influences(target_cube.vtx[0], target_skincluster)
        self.assertNotEqual(source_weightedinfs, target_weightedinfs)
        skinutils.copy_weights_vert_order_inf_order(source_cube, target_cube, source_skincluster, target_skincluster)
        expected = skinutils.get_weighted_influences(source_cube.vtx[0], source_skincluster)
        result = skinutils.get_weighted_influences(target_cube.vtx[0], target_skincluster)
        self.assertDictEqual(expected, result)


class TestGetBindPose(mayatest.MayaTestCase):
    def test_get_bind_pose_from_skinned_mesh(self):
        test_cube, test_joints, test_skincluster = self.create_skinned_cube()
        expected = pm.ls(type='dagPose')[0]
        result = skinutils.get_bind_pose_from_skinned_mesh(test_cube)
        self.assertEqual(expected, result)

    def test_multiple_bind_poses_on_skel(self):
        test_cube, test_joints, test_skincluster = self.create_skinned_cube()
        expected = pm.ls(type='dagPose')[0]
        dummy_cube = self.create_cube()
        test_joints[2].rotateX.set(30)
        skinutils.bind_mesh_to_joints(dummy_cube, test_joints)
        pm.dagPose(test_joints[0], bindPose=True, save=True)
        bind_poses = pm.ls(type='dagPose')
        self.assertEqual(3, len(bind_poses))
        result = skinutils.get_bind_pose_from_skincluster(test_skincluster)
        self.assertEqual(expected, result)


class TestDuplicateSkinnedMesh(mayatest.MayaTestCase):
    def test_default_params(self):
        test_cube, test_joints, test_skincluster = self.create_skinned_cube()
        dup_cube, dup_cluster = skinutils.duplicate_skinned_mesh(test_cube)
        self.scene_nodes.extend([dup_cube, dup_cluster])
        self.assertListEqual(test_joints, dup_cluster.influenceObjects())
        self.assertNotEqual(test_cube, dup_cube)
        test_weights = skinutils.get_vert_indexes_to_weighted_influences(test_skincluster)
        dup_weights = skinutils.get_vert_indexes_to_weighted_influences(dup_cluster)
        self.assertDictEqual(test_weights, dup_weights)

    def test_dup_skinnedmesh_and_skel(self):
        test_cube, test_joints, test_skincluster = self.create_skinned_cube()
        dup_cube, dup_root, dup_cluster = skinutils.duplicate_skinned_mesh_and_skeleton(test_cube)
        self.scene_nodes.extend([dup_cube, dup_root, dup_cluster])
        self.assertEqual(len(test_joints), len(dup_cluster.influenceObjects()))
        self.assertNotEqual(test_joints, dup_cluster.influenceObjects())
        self.assertNotEqual(test_cube, dup_cube)

    def test_dup_namespace(self):
        test_cube, test_joints, test_skincluster = self.create_skinned_cube()
        pm.namespace(set=':')
        self.create_namespace('foo')
        dup_cube, dup_root, dup_cluster = skinutils.duplicate_skinned_mesh_and_skeleton(test_cube, dup_namespace='foo')
        self.scene_nodes.extend([dup_cube, dup_root, dup_cluster])
        expected_joint_names = [x.nodeName(stripNamespace=True) for x in skelutils.get_hierarchy_from_root(test_joints[0])]
        result_joint_names = [x.nodeName(stripNamespace=True) for x in skelutils.get_hierarchy_from_root(dup_root)]
        self.assertListEqual(expected_joint_names, result_joint_names)
        self.assertNotEqual(test_joints, dup_cluster.influenceObjects())
        self.assertNotEqual(test_cube, dup_cube)
        self.assertEqual('foo', dup_root.parentNamespace())


class TestSetWeights(mayatest.MayaTestCase):
    def test_basic(self):
        test_cube, test_joints, test_skincluster = self.create_skinned_cube(joint_count=2)
        pm.skinPercent(test_skincluster, test_cube.vtx, transformValue=(test_joints[0], 1.0))
        test_skincluster.forceNormalizeWeights()
        verts_to_infs_wts = {0: {test_joints[1]: 1.0}}
        skinutils.set_weights(verts_to_infs_wts, skinned_mesh=test_cube, skin_cluster=test_skincluster)
        inf_values = pm.skinPercent(test_skincluster, test_cube.vtx[0], q=True, value=True)
        self.assertListEqual([0.0, 1.0], inf_values)
        inf_values = pm.skinPercent(test_skincluster, test_cube.vtx[1], q=True, value=True)
        self.assertListEqual([1.0, 0.0], inf_values)

    def test_more_complicated(self):
        test_cube, test_joints, test_skincluster = self.create_skinned_cube()
        pm.skinPercent(test_skincluster, test_cube.vtx, transformValue=(test_joints[0], 1.0))
        test_skincluster.forceNormalizeWeights()
        verts_to_infs_wts = {0: {test_joints[1]: 1.0},
                             3: {test_joints[3]: 1.0},
                             5: {test_joints[4]: 0.5, test_joints[0]: 0.5}}
        skinutils.set_weights(verts_to_infs_wts, skinned_mesh=test_cube, skin_cluster=test_skincluster)
        inf_values = pm.skinPercent(test_skincluster, test_cube.vtx[0], q=True, value=True)
        self.assertListEqual([0.0, 1.0, 0.0, 0.0, 0.0], inf_values)
        inf_values = pm.skinPercent(test_skincluster, test_cube.vtx[3], q=True, value=True)
        self.assertListEqual([0.0, 0.0, 0.0, 1.0, 0.0], inf_values)
        inf_values = pm.skinPercent(test_skincluster, test_cube.vtx[5], q=True, value=True)
        self.assertListEqual([0.5, 0.0, 0.0, 0.0, 0.5], inf_values)

    def test_raises_value_error_if_no_cluster_or_mesh(self):
        verts_to_infs_wts = {0: {'foo': 1.0}}
        self.assertRaises(ValueError, skinutils.set_weights, verts_to_infs_wts)



class TestGetSkMeshFromSkinCl(mayatest.MayaTestCase):
    def test_basic(self):
        test_cube, test_joints, test_skincluster = self.create_skinned_cube()
        result = skinutils.get_skinned_mesh_from_skin_cluster(test_skincluster)
        self.assertEqual(test_cube, result)

    def test_multiple_skinned_meshes(self):
        test_cube, test_joints, test_skincluster = self.create_skinned_cube()
        test_cube2 = self.create_cube()
        test_cl2 = skinutils.bind_mesh_to_joints(test_cube2, test_joints)
        result = skinutils.get_skinned_mesh_from_skin_cluster(test_skincluster)
        self.assertEqual(test_cube, result)