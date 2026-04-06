from typing import NamedTuple

import pymel.core as pm

import flottitools.rigging.ue_rig_modules as ue_rig
import flottitools.rigging.ue_rig_modules.arm as arm
import flottitools.rigging.ue_rig_modules.foot as foot
import flottitools.rigging.ue_rig_modules.hand as hand
import flottitools.rigging.ue_rig_modules.leg as leg
import flottitools.rigging.ue_rig_modules.spine as spine
import flottitools.utils.rigutils as rigutils


class BipedJoints(NamedTuple):
    root: pm.nt.Joint
    ik_foot_root: pm.nt.Joint
    ik_hand_root: pm.nt.Joint


class BipedRigComponents(NamedTuple):
    module_group: pm.nt.Transform
    joints_bind: BipedJoints
    joints_fk: BipedJoints

    controller_root: pm.nt.Transform
    controller_ik_foot_root: pm.nt.Transform
    controller_ik_hand_root: pm.nt.Transform

    arm_left: arm.ArmRig
    arm_right: arm.ArmRig

    hand_left: hand.HandRig
    hand_right: hand.HandRig

    leg_left: leg.LegRig
    leg_right: leg.LegRig

    foot_left: foot.FootRig
    foot_right: foot.FootRig

    spine: spine.SpineRig


class BipedRig(ue_rig.RigModule):
    side_suffix = ''
    bind_joints = None
    rig_components = None
    rig_to_bind_constraints = []
    bind_to_rig_constraints = []
    controllers_to_bake = []
    pole_vector_to_transforms = {}
    parent_node = None
    module_name = 'biped'

    def __init__(self, module_name='', parent_node=None):
        side_suffix = ''
        super().__init__(side_suffix, module_name=module_name, parent_node=parent_node)

    def get_joints_from_scene(self):
        self.bind_joints = get_biped_joints_from_scene()

    def build_rig(self):
        self.rig_components = build_biped_rig(self.bind_joints)

    def constrain_rig_to_bind_joints(self):
        self.rig_to_bind_constraints = biped_constrain_rig_to_bind_joints(self.rig_components)
        self.rig_to_bind_constraints.extend(self.rig_components.arm_left.constrain_rig_to_bind_joints())
        self.rig_to_bind_constraints.extend(self.rig_components.arm_right.constrain_rig_to_bind_joints())
        self.rig_to_bind_constraints.extend(self.rig_components.hand_left.constrain_rig_to_bind_joints())
        self.rig_to_bind_constraints.extend(self.rig_components.hand_right.constrain_rig_to_bind_joints())
        self.rig_to_bind_constraints.extend(self.rig_components.leg_left.constrain_rig_to_bind_joints())
        self.rig_to_bind_constraints.extend(self.rig_components.leg_right.constrain_rig_to_bind_joints())
        self.rig_to_bind_constraints.extend(self.rig_components.foot_left.constrain_rig_to_bind_joints())
        self.rig_to_bind_constraints.extend(self.rig_components.foot_right.constrain_rig_to_bind_joints())
        self.rig_to_bind_constraints.extend(self.rig_components.spine.constrain_rig_to_bind_joints())

    def constrain_bind_joints_to_rig(self):
        self.bind_to_rig_constraints = biped_constrain_bind_joints_to_rig(self.rig_components)
        self.bind_to_rig_constraints.extend(self.rig_components.arm_left.constrain_bind_joints_to_rig())
        self.bind_to_rig_constraints.extend(self.rig_components.arm_right.constrain_bind_joints_to_rig())
        self.bind_to_rig_constraints.extend(self.rig_components.hand_left.constrain_bind_joints_to_rig())
        self.bind_to_rig_constraints.extend(self.rig_components.hand_right.constrain_bind_joints_to_rig())
        self.bind_to_rig_constraints.extend(self.rig_components.leg_left.constrain_bind_joints_to_rig())
        self.bind_to_rig_constraints.extend(self.rig_components.leg_right.constrain_bind_joints_to_rig())
        self.bind_to_rig_constraints.extend(self.rig_components.foot_left.constrain_bind_joints_to_rig())
        self.bind_to_rig_constraints.extend(self.rig_components.foot_right.constrain_bind_joints_to_rig())
        self.bind_to_rig_constraints.extend(self.rig_components.spine.constrain_bind_joints_to_rig())

    def get_controllers_to_bake(self):
        self.controllers_to_bake = biped_get_controllers_to_bake(self.rig_components)
        self.controllers_to_bake.extend(self.rig_components.arm_left.get_controllers_to_bake())
        self.controllers_to_bake.extend(self.rig_components.arm_right.get_controllers_to_bake())
        self.controllers_to_bake.extend(self.rig_components.hand_left.get_controllers_to_bake())
        self.controllers_to_bake.extend(self.rig_components.hand_right.get_controllers_to_bake())
        self.controllers_to_bake.extend(self.rig_components.leg_left.get_controllers_to_bake())
        self.controllers_to_bake.extend(self.rig_components.leg_right.get_controllers_to_bake())
        self.controllers_to_bake.extend(self.rig_components.foot_left.get_controllers_to_bake())
        self.controllers_to_bake.extend(self.rig_components.foot_right.get_controllers_to_bake())
        self.controllers_to_bake.extend(self.rig_components.spine.get_controllers_to_bake())
        return self.controllers_to_bake

    def get_pole_vector_to_transforms(self):
        self.pole_vector_to_transforms = self.rig_components.arm_left.get_pole_vector_to_transforms()
        self.pole_vector_to_transforms.update(self.rig_components.arm_right.get_pole_vector_to_transforms())
        self.pole_vector_to_transforms = self.rig_components.leg_left.get_pole_vector_to_transforms()
        self.pole_vector_to_transforms.update(self.rig_components.leg_right.get_pole_vector_to_transforms())
        return self.pole_vector_to_transforms

    def get_bind_joints_in_rig(self):
        bind_joints = list(self.rig_components.joints_bind)
        bind_joints.extend(list(self.rig_components.arm_left.bind_joints))
        bind_joints.extend(list(self.rig_components.arm_right.bind_joints))
        bind_joints.extend(self.rig_components.hand_left.get_bind_joints_in_rig())
        bind_joints.extend(self.rig_components.hand_right.get_bind_joints_in_rig())
        bind_joints.extend(list(self.rig_components.leg_left.bind_joints))
        bind_joints.extend(list(self.rig_components.leg_right.bind_joints))
        bind_joints.extend(list(self.rig_components.foot_left.bind_joints))
        bind_joints.extend(list(self.rig_components.foot_right.bind_joints))
        bind_joints.extend(list(self.rig_components.spine.bind_joints))
        return bind_joints

    def tear_down(self):
        stuff_to_delete = self.bind_to_rig_constraints[:]
        stuff = [self.rig_components.module_group, self.rig_components.arm_left.rig_components.module_group,
                 self.rig_components.arm_right.rig_components.module_group,
                 self.rig_components.hand_left.rig_components.module_group,
                 self.rig_components.hand_right.rig_components.module_group,
                 self.rig_components.leg_left.rig_components.module_group,
                 self.rig_components.leg_right.rig_components.module_group,
                 self.rig_components.foot_left.rig_components.module_group,
                 self.rig_components.foot_right.rig_components.module_group,
                 self.rig_components.spine.rig_components.module_group]
        stuff_to_delete.extend(stuff)
        pm.delete(stuff_to_delete)


def get_biped_joints_from_scene():
    names = [ue_rig.JOINT_NAME_ROOT, ue_rig.JOINT_NAME_IK_FOOTROOT, ue_rig.JOINT_NAME_IK_HANDROOT]
    joints = [ue_rig.get_joint_by_name(name) for name in names]
    return BipedJoints(*joints)


def build_biped_rig(biped_joints: BipedJoints, module_name='biped', module_group=None):
    # side_suffix = side_suffix or ue_rig.get_side_from_name(biped_joints[0].nodeName())
    side_suffix = ''
    module_group, controls_group, components_group, _, fk_group = ue_rig.setup_module_groups(
        module_name, side_suffix, module_group, ik_parent=ue_rig.SKIP_SENTINEL)

    fk_joints = duplicate_biped_joints(biped_joints, ue_rig.RIG_FK_PREFIX, fk_group)
    root_controller, root_loc_ori_node, root_con = rigutils.create_controller_and_constrain_joint(
        fk_joints.root, shape_scale=(10, 10, 10), shape_rotation=(90, 0, 0))
    ik_hand_controller, ik_hand_loc_ori_node, ik_hand_con = rigutils.create_controller_and_constrain_joint(
        fk_joints.ik_hand_root, shape_scale=(8, 8, 8), shape_rotation=(90, 0, 0))
    ik_foot_controller, ik_foot_loc_ori_node, ik_foot_con = rigutils.create_controller_and_constrain_joint(
        fk_joints.ik_foot_root, shape_scale=(7, 7, 7), shape_rotation=(90, 0, 0))
    ik_hand_loc_ori_node.setParent(root_controller)
    ik_foot_loc_ori_node.setParent(root_controller)
    root_loc_ori_node.setParent(controls_group)

    left_arm = arm.ArmRig(side_suffix=ue_rig.SIDE_SUFFIX_LEFT)
    left_arm.build_rig()

    right_arm = arm.ArmRig(side_suffix=ue_rig.SIDE_SUFFIX_RIGHT)
    right_arm.build_rig()

    left_hand = hand.HandRig(ue_rig.SIDE_SUFFIX_LEFT, left_arm.rig_components)
    left_hand.build_rig()

    right_hand = hand.HandRig(ue_rig.SIDE_SUFFIX_RIGHT, right_arm.rig_components)
    right_hand.build_rig()

    left_leg = leg.LegRig(side_suffix=ue_rig.SIDE_SUFFIX_LEFT)
    left_leg.build_rig()

    right_leg = leg.LegRig(side_suffix=ue_rig.SIDE_SUFFIX_RIGHT)
    right_leg.build_rig()

    left_foot = foot.FootRig(ue_rig.SIDE_SUFFIX_LEFT, left_leg.rig_components)
    left_foot.build_rig()

    right_foot = foot.FootRig(ue_rig.SIDE_SUFFIX_RIGHT, right_leg.rig_components)
    right_foot.build_rig()

    spine_rig = spine.SpineRig()
    spine_rig.build_rig()
    ik_thigh_loc_oris = (left_leg.rig_components.controller_ik_thigh.getParent(),
                         right_leg.rig_components.controller_ik_thigh.getParent())
    thigh_parents = (spine_rig.rig_components.joints_ik.pelvis, spine_rig.rig_components.joints_fk.pelvis)
    # [pm.parentConstraint(spine_rig.rig_components.joints_ik.pelvis, ik_thigh, maintainOffset=True)
    [rigutils.set_up_parent_switch(ik_thigh, thigh_parents, spine_rig.rig_components.parent_blend_attr)
     for ik_thigh in ik_thigh_loc_oris]
    fk_thigh_loc_oris = [left_leg.rig_components.controller_fk_thigh.getParent(),
                         right_leg.rig_components.controller_fk_thigh.getParent()]
    # [pm.parentConstraint(spine_rig.rig_components.joints_fk.pelvis, ik_thigh, maintainOffset=True)
    #  for ik_thigh in fk_thigh_loc_oris]
    [rigutils.set_up_parent_switch(fk_thigh, thigh_parents, spine_rig.rig_components.parent_blend_attr)
     for fk_thigh in fk_thigh_loc_oris]
    clavicle_loc_oris = (left_arm.rig_components.controller_clavicle.getParent(),
                         right_arm.rig_components.controller_clavicle.getParent())
    clav_parent = (spine_rig.rig_components.joints_ik.spine_03, spine_rig.rig_components.joints_fk.spine_03)
    [rigutils.set_up_parent_switch(clav, clav_parent, spine_rig.rig_components.parent_blend_attr)
     for clav in clavicle_loc_oris]

    return BipedRigComponents(module_group, biped_joints, fk_joints, root_controller, ik_foot_controller,
                              ik_hand_controller, left_arm, right_arm, left_hand, right_hand,
                              left_leg, right_leg, left_foot, right_foot, spine_rig)


def duplicate_biped_joints(biped_joints: BipedJoints, prefix, parent=None):
    dup_joints = pm.duplicate(biped_joints, parentOnly=True)
    new_biped_joints = BipedJoints(*dup_joints)
    rigutils.safe_parent(new_biped_joints.root, new_biped_joints.ik_foot_root)
    rigutils.safe_parent(new_biped_joints.root, new_biped_joints.ik_hand_root)
    if parent:
        new_biped_joints.root.setParent(parent)
    for source_joint, dup_joint in zip(biped_joints, new_biped_joints):
        dup_name = '{0}{1}'.format(prefix, source_joint.nodeName())
        dup_joint.rename(dup_name)
    return new_biped_joints


def biped_constrain_rig_to_bind_joints(biped_rig_components: BipedRigComponents):
    controllers = [biped_rig_components.controller_root, biped_rig_components.controller_ik_foot_root,
                   biped_rig_components.controller_ik_hand_root]
    constraints = []
    for bind_joint, controller in zip(biped_rig_components.joints_bind, controllers):
        constraints.append(rigutils.parent_constraint_shortest(bind_joint, controller))
    return constraints


def biped_get_controllers_to_bake(biped_rig_components: BipedRigComponents):
    controllers = [biped_rig_components.controller_root, biped_rig_components.controller_ik_foot_root,
                   biped_rig_components.controller_ik_hand_root]
    return controllers


def biped_constrain_bind_joints_to_rig(biped_rig_components: BipedRigComponents):
    controllers = [biped_rig_components.controller_root, biped_rig_components.controller_ik_foot_root,
                   biped_rig_components.controller_ik_hand_root]
    constraints = []
    for controller, bind_joint in zip(controllers, biped_rig_components.joints_bind):
        constraints.append(rigutils.parent_constraint_shortest(controller, bind_joint))
    return constraints
