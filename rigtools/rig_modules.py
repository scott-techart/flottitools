import os
from typing import NamedTuple

import maya.api.OpenMaya as om
import pymel.core as pm

import flottitools.path_consts as path_consts
import flottitools.utils.rigutils as rigutils
import flottitools.utils.skeletonutils as skelutils
import flottitools.utils.stringutils as stringutils
import flottitools.utils.transformutils as xformutils

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

OFFSET_JOINT_TAG = '_offset_'

SHAPE_CIRCLE = 'circle'
SHAPE_SPHERE = 'sphere'
SHAPE_HALF_CIRCLE = 'halfCircle'
SHAPE_HALF_CIRCLE_QUA_DIR = 'halfCircleQuaDir'
SHAPE_CIRCLE_DIRECTIONAL = 'circleDirectional'
SHAPE_FOUR_DIRECTIONAL = 'rootMotion'

SKIP_SENTINEL = object()


class LegJoints(NamedTuple):
    hip: pm.nt.Joint
    knee: pm.nt.Joint
    ankle: pm.nt.Joint


class FootJoints(NamedTuple):
    ankle: pm.nt.Joint
    ball: pm.nt.Joint
    toe: pm.nt.Joint


class ArmJoints(NamedTuple):
    shoulder: pm.nt.Joint
    elbow: pm.nt.Joint
    forearm_twist: pm.nt.Joint
    wrist: pm.nt.Joint


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
    wrist: pm.nt.Joint


class HandRig(NamedTuple):
    joints_bind: HandJoints
    joints_fk: HandJoints
    wrist_controller: pm.nt.Transform
    all_fingers_grip_attr: pm.Attribute
    all_fingers_spread_attr: pm.Attribute
    finger_rigs: FingerRig


class LegControlsStruct(NamedTuple):
    ankle_joint_bind: pm.nt.Joint
    ankle_joint_fk: pm.nt.Joint
    ankle_joint_ik: pm.nt.Joint
    ankle_control_fk: pm.nt.Transform
    parent_blend_attr: pm.Attribute
    ik_handle: pm.nt.IkHandle


class ArmRig(NamedTuple):
    joints_bind: ArmJoints
    joints_ik: ArmJoints
    joints_fk: ArmJoints

    controller_ik: pm.nt.Transform

    controller_fk_shoulder: pm.nt.Transform
    controller_fk_elbow: pm.nt.Transform
    controller_fk_wrist: pm.nt.Transform

    parent_blend_attr: pm.Attribute
    ik_handle: pm.nt.IkHandle
    switch_controller: pm.nt.Transform


def get_leg_from_scene(side=skelutils.LABEL_SIDE_LEFT):
    hip_joint = pm.ls('hip{}JNT'.format(side))[0]
    knee_joint = pm.ls('knee{}JNT'.format(side))[0]
    ankle_joint = pm.ls('ankle{}JNT'.format(side))[0]
    leg_joints = LegJoints(hip_joint, knee_joint, ankle_joint)
    return leg_joints


def get_foot_joints_from_scene(side=skelutils.LABEL_SIDE_LEFT):
    ankle_joint = pm.ls('ankle{}JNT'.format(side))[0]
    ball_joint = pm.ls('ball{}JNT'.format(side))[0]
    toe_joint = pm.ls('toe{}JNT'.format(side))[0]
    foot_joints = FootJoints(ankle_joint, ball_joint, toe_joint)
    return foot_joints


def get_arm_joints_from_scene(side=skelutils.LABEL_SIDE_LEFT):
    shoulder_joint = pm.ls('shoulder{}JNT'.format(side))[0]
    elbow_joint = pm.ls('elbow{}JNT'.format(side))[0]
    forearm_twist_joint = pm.ls('forearm_twist{}JNT'.format(side))[0]
    wrist_joint = pm.ls('wrist{}JNT'.format(side))[0]
    arm_joints = ArmJoints(shoulder_joint, elbow_joint, forearm_twist_joint, wrist_joint)
    return arm_joints


def get_hand_joints_from_scene(side=skelutils.LABEL_SIDE_LEFT):
    wrist_joint = pm.ls('wrist{}JNT'.format(side))[0]
    wrist_joints = HandJoints(wrist_joint)
    thumb01 = pm.ls('thumb01{}JNT'.format(side))[0]
    thumb02 = pm.ls('thumb02{}JNT'.format(side))[0]
    thumb03 = pm.ls('thumb03{}JNT'.format(side))[0]
    thumb_joints = FingerJoints(thumb01, thumb02, thumb03)
    index01 = pm.ls('index01{}JNT'.format(side))[0]
    index02 = pm.ls('index02{}JNT'.format(side))[0]
    index03 = pm.ls('index03{}JNT'.format(side))[0]
    index_joints = FingerJoints(index01, index02, index03)
    middle01 = pm.ls('middle01{}JNT'.format(side))[0]
    middle02 = pm.ls('middle02{}JNT'.format(side))[0]
    middle03 = pm.ls('middle03{}JNT'.format(side))[0]
    middle_joints = FingerJoints(middle01, middle02, middle03)
    ring01 = pm.ls('ring01{}JNT'.format(side))[0]
    ring02 = pm.ls('ring02{}JNT'.format(side))[0]
    ring03 = pm.ls('ring03{}JNT'.format(side))[0]
    ring_joints = FingerJoints(ring01, ring02, ring03)
    pinky01 = pm.ls('pinky01{}JNT'.format(side))[0]
    pinky02 = pm.ls('pinky02{}JNT'.format(side))[0]
    pinky03 = pm.ls('pinky03{}JNT'.format(side))[0]
    pinky_joints = FingerJoints(pinky01, pinky02, pinky03)

    return wrist_joints, thumb_joints, index_joints, middle_joints, ring_joints, pinky_joints


def rig_selected_neck(fk_parent=None, module_group=None, controls_group=None, module_name='head',
                      control_shape=SHAPE_CIRCLE):
    sel = pm.selected()
    side = rigutils.get_side_from_name(sel[0].nodeName())

    module_group, controls_group, components_group, _, fk_parent = setup_module_groups(
        module_name, side, module_group, controls_group, ik_parent=SKIP_SENTINEL, fk_parent=fk_parent)

    dup_joints = pm.duplicate(sel, parentOnly=True)
    dup_joints[0].setParent(fk_parent)
    for b_joint, dup_joint in zip(sel, dup_joints):
        dup_name = stringutils.replace_suffix(b_joint.nodeName(), rigutils.SUFFIX_FK)
        dup_joint.rename(dup_name)
    controls, loc_oris, cons = rigutils.make_fk_controls(dup_joints, side, shape_type=control_shape)
    loc_oris[0].setParent(controls_group)

    for b_joint, fk_joint in zip(sel, dup_joints):
        pm.parentConstraint(fk_joint, b_joint, maintainOffset=True)

    return fk_parent, module_group, controls_group


def rig_selected_whole_arm():
    sel = pm.selected()[0]
    joint_chain = sel.getChildren(allDescendents=True)
    joint_chain.append(sel)
    joint_chain.reverse()
    arm_chain = joint_chain[:4]
    print('arm chain: ', arm_chain)
    arm_joint_struct = ArmJoints(*arm_chain)
    arm_rig = rig_arm(arm_joint_struct)
    hand_chain = joint_chain[3:]
    print('hand chain: ', hand_chain)
    hand_rig = rig_joints_as_hand(hand_chain, arm_rig)
    return arm_rig, hand_rig


def rig_selected_arm():
    sel = pm.selected()[0]
    joint_chain = sel.getChildren(allDescendents=True)
    joint_chain.append(sel)
    joint_chain.reverse()
    arm_chain = joint_chain[:4]
    arm_joint_struct = ArmJoints(*arm_chain)
    return rig_arm(arm_joint_struct)


def rig_arm(arm_joints_struct: ArmJoints, module_name='arm', module_group=None):
    side = rigutils.get_side_from_name(arm_joints_struct.shoulder.nodeName())
    module_group, controls_group, components_group, ik_group, fk_group = setup_module_groups(
        module_name, side, module_group)

    ik_joints_struct = duplicate_arm_joints(arm_joints_struct, rigutils.SUFFIX_IK, ik_group)
    fk_joints_struct = duplicate_arm_joints(arm_joints_struct, rigutils.SUFFIX_FK, fk_group)

    ik_joints = [ik_joints_struct.shoulder, ik_joints_struct.elbow, ik_joints_struct.wrist]
    pv_loc_ori, ik_handle = rigutils.set_up_ik_rig(ik_joints, ik_group, module_name, side)
    pv_loc_ori.setParent(controls_group)
    ik_handle.setParent(ik_group)

    ik_wrist_controller_name = rigutils.get_control_name_from_module_name('wrist', side)
    wrist_loc = ik_joints_struct.wrist.getTranslation(space='world')
    wrist_ori = ik_joints_struct.wrist.getRotation(space='world')
    ik_wrist_ctr, ik_wrist_loc_ori = rigutils.make_controller_node(ik_wrist_controller_name, side, shape_name='wedge',
                                                                   mirror=(-1, -1, -1),
                                                                   shape_rotation=(0, 180, 0), shape_scale=(8, 1, 14),
                                                                   location=wrist_loc, rotation=wrist_ori, move_cv_x=-8)
    ik_wrist_loc_ori.setParent(controls_group)
    pm.parentConstraint(ik_wrist_ctr, ik_handle, maintainOffset=True)
    pm.orientConstraint(ik_wrist_ctr, ik_joints_struct.wrist, maintainOffset=True)

    fk_joints = [fk_joints_struct.shoulder, fk_joints_struct.elbow, fk_joints_struct.wrist]
    fk_controls, fk_loc_oris, cons = rigutils.make_fk_controls(fk_joints, side)
    fk_loc_oris[0].setParent(controls_group)

    twist_joint = pm.duplicate(arm_joints_struct.forearm_twist, parentOnly=True)[0]
    twist_joint_name = stringutils.replace_suffix(arm_joints_struct.forearm_twist.nodeName(), rigutils.SUFFIX_FK)
    twist_joint.setParent(fk_group)
    twist_joint.rename(twist_joint_name)
    twist_control, twist_loc_ori, twist_cons = rigutils.make_fk_controls(
        [twist_joint], side, shape_type=SHAPE_CIRCLE_DIRECTIONAL, shape_scale=(4, 4, 4))
    twist_control = twist_control[0]
    twist_loc_ori = twist_loc_ori[0]
    twist_loc_ori.setParent(controls_group)
    # twist_offset_group = create_offset_group(twist_control)
    pm.parentConstraint(twist_joint, arm_joints_struct.forearm_twist, maintainOffset=True, weight=1)

    twist_strength_attr = rigutils.make_parent_switch_attr(twist_control, 'twistStrength')

    def orient_x_constraint(parent_node, child_node):
        return pm.orientConstraint(parent_node, child_node, skip=('y', 'z'), weight=1.0, maintainOffset=True)

    rigutils.set_up_parent_switch(ik_joints_struct.forearm_twist,
                                  (ik_joints_struct.elbow, ik_joints_struct.wrist), twist_strength_attr,
                                  constraint_method=orient_x_constraint)
    rigutils.set_up_parent_switch(fk_joints_struct.forearm_twist,
                                  (fk_joints_struct.elbow, fk_joints_struct.wrist), twist_strength_attr,
                                  constraint_method=orient_x_constraint)
    twist_strength_attr.set(0.6)

    # ik_joints fk_joints
    blendy_joints = [arm_joints_struct.shoulder, arm_joints_struct.elbow, twist_loc_ori, arm_joints_struct.wrist]
    # blendy_joints.forearm_twist = twist_joint
    switch_control_name = '{0}{1}{2}_{3}'.format(module_name, side, 'switch', rigutils.SUFFIX_CONTROL)
    switch_ctr, switch_loc_ori, parent_blend_attr = rigutils.set_up_ikfk_blend_controller(
        arm_joints_struct.wrist, side, switch_control_name)
    switch_loc_ori.setParent(controls_group)
    for b_joint, ik_joint, fk_joint in zip(blendy_joints, ik_joints_struct, fk_joints_struct):
        rigutils.set_up_parent_switch(b_joint, [ik_joint, fk_joint], parent_blend_attr)

    rigutils.set_up_visibility_switch(fk_loc_oris[0], parent_blend_attr)
    rigutils.set_up_visibility_switch(pv_loc_ori, parent_blend_attr, use_one_minus=True)
    rigutils.set_up_visibility_switch(ik_wrist_loc_ori, parent_blend_attr, use_one_minus=True)

    arm_rig_struct = ArmRig(arm_joints_struct, ik_joints_struct, fk_joints_struct, ik_wrist_ctr, fk_controls[0],
                            fk_controls[1], fk_controls[2], parent_blend_attr, ik_handle, switch_ctr)
    return arm_rig_struct


def duplicate_arm_joints(arm_joints_struct: ArmJoints, suffix, parent=None):
    joints = [arm_joints_struct.shoulder, arm_joints_struct.elbow, arm_joints_struct.forearm_twist,
              arm_joints_struct.wrist]
    dup_joints = pm.duplicate(joints, parentOnly=True)
    new_arm_joints_struct = ArmJoints(*dup_joints)
    if parent:
        new_arm_joints_struct.shoulder.setParent(parent)
    # new_arm_joints_struct.elbow.setParent(new_arm_joints_struct.shoulder)
    rigutils.safe_parent(new_arm_joints_struct.shoulder, new_arm_joints_struct.elbow)
    # new_arm_joints_struct.forearm_twist.setParent(new_arm_joints_struct.elbow)
    rigutils.safe_parent(new_arm_joints_struct.elbow, new_arm_joints_struct.forearm_twist)
    # new_arm_joints_struct.wrist.setParent(new_arm_joints_struct.elbow)
    rigutils.safe_parent(new_arm_joints_struct.elbow, new_arm_joints_struct.wrist)

    for source_joint, dup_joint in zip(joints, dup_joints):
        dup_name = stringutils.replace_suffix(source_joint.nodeName(), suffix)
        dup_joint.rename(dup_name)
    return new_arm_joints_struct


def rig_selected_hand():
    sel = pm.selected()[0]
    joints = sel.getChildren(allDescendents=True)
    joints.append(sel)
    joints.reverse()
    rig_joints_as_hand(joints)


def rig_joints_as_hand(joints, arm_rig=None):
    side = rigutils.get_side_from_name(joints[0].nodeName())
    module_name = 'hand{0}{1}'.format(side, rigutils.SUFFIX_MODULE)
    module_group = rigutils.create_group_node(module_name)

    hand_joints_struct = HandJoints(joints[0])
    pinky_joints_struct = FingerJoints(*joints[1:4])
    ring_joints_struct = FingerJoints(*joints[4:7])
    middle_joints_struct = FingerJoints(*joints[7:10])
    index_joints_struct = FingerJoints(*joints[10:13])
    thumb_joints_struct = FingerJoints(*joints[13:])

    finger_structs = [thumb_joints_struct, index_joints_struct, middle_joints_struct, ring_joints_struct,
                      pinky_joints_struct]
    finger_types = [MODULE_TYPE_THUMB_FINGER, MODULE_TYPE_INDEX_FINGER, MODULE_TYPE_MIDDLE_FINGER,
                    MODULE_TYPE_RING_FINGER, MODULE_TYPE_PINKY_FINGER]
    finger_rigs = []
    for finger_struct, type_string in zip(finger_structs, finger_types):
        spread_scalar = FINGER_TYPE_TO_SPREAD_VALUE_MAP.get(type_string, 0.0)
        finger_rig = rig_finger(finger_struct, module_type=type_string, module_parent=module_group,
                                spread_dir=spread_scalar)
        finger_rigs.append(finger_rig)

    hand_rig = rig_hand(hand_joints_struct, finger_rigs, module_name=module_name, module_group=module_group,
                        arm_rig_struct=arm_rig)
    return hand_rig


def rig_hand(hand_joints_struct: HandJoints, finger_rig_structs: [FingerRig], module_name=None, module_group=None,
             arm_rig_struct: ArmRig = None):
    side = rigutils.get_side_from_name(hand_joints_struct.wrist.nodeName())
    module_group, controls_group, components_group, _, fk_group = setup_module_groups(
        module_name, side, module_group, ik_parent=SKIP_SENTINEL)

    if arm_rig_struct:
        fingers_parent = rigutils.create_group_node('{}_root_GRP'.format(module_name), controls_group)
        xformutils.match_worldspace_position_orientation(fingers_parent, hand_joints_struct.wrist)
        hand_grip_control = arm_rig_struct.switch_controller
        rigutils.set_up_parent_switch(fingers_parent, (arm_rig_struct.joints_ik.wrist, arm_rig_struct.joints_fk.wrist),
                                      arm_rig_struct.parent_blend_attr)
        fk_hand_joints_struct = HandJoints(arm_rig_struct.joints_fk.wrist)
        # wrist_control = arm_rig_struct.contr
    else:
        fk_hand_joints_struct = duplicate_hand_joints(hand_joints_struct, rigutils.SUFFIX_FK, parent=fk_group)
        controls, loc_oris, cons = rigutils.make_fk_controls([fk_hand_joints_struct.wrist], side,
                                                             SHAPE_HALF_CIRCLE_QUA_DIR, shape_scale=(5, 5, 5),
                                                             shape_rotation=(0, 0, 180))
        wrist_control = controls[0]
        wrist_loc_ori = loc_oris[0]
        wrist_loc_ori.setParent(controls_group)
        fingers_parent = wrist_control
        hand_grip_control = wrist_control

    grip_attr_name = '{}Grip'.format(module_name.split('_', 1)[0])
    grip_attr = rigutils.make_parent_switch_attr(hand_grip_control, grip_attr_name, values=(-30.0, 90.0))
    spread_attr_name = '{}Spread'.format(module_name.split('_', 1)[0])
    spread_attr = rigutils.make_parent_switch_attr(hand_grip_control, spread_attr_name, values=(-10.0, 30.0))

    for finger_rig_struct in finger_rig_structs:
        pm.parentConstraint(fingers_parent, finger_rig_struct.loc_ori_01, maintainOffset=True)
        if finger_rig_struct.module_type == MODULE_TYPE_THUMB_FINGER:
            continue
        spread_scalar = FINGER_TYPE_TO_SPREAD_VALUE_MAP.get(finger_rig_struct.module_type, 0.0)
        fk_controllers = [finger_rig_struct.fk_controller_01,
                          finger_rig_struct.fk_controller_02,
                          finger_rig_struct.fk_controller_03]
        offset_groups, scalar_nodes = do_grip_attr_stuff(fk_controllers, grip_attr, -1)
        spread_attr = do_spread_attr_stuff(spread_attr, offset_groups[0].rotateY, spread_scalar)
    # pm.parentConstraint(wrist_control, finger_rig_struct.loc_ori_01, maintainOffset=True)

    pm.parentConstraint(fk_hand_joints_struct.wrist, hand_joints_struct.wrist, maintainOffset=True)

    hand_rig_struct = HandRig(hand_joints_struct, fk_hand_joints_struct,
                              fingers_parent, grip_attr, spread_attr, finger_rig_structs)
    return hand_rig_struct


def duplicate_hand_joints(hand_joints_struct: HandJoints, suffix, parent=None):
    dup_joint = pm.duplicate(hand_joints_struct.wrist, parentOnly=True)[0]
    new_hand_joints_struct = HandJoints(dup_joint)
    if parent:
        dup_joint.setParent(parent)
    dup_name = stringutils.replace_suffix(dup_joint.nodeName(), suffix)
    dup_joint.rename(dup_name)
    return new_hand_joints_struct


def rig_finger(finger_joints_struct: FingerJoints, module_type=MODULE_TYPE_DEFAULT_FINGER, module_parent=None,
               spread_dir=1):
    side = rigutils.get_side_from_name(finger_joints_struct.finger_01.nodeName())
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

    bind_joints = [finger_joints_struct.finger_01, finger_joints_struct.finger_02, finger_joints_struct.finger_03]
    for bind_joint, fk_joint in zip(bind_joints, fk_joints):
        pm.parentConstraint(fk_joint, bind_joint, maintainOffset=True)
    finger_rig_struct = FingerRig(finger_joints_struct, fk_finger_joints_struct,
                                  fk_controls[0], fk_controls[1], fk_controls[2],
                                  fk_loc_oris[0], fk_controls[0], grip_attr, spread_attr, module_type)
    return finger_rig_struct


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


def rig_whole_leg(leg_joints_struct: LegJoints, foot_joints_struct: FootJoints):
    leg_controls_struct = rig_leg(leg_joints_struct.hip)
    rig_foot(foot_joints_struct, leg_controls_struct)


def rig_foot(foot_joints_struct: FootJoints, leg_controls_struct=None, module_name='foot', heel_location=None):
    start_joint = foot_joints_struct.ankle
    bind_joints = skelutils.get_hierarchy_from_root(start_joint, joints_only=True)
    side = rigutils.get_side_from_name(bind_joints[0].nodeName())
    module_group, controls_group, components_group, ik_group, fk_group = setup_module_groups(module_name, side)
    if leg_controls_struct:
        fk_ball = pm.duplicate(foot_joints_struct.ball)[0]
        pm.delete(fk_ball.getChildren())
        fk_ball.setParent(leg_controls_struct.ankle_joint_fk)
        new_name = stringutils.replace_suffix(fk_ball.name(), rigutils.SUFFIX_FK)
        fk_ball.rename(new_name)
        fk_controls, fk_loc_oris, cons = rigutils.make_fk_controls([fk_ball], side)
        fk_joints = [leg_controls_struct.ankle_joint_fk, fk_ball]
        fk_loc_oris[0].setParent(leg_controls_struct.ankle_control_fk)
        # ik_joints
        ik_ball = pm.duplicate(foot_joints_struct.ball)[0]
        ik_toe = ik_ball.getChildren()[0]
        ik_ball.setParent(leg_controls_struct.ankle_joint_ik)
        for each in [ik_ball, ik_toe]:
            new_name = stringutils.replace_suffix(each, rigutils.SUFFIX_IK)
            each.rename(new_name)
        ik_foot_joints = [leg_controls_struct.ankle_joint_ik, ik_ball, ik_toe]
    else:
        ik_foot_joints = get_duped_joints_for_three_joint_chain(start_joint, rigutils.SUFFIX_IK, parent=ik_group)
        fk_joints = get_duped_joints_for_three_joint_chain(start_joint, rigutils.SUFFIX_FK, fk_group)
        pm.delete(fk_joints[2])
        fk_joints = fk_joints[:2]
        fk_controls, fk_loc_oris, cons = rigutils.make_fk_controls(fk_joints, side)

    # make foot controller - start
    foot_name = rigutils.get_control_name_from_module_name('foot', side)
    foot_shape_loc, foot_shape_ori = get_foot_loc_ori(*ik_foot_joints[:2])
    foot_ctr, foot_loc_ori = rigutils.make_controller_node(foot_name, side, shape_name='wedge',
                                                           shape_rotation=(0, -90, 0), shape_scale=(13, 10, 18),
                                                           location=foot_shape_loc, rotation=foot_shape_ori, move_cv_z=8)
    floor_cvs(foot_ctr)

    heel_name = rigutils.get_control_name_from_module_name('heel', side)
    heel_loc, heel_ori = get_heel_loc_ori(*ik_foot_joints[:2])
    heel_ctr, heel_loc_ori = rigutils.make_controller_node(heel_name, side, shape_name='halfCircleBiDir',
                                                           shape_rotation=(90, 0, 45), shape_scale=(3, 3, 3),
                                                           location=heel_loc, rotation=heel_ori)

    roll_ball_name = rigutils.get_control_name_from_module_name('roll_ball', side)
    roll_ball_loc = ik_foot_joints[1].getTranslation(space='world')
    roll_ball_ori = ik_foot_joints[1].getRotation(quaternion=True, space='world')
    roll_ball_ctr, roll_ball_loc_ori = rigutils.make_controller_node(roll_ball_name, side,
                                                                     shape_name='halfCircleBiDirIndicator',
                                                                     mirror=(-1, -1, -1),
                                                                     shape_rotation=(90, 0, 90), shape_scale=(3, 3, 3),
                                                                     location=roll_ball_loc, rotation=roll_ball_ori)

    roll_toes_name = rigutils.get_control_name_from_module_name('roll_toes', side)
    roll_toes_loc = ik_foot_joints[2].getTranslation(space='world')
    roll_toes_loc[1] = 0.0
    roll_toes_ori = ik_foot_joints[2].getRotation(quaternion=True, space='world')
    roll_toes_ctr, roll_toes_loc_ori = rigutils.make_controller_node(roll_toes_name, side, shape_name='halfCircleBiDir',
                                                                     mirror=(-1, -1, -1),
                                                                     shape_rotation=(90, 0, -30), shape_scale=(2, 2, 2),
                                                                     location=roll_toes_loc, rotation=roll_toes_ori)

    toes_name = rigutils.get_control_name_from_module_name('toes', side)
    toes_loc = ik_foot_joints[1].getTranslation(space='world')
    toes_ori = ik_foot_joints[1].getRotation(quaternion=True, space='world')
    toes_ctr, toes_loc_ori = rigutils.make_controller_node(toes_name, side, shape_name='circleDirectional',
                                                           mirror=(-1, -1, -1),
                                                           shape_rotation=(270, 0, 0), shape_scale=(3, 3, 3),
                                                           location=toes_loc, rotation=toes_ori)
    # make foot controller - end

    ankle_ik_name = 'ankle_to_ball{0}{1}'.format(side, rigutils.SUFFIX_IK_HANDLE)
    ankle_handle, ankle_effector = rigutils.create_ik_chain(ik_foot_joints[0], ik_foot_joints[1], ankle_ik_name)
    toe_ik_name = 'ball_to_toe{0}{1}'.format(side, rigutils.SUFFIX_IK_HANDLE)
    toe_handle, toe_effector = rigutils.create_ik_chain(ik_foot_joints[1], ik_foot_joints[2], toe_ik_name)

    # parent stuff
    toe_handle.setParent(toes_ctr)

    ankle_handle.setParent(roll_ball_ctr)
    roll_ball_parent_grp, roll_ball_constraint = rigutils.constrain_controller(roll_toes_ctr, roll_ball_ctr)
    toes_parent_grp, toes_constraint = rigutils.constrain_controller(roll_toes_ctr, toes_ctr)
    roll_toes_parent_grp, roll_toes_constraint = rigutils.constrain_controller(heel_ctr, roll_toes_ctr)
    # heel_parent_grp, heel_constraint = constrain_controller(foot_ctr, heel_ctr)
    [lo.setParent(foot_ctr) for lo in [heel_loc_ori, roll_ball_loc_ori, roll_toes_loc_ori, toes_loc_ori]]

    pm.delete(bind_joints[2])
    if leg_controls_struct:
        joint_constraint = pm.parentConstraint(roll_ball_ctr, leg_controls_struct.ik_handle, maintainOffset=True)
        rigutils.set_up_parent_switch(bind_joints[1], [ik_foot_joints[1], fk_joints[1]], leg_controls_struct.parent_blend_attr)
        blend_attr = leg_controls_struct.parent_blend_attr
    else:
        joint_constraint = pm.parentConstraint(roll_ball_ctr, ik_foot_joints[0], maintainOffset=True)
        # parent bind skel
        for parent_joint, bind_joint in zip(ik_foot_joints[:2], bind_joints[:2]):
            pm.parentConstraint(parent_joint, bind_joint, maintainOffset=True)
        # fk foot
        fk_joints = get_duped_joints_for_three_joint_chain(start_joint, rigutils.SUFFIX_FK, fk_group)
        fk_controls, fk_loc_oris, cons = rigutils.make_fk_controls(fk_joints[:2], side)
        for b_joint, ik_joint, fk_joint in zip(bind_joints[:2], ik_foot_joints[:2], fk_joints):
            rigutils.set_up_parent_switch(b_joint, [ik_joint, fk_joint], leg_controls_struct.parent_blend_attr)

    for fk_loc_ori in fk_loc_oris:
        rigutils.set_up_visibility_switch(fk_loc_ori, blend_attr)

    for ik_loc_ori in [heel_loc_ori, roll_ball_loc_ori, roll_toes_loc_ori, toes_loc_ori, foot_loc_ori]:
        rigutils.set_up_visibility_switch(ik_loc_ori, blend_attr, use_one_minus=True)


def rig_leg(start_joint, parent_blend_attr=None, module_name='leg'):
    side = rigutils.get_side_from_name(start_joint.nodeName())
    module_group, controls_group, components_group, ik_group, fk_group = setup_module_groups(module_name, side)
    bind_joints = skelutils.get_hierarchy_from_root(start_joint, joints_only=True)
    ik_joints = get_duped_joints_for_three_joint_chain(start_joint, rigutils.SUFFIX_IK, ik_group)
    ik_joints[0].setParent(ik_group)
    fk_joints = get_duped_joints_for_three_joint_chain(start_joint, rigutils.SUFFIX_FK, fk_group)
    fk_joints[0].setParent(fk_group)

    knee_pv_loc_ori, leg_ik_handle = rigutils.set_up_ik_rig(ik_joints, ik_group, module_name, side)

    fk_controls, fk_loc_oris, cons = rigutils.make_fk_controls(fk_joints, side)

    if not parent_blend_attr:
        _, _, parent_blend_attr = rigutils.set_up_ikfk_blend_controller(bind_joints[2], side)
    for b_joint, ik_joint, fk_joint in zip(bind_joints, ik_joints, fk_joints):
        rigutils.set_up_parent_switch(b_joint, [ik_joint, fk_joint], parent_blend_attr)

    # visibility toggle
    for fk_loc_ori in fk_loc_oris:
        rigutils.set_up_visibility_switch(fk_loc_ori, parent_blend_attr)
    rigutils.set_up_visibility_switch(knee_pv_loc_ori, parent_blend_attr, use_one_minus=True)

    leg_controls_struct = LegControlsStruct(bind_joints[2], fk_joints[2], ik_joints[2], fk_controls[2],
                                            parent_blend_attr, leg_ik_handle)
    return leg_controls_struct


def set_heel_loc_ori(node, joints):
    ankle_loc = joints[0].getTranslation(space='world')
    ball_loc = joints[1].getTranslation(space='world')
    ankle_ball_length = ankle_loc - ball_loc
    ankle_ball_length = ankle_ball_length.length()
    heel_offset = ankle_ball_length * 0.3
    heel_x = ankle_loc[0]
    heel_y = 0.0
    heel_z = ankle_loc[2] - heel_offset
    heel_loc = om.MVector(heel_x, heel_y, heel_z)
    heel_orientation_loc = om.MVector(heel_x, ball_loc[1], ankle_loc[2])
    aim_axis = om.MVector().kXaxisVector
    aim_vector = ball_loc - heel_orientation_loc
    aim_vector.normalize()
    heel_ori_quaternion = om.MQuaternion(aim_axis, aim_vector)
    node.setRotation(heel_ori_quaternion)
    xformutils.move_node_to_worldspace_position(node, heel_loc)
    # pm.xform(rotation=(0, 0, 90), worldSpace=True)


def get_heel_loc_ori(ankle_joint, ball_joint):
    ankle_loc = om.MVector(ankle_joint.getTranslation(space='world'))
    ball_loc = om.MVector(ball_joint.getTranslation(space='world'))
    ankle_ball_length = ankle_loc - ball_loc
    ankle_ball_length = ankle_ball_length.length()
    heel_offset = ankle_ball_length * 0.3
    heel_x = ankle_loc[0]
    heel_y = 0.0
    heel_z = ankle_loc[2] - heel_offset
    heel_loc = om.MVector(heel_x, heel_y, heel_z)
    heel_orientation_loc = om.MVector(heel_x, ball_loc[1], ankle_loc[2])
    aim_axis = om.MVector().kXaxisVector
    aim_vector = ball_loc - heel_orientation_loc
    aim_vector.normalize()
    heel_ori_quaternion = om.MQuaternion(aim_axis, aim_vector)
    return heel_loc, heel_ori_quaternion


def get_foot_loc_ori(ankle_joint, ball_joint):
    ankle_loc = xformutils.get_worldspace_vector(ankle_joint)
    ball_loc = xformutils.get_worldspace_vector(ball_joint)
    foot_loc = ankle_loc
    foot_orientation_loc = om.MVector(ankle_loc[0], ball_loc[1], ankle_loc[2])
    aim_axis = om.MVector().kZaxisVector
    aim_vector = ball_loc - foot_orientation_loc
    aim_vector.normalize()
    heel_ori_quaternion = om.MQuaternion(aim_axis, aim_vector)
    return foot_loc, heel_ori_quaternion


def get_duped_joints_for_three_joint_chain(start_joint, suffix=None, parent=None):
    dup_start_name = None
    if suffix is not None:
        dup_start_name = stringutils.replace_suffix(start_joint.nodeName(), suffix)
    duped_start = pm.duplicate(start_joint, name=dup_start_name)[0]
    all_joints = skelutils.get_hierarchy_from_root(duped_start, joints_only=True)
    if len(all_joints) > 3:
        pm.delete(all_joints[3])
        all_joints = skelutils.get_hierarchy_from_root(duped_start, joints_only=True)
    if suffix is not None:
        for joint in all_joints[1:]:
            new_name = stringutils.replace_suffix(joint.name(), suffix)
            joint.rename(new_name)
    if parent:
        duped_start.setParent(parent)
    return all_joints


def setup_module_groups(module_name, side, module_group=None, controls_group=None,
                        components_group=None, ik_parent=None, fk_parent=None):
    module_group = _setup_module_group_node(module_name, side, rigutils.SUFFIX_MODULE, module_group)
    controls_group = _setup_module_group_node(module_name, side, rigutils.SUFFIX_CONTROLS, controls_group, module_group)
    components_group = _setup_module_group_node(module_name, side, rigutils.SUFFIX_COMP_GROUP, components_group, module_group)
    ik_parent = _setup_module_group_node(module_name, side, rigutils.SUFFIX_IK_GROUP, ik_parent, components_group)
    fk_parent = _setup_module_group_node(module_name, side, rigutils.SUFFIX_FK_GROUP, fk_parent, components_group)
    return module_group, controls_group, components_group, ik_parent, fk_parent


def _setup_module_group_node(module_name, side, suffix, group_node, parent=None):
    if group_node is SKIP_SENTINEL:
        return group_node
    group_node = group_node or rigutils.create_group_node('{}{}{}'.format(module_name, side, suffix))
    if parent:
        rigutils.safe_parent(parent, group_node)
    return group_node


def floor_cvs(curve_node):
    pm.move(curve_node.cv, moveY=True, absolute=True, worldSpace=True)
