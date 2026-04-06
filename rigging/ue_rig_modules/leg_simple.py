from typing import NamedTuple

import pymel.core as pm

import flottitools.rigging.ue_rig_modules as ue_rig
import flottitools.utils.rigutils as rigutils


class LegJoints(NamedTuple):
    thigh: pm.nt.Joint
    calf: pm.nt.Joint
    foot: pm.nt.Joint


class LegRigComponents(NamedTuple):
    module_group: pm.nt.Transform
    joints_bind: LegJoints
    joints_ik: LegJoints
    joints_fk: LegJoints

    controller_ik_thigh: pm.nt.Transform
    controller_ik_foot: pm.nt.Transform

    controller_fk_thigh: pm.nt.Transform
    controller_fk_calf: pm.nt.Transform
    controller_fk_foot: pm.nt.Transform

    parent_blend_attr: pm.Attribute
    ik_handle: pm.nt.IkHandle
    switch_controller: pm.nt.Transform
    controller_pole_vector: pm.nt.Transform


class LegRig(ue_rig.RigModule):
    side_suffix = ''
    bind_joints: LegJoints = None
    rig_components: LegRigComponents = None
    rig_to_bind_constraints = []
    bind_to_rig_constraints = []
    controllers_to_bake = []
    pole_vector_to_transforms = {}
    parent_node = None
    module_name = 'leg'

    def get_joints_from_scene(self):
        self.bind_joints = get_leg_joints_from_scene(self.side_suffix)
        return self.bind_joints

    def build_rig(self):
        self.rig_components = build_leg_rig(self.bind_joints, module_name=self.module_name)
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


def build_leg_rig(bind_leg_joints: LegJoints, module_name='leg', module_group=None):
    side = ue_rig.get_side_from_name(bind_leg_joints[0].nodeName())
    module_group, controls_group, components_group, ik_group, fk_group = ue_rig.setup_module_groups(
        module_name, side, module_group)

    ik_joints_struct = duplicate_leg_joints(bind_leg_joints, ue_rig.RIG_IK_PREFIX, ik_group)
    fk_joints_struct = duplicate_leg_joints(bind_leg_joints, ue_rig.RIG_FK_PREFIX, fk_group)
    limb_bind_joints = LegJoints(*bind_leg_joints)
    limb_ik_joints = LegJoints(*ik_joints_struct)
    limb_fk_joints = LegJoints(*fk_joints_struct)
    (fk_controls, ik_thigh_loc_ori, ik_thigh_ctr, ik_foot_ctr, pole_vector_ctr,
     ik_handle, switch_ctr, parent_blend_attr) = ue_rig.rig_limb_no_twist_joints(
        limb_bind_joints, limb_fk_joints, limb_ik_joints, controls_group, ik_group, controls_group, module_name, side, stuff=(0, 0, -50))

    leg_rig_struct = LegRigComponents(
        module_group, bind_leg_joints, ik_joints_struct, fk_joints_struct, ik_thigh_ctr, ik_foot_ctr,
        fk_controls[0], fk_controls[1], fk_controls[2], parent_blend_attr, ik_handle, switch_ctr, pole_vector_ctr)
    return leg_rig_struct


def duplicate_leg_joints(leg_joints: LegJoints, prefix, parent=None):
    dup_joints = pm.duplicate(leg_joints, parentOnly=True)
    new_leg_joints_struct = LegJoints(*dup_joints)
    rigutils.safe_parent(new_leg_joints_struct.calf, new_leg_joints_struct.foot)
    rigutils.safe_parent(new_leg_joints_struct.thigh, new_leg_joints_struct.calf)
    if parent:
        new_leg_joints_struct.thigh.setParent(parent)
        # new_arm_joints_struct.upperarm.setParent(parent)
    for source_joint, dup_joint in zip(leg_joints, new_leg_joints_struct):
        # dup_name = stringutils.replace_suffix(source_joint.nodeName(), suffix)
        dup_name = '{0}{1}'.format(prefix, source_joint.nodeName())
        dup_joint.rename(dup_name)
    return new_leg_joints_struct


def get_leg_joints_from_scene(side_suffix):
    thigh = ue_rig.get_joint_by_name(ue_rig.JOINT_NAME_THIGH, side_suffix)
    calf = ue_rig.get_joint_by_name(ue_rig.JOINT_NAME_CALF, side_suffix)
    foot = ue_rig.get_joint_by_name(ue_rig.JOINT_NAME_FOOT, side_suffix)
    return LegJoints(thigh, calf, foot)


def leg_constrain_rig_to_bind_skeleton(leg_rig_components: LegRigComponents):
    bind_joints = [leg_rig_components.joints_bind.thigh,
                   leg_rig_components.joints_bind.calf,
                   leg_rig_components.joints_bind.foot]
    fk_controls = [leg_rig_components.controller_fk_thigh,
                   leg_rig_components.controller_fk_calf,
                   leg_rig_components.controller_fk_foot]
    constraints = []
    for bind_joint, fk_control in zip(bind_joints, fk_controls):
        constraints.append(pm.parentConstraint(bind_joint, fk_control, maintainOffset=True))
    constraints.append(pm.parentConstraint(leg_rig_components.controller_fk_thigh,
                                           leg_rig_components.controller_ik_thigh,
                                           maintainOffset=True))
    constraints.append(pm.parentConstraint(leg_rig_components.controller_fk_foot,
                                           leg_rig_components.controller_ik_foot,
                                           maintainOffset=True))
    return constraints, fk_controls


def leg_constrain_bind_joints_to_rig(leg_rig_components: LegRigComponents):
    rig_constraints = []
    bind_joints = [leg_rig_components.joints_bind.thigh,
                   leg_rig_components.joints_bind.calf,
                   leg_rig_components.joints_bind.foot]
    ik_joints = [leg_rig_components.joints_ik.thigh,
                 leg_rig_components.joints_ik.calf,
                 leg_rig_components.joints_ik.foot]
    fk_joints = [leg_rig_components.joints_fk.thigh,
                 leg_rig_components.joints_fk.calf,
                 leg_rig_components.joints_fk.foot]
    for bind_joint, ik_joint, fk_joint in zip(bind_joints, ik_joints, fk_joints):
        parent_cons, one_minus = rigutils.set_up_parent_switch(bind_joint, [ik_joint, fk_joint],
                                                               leg_rig_components.parent_blend_attr)
        # setAttr "clavicle_l_parentConstraint1.interpType" 2;
        for p_con in parent_cons:
            p_con.interpType.set(2)
        rig_constraints.extend(parent_cons)
    return rig_constraints


def leg_get_controllers_to_bake(leg_rig_components: LegRigComponents):
    controllers_to_bake = [leg_rig_components.controller_fk_thigh,
                           leg_rig_components.controller_fk_calf,
                           leg_rig_components.controller_fk_foot,
                           leg_rig_components.controller_ik_thigh]
    return controllers_to_bake


def leg_get_pole_vector_to_transforms(leg_rig_components: LegRigComponents):
    pv_to_transforms = {leg_rig_components.controller_pole_vector: [leg_rig_components.controller_fk_thigh,
                                                                    leg_rig_components.controller_fk_calf,
                                                                    leg_rig_components.controller_fk_foot]}
    return pv_to_transforms

