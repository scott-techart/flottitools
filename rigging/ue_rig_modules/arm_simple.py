from typing import NamedTuple

import pymel.core as pm

import flottitools.rigging.ue_rig_modules as ue_rig
import flottitools.utils.rigutils as rigutils


class ArmJoints(NamedTuple):
    clavicle: pm.nt.Joint
    upperarm: pm.nt.Joint
    lowerarm: pm.nt.Joint
    hand: pm.nt.Joint


class ArmRigComponents(NamedTuple):
    module_group: pm.nt.Transform
    joints_bind: ArmJoints
    joints_ik: ArmJoints
    joints_fk: ArmJoints

    controller_ik_upperarm: pm.nt.Transform
    controller_ik_hand: pm.nt.Transform

    controller_fk_clavicle: pm.nt.Transform
    controller_fk_upperarm: pm.nt.Transform
    controller_fk_lowerarm: pm.nt.Transform
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
        self.rig_components = build_arm_rig(self.bind_joints, module_name=self.module_name)
        self.rig_components.module_group.setParent(self.parent_node)

    def constrain_rig_to_bind_joints(self):
        constraints, fk_controls = leg_constrain_rig_to_bind_skeleton(self.rig_components)
        self.rig_to_bind_constraints = constraints
        return constraints

    def constrain_bind_joints_to_rig(self):
        rig_constraints = leg_constrain_bind_joints_to_rig(self.rig_components)
        self.bind_to_rig_constraints = rig_constraints
        return rig_constraints

    def get_controllers_to_bake(self):
        self.controllers_to_bake = leg_get_controllers_to_bake(self.rig_components)
        return self.controllers_to_bake

    def get_pole_vector_to_transforms(self):
        self.pole_vector_to_transforms = leg_get_pole_vector_to_transforms(self.rig_components)
        return self.pole_vector_to_transforms

    def tear_down(self):
        pm.delete(self.rig_components.module_group)


def build_arm_rig(bind_arm_joints: ArmJoints, module_name='arm', module_group=None):
    side = ue_rig.get_side_from_name(bind_arm_joints[0].nodeName())
    module_group, controls_group, components_group, ik_group, fk_group = ue_rig.setup_module_groups(
        module_name, side, module_group)

    ik_joints_struct = duplicate_arm_joints(bind_arm_joints, ue_rig.RIG_IK_PREFIX, ik_group)
    fk_joints_struct = duplicate_arm_joints(bind_arm_joints, ue_rig.RIG_FK_PREFIX, fk_group)
    limb_bind_joints = ArmJoints(*bind_arm_joints)
    limb_ik_joints = ArmJoints(*ik_joints_struct)
    limb_fk_joints = ArmJoints(*fk_joints_struct)

    clavicle_ctr, clavicle_loc_ori, clavicle_con = rigutils.create_controller_and_constrain_joint(
        fk_joints_struct.clavicle, side=side)
    rigutils.safe_parent(controls_group, clavicle_loc_ori)

    (fk_controls, ik_upperarm_loc_ori, ik_upperarm_ctr, ik_hand_ctr, pole_vector_ctr,
     ik_handle, switch_ctr, parent_blend_attr) = ue_rig.rig_limb_no_twist_joints(
        limb_bind_joints[1:], limb_fk_joints[1:], limb_ik_joints[1:], controls_group, ik_group, clavicle_ctr, module_name, side, stuff=(0, 0, 50))

    rigutils.parent_constraint_shortest(clavicle_ctr, ik_upperarm_loc_ori)
    rigutils.parent_constraint_shortest(clavicle_ctr, fk_controls[0].getParent())
    pm.parentConstraint(ik_hand_ctr, ik_joints_struct.hand, maintainOffset=True, skipTranslate=['x', 'y', 'z'])

    arm_rig_struct = ArmRigComponents(
        module_group, bind_arm_joints, ik_joints_struct, fk_joints_struct, ik_upperarm_ctr, ik_hand_ctr,
        clavicle_ctr, fk_controls[0], fk_controls[1], fk_controls[2], parent_blend_attr, ik_handle, switch_ctr,
        pole_vector_ctr)
    return arm_rig_struct


def duplicate_arm_joints(arm_joints: ArmJoints, prefix, parent=None):
    dup_joints = pm.duplicate(arm_joints, parentOnly=True)
    new_leg_joints_struct = ArmJoints(*dup_joints)
    rigutils.safe_parent(new_leg_joints_struct.lowerarm, new_leg_joints_struct.hand)
    rigutils.safe_parent(new_leg_joints_struct.upperarm, new_leg_joints_struct.lowerarm)
    if parent:
        new_leg_joints_struct.upperarm.setParent(parent)
        # new_arm_joints_struct.upperarm.setParent(parent)
    for source_joint, dup_joint in zip(arm_joints, new_leg_joints_struct):
        # dup_name = stringutils.replace_suffix(source_joint.nodeName(), suffix)
        dup_name = '{0}{1}'.format(prefix, source_joint.nodeName())
        dup_joint.rename(dup_name)
    return new_leg_joints_struct


def get_arm_joints_from_scene(side_suffix):
    clavicle = ue_rig.get_joint_by_name(ue_rig.JOINT_NAME_CLAVICLE, side_suffix)
    upper_arm = ue_rig.get_joint_by_name(ue_rig.JOINT_NAME_UPPERARM, side_suffix)
    lower_arm = ue_rig.get_joint_by_name(ue_rig.JOINT_NAME_LOWERARM, side_suffix)
    hand = ue_rig.get_joint_by_name(ue_rig.JOINT_NAME_HAND, side_suffix)
    return ArmJoints(clavicle, upper_arm, lower_arm, hand)


def leg_constrain_rig_to_bind_skeleton(arm_rig_components: ArmRigComponents):
    bind_joints = [arm_rig_components.joints_bind.upperarm,
                   arm_rig_components.joints_bind.lowerarm,
                   arm_rig_components.joints_bind.hand]
    fk_controls = [arm_rig_components.controller_fk_upperarm,
                   arm_rig_components.controller_fk_lowerarm,
                   arm_rig_components.controller_fk_hand]
    constraints = []
    for bind_joint, fk_control in zip(bind_joints, fk_controls):
        constraints.append(pm.parentConstraint(bind_joint, fk_control, maintainOffset=True))
    constraints.append(pm.parentConstraint(arm_rig_components.controller_fk_upperarm,
                                           arm_rig_components.controller_ik_upperarm,
                                           maintainOffset=True))
    constraints.append(pm.parentConstraint(arm_rig_components.controller_fk_hand,
                                           arm_rig_components.controller_ik_hand,
                                           maintainOffset=True))
    return constraints, fk_controls


def leg_constrain_bind_joints_to_rig(arm_rig_components: ArmRigComponents):
    rig_constraints = []
    bind_joints = [arm_rig_components.joints_bind.upperarm,
                   arm_rig_components.joints_bind.lowerarm,
                   arm_rig_components.joints_bind.hand]
    ik_joints = [arm_rig_components.joints_ik.upperarm,
                 arm_rig_components.joints_ik.lowerarm,
                 arm_rig_components.joints_ik.hand]
    fk_joints = [arm_rig_components.joints_fk.upperarm,
                 arm_rig_components.joints_fk.lowerarm,
                 arm_rig_components.joints_fk.hand]
    for bind_joint, ik_joint, fk_joint in zip(bind_joints, ik_joints, fk_joints):
        parent_cons, one_minus = rigutils.set_up_parent_switch(bind_joint, [ik_joint, fk_joint],
                                                               arm_rig_components.parent_blend_attr)
        # setAttr "clavicle_l_parentConstraint1.interpType" 2;
        for p_con in parent_cons:
            p_con.interpType.set(2)
        rig_constraints.extend(parent_cons)
    return rig_constraints


def leg_get_controllers_to_bake(arm_rig_components: ArmRigComponents):
    controllers_to_bake = [arm_rig_components.controller_fk_upperarm,
                           arm_rig_components.controller_fk_lowerarm,
                           arm_rig_components.controller_fk_hand,
                           arm_rig_components.controller_ik_upperarm,
                           arm_rig_components.controller_ik_hand]
    return controllers_to_bake


def leg_get_pole_vector_to_transforms(arm_rig_components: ArmRigComponents):
    pv_to_transforms = {arm_rig_components.controller_pole_vector: [arm_rig_components.controller_fk_upperarm,
                                                                    arm_rig_components.controller_fk_lowerarm,
                                                                    arm_rig_components.controller_fk_hand]}
    return pv_to_transforms

