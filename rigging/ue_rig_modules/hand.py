from typing import NamedTuple

import pymel.core as pm

import flottitools.rigging.ue_rig_modules as ue_rig
import flottitools.rigging.ue_rig_modules.arm as arm_rig
import flottitools.utils.rigutils as rigutils
import flottitools.utils.stringutils as stringutils
import flottitools.utils.transformutils as xformutils


FINGER_TYPE_TO_SPREAD_VALUE_MAP = {ue_rig.JOINT_NAME_THUMB: 0.0,
                                   ue_rig.JOINT_NAME_INDEX: 0.5,
                                   ue_rig.JOINT_NAME_MIDDLE: 0.0,
                                   ue_rig.JOINT_NAME_RING: -0.5,
                                   ue_rig.JOINT_NAME_PINKY: -1.0}

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

    module_type: str = ue_rig.MODULE_TYPE_DEFAULT_FINGER


class HandJoints(NamedTuple):
    hand: pm.nt.Joint


class HandRigComponents(NamedTuple):
    module_group: pm.nt.Transform
    joints_bind: HandJoints
    joints_fk: HandJoints
    wrist_controller: pm.nt.Transform
    all_fingers_grip_attr: pm.Attribute
    all_fingers_spread_attr: pm.Attribute
    finger_rigs: FingerRig


class HandRig(ue_rig.RigModule):
    side_suffix = ''
    bind_joints = None
    rig_components = None
    rig_to_bind_constraints = []
    bind_to_rig_constraints = []
    controllers_to_bake = []
    pole_vector_to_transforms = {}
    parent_node = None
    module_name = ''

    def __init__(self, side_suffix, arm_rig_components, module_name='hand', parent_node=None):
        super().__init__(side_suffix, module_name=module_name, parent_node=parent_node)
        self.arm_rig = arm_rig_components
        self.finger_bind_joints = []

    def get_joints_from_scene(self):
        hand_joints_struct, finger_joint_structs = get_hand_and_finger_joints_from_scene(self.side_suffix)
        # bind_joints = list(hand_joints_struct)
        # for finger_joint_struct in finger_joint_structs:
        #     bind_joints.extend(list(finger_joint_struct))
        self.bind_joints = hand_joints_struct
        self.finger_bind_joints = finger_joint_structs

    def build_rig(self):
        hand_joints_struct, finger_joint_structs = get_hand_and_finger_joints_from_scene(self.side_suffix)
        self.rig_components = build_hand_rig(hand_joints_struct, finger_joint_structs,
                                             side_suffix=self.side_suffix, arm_rig_struct=self.arm_rig)

    def constrain_rig_to_bind_joints(self):
        constraints = hand_constrain_rig_to_bind_skeleton(self.rig_components)
        self.rig_to_bind_constraints = constraints
        return constraints

    def constrain_bind_joints_to_rig(self):
        constraints = hand_constrain_bind_joints_to_rig(self.rig_components)
        self.bind_to_rig_constraints = constraints
        return constraints

    def get_controllers_to_bake(self):
        controllers_to_bake = hand_get_controllers_to_bake(self.rig_components)
        return controllers_to_bake

    def get_pole_vector_to_transforms(self):
        return {}

    def get_bind_joints_in_rig(self):
        bind_joints = list(self.bind_joints)
        for finger_joints_struct in self.finger_bind_joints:
            bind_joints.extend(list(finger_joints_struct))
        return bind_joints

    def tear_down(self):
        pm.delete(self.rig_components.module_group)


def rig_right_hand(arm_rig_components: arm_rig.ArmRigComponents = None):
    hand_joints_struct, finger_joint_structs = get_hand_and_finger_joints_from_scene(ue_rig.SIDE_SUFFIX_RIGHT)
    return build_hand_rig(hand_joints_struct, finger_joint_structs, arm_rig_struct=arm_rig_components)


def rig_left_hand(arm_rig_components: arm_rig.ArmRigComponents = None):
    hand_joints_struct, finger_joint_structs = get_hand_and_finger_joints_from_scene(ue_rig.SIDE_SUFFIX_LEFT)
    return build_hand_rig(hand_joints_struct, finger_joint_structs, arm_rig_struct=arm_rig_components)


def get_hand_and_finger_joints_from_scene(side_suffix):
    hand_joints_struct = HandJoints(ue_rig.get_joint_by_name(ue_rig.JOINT_NAME_HAND, side_suffix=side_suffix))

    def get_finger_joints_by_name(base_finger_name):
        finger_joints = []
        for i in range(1, 4):
            finger_joint_name = '{0}_0{1}'.format(base_finger_name, i)
            finger_joints.append(ue_rig.get_joint_by_name(finger_joint_name, side_suffix=side_suffix))
        return finger_joints

    finger_joint_structs = [FingerJoints(*get_finger_joints_by_name(name)) for name in ue_rig.FINGER_NAMES]
    return hand_joints_struct, finger_joint_structs


def build_hand_rig(hand_joints_struct: HandJoints, finger_joints: [FingerJoints],
                   module_name='hand', module_group=None, side_suffix=None,
                   arm_rig_struct: arm_rig.ArmRigComponents = None):
    side = side_suffix or ue_rig.get_side_from_name(hand_joints_struct.hand.nodeName())
    # module_name = module_name or 'hand{0}_{1}'.format(side, rigutils.SUFFIX_MODULE)
    module_group, controls_group, components_group, _, fk_group = ue_rig.setup_module_groups(
        module_name, side, module_group, ik_parent=ue_rig.SKIP_SENTINEL)

    # if arm_rig_struct:
    fingers_parent = rigutils.create_group_node('{}_root_GRP'.format(module_name), controls_group)
    xformutils.match_worldspace_position_orientation(fingers_parent, hand_joints_struct.hand)
    hand_grip_control = arm_rig_struct.switch_controller
    parent_cons, _ = rigutils.set_up_parent_switch(fingers_parent,
                                                   (arm_rig_struct.joints_ik.hand, arm_rig_struct.joints_fk.hand),
                                                   arm_rig_struct.parent_blend_attr)
    fk_hand_joints_struct = HandJoints(arm_rig_struct.joints_fk.hand)


    grip_attr_name = '{}Grip'.format(module_name.split('_', 1)[0])
    grip_attr = rigutils.make_parent_switch_attr(hand_grip_control, grip_attr_name, values=(-30.0, 90.0))
    spread_attr_name = '{}Spread'.format(module_name.split('_', 1)[0])
    spread_attr = rigutils.make_parent_switch_attr(hand_grip_control, spread_attr_name, values=(-10.0, 30.0))

    finger_rig_structs = []
    for finger_struct, type_string in zip(finger_joints, ue_rig.FINGER_NAMES):
        spread_scalar = FINGER_TYPE_TO_SPREAD_VALUE_MAP.get(type_string, 0.0)
        finger_rig = build_finger_rig(finger_struct, module_name=type_string, module_parent=module_group,
                                      spread_dir=spread_scalar)
        finger_rig_structs.append(finger_rig)

    for finger_rig_struct in finger_rig_structs:
        pm.parentConstraint(fingers_parent, finger_rig_struct.loc_ori_01, maintainOffset=True)
        if finger_rig_struct.module_type == ue_rig.MODULE_TYPE_THUMB_FINGER:
            continue
        spread_scalar = FINGER_TYPE_TO_SPREAD_VALUE_MAP.get(finger_rig_struct.module_type, 0.0)
        fk_controllers = [finger_rig_struct.fk_controller_01,
                          finger_rig_struct.fk_controller_02,
                          finger_rig_struct.fk_controller_03]
        offset_groups, scalar_nodes = do_grip_attr_stuff(fk_controllers, grip_attr, 1)
        spread_attr = do_spread_attr_stuff(spread_attr, offset_groups[0].rotateY, spread_scalar)
    # pm.parentConstraint(wrist_control, finger_rig_struct.loc_ori_01, maintainOffset=True)

    # pm.parentConstraint(fk_hand_joints_struct.hand, hand_joints_struct.hand, maintainOffset=True)

    hand_rig_struct = HandRigComponents(module_group, hand_joints_struct, fk_hand_joints_struct,
                                        fingers_parent, grip_attr, spread_attr, finger_rig_structs)
    return hand_rig_struct


def duplicate_hand_joints(hand_joints_struct: HandJoints, suffix, parent=None):
    dup_joint = pm.duplicate(hand_joints_struct.hand, parentOnly=True)[0]
    new_hand_joints_struct = HandJoints(dup_joint)
    if parent:
        dup_joint.setParent(parent)
    # dup_name = stringutils.replace_suffix(dup_joint.nodeName(), suffix)
    dup_name = '{}_{}'.format(hand_joints_struct.hand.nodeName(), suffix)
    dup_joint.rename(dup_name)
    return new_hand_joints_struct


def build_finger_rig(finger_joints_struct: FingerJoints, module_name=ue_rig.MODULE_TYPE_DEFAULT_FINGER,
                     module_parent=None, spread_dir=1):
    side = ue_rig.get_side_from_name(finger_joints_struct.finger_01.nodeName())
    # module_name = '{0}{1}'.format(module_type, side)
    # module_group_name = '{0}{1}'.format(module_name, rigutils.SUFFIX_MODULE)
    module_group, controls_group, components_group, _, fk_group = ue_rig.setup_module_groups(
        module_name, side, ik_parent=ue_rig.SKIP_SENTINEL)
    if module_parent:
        rigutils.safe_parent(module_parent, module_group)

    fk_finger_joints_struct = duplicate_finger_joints(finger_joints_struct, rigutils.SUFFIX_FK, fk_group)

    fk_joints = [fk_finger_joints_struct.finger_01, fk_finger_joints_struct.finger_02,
                 fk_finger_joints_struct.finger_03]
    fk_controls, fk_loc_oris, cons = rigutils.make_fk_controls(fk_joints, side, shape_type='halfCircleBiDirIndicator',
                                                               shape_rotation=(90, 0, 90), shape_scale=(1, 1, 1))
    fk_loc_oris[0].setParent(controls_group)

    # grip_attr_name = '{}Grip'.format(module_group_name.split('_', 1)[0])
    grip_attr_name = '{}Grip'.format(module_name)
    grip_attr = rigutils.make_parent_switch_attr(fk_controls[0], grip_attr_name, values=(-30.0, 90.0))

    # spread_attr_name = '{}Spread'.format(module_group_name.split('_', 1)[0])
    spread_attr_name = '{}Spread'.format(module_name)
    spread_attr = rigutils.make_parent_switch_attr(fk_controls[0], spread_attr_name, values=(-10.0, 30.0))

    offset_groups, scalar_nodes = do_grip_attr_stuff(fk_controls, grip_attr, -1)
    spread_attr = do_spread_attr_stuff(spread_attr, offset_groups[0].rotateY, spread_dir)

    # bind_joints = [finger_joints_struct.finger_01, finger_joints_struct.finger_02, finger_joints_struct.finger_03]
    # for bind_joint, fk_joint in zip(bind_joints, fk_joints):
    #     pm.parentConstraint(fk_joint, bind_joint, maintainOffset=True)
    finger_rig_struct = FingerRig(finger_joints_struct, fk_finger_joints_struct,
                                  fk_controls[0], fk_controls[1], fk_controls[2],
                                  fk_loc_oris[0], fk_controls[0], grip_attr, spread_attr, module_name)
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
            constraints.append(rigutils.parent_constraint_shortest(bind_joint, fk_controller, maintain_offset=True))
    return constraints


def hand_constrain_bind_joints_to_rig(hand_rig_components: HandRigComponents):
    constraints = []
    for finger_rig in hand_rig_components.finger_rigs:
        finger_rig: FingerRig
        fk_controllers = [finger_rig.fk_controller_01, finger_rig.fk_controller_02, finger_rig.fk_controller_03]
        for bind_joint, fk_controller in zip(finger_rig.finger_joints_bind, fk_controllers):
            # constraints.append(pm.parentConstraint(fk_controller, bind_joint, maintainOffset=True))
            constraints.append(rigutils.parent_constraint_shortest(fk_controller, bind_joint, maintain_offset=True))
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
        # dup_name = stringutils.replace_suffix(source_joint.nodeName(), suffix)
        # dup_name = source_joint.nodeName() + suffix
        dup_name = '{}_{}'.format(source_joint.nodeName(), suffix)
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
    controllers_to_bake = []
    for finger_rig in hand_rig_components.finger_rigs:
        thing = [finger_rig.fk_controller_01, finger_rig.fk_controller_02, finger_rig.fk_controller_03]
        controllers_to_bake.extend(thing)
    return controllers_to_bake
