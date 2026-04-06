from typing import NamedTuple

import pymel.core as pm

import flottitools.rigging.ue_rig_modules as rig_modules
import flottitools.utils.rigutils as rigutils
import flottitools.utils.skeletonutils as skelutils
import flottitools.utils.stringutils as stringutils
import flottitools.utils.transformutils as xformutils


SKIP_SENTINEL = object()

RIG_IK_PREFIX = 'ikj_'
RIG_FK_PREFIX = 'fkj_'

SIDE_SUFFIX_LEFT = '_l'
SIDE_SUFFIX_RIGHT = '_r'
COLOR_RED = 13
COLOR_GREEN = 14
COLOR_YELLOW = 17
SIDE_TO_COLOR_MAP = {SIDE_SUFFIX_LEFT: COLOR_RED,
                     SIDE_SUFFIX_RIGHT: COLOR_GREEN}

MODULE_TYPE_THUMB_FINGER = 'thumb'
MODULE_TYPE_INDEX_FINGER = 'index'
MODULE_TYPE_MIDDLE_FINGER = 'middle'
MODULE_TYPE_RING_FINGER = 'ring'
MODULE_TYPE_PINKY_FINGER = 'pinky'
MODULE_TYPE_DEFAULT_FINGER = 'finger'
FINGER_TYPE_TO_SPREAD_VALUE_MAP = {MODULE_TYPE_THUMB_FINGER: 0.0,
                                   MODULE_TYPE_INDEX_FINGER: 0.5,
                                   MODULE_TYPE_MIDDLE_FINGER: 0.0,
                                   MODULE_TYPE_RING_FINGER: -0.5,
                                   MODULE_TYPE_PINKY_FINGER: -1.0}

SHAPE_CIRCLE = 'circle'
SHAPE_SPHERE = 'sphere'
SHAPE_HALF_CIRCLE = 'halfCircle'
SHAPE_HALF_CIRCLE_QUA_DIR = 'halfCircleQuaDir'
SHAPE_CIRCLE_DIRECTIONAL = 'circleDirectional'
SHAPE_FOUR_DIRECTIONAL = 'rootMotion'

JOINT_NAME_ROOT = 'root'
JOINT_NAME_PELVIS = 'pelvis'
JOINT_NAME_SPINE01 = 'spine_01'
JOINT_NAME_SPINE02 = 'spine_02'
JOINT_NAME_SPINE03 = 'spine_03'
JOINT_NAME_NECK01 = 'neck_01'
JOINT_NAME_HEAD = 'head'
JOINT_NAME_CLAVICLE = 'clavicle'
JOINT_NAME_UPPERARM = 'upperarm'
JOINT_NAME_UPPERARMTWIST = 'upperarm_twist_01'
JOINT_NAME_LOWERARM = 'lowerarm'
JOINT_NAME_LOWERARMTWIST = 'lowerarm_twist_01'
JOINT_NAME_HAND = 'hand'
JOINT_NAME_INDEX = 'index'
JOINT_NAME_INDEX01 = 'index_01'
JOINT_NAME_INDEX02 = 'index_02'
JOINT_NAME_INDEX03 = 'index_03'
JOINT_NAME_MIDDLE = 'middle'
JOINT_NAME_MIDDLE01 = 'middle_01'
JOINT_NAME_MIDDLE02 = 'middle_02'
JOINT_NAME_MIDDLE03 = 'middle_03'
JOINT_NAME_RING = 'ring'
JOINT_NAME_RING01 = 'ring_01'
JOINT_NAME_RING02 = 'ring_02'
JOINT_NAME_RING03 = 'ring_03'
JOINT_NAME_PINKY = 'pinky'
JOINT_NAME_PINKY01 = 'pinky_01'
JOINT_NAME_PINKY02 = 'pinky_02'
JOINT_NAME_PINKY03 = 'pinky_03'
JOINT_NAME_THUMB = 'thumb'
JOINT_NAME_THUMB01 = 'thumb_01'
JOINT_NAME_THUMB02 = 'thumb_02'
JOINT_NAME_THUMB03 = 'thumb_03'
JOINT_NAME_THIGH = 'thigh'
JOINT_NAME_THIGHTWIST = 'thigh_twist_01'
JOINT_NAME_CALF = 'calf'
JOINT_NAME_CALFTWIST = 'calf_twist_01'
JOINT_NAME_FOOT = 'foot'
JOINT_NAME_IK_FOOTROOT = 'ik_foot_root'
JOINT_NAME_IK_FOOT = 'ik_foot'
JOINT_NAME_IK_HANDROOT = 'ik_hand_root'
JOINT_NAME_IK_HANDGUN = 'ik_hand_gun'
JOINT_NAME_IK_HAND = 'ik_hand'
FINGER_NAMES = [JOINT_NAME_PINKY, JOINT_NAME_RING, JOINT_NAME_MIDDLE, JOINT_NAME_INDEX, JOINT_NAME_THUMB]

SKELETON_JOINT_NAMES = [JOINT_NAME_ROOT,
                        JOINT_NAME_PELVIS,
                        JOINT_NAME_SPINE01,
                        JOINT_NAME_SPINE02,
                        JOINT_NAME_SPINE03,
                        JOINT_NAME_NECK01,
                        JOINT_NAME_HEAD,
                        JOINT_NAME_CLAVICLE,
                        JOINT_NAME_UPPERARM,
                        JOINT_NAME_UPPERARMTWIST,
                        JOINT_NAME_LOWERARM,
                        JOINT_NAME_LOWERARMTWIST,
                        JOINT_NAME_HAND,
                        JOINT_NAME_INDEX01,
                        JOINT_NAME_INDEX02,
                        JOINT_NAME_INDEX03,
                        JOINT_NAME_MIDDLE01,
                        JOINT_NAME_MIDDLE02,
                        JOINT_NAME_MIDDLE03,
                        JOINT_NAME_RING01,
                        JOINT_NAME_RING02,
                        JOINT_NAME_RING03,
                        JOINT_NAME_PINKY01,
                        JOINT_NAME_PINKY02,
                        JOINT_NAME_PINKY03,
                        JOINT_NAME_THUMB01,
                        JOINT_NAME_THUMB02,
                        JOINT_NAME_THUMB03,
                        JOINT_NAME_THIGH,
                        JOINT_NAME_THIGHTWIST,
                        JOINT_NAME_CALF,
                        JOINT_NAME_CALFTWIST,
                        JOINT_NAME_FOOT,
                        JOINT_NAME_IK_FOOTROOT,
                        JOINT_NAME_IK_FOOT,
                        JOINT_NAME_IK_HANDROOT,
                        JOINT_NAME_IK_HANDGUN,
                        JOINT_NAME_IK_HAND]


class ArmJoints(NamedTuple):
    clavicle: pm.nt.Joint
    upperarm: pm.nt.Joint
    upperarm_twist: pm.nt.Joint
    lowerarm: pm.nt.Joint
    lowerarm_twist: pm.nt.Joint
    hand: pm.nt.Joint


class FingerJoints(NamedTuple):
    finger_01: pm.nt.Joint
    finger_02: pm.nt.Joint
    finger_03: pm.nt.Joint


class FingerRig(NamedTuple):
    finger_joints_bind: FingerJoints
    finger_joints_fk: FingerJoints

    fk_controller_01: pm.nt.Transform
    fk_controller_02: pm.nt.Transform
    fk_controller_03: pm.nt.Transform

    loc_ori_01: pm.nt.Transform

    grip_controller: pm.nt.Transform
    grip_attr: pm.Attribute
    spread_attr: pm.Attribute

    module_type: str = MODULE_TYPE_DEFAULT_FINGER


class HandJoints(NamedTuple):
    hand: pm.nt.Joint


class HandRigComponents(NamedTuple):
    joints_bind: HandJoints
    joints_fk: HandJoints
    wrist_controller: pm.nt.Transform
    all_fingers_grip_attr: pm.Attribute
    all_fingers_spread_attr: pm.Attribute
    finger_rigs: FingerRig


class ArmRigComponents(NamedTuple):
    module_group: pm.nt.Transform
    joints_bind: ArmJoints
    joints_ik: ArmJoints
    joints_fk: ArmJoints

    controller_clavicle: pm.nt.Transform

    controller_ik_shoulder: pm.nt.Transform
    controller_ik_wrist: pm.nt.Transform

    controller_fk_upperarm: pm.nt.Transform
    controller_fk_upperarm_twist: pm.nt.Transform
    controller_fk_lowerarm: pm.nt.Transform
    controller_fk_lowerarm_twist: pm.nt.Transform
    controller_fk_hand: pm.nt.Transform

    parent_blend_attr: pm.Attribute
    ik_handle: pm.nt.IkHandle
    switch_controller: pm.nt.Transform
    controller_pole_vector: pm.nt.Transform


# class ArmRig(object):
#     def __init__(self, joints_bind: ArmJoints, joints_ik=None, joints_fk=None, controller_clavicle=None,
#                  controller_ik=None, controller_fk_upperarm=None, controller_fk_upperarm_twist=None,
#                  controller_fk_lowerarm=None, controller_fk_lowerarm_twist=None, controller_fk_arm=None,
#                  parent_blend_attr=None, ik_handle=None, switch_controller=None):
#         self.joints_bind = joints_bind



def get_left_arm_joints_from_scene():
    return _get_arm_joints_from_scene(SIDE_SUFFIX_LEFT)


def get_right_arm_joints_from_scene():
    return _get_arm_joints_from_scene(SIDE_SUFFIX_RIGHT)


def _get_arm_joints_from_scene(side_suffix):
    # clavicle = pm.ls('::{0}{1}'.format(JOINT_NAME_CLAVICLE, side_suffix), type=pm.nt.Joint)[0]
    clavicle = _get_joint_by_name(JOINT_NAME_CLAVICLE, side_suffix)
    upperarm = _get_joint_by_name(JOINT_NAME_UPPERARM, side_suffix)
    upperarm_twist = _get_joint_by_name(JOINT_NAME_UPPERARMTWIST, side_suffix)
    lowerarm = _get_joint_by_name(JOINT_NAME_LOWERARM, side_suffix)
    lowerarm_twist = _get_joint_by_name(JOINT_NAME_LOWERARMTWIST, side_suffix)
    hand = _get_joint_by_name(JOINT_NAME_HAND, side_suffix)
    return ArmJoints(clavicle, upperarm, upperarm_twist, lowerarm, lowerarm_twist, hand)
    # return ArmJoints(clavicle, upperarm, upperarm_twist, lowerarm, lowerarm_twist, hand)


def _get_joint_by_name(joint_name, side_suffix=None):
    # name = '::{0}{1}'.format(joint_name, side_suffix)
    name = '::{0}'.format(joint_name)
    if side_suffix:
        name += side_suffix
    return pm.ls(name, type=pm.nt.Joint)[0]


def rig_left_arm():
    left_arm_joints = get_left_arm_joints_from_scene()
    return build_arm_rig(left_arm_joints)


def rig_right_arm():
    right_arm_joints = get_right_arm_joints_from_scene()
    return build_arm_rig(right_arm_joints)


def build_arm_rig(arm_joints_struct: ArmJoints, module_name='arm', module_group=None):
    side = get_side_from_name(arm_joints_struct[0].nodeName())
    module_group, controls_group, components_group, ik_group, fk_group = setup_module_groups(
        module_name, side, module_group)

    ik_joints_struct = duplicate_arm_joints(arm_joints_struct, RIG_IK_PREFIX, ik_group)
    fk_joints_struct = duplicate_arm_joints(arm_joints_struct, RIG_FK_PREFIX, fk_group)
    ik_joints = [ik_joints_struct.upperarm, ik_joints_struct.lowerarm, ik_joints_struct.hand]
    #todo: refactor to return pv controller
    pv_loc_ori, ik_handle = rigutils.set_up_ik_rig(ik_joints, ik_group, module_name, side)
    ctr_pole_vector = pv_loc_ori.getChildren()[0]
    pv_loc_ori.setParent(controls_group)
    ik_handle.setParent(ik_group)

    ik_wrist_controller_name = rigutils.get_control_name_from_module_name('wrist', side)
    wrist_loc = ik_joints_struct.hand.getTranslation(space='world')
    wrist_ori = ik_joints_struct.hand.getRotation(space='world')
    ik_wrist_ctr, ik_wrist_loc_ori = rigutils.make_controller_node(
        ik_wrist_controller_name, side, shape_name='wedge', mirror=(1, 1, 1),
        shape_rotation=(0, 180, 0), shape_scale=(-12, 1, 18), location=wrist_loc, rotation=wrist_ori, move_cv_x=12)
    ik_wrist_loc_ori.setParent(controls_group)
    pm.parentConstraint(ik_wrist_ctr, ik_handle, maintainOffset=True)
    pm.orientConstraint(ik_wrist_ctr, ik_joints_struct.hand, maintainOffset=True)

    ik_shoulder_controller_name = rigutils.get_control_name_from_module_name('shoulder', side)
    shoulder_loc = ik_joints_struct.upperarm.getTranslation(space='world')
    shoulder_ori = ik_joints_struct.upperarm.getRotation(space='world')
    ik_shoulder_ctr, ik_shoulder_loc_ori = rigutils.make_controller_node(
        ik_shoulder_controller_name, side, shape_name='cube', mirror=(-1, -1, -1),
        shape_rotation=(0, 0, 0), shape_scale=(3, 3, 3), location=shoulder_loc, rotation=shoulder_ori)
    ik_shoulder_loc_ori.setParent(controls_group)
    pm.parentConstraint(ik_shoulder_ctr, ik_joints_struct.upperarm, maintainOffset=True)

    fk_joints = [fk_joints_struct.clavicle, fk_joints_struct.upperarm, fk_joints_struct.lowerarm, fk_joints_struct.hand]
    fk_controls, fk_loc_oris, cons = rigutils.make_fk_controls(fk_joints, side)
    fk_loc_oris[0].setParent(controls_group)

    pm.parentConstraint(fk_controls[0], ik_shoulder_loc_ori, maintainOffset=True)

    def orient_x_constraint(parent_node, child_node):
        return pm.orientConstraint(parent_node, child_node, skip=['y', 'z'], weight=1.0, maintainOffset=True)

    def parent_constraint(parent_node, child_node):
        return pm.parentConstraint(parent_node, child_node, skipRotate=['x'], weight=1.0, maintainOffset=True)

    def set_up_twist_controller(twist_joint, ik_child, ik_parents, fk_child, fk_parents):
        twist_control, twist_loc_ori, twist_cons = rigutils.make_fk_controls(
            [twist_joint], side, shape_type=SHAPE_CIRCLE_DIRECTIONAL, shape_scale=(6, 6, 6))
        pm.delete(twist_cons)
        twist_control = twist_control[0]
        twist_loc_ori = twist_loc_ori[0]
        twist_loc_ori.setParent(controls_group)
        twist_strength_attr = rigutils.make_parent_switch_attr(twist_control, 'twistStrength')
        rigutils.set_up_parent_switch(ik_child,
                                      ik_parents, twist_strength_attr,
                                      constraint_method=orient_x_constraint)
        rigutils.set_up_parent_switch(fk_child,
                                      fk_parents, twist_strength_attr,
                                      constraint_method=orient_x_constraint)
        # pm.parentConstraint(ik_parents[0], ik_child, skipRotate=['x'], weight=1.0, maintainOffset=True)
        # pm.parentConstraint(fk_parents[0], fk_child, skipRotate=['x'], weight=1.0, maintainOffset=True)
        twist_strength_attr.set(0.6)
        return twist_control

    upper_twist_control = set_up_twist_controller(arm_joints_struct.upperarm_twist,
                                                  ik_joints_struct.lowerarm_twist,
                                                  (ik_joints_struct.lowerarm, ik_joints_struct.hand),
                                                  fk_joints_struct.lowerarm_twist,
                                                  (fk_joints_struct.lowerarm, fk_joints_struct.hand))
    lower_twist_control = set_up_twist_controller(arm_joints_struct.lowerarm_twist,
                                                  ik_joints_struct.upperarm_twist,
                                                  (ik_joints_struct.upperarm, ik_joints_struct.lowerarm),
                                                  fk_joints_struct.upperarm_twist,
                                                  (fk_joints_struct.upperarm, fk_joints_struct.lowerarm))

    switch_control_name = '{0}_{1}_{2}_{3}'.format(module_name, 'switch', rigutils.SUFFIX_CONTROL, side)
    switch_ctr, switch_loc_ori, parent_blend_attr = rigutils.set_up_ikfk_blend_controller(
        arm_joints_struct.hand, side, switch_control_name)
    switch_loc_ori.setParent(controls_group)

    rigutils.set_up_visibility_switch(fk_loc_oris[1], parent_blend_attr)
    rigutils.set_up_visibility_switch(pv_loc_ori, parent_blend_attr, use_one_minus=True)
    rigutils.set_up_visibility_switch(ik_wrist_loc_ori, parent_blend_attr, use_one_minus=True)
    rigutils.set_up_visibility_switch(ik_shoulder_loc_ori, parent_blend_attr, use_one_minus=True)

    arm_rig_struct = ArmRigComponents(
        module_group, arm_joints_struct, ik_joints_struct, fk_joints_struct, fk_controls[0], ik_shoulder_ctr, ik_wrist_ctr,
        fk_controls[1], upper_twist_control, fk_controls[2], lower_twist_control, fk_controls[3], parent_blend_attr,
        ik_handle, switch_ctr, ctr_pole_vector)
    return arm_rig_struct


def duplicate_arm_joints(arm_joints_struct: ArmJoints, prefix, parent=None):
    dup_joints = pm.duplicate(arm_joints_struct, parentOnly=True)
    new_arm_joints_struct = ArmJoints(*dup_joints)
    rigutils.safe_parent(new_arm_joints_struct.lowerarm, new_arm_joints_struct.hand)
    rigutils.safe_parent(new_arm_joints_struct.lowerarm, new_arm_joints_struct.lowerarm_twist)
    rigutils.safe_parent(new_arm_joints_struct.upperarm, new_arm_joints_struct.lowerarm)
    rigutils.safe_parent(new_arm_joints_struct.upperarm, new_arm_joints_struct.upperarm_twist)
    rigutils.safe_parent(new_arm_joints_struct.clavicle, new_arm_joints_struct.upperarm)
    if parent:
        new_arm_joints_struct.clavicle.setParent(parent)
        # new_arm_joints_struct.upperarm.setParent(parent)
    for source_joint, dup_joint in zip(arm_joints_struct, new_arm_joints_struct):
        # dup_name = stringutils.replace_suffix(source_joint.nodeName(), suffix)
        dup_name = '{0}{1}'.format(prefix, source_joint.nodeName())
        dup_joint.rename(dup_name)
    return new_arm_joints_struct


def get_side_from_name(name):
    side = ''
    if name.lower().endswith(SIDE_SUFFIX_RIGHT):
        side = SIDE_SUFFIX_RIGHT
    elif name.lower().endswith(SIDE_SUFFIX_LEFT):
        side = SIDE_SUFFIX_LEFT
    return side


def setup_module_groups(module_name, side, module_group=None, controls_group=None,
                        components_group=None, ik_parent=None, fk_parent=None):
    module_group = _setup_module_group_node(module_name, side, rigutils.SUFFIX_MODULE, module_group)
    controls_group = _setup_module_group_node(module_name, side, rigutils.SUFFIX_CONTROLS, controls_group, module_group)
    components_group = _setup_module_group_node(module_name, side, rigutils.SUFFIX_COMP_GROUP, components_group, module_group)
    components_group.visibility.set(0)
    ik_parent = _setup_module_group_node(module_name, side, rigutils.SUFFIX_IK_GROUP, ik_parent, components_group)
    fk_parent = _setup_module_group_node(module_name, side, rigutils.SUFFIX_FK_GROUP, fk_parent, components_group)
    return module_group, controls_group, components_group, ik_parent, fk_parent


def _setup_module_group_node(module_name, side, suffix, group_node, parent=None):
    if group_node is SKIP_SENTINEL:
        return
    group_node = group_node or rigutils.create_group_node('{}_{}{}'.format(module_name, suffix, side))
    if parent:
        rigutils.safe_parent(parent, group_node)
    return group_node


def arm_bake_to_rig_and_constrain_bind_skeleton(arm_rig_components: ArmRigComponents):
    constraints, fk_controls = arm_constrain_rig_to_bind_skeleton(arm_rig_components)
    arm_bake_anim_to_rig(arm_rig_components, constraints, fk_controls)
    arm_constrain_bind_joints_to_rig(arm_rig_components)


def arm_constrain_rig_to_bind_skeleton(arm_rig_components):
    # arm_rig_components.joints_bind.clavicle
    bind_joints = [arm_rig_components.joints_bind.clavicle,
                   arm_rig_components.joints_bind.upperarm,
                   # arm_rig_components.joints_bind.upperarm_twist,
                   arm_rig_components.joints_bind.lowerarm,
                   # arm_rig_components.joints_bind.lowerarm_twist,
                   arm_rig_components.joints_bind.hand]
    fk_controls = [arm_rig_components.controller_clavicle,
                   arm_rig_components.controller_fk_upperarm,
                   # arm_rig_components.controller_fk_upperarm_twist,
                   arm_rig_components.controller_fk_lowerarm,
                   # arm_rig_components.controller_fk_lowerarm_twist,
                   arm_rig_components.controller_fk_hand]
    constraints = []
    for bind_joint, fk_control in zip(bind_joints, fk_controls):
        constraints.append(pm.parentConstraint(bind_joint, fk_control, maintainOffset=True))
    for parent, child in [
        (arm_rig_components.joints_bind.upperarm_twist, arm_rig_components.controller_fk_upperarm_twist),
        (arm_rig_components.controller_fk_upperarm_twist, arm_rig_components.controller_fk_lowerarm_twist)]:
        constraints.append(pm.orientConstraint(parent, child, skip=['y', 'z'], weight=1.0, maintainOffset=True))
    constraints.append(pm.parentConstraint(arm_rig_components.controller_fk_hand,
                                           arm_rig_components.controller_ik_wrist,
                                           maintainOffset=True))
    constraints.append(pm.parentConstraint(arm_rig_components.controller_fk_upperarm,
                                           arm_rig_components.controller_ik_shoulder,
                                           maintainOffset=True))
    return constraints, fk_controls


def arm_bake_anim_to_rig(arm_rig_components, constraints, fk_controls):
    controllers_to_bake = fk_controls[:]
    controllers_to_bake.append(arm_rig_components.controller_ik_wrist)
    controllers_to_bake.append(arm_rig_components.controller_ik_shoulder)
    controllers_to_bake.append(arm_rig_components.controller_fk_upperarm_twist)
    controllers_to_bake.append(arm_rig_components.controller_fk_lowerarm_twist)
    start_frame = int(pm.playbackOptions(minTime=True, q=True))
    end_frame = int(pm.playbackOptions(maxTime=True, q=True))
    bake_animation_to_nodes(controllers_to_bake, start_frame, end_frame)
    key_pv_every_frame(arm_rig_components, start_frame, end_frame)
    pm.delete(constraints)


def arm_get_controllers_to_bake(arm_rig_components: ArmRigComponents):
    controllers_to_bake = [arm_rig_components.controller_clavicle, arm_rig_components.controller_fk_upperarm,
                           arm_rig_components.controller_fk_upperarm_twist, arm_rig_components.controller_fk_lowerarm,
                           arm_rig_components.controller_fk_lowerarm_twist, arm_rig_components.controller_fk_hand,
                           arm_rig_components.controller_ik_wrist, arm_rig_components.controller_ik_shoulder]
    # controllers_to_bake.append(arm_rig_components.controller_ik_wrist)
    # controllers_to_bake.append(arm_rig_components.controller_ik_shoulder)
    # controllers_to_bake.append(arm_rig_components.controller_fk_upperarm_twist)
    # controllers_to_bake.append(arm_rig_components.controller_fk_lowerarm_twist)
    pv_to_transforms = {arm_rig_components.controller_pole_vector: [arm_rig_components.controller_fk_upperarm,
                                                                    arm_rig_components.controller_fk_lowerarm,
                                                                    arm_rig_components.controller_fk_hand]}
    return controllers_to_bake, pv_to_transforms


def arm_constrain_bind_joints_to_rig(arm_rig_components):
    rig_constraints = []
    rig_constraints.append(pm.parentConstraint(arm_rig_components.controller_fk_lowerarm_twist,
                                               arm_rig_components.joints_bind.lowerarm_twist, maintainOffset=True))
    rig_constraints.append(pm.parentConstraint(arm_rig_components.controller_fk_upperarm_twist,
                                               arm_rig_components.joints_bind.upperarm_twist, maintainOffset=True))
    rig_constraints.append(pm.parentConstraint(arm_rig_components.controller_clavicle,
                                               arm_rig_components.joints_bind.clavicle, maintainOffset=True))
    bind_joints = [arm_rig_components.joints_bind.upperarm,
                   arm_rig_components.joints_bind.lowerarm,
                   arm_rig_components.joints_bind.hand,
                   arm_rig_components.controller_fk_upperarm_twist.getParent(),
                   arm_rig_components.controller_fk_lowerarm_twist.getParent()]
    ik_joints = [arm_rig_components.joints_ik.upperarm,
                 arm_rig_components.joints_ik.lowerarm,
                 arm_rig_components.joints_ik.hand,
                 arm_rig_components.joints_ik.upperarm_twist,
                 arm_rig_components.joints_ik.lowerarm_twist]
    fk_joints = [arm_rig_components.joints_fk.upperarm,
                 arm_rig_components.joints_fk.lowerarm,
                 arm_rig_components.joints_fk.hand,
                 arm_rig_components.joints_fk.upperarm_twist,
                 arm_rig_components.joints_fk.lowerarm_twist]
    for bind_joint, ik_joint, fk_joint in zip(bind_joints, ik_joints, fk_joints):
        parent_cons, one_minus = rigutils.set_up_parent_switch(bind_joint, [ik_joint, fk_joint],
                                                               arm_rig_components.parent_blend_attr)
        # setAttr "clavicle_l_parentConstraint1.interpType" 2;
        for p_con in parent_cons:
            p_con.interpType.set(2)
        rig_constraints.extend(parent_cons)


# def rig_joints_as_hand(joints, arm_rig=None):
#     _get_arm_joints_from_scene(SIDE_SUFFIX_RIGHT)
#     side = rigutils.get_side_from_name(joints[0].nodeName())
#     module_name = 'hand{0}{1}'.format(side, rigutils.SUFFIX_MODULE)
#     module_group = rigutils.create_group_node(module_name)
#
#     hand_joints_struct = HandJoints(joints[0])
#     hand_joints_struct = _get_joint_by_name(JOINT_NAME_HAND)
#     def get_finger_joints_by_name(base_finger_name):
#         finger_joints = []
#         for i in range(1, 4):
#             finger_joint_name = '{0}_0{1}'.format(base_finger_name, i)
#             finger_joints.append(_get_joint_by_name(finger_joint_name))
#         return finger_joints
#
#     pinky_joints_struct = FingerJoints(*get_finger_joints_by_name(JOINT_NAME_PINKY))
#     ring_joints_struct = FingerJoints(*get_finger_joints_by_name(JOINT_NAME_RING))
#     middle_joints_struct = FingerJoints(*get_finger_joints_by_name(JOINT_NAME_MIDDLE))
#     index_joints_struct = FingerJoints(*get_finger_joints_by_name(JOINT_NAME_INDEX))
#     thumb_joints_struct = FingerJoints(*get_finger_joints_by_name(JOINT_NAME_THUMB))
#
#     finger_structs = [thumb_joints_struct, index_joints_struct, middle_joints_struct, ring_joints_struct,
#                       pinky_joints_struct]
#     finger_types = [MODULE_TYPE_THUMB_FINGER, MODULE_TYPE_INDEX_FINGER, MODULE_TYPE_MIDDLE_FINGER,
#                     MODULE_TYPE_RING_FINGER, MODULE_TYPE_PINKY_FINGER]
#     finger_rigs = []
#     for finger_struct, type_string in zip(finger_structs, finger_types):
#         spread_scalar = FINGER_TYPE_TO_SPREAD_VALUE_MAP.get(type_string, 0.0)
#         finger_rig = rig_finger(finger_struct, module_type=type_string, module_parent=module_group,
#                                 spread_dir=spread_scalar)
#         finger_rigs.append(finger_rig)
#
#     hand_rig = build_hand_rig(hand_joints_struct, finger_rigs, module_name=module_name, module_group=module_group,
#                               arm_rig_struct=arm_rig)
#     return hand_rig

def rig_right_hand(arm_rig_components: ArmRigComponents = None):
    hand_joints_struct, finger_joint_structs = _get_hand_joints_from_scene(SIDE_SUFFIX_RIGHT)
    return build_hand_rig(hand_joints_struct, finger_joint_structs, arm_rig_struct=arm_rig_components)


def rig_left_hand(arm_rig_components: ArmRigComponents = None):
    hand_joints_struct, finger_joint_structs = _get_hand_joints_from_scene(SIDE_SUFFIX_LEFT)
    return build_hand_rig(hand_joints_struct, finger_joint_structs, arm_rig_struct=arm_rig_components)


def _get_hand_joints_from_scene(side_suffix):
    # module_name = 'hand{0}{1}'.format(rigutils.SUFFIX_MODULE, side_suffix)
    # module_group = rigutils.create_group_node(module_name)

    hand_joints_struct = HandJoints(_get_joint_by_name(JOINT_NAME_HAND, side_suffix=side_suffix))

    def get_finger_joints_by_name(base_finger_name):
        finger_joints = []
        for i in range(1, 4):
            finger_joint_name = '{0}_0{1}'.format(base_finger_name, i)
            finger_joints.append(_get_joint_by_name(finger_joint_name, side_suffix=side_suffix))
        return finger_joints

    finger_joint_structs = [FingerJoints(*get_finger_joints_by_name(name)) for name in FINGER_NAMES]
    # pinky_joints_struct = FingerJoints(*get_finger_joints_by_name(JOINT_NAME_PINKY))
    # ring_joints_struct = FingerJoints(*get_finger_joints_by_name(JOINT_NAME_RING))
    # middle_joints_struct = FingerJoints(*get_finger_joints_by_name(JOINT_NAME_MIDDLE))
    # index_joints_struct = FingerJoints(*get_finger_joints_by_name(JOINT_NAME_INDEX))
    # thumb_joints_struct = FingerJoints(*get_finger_joints_by_name(JOINT_NAME_THUMB))
    return hand_joints_struct, finger_joint_structs


def build_hand_rig(hand_joints_struct: HandJoints, finger_joints: [FingerJoints],
                   module_name=None, module_group=None, side_suffix=None,
                   arm_rig_struct: ArmRigComponents = None):
    side = side_suffix or get_side_from_name(hand_joints_struct.hand.nodeName())
    module_name = module_name or 'hand{0}{1}'.format(rigutils.SUFFIX_MODULE, side)
    module_group, controls_group, components_group, _, fk_group = setup_module_groups(
        module_name, side, module_group, ik_parent=SKIP_SENTINEL)

    # if arm_rig_struct:
    fingers_parent = rigutils.create_group_node('{}_root_GRP'.format(module_name), controls_group)
    xformutils.match_worldspace_position_orientation(fingers_parent, hand_joints_struct.hand)
    hand_grip_control = arm_rig_struct.switch_controller
    parent_cons, _ = rigutils.set_up_parent_switch(fingers_parent,
                                                   (arm_rig_struct.joints_ik.hand, arm_rig_struct.joints_fk.hand),
                                                   arm_rig_struct.parent_blend_attr)
    # [p_con.interpType.set(2) for p_con in parent_cons]
    fk_hand_joints_struct = HandJoints(arm_rig_struct.joints_fk.hand)
        # wrist_control = arm_rig_struct.contr
    # else:
    #     fk_hand_joints_struct = duplicate_hand_joints(hand_joints_struct, rigutils.SUFFIX_FK, parent=fk_group)
    #     controls, loc_oris, cons = rigutils.make_fk_controls([fk_hand_joints_struct.hand], side,
    #                                                          SHAPE_HALF_CIRCLE_QUA_DIR, shape_scale=(5, 5, 5),
    #                                                          shape_rotation=(0, 0, 180))
    #     wrist_control = controls[0]
    #     wrist_loc_ori = loc_oris[0]
    #     wrist_loc_ori.setParent(controls_group)
    #     fingers_parent = wrist_control
    #     hand_grip_control = wrist_control

    grip_attr_name = '{}Grip'.format(module_name.split('_', 1)[0])
    grip_attr = rigutils.make_parent_switch_attr(hand_grip_control, grip_attr_name, values=(-30.0, 90.0))
    spread_attr_name = '{}Spread'.format(module_name.split('_', 1)[0])
    spread_attr = rigutils.make_parent_switch_attr(hand_grip_control, spread_attr_name, values=(-10.0, 30.0))

    finger_rig_structs = []
    for finger_struct, type_string in zip(finger_joints, FINGER_NAMES):
        spread_scalar = FINGER_TYPE_TO_SPREAD_VALUE_MAP.get(type_string, 0.0)
        finger_rig = build_finger_rig(finger_struct, module_type=type_string, module_parent=module_group,
                                      spread_dir=spread_scalar)
        finger_rig_structs.append(finger_rig)

    for finger_rig_struct in finger_rig_structs:
        pm.parentConstraint(fingers_parent, finger_rig_struct.loc_ori_01, maintainOffset=True)
        if finger_rig_struct.module_type == MODULE_TYPE_THUMB_FINGER:
            continue
        spread_scalar = FINGER_TYPE_TO_SPREAD_VALUE_MAP.get(finger_rig_struct.module_type, 0.0)
        fk_controllers = [finger_rig_struct.fk_controller_01,
                          finger_rig_struct.fk_controller_02,
                          finger_rig_struct.fk_controller_03]
        offset_groups, scalar_nodes = do_grip_attr_stuff(fk_controllers, grip_attr, 1)
        spread_attr = do_spread_attr_stuff(spread_attr, offset_groups[0].rotateY, spread_scalar)
    # pm.parentConstraint(wrist_control, finger_rig_struct.loc_ori_01, maintainOffset=True)

    # pm.parentConstraint(fk_hand_joints_struct.hand, hand_joints_struct.hand, maintainOffset=True)

    hand_rig_struct = HandRigComponents(hand_joints_struct, fk_hand_joints_struct,
                                        fingers_parent, grip_attr, spread_attr, finger_rig_structs)
    return hand_rig_struct


def duplicate_hand_joints(hand_joints_struct: HandJoints, suffix, parent=None):
    dup_joint = pm.duplicate(hand_joints_struct.hand, parentOnly=True)[0]
    new_hand_joints_struct = HandJoints(dup_joint)
    if parent:
        dup_joint.setParent(parent)
    dup_name = stringutils.replace_suffix(dup_joint.nodeName(), suffix)
    dup_joint.rename(dup_name)
    return new_hand_joints_struct


def build_finger_rig(finger_joints_struct: FingerJoints, module_type=MODULE_TYPE_DEFAULT_FINGER, module_parent=None,
                     spread_dir=1):
    side = get_side_from_name(finger_joints_struct.finger_01.nodeName())
    module_name = '{0}{1}'.format(module_type, side)
    module_group_name = '{0}{1}'.format(module_name, rigutils.SUFFIX_MODULE)
    module_group, controls_group, components_group, _, fk_group = setup_module_groups(
        module_name, side, ik_parent=SKIP_SENTINEL)
    if module_parent:
        rigutils.safe_parent(module_parent, module_group)

    fk_finger_joints_struct = duplicate_finger_joints(finger_joints_struct, rigutils.SUFFIX_IK, fk_group)

    fk_joints = [fk_finger_joints_struct.finger_01, fk_finger_joints_struct.finger_02,
                 fk_finger_joints_struct.finger_03]
    fk_controls, fk_loc_oris, cons = rigutils.make_fk_controls(fk_joints, side, shape_type='halfCircleBiDirIndicator',
                                                               shape_rotation=(90, 0, 90), shape_scale=(1, 1, 1))
    fk_loc_oris[0].setParent(controls_group)

    grip_attr_name = '{}Grip'.format(module_group_name.split('_', 1)[0])
    grip_attr = rigutils.make_parent_switch_attr(fk_controls[0], grip_attr_name, values=(-30.0, 90.0))

    spread_attr_name = '{}Spread'.format(module_group_name.split('_', 1)[0])
    spread_attr = rigutils.make_parent_switch_attr(fk_controls[0], spread_attr_name, values=(-10.0, 30.0))

    offset_groups, scalar_nodes = do_grip_attr_stuff(fk_controls, grip_attr, -1)
    spread_attr = do_spread_attr_stuff(spread_attr, offset_groups[0].rotateY, spread_dir)

    # bind_joints = [finger_joints_struct.finger_01, finger_joints_struct.finger_02, finger_joints_struct.finger_03]
    # for bind_joint, fk_joint in zip(bind_joints, fk_joints):
    #     pm.parentConstraint(fk_joint, bind_joint, maintainOffset=True)
    finger_rig_struct = FingerRig(finger_joints_struct, fk_finger_joints_struct,
                                  fk_controls[0], fk_controls[1], fk_controls[2],
                                  fk_loc_oris[0], fk_controls[0], grip_attr, spread_attr, module_type)
    return finger_rig_struct


def hand_constrain_rig_to_bind_skeleton(hand_rig_components: HandRigComponents):
    # hand_rig_components.joints_bind.hand
    # hand_rig_components.wrist_controller
    constraints = []
    for finger_rig in hand_rig_components.finger_rigs:
        finger_rig: FingerRig
        fk_controllers = [finger_rig.fk_controller_01, finger_rig.fk_controller_02, finger_rig.fk_controller_03]
        for bind_joint, fk_controller in zip(finger_rig.finger_joints_bind, fk_controllers):
            # constraints.append(pm.parentConstraint(bind_joint, fk_controller, maintainOffset=True))
            constraints.append(parent_constraint_shortest(bind_joint, fk_controller, maintain_offset=True))
    return constraints


def hand_constrain_bind_joints_to_rig(hand_rig_components: HandRigComponents):
    constraints = []
    for finger_rig in hand_rig_components.finger_rigs:
        finger_rig: FingerRig
        fk_controllers = [finger_rig.fk_controller_01, finger_rig.fk_controller_02, finger_rig.fk_controller_03]
        for bind_joint, fk_controller in zip(finger_rig.finger_joints_bind, fk_controllers):
            # constraints.append(pm.parentConstraint(fk_controller, bind_joint, maintainOffset=True))
            constraints.append(parent_constraint_shortest(fk_controller, bind_joint, maintain_offset=True))
    return constraints


def duplicate_finger_joints(finger_joints_struct: FingerJoints, suffix, parent=None):
    joints = [finger_joints_struct.finger_01, finger_joints_struct.finger_02, finger_joints_struct.finger_03]
    dup_joints = pm.duplicate(joints, parentOnly=True)
    new_finger_bones_struct = FingerJoints(*dup_joints)
    if parent:
        dup_joints[0].setParent(parent)
    for i, j in enumerate(dup_joints[1:]):
        if j.getParent() != dup_joints[i]:
            j.setParent(dup_joints[i])
    for source_joint, dup_joint in zip(joints, dup_joints):
        dup_name = stringutils.replace_suffix(source_joint.nodeName(), suffix)
        dup_joint.rename(dup_name)
    return new_finger_bones_struct


def do_grip_attr_stuff(fk_controllers, grip_attr, scalar=-1):
    offset_groups = []
    scalar_nodes = []
    for fk_controller in fk_controllers:
        offset_group = rigutils.create_offset_group(fk_controller)
        offset_groups.append(offset_group)
        grip_dir_scaler_node = rigutils.create_scaler_node(grip_attr, scalar, offset_group.rotateZ)
        scalar_nodes.append(grip_dir_scaler_node)
    return offset_groups, scalar_nodes


def do_spread_attr_stuff(spread_attr, target_attr, scalar=0.0):
    if scalar:
        if scalar == 1:
            spread_attr.connect(target_attr)
        else:
            spread_dir_scaler_node = rigutils.create_scaler_node(spread_attr, scalar, target_attr)
    return spread_attr


def hand_get_controllers_to_bake(hand_rig_components: HandRigComponents):
    # controllers_to_bake = [hand_rig_components.wrist_controller]
    controllers_to_bake = []
    for finger_rig in hand_rig_components.finger_rigs:
        thing = [finger_rig.fk_controller_01, finger_rig.fk_controller_02, finger_rig.fk_controller_03]
        controllers_to_bake.extend(thing)
    return controllers_to_bake
    # joints_bind: HandJoints
    # joints_fk: HandJoints
    # wrist_controller: pm.nt.Transform
    # all_fingers_grip_attr: pm.Attribute
    # all_fingers_spread_attr: pm.Attribute
    # finger_rigs: [FingerRig]

    # finger_joints_bind: FingerJoints
    # finger_joints_fk: FingerJoints
    #
    # fk_controller_01: pm.nt.Transform
    # fk_controller_02: pm.nt.Transform
    # fk_controller_03: pm.nt.Transform
    #
    # loc_ori_01: pm.nt.Transform
    #
    # grip_controller: pm.nt.Transform
    # grip_attr: pm.Attribute
    # spread_attr: pm.Attribute
    #
    # module_type: str = MODULE_TYPE_DEFAULT_FINGER




def bake_anim_to_skel_and_tear_down_rig(bake_joints, stuff_do_delete, start_frame=None, end_frame=None):
    bake_animation_to_nodes(bake_joints, start_frame, end_frame)
    pm.delete(stuff_do_delete)


def bake_animation_to_nodes(nodes, start_frame=None, end_frame=None):
    start_frame = start_frame or pm.playbackOptions(minTime=True, q=True)
    end_frame = end_frame or pm.playbackOptions(maxTime=True, q=True)
    pm.bakeResults(nodes, simulation=True, time=str(start_frame) + ":" + str(end_frame), sampleBy=1,
                   oversamplingRate=1, disableImplicitControl=True, preserveOutsideKeys=False,
                   sparseAnimCurveBake=False, removeBakedAttributeFromLayer=True, removeBakedAnimFromLayer=False,
                   bakeOnOverrideLayer=False, minimizeRotation=False, controlPoints=False, shape=True)


# def key_pv_every_frame(arm_rig_components: ArmRigComponents, start_frame, end_frame):
#
#     pv_to_transforms = {arm_rig_components.controller_pole_vector: [arm_rig_components.controller_fk_upperarm,
#                                                                     arm_rig_components.controller_fk_lowerarm,
#                                                                     arm_rig_components.controller_fk_hand]}
#     pm.setKeyframe(list(pv_to_transforms.keys()), at='translate')
#     for i in range(start_frame, end_frame+1):
#         pm.currentTime(i)
#         for pvc, fkc in pv_to_transforms.items():
#             pv_loc = get_pv_controller_position(*fkc)
#             pvc.setTranslation(pv_loc, space='world')
#             pm.setKeyframe(pvc, at='translate')


def key_pv_every_frame(pv_to_transforms, start_frame, end_frame):
    pm.setKeyframe(list(pv_to_transforms.keys()), at='translate')
    for i in range(start_frame, end_frame+1):
        pm.currentTime(i)
        for pvc, fkc in pv_to_transforms.items():
            pv_loc = get_pv_controller_position(*fkc)
            pvc.setTranslation(pv_loc, space='world')
            pm.setKeyframe(pvc, at='translate')


def get_pv_controller_position(start_joint, mid_joint, end_joint, scalar=40.0):
    start_pos = xformutils.get_worldspace_vector(start_joint)
    mid_pos = xformutils.get_worldspace_vector(mid_joint)
    end_pos = xformutils.get_worldspace_vector(end_joint)
    start_mid = mid_pos - start_pos
    mid_end = end_pos - mid_pos
    start_end = end_pos - start_pos
    cross1 = start_mid ^ mid_end
    new_pv_vector = start_end ^ cross1
    new_pv_vector.normalize()
    new_pv_pos = (new_pv_vector * scalar) + mid_pos
    return new_pv_pos


def parent_constraint_shortest(parent, child, maintain_offset=True):
    constraint = pm.parentConstraint(parent, child, maintainOffset=maintain_offset)
    constraint.interpType.set(2)
    return constraint


def foo():
    arm_rig_components = rig_left_arm()
    constraints = arm_bake_to_rig_and_constrain_bind_skeleton(arm_rig_components)
    return arm_rig_components


def bar(arm_rig_components: ArmRigComponents):
    bake_anim_to_skel_and_tear_down_rig(arm_rig_components.joints_bind, arm_rig_components.module_group)


def prepare_skeleton_for_export(root_joint):
    # skelutils.get_extra_nodes_in_skeleton()
    only_joints = set(root_joint.getChildren(allDescendents=True, type='joint'))
    all_nodes = set(root_joint.getChildren(allDescendents=True))
    other_nodes = list(all_nodes.symmetric_difference(only_joints))
    pm.delete(other_nodes)
    root_joint.setParent(world=True)


def rig_biped():
    controllers_to_bake = []
    pv_to_transforms = {}
    constraints = []
    left_arm_rig_components = rig_left_arm()
    left_arm_constraints, left_arm_fk_controls = arm_constrain_rig_to_bind_skeleton(left_arm_rig_components)
    left_arm_controllers_to_bake, left_arm_pv_to_transforms = arm_get_controllers_to_bake(left_arm_rig_components)
    controllers_to_bake.extend(left_arm_controllers_to_bake)
    pv_to_transforms.update(left_arm_pv_to_transforms)
    constraints.extend(left_arm_constraints)

    right_arm_rig_components = rig_right_arm()
    right_arm_constraints, right_arm_fk_controls = arm_constrain_rig_to_bind_skeleton(right_arm_rig_components)
    right_arm_controllers_to_bake, right_arm_pv_to_transforms = arm_get_controllers_to_bake(right_arm_rig_components)
    controllers_to_bake.extend(right_arm_controllers_to_bake)
    pv_to_transforms.update(right_arm_pv_to_transforms)
    constraints.extend(right_arm_constraints)

    right_hand_rig_components = rig_right_hand(right_arm_rig_components)
    constraints.extend(hand_constrain_rig_to_bind_skeleton(right_hand_rig_components))
    right_hand_controllers_to_bake = hand_get_controllers_to_bake(right_hand_rig_components)
    controllers_to_bake.extend(right_hand_controllers_to_bake)
    left_hand_rig_components = rig_left_hand(left_arm_rig_components)
    constraints.extend(hand_constrain_rig_to_bind_skeleton(left_hand_rig_components))
    left_hand_controllers_to_bake = hand_get_controllers_to_bake(left_hand_rig_components)
    controllers_to_bake.extend(left_hand_controllers_to_bake)


    start_frame = int(pm.playbackOptions(minTime=True, q=True))
    end_frame = int(pm.playbackOptions(maxTime=True, q=True))
    bake_animation_to_nodes(controllers_to_bake, start_frame, end_frame)
    key_pv_every_frame(pv_to_transforms, start_frame, end_frame)
    pm.delete(constraints)

    # arm_bake_anim_to_rig(left_arm_rig_components, constraints, fk_controls)
    arm_constrain_bind_joints_to_rig(left_arm_rig_components)
    arm_constrain_bind_joints_to_rig(right_arm_rig_components)
    hand_constrain_bind_joints_to_rig(right_hand_rig_components)
    hand_constrain_bind_joints_to_rig(left_hand_rig_components)

