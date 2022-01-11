import pymel.core as pm

import flottitools.test as mayatest
import flottitools.utils.skeletonutils as skeletonutils


class TestGetJointLabel(mayatest.MayaTestCase):
    def test_default_joint(self):
        test_joint = self.create_joint()
        result = skeletonutils.get_joint_label(test_joint)
        self.assertTupleEqual((0, 0, None), result)

    def test_returns_correct_side(self):
        test_joint = self.create_joint()

        def assert_side(side):
            test_joint.side.set(side)
            expected = (side, 0, None)
            result = skeletonutils.get_joint_label(test_joint)
            self.assertTupleEqual(expected, result)
        for side in skeletonutils.LABEL_SIDES_LIST:
            assert_side(side)

    def test_returns_correct_type(self):
        test_joint = self.create_joint()

        def assert_label_type(label_type, expected=None):
            test_joint.attr('type').set(label_type)
            expected = expected or (0, label_type, None)
            result = skeletonutils.get_joint_label(test_joint)
            self.assertTupleEqual(expected, result)
        for label_type in skeletonutils.LABEL_INT_LIST:
            if label_type == skeletonutils.LABEL_INT_OTHER:
                # test the otherType joint label in another test
                continue
            assert_label_type(label_type)

    def test_other_type(self):
        test_joint = self.create_joint()
        test_joint.attr('type').set(skeletonutils.LABEL_INT_OTHER)
        test_joint.otherType.set('foo')
        expected = (0, skeletonutils.LABEL_INT_OTHER, 'foo')
        result = skeletonutils.get_joint_label(test_joint)
        self.assertTupleEqual(expected, result)

    def test_other_type_returns_none_if_type_not_other(self):
        test_joint = self.create_joint()
        test_joint.attr('type').set(skeletonutils.LABEL_INT_KNEE)
        test_joint.otherType.set('foo')
        expected = (0, skeletonutils.LABEL_INT_KNEE, None)
        result = skeletonutils.get_joint_label(test_joint)
        self.assertTupleEqual(expected, result)


class TestGetInfluenceMap(mayatest.MayaTestCase):
    def test_get_by_label(self):
        source_joints = [self.create_joint() for _ in range(5)]
        target_joints = [self.create_joint() for _ in range(5)]
        for i, source_and_target in enumerate(zip(source_joints, target_joints)):
            for joint in source_and_target:
                joint.side.set(skeletonutils.LABEL_SIDE_LEFT)
                joint.attr('type').set(skeletonutils.LABEL_INT_LIST[i+1])
        result_map, result_remaining = skeletonutils.update_inf_map_by_label(source_joints, target_joints)
        expected_map = dict([(x, [y]) for x, y in zip(source_joints, target_joints)])
        self.assertDictEqual(result_map, expected_map)
        self.assertListEqual([], result_remaining)

    def test_by_label_not_in_index_order(self):
        source_joints = [self.create_joint() for _ in range(5)]
        target_joints = [self.create_joint() for _ in range(5)]
        for i, source_joint in enumerate(source_joints):
            source_joint.attr('type').set(skeletonutils.LABEL_INT_LIST[i+1])
        for i, target_joint in enumerate(reversed(target_joints)):
            target_joint.attr('type').set(skeletonutils.LABEL_INT_LIST[i+1])
        result_map, result_remaining = skeletonutils.update_inf_map_by_label(source_joints, target_joints)
        expected_map = dict([(x, [y]) for x, y in zip(source_joints, reversed(target_joints))])
        self.assertDictEqual(result_map, expected_map)
        self.assertListEqual([], result_remaining)

    def test_by_label_multiple_targets_for_one_source(self):
        source_joints = [self.create_joint() for _ in range(5)]
        target_joints = [self.create_joint() for _ in range(8)]
        expected_map = {}
        for i, source_joint in enumerate(source_joints):
            source_joint.attr('type').set(skeletonutils.LABEL_INT_LIST[i+1])
        for i, target_joint in enumerate(target_joints):
            index = i % 4
            target_joint.attr('type').set(skeletonutils.LABEL_INT_LIST[index+1])
            thing = expected_map.setdefault(source_joints[index], [])
            thing.append(target_joint)
        result_map, result_remaining = skeletonutils.update_inf_map_by_label(source_joints, target_joints)
        self.assertDictEqual(result_map, expected_map)
        self.assertListEqual([], result_remaining)

    def test_by_label_unmapped_joints(self):
        source_joints = [self.create_joint() for _ in range(5)]
        target_joints = [self.create_joint() for _ in range(8)]
        expected_map = {}
        for i, source_joint in enumerate(source_joints):
            source_joint.attr('type').set(skeletonutils.LABEL_INT_LIST[i+1])
            expected_map[source_joint] = [target_joints[i]]
        for i, target_joint in enumerate(target_joints):
            target_joint.attr('type').set(skeletonutils.LABEL_INT_LIST[i+1])
        result_map, result_remaining = skeletonutils.update_inf_map_by_label(source_joints, target_joints)
        self.assertDictEqual(result_map, expected_map)
        self.assertListEqual(target_joints[5:], result_remaining)

    def test_by_label_sides(self):
        source_joints = [self.create_joint() for _ in range(5)]
        target_joints = [self.create_joint() for _ in range(5)]
        expected_map = {}
        for i, source_joint in enumerate(source_joints):
            source_joint.attr('type').set(skeletonutils.LABEL_SIDES_LIST[i % 3])
            source_joint.attr('type').set(skeletonutils.LABEL_INT_LIST[i+1])
        for i, target_joint in enumerate(target_joints):
            target_joint.attr('type').set(skeletonutils.LABEL_SIDES_LIST[i % 3])
            target_joint.attr('type').set(skeletonutils.LABEL_INT_LIST[i+1])
            expected_map[source_joints[i]] = [target_joint]
        result_map, result_remaining = skeletonutils.update_inf_map_by_label(source_joints, target_joints)
        self.assertDictEqual(result_map, expected_map)
        self.assertListEqual([], result_remaining)

    def test_by_label_other_type(self):
        source_joints = [self.create_joint() for _ in range(5)]
        target_joints = [self.create_joint() for _ in range(5)]
        expected_map = {}
        for i, source_joint in enumerate(source_joints):
            source_joint.attr('type').set(skeletonutils.LABEL_INT_OTHER)
            source_joint.otherType.set('foo{}'.format(i))
        for i, target_joint in enumerate(target_joints):
            target_joint.attr('type').set(skeletonutils.LABEL_INT_OTHER)
            target_joint.otherType.set('foo{}'.format(i))
            expected_map[source_joints[i]] = [target_joint]
        result_map, result_remaining = skeletonutils.update_inf_map_by_label(source_joints, target_joints)
        self.assertDictEqual(result_map, expected_map)
        self.assertListEqual([], result_remaining)

    def test_by_label_no_label(self):
        source_joints = [self.create_joint() for _ in range(5)]
        target_joints = [self.create_joint() for _ in range(5)]
        result_map, result_remaining = skeletonutils.update_inf_map_by_label(source_joints, target_joints)
        self.assertDictEqual(result_map, {})
        self.assertListEqual(target_joints, result_remaining)

    def test_by_name(self):
        source_joints = [self.create_joint() for _ in range(5)]
        target_joints = [self.create_joint() for _ in range(5)]
        expected_map = {}
        for i, (sj, tj) in enumerate(zip(source_joints[1:], target_joints[1:])):
            new_name = 'foo{}'.format(i)
            sj.rename(new_name)
            tj.rename(new_name)
            expected_map[sj] = [tj]
        result_map, result_remaining = skeletonutils.update_inf_map_by_name(source_joints, target_joints)
        self.assertDictEqual(result_map, expected_map)
        self.assertListEqual([target_joints[0]], result_remaining)

    def test_by_name_different_namespaces(self):
        source_namespace = self.pm.namespace(addNamespace='foo')
        pm.namespace(setNamespace=':')
        target_namespace = self.pm.namespace(addNamespace='bar')
        pm.namespace(setNamespace=source_namespace)
        source_joints = [self.create_joint() for _ in range(5)]
        pm.namespace(setNamespace=':')
        pm.namespace(setNamespace=target_namespace)
        target_joints = [self.create_joint() for _ in range(5)]
        pm.namespace(setNamespace=':')
        expected_map = {}
        for i, (sj, tj) in enumerate(zip(source_joints[1:], target_joints[1:])):
            new_name = 'foo{}'.format(i)
            sj.rename(new_name)
            tj.rename(new_name)
            expected_map[sj] = [tj]
        result_map, result_remaining = skeletonutils.update_inf_map_by_name(source_joints, target_joints)
        self.assertDictEqual(result_map, expected_map)
        self.assertListEqual([target_joints[0]], result_remaining)

    def test_by_worldspace_position(self):
        source_joints = [self.create_joint() for _ in range(5)]
        target_joints = [self.create_joint() for _ in range(5)]
        target_joints[0].setParent(world=True)
        expected_map = {}
        for sj, tj in zip(source_joints, target_joints):
            pm.move(sj, (1, 0, 0), objectSpace=True)
            pm.move(tj, (1, 0, 0), objectSpace=True)
            expected_map[sj] = [tj]
        result_map, result_remaining = skeletonutils.update_inf_map_by_worldspace_position(source_joints, target_joints)
        self.assertDictEqual(result_map, expected_map)
        self.assertListEqual([], result_remaining)

    def test_by_worldspace_position_remaining_infs(self):
        source_joints = [self.create_joint() for _ in range(5)]
        target_joints = [self.create_joint() for _ in range(5)]
        target_joints[0].setParent(world=True)
        expected_map = {}
        pm.move(target_joints[0], (20, 0, 0))
        pm.move(target_joints[-1], (-20, 0, 0))
        for i, (sj, tj) in enumerate(zip(source_joints[1:-1], target_joints[1:-1])):
            pm.move(sj, (i+10, 0, 0))
            pm.move(tj, (i+10, 0, 0))
            expected_map[sj] = [tj]
        result_map, result_remaining = skeletonutils.update_inf_map_by_worldspace_position(source_joints, target_joints)
        self.assertDictEqual(result_map, expected_map)
        self.assertListEqual([target_joints[0], target_joints[-1]], result_remaining)

    def test_by_influence_order(self):
        source_cube, source_joints, source_skin_cluster = self.create_skinned_cube()
        target_cube, target_joints, target_skin_cluster = self.create_skinned_cube()
        expected_map = dict([(x, [y]) for x, y in zip(source_joints, target_joints)])
        result_map, result_remaining = skeletonutils.update_inf_map_by_influence_order(source_joints, target_joints)
        self.assertDictEqual(result_map, expected_map)
        self.assertListEqual([], result_remaining)

    def test_influence_order_extra_sources(self):
        source_cube = self.create_cube()
        source_joints = [self.create_joint() for _ in range(8)]
        source_skin_cluster = self.pm.skinCluster(source_joints, source_cube, maximumInfluences=4)
        self.scene_nodes.append(source_skin_cluster)
        target_cube, target_joints, target_skin_cluster = self.create_skinned_cube()
        expected_map = dict([(x, [y]) for x, y in zip(source_joints[:5], target_joints)])
        result_map, result_remaining = skeletonutils.update_inf_map_by_influence_order(source_joints, target_joints)
        self.assertDictEqual(result_map, expected_map)
        self.assertListEqual([], result_remaining)

    def test_influence_order_extra_targets(self):
        source_cube, source_joints, source_skin_cluster = self.create_skinned_cube()
        target_cube = self.create_cube()
        target_joints = [self.create_joint() for _ in range(8)]
        target_skin_cluster = self.pm.skinCluster(target_joints, target_cube, maximumInfluences=4)
        self.scene_nodes.append(target_skin_cluster)
        expected_map = dict([(x, [y]) for x, y in zip(source_joints, target_joints[:5])])
        result_map, result_remaining = skeletonutils.update_inf_map_by_influence_order(source_joints, target_joints)
        self.assertDictEqual(result_map, expected_map)
        self.assertListEqual(target_joints[5:], result_remaining)

    def test_get_influence_map(self):
        source_joints = [self.create_joint() for _ in range(15)]
        target_joints = [self.create_joint() for _ in range(15)]
        target_joints[0].setParent(world=True)
        for i, source_joint in enumerate(source_joints[:5]):
            source_joint.attr('type').set(skeletonutils.LABEL_INT_LIST[i+1])
        for i, target_joint in enumerate(reversed(target_joints[:5])):
            target_joint.attr('type').set(skeletonutils.LABEL_INT_LIST[i+1])
        expected_map = dict([(x, [y]) for x, y in zip(source_joints[:5], reversed(target_joints[:5]))])
        for i, (sj, tj) in enumerate(zip(source_joints[5:10], target_joints[5:10])):
            new_name = 'foo{}'.format(i)
            sj.rename(new_name)
            tj.rename(new_name)
            expected_map[sj] = [tj]
        target_joints[0].setParent(world=True)
        for sj, tj in zip(source_joints[10:], target_joints[10:]):
            pm.move(sj, (1, 0, 0), objectSpace=True)
            pm.move(tj, (1, 0, 0), objectSpace=True)
            expected_map[sj] = [tj]
        result_map, result_remaining = skeletonutils.get_influence_map(source_joints, target_joints)
        self.assertDictEqual(result_map, expected_map)
        self.assertListEqual([], result_remaining)

    def test_update_inf_map_by_closest_inf(self):
        source_joints = [self.create_joint(position=(i, 0, 0), absolute=True) for i in range(5)]
        target_joints = [self.create_joint(position=(i+.02, 0, 0), absolute=True) for i in range(5)]
        result, _ = skeletonutils.update_inf_map_by_closest_inf(source_joints, target_joints)
        expected = dict([(sj, [tj]) for sj, tj in zip(source_joints, target_joints)])
        self.assertDictEqual(expected, result)

    def test_closet_inf_different_order(self):
        source_joints = [self.create_joint(position=(i, 0, 0), absolute=True) for i in range(5)]
        target_joints = [self.create_joint(position=(4.2-i, 0, 0), absolute=True) for i in range(5)]
        result, _ = skeletonutils.update_inf_map_by_closest_inf(source_joints, target_joints)
        expected = dict([(sj, [tj]) for sj, tj in zip(source_joints, reversed(target_joints))])
        self.assertDictEqual(expected, result)

    def test_closest_inf_more_than_one_target(self):
        source_joints = [self.create_joint(position=(i, 0, 0), absolute=True) for i in range(5)]
        target_joints = [self.create_joint(position=(5.2-i, 0, 0), absolute=True) for i in range(5)]
        result, _ = skeletonutils.update_inf_map_by_closest_inf(source_joints, target_joints)
        expected = {source_joints[4]: [target_joints[0], target_joints[1]],
                    source_joints[3]: [target_joints[2]],
                    source_joints[2]: [target_joints[3]],
                    source_joints[1]: [target_joints[4]]}
        self.assertDictEqual(expected, result)


class TestGetRootFromChild(mayatest.MayaTestCase):
    def test_get_root_joint_from_child(self):
        test_joints = [self.create_joint() for _ in range(5)]
        result = skeletonutils.get_root_joint_from_child(test_joints[4])
        self.assertEqual(test_joints[0], result)

    def test_root_joint_under_transform_node(self):
        test_node = self.create_transform_node()
        test_joints = [self.create_joint() for _ in range(5)]
        test_joints[0].setParent(test_node)
        result = skeletonutils.get_root_joint_from_child(test_joints[4])
        self.assertEqual(test_joints[0], result)

    def test_node_is_root_joint(self):
        test_joints = [self.create_joint() for _ in range(5)]
        result = skeletonutils.get_root_joint_from_child(test_joints[0])
        self.assertEqual(test_joints[0], result)


class TestGetBindPoses(mayatest.MayaTestCase):
    def test_get_bind_poses(self):
        test_joints = [self.create_joint(position=(i, i, i)) for i in range(5)]
        expected = [pm.dagPose(test_joints[0], bindPose=True, save=True)]
        result = skeletonutils.get_bind_poses(test_joints[0])
        self.assertEqual(expected, result)


class TestDuplicateSkeleton(mayatest.MayaTestCase):
    def test_duplicates_skeleton(self):
        test_joints = [self.create_joint(position=(i, i, i)) for i in range(5)]
        dup_root = skeletonutils.duplicate_skeleton(test_joints[0])
        expected = [x.nodeName() for x in skeletonutils.get_hierarchy_from_root(test_joints[0])[1:]]
        result = [x.nodeName() for x in skeletonutils.get_hierarchy_from_root(dup_root)[1:]]
        self.assertListEqual(expected, result)

    def test_cleans_trash(self):
        test_joints = [self.create_joint(position=(i, i, i)) for i in range(5)]
        dummy_cube = self.create_cube()
        pm.parentConstraint(dummy_cube, test_joints[1])
        dup_root = skeletonutils.duplicate_skeleton(test_joints[0])
        dup_joints = dup_root.getChildren(allDescendents=True)
        dup_joints.append(dup_root)
        self.assertEqual(5, len(dup_joints))

    def test_parent(self):
        test_joints = [self.create_joint(position=(i, i, i)) for i in range(5)]
        parent_node = self.create_transform_node()
        dup_root = skeletonutils.duplicate_skeleton(test_joints[0], dup_parent=parent_node)
        expected = [x.nodeName() for x in skeletonutils.get_hierarchy_from_root(test_joints[0])]
        result = [x.nodeName() for x in skeletonutils.get_hierarchy_from_root(dup_root)]
        self.assertListEqual(expected, result)
        self.assertEqual(parent_node, dup_root.getParent())

    def test_namespace(self):
        test_joints = [self.create_joint(position=(i, i, i)) for i in range(5)]
        self.create_namespace('foo')
        dup_root = skeletonutils.duplicate_skeleton(test_joints[0], dup_namespace='foo')
        expected = [x.nodeName(stripNamespace=True) for x in skeletonutils.get_hierarchy_from_root(test_joints[0])]
        result = [x.nodeName(stripNamespace=True) for x in skeletonutils.get_hierarchy_from_root(dup_root)]
        self.assertListEqual(expected, result)
        self.assertEqual('foo', dup_root.parentNamespace())


class TestGetExtraNodesInSkeleton(mayatest.MayaTestCase):
    def test_several_cases(self):
        test_joints = [self.create_joint(position=(i, i, i)) for i in range(5)]
        dummy_cube = self.create_cube()
        dummy_cube2 = self.create_cube()
        dummy_cube3 = self.create_cube()
        con = pm.parentConstraint(dummy_cube, test_joints[0])
        dummy_cube2.setParent(test_joints[1])
        dummy_cube3.setParent(test_joints[2])
        test_joints[4].setParent(dummy_cube3)
        expected = [con, dummy_cube2]
        hierarchy = test_joints[0].getChildren(allDescendents=True, type='transform')
        hierarchy.append(test_joints[0])
        hierarchy.reverse()
        result = skeletonutils.get_extra_nodes_in_skeleton(hierarchy)
        self.assertListEqual(expected, result)


class TestGetHierarchyFromRoot(mayatest.MayaTestCase):
    def test_default_params(self):
        test_joints = [self.create_joint(position=(i, i, i)) for i in range(5)]
        dummy_cube = self.create_cube()
        dummy_cube2 = self.create_cube()
        dummy_cube3 = self.create_cube()
        con = pm.parentConstraint(dummy_cube, test_joints[0])
        dummy_cube2.setParent(test_joints[1])
        dummy_cube3.setParent(test_joints[2])
        test_joints[4].setParent(dummy_cube3)
        expected = test_joints[0].getChildren(allDescendents=True, type='transform')
        expected.append(test_joints[0])
        expected.reverse()
        result = skeletonutils.get_hierarchy_from_root(test_joints[0])
        self.assertListEqual(expected, result)

    def test_joints_only(self):
        test_joints = [self.create_joint(position=(i, i, i)) for i in range(5)]
        dummy_cube = self.create_cube()
        dummy_cube2 = self.create_cube()
        dummy_cube3 = self.create_cube()
        con = pm.parentConstraint(dummy_cube, test_joints[0])
        dummy_cube2.setParent(test_joints[1])
        dummy_cube3.setParent(test_joints[2])
        test_joints[4].setParent(dummy_cube3)
        expected = test_joints[0].getChildren(allDescendents=True, type='transform')
        expected.append(test_joints[0])
        expected.reverse()
        expected = pm.ls(expected, type='joint')
        result = skeletonutils.get_hierarchy_from_root(test_joints[0], joints_only=True)
        self.assertListEqual(expected, result)


