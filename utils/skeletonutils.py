from pymel import core as pm

import flottitools.utils.namespaceutils as namespaceutils
import flottitools.utils.transformutils as xformutils

# joint label side
LABEL_SIDE_CENTER = 0
LABEL_SIDE_LEFT = 1
LABEL_SIDE_RIGHT = 2
LABEL_SIDE_NONE = 3

# joint label names
LABEL_STR_NONE = 'None'
LABEL_STR_ROOT = 'Root'
LABEL_STR_HIP = 'Hip'
LABEL_STR_KNEE = 'Knee'
LABEL_STR_FOOT = 'Foot'
LABEL_STR_TOE = 'Toe'
LABEL_STR_SPINE = 'Spine'
LABEL_STR_NECK = 'Neck'
LABEL_STR_HEAD = 'Head'
LABEL_STR_COLLAR = 'Collar'
LABEL_STR_SHOULDER = 'Shoulder'
LABEL_STR_ELBOW = 'Elbow'
LABEL_STR_HAND = 'Hand'
LABEL_STR_FINGER = 'Finger'
LABEL_STR_THUMB = 'Thumb'
LABEL_STR_PROP_A = 'PropA'
LABEL_STR_PROP_B = 'PropB'
LABEL_STR_PROP_C = 'PropC'
LABEL_STR_OTHER = 'Other'
LABEL_STR_INDEX_FINGER = 'Index Finger'
LABEL_STR_MIDDLE_FINGER = 'Middle Finger'
LABEL_STR_RING_FINGER = 'Ring Finger'
LABEL_STR_PINKY_FINGER = 'Pinky Finger'
LABEL_STR_EXTRA_FINGER = 'Extra Finger'
LABEL_STR_BIG_TOE = 'Big Toe'
LABEL_STR_INDEX_TOE = 'Index Toe'
LABEL_STR_MIDDLE_TOE = 'Middle Toe'
LABEL_STR_RING_TOE = 'Ring Toe'
LABEL_STR_PINKY_TOE = 'Pinky Toe'
LABEL_STR_FOOT_THUMB = 'Extra Toe'

LABEL_INT_NONE = 0
LABEL_INT_ROOT = 1
LABEL_INT_HIP = 2
LABEL_INT_KNEE = 3
LABEL_INT_FOOT = 4
LABEL_INT_TOE = 5
LABEL_INT_SPINE = 6
LABEL_INT_NECK = 7
LABEL_INT_HEAD = 8
LABEL_INT_COLLAR = 9
LABEL_INT_SHOULDER = 10
LABEL_INT_ELBOW = 11
LABEL_INT_HAND = 12
LABEL_INT_FINGER = 13
LABEL_INT_THUMB = 14
LABEL_INT_PROP_A = 15
LABEL_INT_PROP_B = 16
LABEL_INT_PROP_C = 17
LABEL_INT_OTHER = 18
LABEL_INT_INDEX_FINGER = 19
LABEL_INT_MIDDLE_FINGER = 20
LABEL_INT_RING_FINGER = 21
LABEL_INT_PINKY_FINGER = 22
LABEL_INT_EXTRA_FINGER = 23
LABEL_INT_BIG_TOE = 24
LABEL_INT_INDEX_TOE = 25
LABEL_INT_MIDDLE_TOE = 26
LABEL_INT_RING_TOE = 27
LABEL_INT_PINKY_TOE = 28
LABEL_INT_FOOT_THUMB = 29

LABEL_SIDES_LIST = [LABEL_SIDE_CENTER,
                    LABEL_SIDE_LEFT,
                    LABEL_SIDE_RIGHT,
                    LABEL_SIDE_NONE]

LABEL_STR_LIST = [LABEL_STR_NONE,
                  LABEL_STR_ROOT,
                  LABEL_STR_HIP,
                  LABEL_STR_KNEE,
                  LABEL_STR_FOOT,
                  LABEL_STR_TOE,
                  LABEL_STR_SPINE,
                  LABEL_STR_NECK,
                  LABEL_STR_HEAD,
                  LABEL_STR_COLLAR,
                  LABEL_STR_SHOULDER,
                  LABEL_STR_ELBOW,
                  LABEL_STR_HAND,
                  LABEL_STR_FINGER,
                  LABEL_STR_THUMB,
                  LABEL_STR_PROP_A,
                  LABEL_STR_PROP_B,
                  LABEL_STR_PROP_C,
                  LABEL_STR_OTHER,
                  LABEL_STR_INDEX_FINGER,
                  LABEL_STR_MIDDLE_FINGER,
                  LABEL_STR_RING_FINGER,
                  LABEL_STR_PINKY_FINGER,
                  LABEL_STR_EXTRA_FINGER,
                  LABEL_STR_BIG_TOE,
                  LABEL_STR_INDEX_TOE,
                  LABEL_STR_MIDDLE_TOE,
                  LABEL_STR_RING_TOE,
                  LABEL_STR_PINKY_TOE,
                  LABEL_STR_FOOT_THUMB]

LABEL_INT_LIST = [LABEL_INT_NONE,
                  LABEL_INT_ROOT,
                  LABEL_INT_HIP,
                  LABEL_INT_KNEE,
                  LABEL_INT_FOOT,
                  LABEL_INT_TOE,
                  LABEL_INT_SPINE,
                  LABEL_INT_NECK,
                  LABEL_INT_HEAD,
                  LABEL_INT_COLLAR,
                  LABEL_INT_SHOULDER,
                  LABEL_INT_ELBOW,
                  LABEL_INT_HAND,
                  LABEL_INT_FINGER,
                  LABEL_INT_THUMB,
                  LABEL_INT_PROP_A,
                  LABEL_INT_PROP_B,
                  LABEL_INT_PROP_C,
                  LABEL_INT_OTHER,
                  LABEL_INT_INDEX_FINGER,
                  LABEL_INT_MIDDLE_FINGER,
                  LABEL_INT_RING_FINGER,
                  LABEL_INT_PINKY_FINGER,
                  LABEL_INT_EXTRA_FINGER,
                  LABEL_INT_BIG_TOE,
                  LABEL_INT_INDEX_TOE,
                  LABEL_INT_MIDDLE_TOE,
                  LABEL_INT_RING_TOE,
                  LABEL_INT_PINKY_TOE,
                  LABEL_INT_FOOT_THUMB]


def get_joint_label(joint_node):
    label_side = joint_node.side.get()
    label_type = joint_node.attr('type').get()
    label_other_string = None
    if label_type == LABEL_INT_OTHER:
        label_other_string = joint_node.otherType.get()
    return label_side, label_type, label_other_string


def get_influence_map(source_influences, target_influences, mapping_methods=None):
    # mapping methods should try to have one source to one target.
    # If there are more targets than sources then all sources should be used and extra targets are left unmapped.
    # If there are more sources than targets then targets should be used by multiple sources
    # I can't think of a case for one source multiple targets...
    mapping_methods = mapping_methods or [update_inf_map_by_label,
                                          update_inf_map_by_name,
                                          update_inf_map_by_worldspace_position,
                                          update_inf_map_by_influence_order]
    influence_map = {}
    unmapped_target_infs = target_influences
    unmapped_source_infs = source_influences
    for mapping_method in mapping_methods:
        if not unmapped_source_infs:
            # If every source influence has one target influence then we're done.
            break
        if not unmapped_target_infs:
            # If we still have unmapped source influences but we've used all the target influences
            # then we need to start re-using target influences until all sources have a target.
            unmapped_target_infs = target_influences
        influence_map, unmapped_target_infs, unmapped_source_infs = mapping_method(
            unmapped_source_infs, unmapped_target_infs, influence_map)
    return influence_map, unmapped_target_infs, unmapped_source_infs


def update_inf_map_by_label(source_infs, target_infs, influence_map=None):
    """influence_map data structure: {source_inf: [target_inf1]}"""
    def _match_label(source_influence, target_influences):
        source_label_parts = get_joint_label(source_influence)
        for target_inf in target_influences:
            target_label_parts = get_joint_label(target_inf)
            if target_label_parts[1] == LABEL_INT_NONE:
                continue
            if all([x == y for x, y in zip(source_label_parts, target_label_parts)]):
                return target_inf
    return _update_inf_map(source_infs, target_infs, influence_map, _match_label)


def update_inf_map_by_name(source_joints, target_joints, influence_map=None):
    influence_map = influence_map or {}

    def names_match(source_influence, target_influences):
        for target_influence in target_influences:
            if source_influence.nodeName(stripNamespace=True) == target_influence.nodeName(stripNamespace=True):
                return target_influence
    return _update_inf_map(source_joints, target_joints, influence_map, names_match)


def update_inf_map_by_worldspace_position(source_joints, target_joints, influence_map=None, tolerance=0.001):
    influence_map = influence_map or {}

    def worldspace_position_matches(source_influence, target_influences):
        source_pos = xformutils.get_worldspace_vector(source_influence)
        for target_influence in target_influences:
            if xformutils.node_almost_matches_worldspace_position(target_influence, source_pos, tolerance=tolerance):
                return target_influence
    return _update_inf_map(source_joints, target_joints, influence_map, worldspace_position_matches)


def update_inf_map_by_closest_inf(source_infs, target_infs, influence_map=None):
    influence_map = influence_map or {}

    def find_closest_inf(source_influence, target_influences):
        source_position = xformutils.get_worldspace_vector(source_influence)
        min_dis = None
        min_dis_target_inf = None
        for target_influence in target_influences:
            target_position = xformutils.get_worldspace_vector(target_influence)
            distance = abs((source_position - target_position).length())
            min_dis = min_dis or distance
            min_dis_target_inf = min_dis_target_inf or target_influence
            if distance < min_dis:
                min_dis = distance
                min_dis_target_inf = target_influence
        return min_dis_target_inf
    return _update_inf_map(source_infs, target_infs, influence_map, find_closest_inf)


def update_inf_map_by_influence_order(source_joints, target_joints, influence_map=None):
    inf_map = influence_map or {}
    [append_target_to_influence_map(inf_map, *x) for x in zip(source_joints, target_joints)]
    remaining_target_infs = []
    if len(target_joints) > len(source_joints):
        remaining_target_infs = target_joints[len(source_joints):]
    remaining_source_infs = []
    if len(source_joints) > len(target_joints):
        remaining_source_infs = source_joints[len(target_joints):]
    return inf_map, remaining_target_infs, remaining_source_infs


def append_target_to_influence_map(influence_map, map_key, value_to_append):
    source_inf_value = influence_map.setdefault(map_key, [])
    if value_to_append not in source_inf_value:
        source_inf_value.append(value_to_append)


def _update_inf_map(source_infs, target_infs, influence_map=None, get_matching_influence_method=None):
    inf_map = influence_map or {}
    unmapped_target_infs = target_infs[:]
    unmapped_source_infs = source_infs[:]
    for source_inf in source_infs:
        matching_target_inf = get_matching_influence_method(source_inf, unmapped_target_infs)
        if matching_target_inf:
            append_target_to_influence_map(inf_map, source_inf, matching_target_inf)
            unmapped_target_infs.remove(matching_target_inf)
            unmapped_source_infs.remove(source_inf)
    return inf_map, unmapped_target_infs, unmapped_source_infs


def duplicate_skeleton(root_joint, dup_parent=None, dup_namespace=None):
    dup_namespace = dup_namespace or pm.namespaceInfo(currentNamespace=True)
    dup_root = namespaceutils.duplicate_to_namespace(
        [root_joint], dup_namespace=dup_namespace, dup_parent=dup_parent)[0]
    dup_hierarchy = get_hierarchy_from_root(dup_root)
    to_delete = get_extra_nodes_in_skeleton(dup_hierarchy)
    pm.delete(to_delete)
    return dup_root


def get_extra_nodes_in_skeleton(skeleton_nodes):
    only_joints = pm.ls(skeleton_nodes, type='joint')
    if len(only_joints) == len(skeleton_nodes):
        return []
    not_joints = [x for x in skeleton_nodes if not isinstance(x, pm.nt.Joint)]
    extra_nodes = []
    for each in not_joints:
        children = each.getChildren(allDescendents=True)
        child_joints = pm.ls(children, type='joint')
        if not child_joints:
            extra_nodes.append(each)
    return extra_nodes


def get_hierarchy_from_root(root_node, joints_only=False):
    hierarchy = root_node.getChildren(allDescendents=True, type=pm.nt.Transform)
    hierarchy.append(root_node)
    hierarchy.reverse()
    if joints_only:
        hierarchy = pm.ls(hierarchy, type=pm.nt.Joint)
    return hierarchy


def get_bind_poses(joint):
    root_joint = get_root_joint_from_child(joint)
    return list(set(root_joint.outputs(type=pm.nt.DagPose)))


def get_root_joint_from_child(dag_node):
    all_parents = dag_node.getAllParents()
    all_parent_joints = pm.ls(all_parents, type=pm.nt.Joint)
    try:
        return all_parent_joints[-1]
    except IndexError:
        if isinstance(dag_node, pm.nt.Joint):
            return dag_node


def get_perpendicular_vector_from_three_points(vec1, vec2, vec3):
    v1 = vec1 - vec2
    v2 = vec1 - vec3
    cross_product = v1 ^ v2
    world_up_v = cross_product.normalize()
    return world_up_v


def orient_three_joints(joint1, joint2, joint3, world_up_v=None, flippy=1, up_v=(0, 0, 1)):
    joints = [joint1, joint2, joint3]
    if world_up_v is None:
        jv1 = xformutils.get_worldspace_vector(joint1)
        jv2 = xformutils.get_worldspace_vector(joint2)
        jv3 = xformutils.get_worldspace_vector(joint3)
        v1 = jv1 - jv2
        v2 = jv1 - jv3
        cross_product = v1 ^ v2
        world_up_v = cross_product.normalize()
    world_up_v = world_up_v * flippy

    aim_vector = (1, 0, 0)
    # up_v = (0, 0, 1)
    # aimConstraint -offset 0 0 0 -weight 1 -aimVector 1 0 0 -upVector 0 0 1 -worldUpType "vector" -worldUpVector 0 0 1;
    for i, joint in enumerate(joints):
        next_index = i + 1
        try:
            next_joint = joints[next_index]
            # next_jv = joint_vectors[next_index]
        except IndexError:
            if not joint.getChildren():
                joint.jointOrient.set(0, 0, 0)
            return
        jp = joint.getParent()
        # jv = joint_vectors[i]
        joint.setParent(world=True)
        next_joint.setParent(world=True)

        aim_con = pm.aimConstraint(
            next_joint, joint, aimVector=aim_vector, upVector=up_v, worldUpType="vector", worldUpVector=world_up_v)
        pm.delete(aim_con)
        # makeIdentity -apply true -t 0 -r 1 -s 0 -n 0 -pn 1;
        pm.makeIdentity(joint, apply=True, t=False, r=True, s=False, n=False, pn=True)
        pm.makeIdentity(next_joint, apply=True, t=False, r=True, s=False, n=False, pn=True)
        joint.setParent(jp)
        next_joint.setParent(joint)


def orient_joints(joints, world_up_v, up_v=(0, 0, 1), aim_vector=(1, 0, 0), flippy=1):
    world_up_v = world_up_v * flippy
    for i, joint in enumerate(joints):
        next_index = i + 1
        try:
            next_joint = joints[next_index]
            # next_jv = joint_vectors[next_index]
        except IndexError:
            if not joint.getChildren():
                joint.jointOrient.set(0, 0, 0)
            return
        jp = joint.getParent()
        # jv = joint_vectors[i]
        joint.setParent(world=True)
        next_joint.setParent(world=True)

        aim_con = pm.aimConstraint(
            next_joint, joint, aimVector=aim_vector, upVector=up_v, worldUpType="vector", worldUpVector=world_up_v)
        pm.delete(aim_con)
        # makeIdentity -apply true -t 0 -r 1 -s 0 -n 0 -pn 1;
        pm.makeIdentity(joint, apply=True, t=False, r=True, s=False, n=False, pn=True)
        pm.makeIdentity(next_joint, apply=True, t=False, r=True, s=False, n=False, pn=True)
        joint.setParent(jp)
        next_joint.setParent(joint)


def get_extra_root_joints_from_root_joint(root_joint):
    all_children = root_joint.getChildren(allDescendents=True)
    extra_nodes = [x for x in all_children if x.type() != 'joint']
    extra_roots = []
    for extra_node in extra_nodes:
        extra_joints = extra_node.getChildren(allDescendents=True, type=pm.nt.Joint)
        try:
            extra_roots.append(extra_joints[-1])
        except IndexError:
            pass
    return extra_roots
