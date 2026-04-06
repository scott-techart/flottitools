from typing import NamedTuple

import pymel.core as pm

import flottitools.rigging.ue_rig_modules as ue_rig
import flottitools.utils.rigutils as rigutils

class ArmJoints(NamedTuple):
    clavicle: pm.nt.Joint
    upperarm: pm.nt.Joint
    upperarm_twist: pm.nt.Joint
    lowerarm: pm.nt.Joint
    lowerarm_twist: pm.nt.Joint
    hand: pm.nt.Joint


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


class ArmRig(ue_rig.RigModule):
    side_suffix = ''
    bind_joints: ArmJoints = None
    rig_components: ArmRigComponents = None
    rig_to_bind_constraints = []
    bind_to_rig_constraints = []
    controllers_to_bake = []
    pole_vector_to_transforms = {}
    parent_node = None
    module_name = 'arm'

    def get_joints_from_scene(self):
        self.bind_joints = get_arm_joints_from_scene(self.side_suffix)
        return self.bind_joints

    def build_rig(self):
        self.rig_components = build_arm_rig(self.bind_joints)

    def constrain_rig_to_bind_joints(self):
        constraints, fk_controls = arm_constrain_rig_to_bind_skeleton(self.rig_components)
        self.rig_to_bind_constraints = constraints
        return constraints

    def constrain_bind_joints_to_rig(self):
        rig_constraints = arm_constrain_bind_joints_to_rig(self.rig_components)
        self.bind_to_rig_constraints = rig_constraints
        return rig_constraints

    def get_controllers_to_bake(self):
        self.controllers_to_bake = arm_get_controllers_to_bake(self.rig_components)
        return self.controllers_to_bake

    def get_pole_vector_to_transforms(self):
        self.pole_vector_to_transforms = arm_get_pole_vector_to_transforms(self.rig_components)
        return self.pole_vector_to_transforms

    def tear_down(self):
        pm.delete(self.rig_components.module_group)


def get_left_arm_joints_from_scene():
    return get_arm_joints_from_scene(ue_rig.SIDE_SUFFIX_LEFT)


def get_right_arm_joints_from_scene():
    return get_arm_joints_from_scene(ue_rig.SIDE_SUFFIX_RIGHT)


def get_arm_joints_from_scene(side_suffix):
    clavicle = ue_rig.get_joint_by_name(ue_rig.JOINT_NAME_CLAVICLE, side_suffix)
    upperarm = ue_rig.get_joint_by_name(ue_rig.JOINT_NAME_UPPERARM, side_suffix)
    upperarm_twist = ue_rig.get_joint_by_name(ue_rig.JOINT_NAME_UPPERARMTWIST, side_suffix)
    lowerarm = ue_rig.get_joint_by_name(ue_rig.JOINT_NAME_LOWERARM, side_suffix)
    lowerarm_twist = ue_rig.get_joint_by_name(ue_rig.JOINT_NAME_LOWERARMTWIST, side_suffix)
    hand = ue_rig.get_joint_by_name(ue_rig.JOINT_NAME_HAND, side_suffix)
    return ArmJoints(clavicle, upperarm, upperarm_twist, lowerarm, lowerarm_twist, hand)


def rig_left_arm():
    left_arm_joints = get_left_arm_joints_from_scene()
    return build_arm_rig(left_arm_joints)


def rig_right_arm():
    right_arm_joints = get_right_arm_joints_from_scene()
    return build_arm_rig(right_arm_joints)


def build_arm_rig(arm_joints_struct: ArmJoints, module_name='arm', module_group=None):
    side = ue_rig.get_side_from_name(arm_joints_struct[0].nodeName())
    module_group, controls_group, components_group, ik_group, fk_group = ue_rig.setup_module_groups(
        module_name, side, module_group)

    ik_joints_struct = duplicate_arm_joints(arm_joints_struct, ue_rig.RIG_IK_PREFIX, ik_group)
    fk_joints_struct = duplicate_arm_joints(arm_joints_struct, ue_rig.RIG_FK_PREFIX, fk_group)
    ik_joints = [ik_joints_struct.upperarm, ik_joints_struct.lowerarm, ik_joints_struct.hand]
    #todo: refactor to return pv controller
    clavicle_ctr, clavicle_loc_ori, _ = rigutils.create_controller_and_constrain_joint(fk_joints_struct.clavicle)
    clavicle_loc_ori.setParent(controls_group)
    limb_bind_joints = ue_rig.LimbJoints(arm_joints_struct.upperarm, arm_joints_struct.upperarm_twist,
                                         arm_joints_struct.lowerarm, arm_joints_struct.lowerarm_twist,
                                         arm_joints_struct.hand)
    limb_ik_joints = ue_rig.LimbJoints(ik_joints_struct.upperarm, ik_joints_struct.upperarm_twist,
                                       ik_joints_struct.lowerarm, ik_joints_struct.lowerarm_twist,
                                       ik_joints_struct.hand)
    limb_fk_joints = ue_rig.LimbJoints(fk_joints_struct.upperarm, fk_joints_struct.upperarm_twist,
                                       fk_joints_struct.lowerarm, fk_joints_struct.lowerarm_twist,
                                       fk_joints_struct.hand)
    (fk_controls, ik_shoulder_loc_ori, ik_shoulder_ctr, ik_hand_ctr, pole_vector_ctr,
     ik_handle, upper_twist_ctr, lower_twist_ctr, switch_ctr, parent_blend_attr) = ue_rig.rig_limb(
        limb_bind_joints, limb_fk_joints, limb_ik_joints, controls_group, ik_group, clavicle_ctr, module_name, side)

    # ik_wrist_controller_name = rigutils.get_control_name_from_module_name('hand', side)
    # hand_loc = ik_joints_struct.hand.getTranslation(space='world')
    # hand_ori = ik_joints_struct.hand.getRotation(space='world')
    # ik_hand_ctr, ik_hand_loc_ori = rigutils.make_controller_node(
    #     ik_wrist_controller_name, side, shape_name='wedge', mirror=(1, 1, 1),
    #     shape_rotation=(-90, 180, 0), shape_scale=(-12, 1, 18), location=hand_loc, rotation=hand_ori, move_cv_x=12)
    # ik_hand_loc_ori.setParent(controls_group)
    # pm.parentConstraint(ik_hand_ctr, ik_handle, maintainOffset=True)
    # pm.orientConstraint(ik_hand_ctr, ik_joints_struct.hand, maintainOffset=True)

    pm.parentConstraint(clavicle_ctr, ik_shoulder_loc_ori, maintainOffset=True)
    pm.parentConstraint(clavicle_ctr, ik_joints_struct.clavicle, maintainOffset=True)

    # rigutils.set_up_visibility_switch(ik_hand_loc_ori, parent_blend_attr, use_one_minus=True)

    arm_rig_struct = ArmRigComponents(
        module_group, arm_joints_struct, ik_joints_struct, fk_joints_struct, clavicle_ctr, ik_shoulder_ctr,
        ik_hand_ctr, fk_controls[0], upper_twist_ctr, fk_controls[1], lower_twist_ctr, fk_controls[2],
        parent_blend_attr, ik_handle, switch_ctr, pole_vector_ctr)
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
        # constraining translate creates issues when the controller's position is controlled by the rig later.
        # constraints.append(pm.parentConstraint(parent, child, skipRotate=['x', 'y', 'z'], weight=1.0, maintainOffset=True))
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
    ue_rig.bake_animation_to_nodes(controllers_to_bake, start_frame, end_frame)
    ue_rig.key_pv_every_frame(arm_rig_components, start_frame, end_frame)
    pm.delete(constraints)


def arm_get_controllers_to_bake(arm_rig_components: ArmRigComponents):
    controllers_to_bake = [arm_rig_components.controller_clavicle, arm_rig_components.controller_fk_upperarm,
                           arm_rig_components.controller_fk_upperarm_twist, arm_rig_components.controller_fk_lowerarm,
                           arm_rig_components.controller_fk_lowerarm_twist, arm_rig_components.controller_fk_hand,
                           arm_rig_components.controller_ik_wrist, arm_rig_components.controller_ik_shoulder]
    return controllers_to_bake


def arm_get_pole_vector_to_transforms(arm_rig_components: ArmRigComponents):
    pv_to_transforms = {arm_rig_components.controller_pole_vector: [arm_rig_components.controller_fk_upperarm,
                                                                    arm_rig_components.controller_fk_lowerarm,
                                                                    arm_rig_components.controller_fk_hand]}
    return pv_to_transforms


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
    return rig_constraints
