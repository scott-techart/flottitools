from pymel import core as pm

import flottitools.utils.namespaceutils as nsutils
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


def update_inf_map_by_label(source_infs, target_infs, influence_map=None):
    """influence_map data structure: {source_inf: [target_inf1]}"""
    source_labels = [get_joint_label(source_inf) for source_inf in source_infs]
    inf_map = influence_map or {}
    unmapped_target_infs = target_infs[:]
    for target_inf in target_infs:
        tgt_stuff = get_joint_label(target_inf)
        if tgt_stuff[1] == LABEL_INT_NONE:
            continue
        for i, src_stuff in enumerate(source_labels):
            if src_stuff[1] == LABEL_INT_NONE:
                continue
            if all([x == y for x, y in zip(src_stuff, tgt_stuff)]):
                append_target_to_influence_map(inf_map, source_infs[i], target_inf)
                unmapped_target_infs.remove(target_inf)
                break
    return inf_map, unmapped_target_infs


def get_joint_label(joint_node):
    label_side = joint_node.side.get()
    label_type = joint_node.attr('type').get()
    label_other_string = None
    if label_type == LABEL_INT_OTHER:
        label_other_string = joint_node.otherType.get()
    return label_side, label_type, label_other_string


def update_inf_map_by_name(source_joints, target_joints, influence_map=None):
    inf_map = influence_map or {}

    def names_match(source_inf, target_inf):
        return source_inf.nodeName() == target_inf.nodeName()
    unmapped_target_infs = _get_remaining_unmapped_infs(source_joints, target_joints, names_match, inf_map)
    return inf_map, unmapped_target_infs


def update_inf_map_by_worldspace_position(source_joints, target_joints, influence_map=None, tolerance=0.001):
    inf_map = influence_map or {}
    predicate = xformutils.nodes_almost_match_worldspace_position
    unmapped_target_infs = _get_remaining_unmapped_infs(source_joints, target_joints, predicate, inf_map, tolerance)
    return inf_map, unmapped_target_infs


def update_inf_map_by_closest_inf(source_infs, target_infs, influence_map=None):
    influence_map = influence_map or {}
    for target_inf in target_infs:
        target_wsv = xformutils.get_worldspace_vector(target_inf)
        min_dis = None
        min_dis_source_inf = None
        for source_inf in source_infs:
            source_wsv = xformutils.get_worldspace_vector(source_inf)
            distance = abs((target_wsv - source_wsv).length())
            min_dis = min_dis or distance
            min_dis_source_inf = min_dis_source_inf or source_inf
            if distance < min_dis:
                min_dis = distance
                min_dis_source_inf = source_inf
        append_target_to_influence_map(influence_map, min_dis_source_inf, target_inf)
    # This method should not leave any target influences unmapped.
    # So we just return an empty list to keep the return signature consistent.
    unmapped_target_infs = []
    return influence_map, unmapped_target_infs


def update_inf_map_by_influence_order(source_joints, target_joints, influence_map=None):
    inf_map = influence_map or {}
    [append_target_to_influence_map(inf_map, *x) for x in zip(source_joints, target_joints)]
    remaining_target_infs = []
    if len(target_joints) > len(source_joints):
        remaining_target_infs = target_joints[len(source_joints):]
    return inf_map, remaining_target_infs


def _get_remaining_unmapped_infs(source_influences, target_influences, predicate, influence_map, *args):
    unmapped_target_infs = target_influences[:]
    for target_joint in target_influences:
        for source_joint in source_influences:
            if predicate(source_joint, target_joint, *args):
                append_target_to_influence_map(influence_map, source_joint, target_joint)
                unmapped_target_infs.remove(target_joint)
                break
    return unmapped_target_infs


def append_target_to_influence_map(influence_map, source_inf, target_inf):
    source_inf_value = influence_map.setdefault(source_inf, [])
    if target_inf not in source_inf_value:
        source_inf_value.append(target_inf)


def update_influence_map(influence_map, update_map):
    for update_source, update_targets in update_map.items():
        append_target_to_influence_map(influence_map, update_source, update_targets)


def get_influence_map(source_influences, target_influences, mapping_methods=None):
    mapping_methods = mapping_methods or [update_inf_map_by_label,
                                          update_inf_map_by_name,
                                          update_inf_map_by_worldspace_position,
                                          update_inf_map_by_influence_order]
    influence_map = {}
    unmapped_infs = target_influences
    for mapping_method in mapping_methods:
        if not unmapped_infs:
            break
        influence_map, unmapped_infs = mapping_method(source_influences, unmapped_infs, influence_map)
    return influence_map, unmapped_infs


def duplicate_skeleton(root_joint, dup_parent=None, dup_namespace=None):
    dup_namespace = dup_namespace or pm.namespaceInfo(currentNamespace=True)
    dup_root = nsutils.duplicate_to_namespace(
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
    hierarchy = root_node.getChildren(allDescendents=True, type='transform')
    hierarchy.append(root_node)
    hierarchy.reverse()
    if joints_only:
        hierarchy = pm.ls(hierarchy, type='joint')
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