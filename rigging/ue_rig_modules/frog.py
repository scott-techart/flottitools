from typing import NamedTuple

import pymel.core as pm

import flottitools.rigging.ue_rig_modules as ue_rig
import flottitools.rigging.ue_rig_modules.arm_simple as arm
import flottitools.rigging.ue_rig_modules.foot as foot
import flottitools.rigging.ue_rig_modules.leg_simple as leg
import flottitools.rigging.ue_rig_modules.spine as spine
import flottitools.utils.rigutils as rigutils
import flottitools.utils.transformutils as xformutils


class FrogJoints(NamedTuple):
    root: pm.nt.Joint


class FrogRigComponents(NamedTuple):
    module_group: pm.nt.Transform
    joints_bind: FrogJoints
    joints_fk: FrogJoints

    controller_root: pm.nt.Transform

    arm_left: arm.ArmRig
    arm_right: arm.ArmRig

    leg_left: leg.LegRig
    leg_right: leg.LegRig

    foot_left: foot.FootRig
    foot_right: foot.FootRig

    spine: spine.SpineRig


class FrogRig(ue_rig.RigModule):
    side_suffix = ''
    bind_joints = None
    rig_components = None
    rig_to_bind_constraints = []
    bind_to_rig_constraints = []
    controllers_to_bake = []
    pole_vector_to_transforms = {}
    parent_node = None
    module_name = 'frog'

    def __init__(self, module_name='', parent_node=None):
        side_suffix = ''
        super().__init__(side_suffix, module_name=module_name, parent_node=parent_node)

    def get_joints_from_scene(self):
        self.bind_joints = get_frog_joints_from_scene()

    def build_rig(self):
        self.rig_components = build_frog_rig(self.bind_joints)

    def constrain_rig_to_bind_joints(self):
        self.rig_to_bind_constraints = frog_constrain_rig_to_bind_joints(self.rig_components)
        self.rig_to_bind_constraints.extend(self.rig_components.arm_left.constrain_rig_to_bind_joints())
        self.rig_to_bind_constraints.extend(self.rig_components.arm_right.constrain_rig_to_bind_joints())
        self.rig_to_bind_constraints.extend(self.rig_components.leg_left.constrain_rig_to_bind_joints())
        self.rig_to_bind_constraints.extend(self.rig_components.leg_right.constrain_rig_to_bind_joints())
        self.rig_to_bind_constraints.extend(self.rig_components.foot_left.constrain_rig_to_bind_joints())
        self.rig_to_bind_constraints.extend(self.rig_components.foot_right.constrain_rig_to_bind_joints())
        self.rig_to_bind_constraints.extend(self.rig_components.spine.constrain_rig_to_bind_joints())

    def constrain_bind_joints_to_rig(self):
        self.bind_to_rig_constraints = frog_constrain_bind_joints_to_rig(self.rig_components)
        self.bind_to_rig_constraints.extend(self.rig_components.arm_left.constrain_bind_joints_to_rig())
        self.bind_to_rig_constraints.extend(self.rig_components.arm_right.constrain_bind_joints_to_rig())
        self.bind_to_rig_constraints.extend(self.rig_components.leg_left.constrain_bind_joints_to_rig())
        self.bind_to_rig_constraints.extend(self.rig_components.leg_right.constrain_bind_joints_to_rig())
        self.bind_to_rig_constraints.extend(self.rig_components.foot_left.constrain_bind_joints_to_rig())
        self.bind_to_rig_constraints.extend(self.rig_components.foot_right.constrain_bind_joints_to_rig())
        self.bind_to_rig_constraints.extend(self.rig_components.spine.constrain_bind_joints_to_rig())

    def get_controllers_to_bake(self):
        self.controllers_to_bake = frog_get_controllers_to_bake(self.rig_components)
        self.controllers_to_bake.extend(self.rig_components.arm_left.get_controllers_to_bake())
        self.controllers_to_bake.extend(self.rig_components.arm_right.get_controllers_to_bake())
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
                 self.rig_components.leg_left.rig_components.module_group,
                 self.rig_components.leg_right.rig_components.module_group,
                 self.rig_components.foot_left.rig_components.module_group,
                 self.rig_components.foot_right.rig_components.module_group,
                 self.rig_components.spine.rig_components.module_group]
        stuff_to_delete.extend(stuff)
        pm.delete(stuff_to_delete)


def get_frog_joints_from_scene():
    names = [ue_rig.JOINT_NAME_ROOT]
    joints = [ue_rig.get_joint_by_name(name) for name in names]
    return FrogJoints(*joints)


def build_frog_rig(frog_joints: FrogJoints, module_name='frog', module_group=None):
    # side_suffix = side_suffix or ue_rig.get_side_from_name(biped_joints[0].nodeName())
    frog_group = rigutils.create_group_node('frog_rig')
    side_suffix = ''
    module_group, controls_group, components_group, _, fk_group = ue_rig.setup_module_groups(
        module_name, side_suffix, module_group, ik_parent=ue_rig.SKIP_SENTINEL)
    module_group.setParent(frog_group)

    fk_joints = duplicate_frog_joints(frog_joints, ue_rig.RIG_FK_PREFIX, fk_group)
    root_controller, root_loc_ori_node, root_con = rigutils.create_controller_and_constrain_joint(
        fk_joints.root, shape_scale=(10, 10, 10), shape_rotation=(90, 0, 0))
    root_loc_ori_node.setParent(controls_group)

    left_arm = arm.ArmRig(side_suffix=ue_rig.SIDE_SUFFIX_LEFT, module_name='arm', parent_node=frog_group)
    left_arm.build_rig()

    right_arm = arm.ArmRig(side_suffix=ue_rig.SIDE_SUFFIX_RIGHT, module_name='arm', parent_node=frog_group)
    right_arm.build_rig()

    left_leg = leg.LegRig(side_suffix=ue_rig.SIDE_SUFFIX_LEFT, module_name='leg', parent_node=frog_group)
    left_leg.build_rig()

    right_leg = leg.LegRig(side_suffix=ue_rig.SIDE_SUFFIX_RIGHT, module_name='leg', parent_node=frog_group)
    right_leg.build_rig()

    left_foot = foot.FootRig(ue_rig.SIDE_SUFFIX_LEFT, left_leg.rig_components, module_name='foot', parent_node=frog_group)
    left_foot.build_rig()

    right_foot = foot.FootRig(ue_rig.SIDE_SUFFIX_RIGHT, right_leg.rig_components, module_name='foot', parent_node=frog_group)
    right_foot.build_rig()

    spine_rig = spine.SpineRig(module_name='spine', parent_node=frog_group)
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
    clavicle_loc_oris = (left_arm.rig_components.controller_fk_clavicle.getParent(),
                         right_arm.rig_components.controller_fk_clavicle.getParent())
    clav_parent = (spine_rig.rig_components.joints_ik.spine_03, spine_rig.rig_components.joints_fk.spine_03)
    [rigutils.set_up_parent_switch(clav, clav_parent, spine_rig.rig_components.parent_blend_attr)
     for clav in clavicle_loc_oris]

    #tail
    tail_module_group, tail_controls_group, tail_components_group, _, tail_fk_group = ue_rig.setup_module_groups(
        'tail', side='', module_group=None, ik_parent=ue_rig.SKIP_SENTINEL)
    tail_module_group.setParent(frog_group)
    names = ['tail_01', 'tail_02', 'tail_03']
    tail_joints = [ue_rig.get_joint_by_name(name) for name in names]
    fk_tail_joints = pm.duplicate(tail_joints, parentOnly=True)
    rigutils.safe_parent(tail_fk_group, fk_tail_joints[0])
    for source_joint, dup_joint in zip(tail_joints, fk_tail_joints):
        dup_name = '{0}{1}'.format(ue_rig.RIG_FK_PREFIX, source_joint.nodeName())
        dup_joint.rename(dup_name)
    tail_fk_controls, tail_fk_loc_oris, tail_fk_cons = rigutils.make_fk_controls(fk_tail_joints, parent=tail_controls_group)
    for fk_controller, fk_joint in zip(tail_fk_controls, fk_tail_joints):
        pm.scaleConstraint(fk_controller, fk_joint)
    for bind_joint, fk_joint in zip(tail_joints, fk_tail_joints):
        rigutils.parent_constraint_shortest(fk_joint, bind_joint)
        pm.scaleConstraint(fk_joint, bind_joint)
    # tail_fk_loc_oris[0].setParent(spine_rig.rig_components.fk_controls)
    rigutils.parent_constraint_shortest(spine_rig.rig_components.joints_driver.pelvis, tail_fk_loc_oris[0])

    #jaw
    jaw_joint = ue_rig.get_joint_by_name('jaw')
    fk_jaw_joint = pm.duplicate(jaw_joint, parentOnly=True)[0]
    rigutils.safe_parent(spine_rig.rig_components.joints_fk[-1], fk_jaw_joint)
    dup_name = '{0}{1}'.format(ue_rig.RIG_FK_PREFIX, jaw_joint.nodeName())
    fk_jaw_joint.rename(dup_name)
    rigutils.parent_constraint_shortest(fk_jaw_joint, jaw_joint)
    jaw_controller, jaw_loc_ori_node, jaw_constraint = rigutils.create_controller_and_constrain_joint(fk_jaw_joint)
    rigutils.safe_parent(spine_rig.rig_components.head_ctr, jaw_loc_ori_node)

    #tongue
    tongue_module_group, tongue_controls_group, tongue_components_group, _, tongue_fk_group = ue_rig.setup_module_groups(
        'tongue', side='', module_group=None, ik_parent=ue_rig.SKIP_SENTINEL)
    tongue_module_group.setParent(frog_group)
    names = ['tongue_01', 'tongue_02', 'tongue_03', 'tongue_04']
    tongue_joints = [ue_rig.get_joint_by_name(name) for name in names]
    fk_tongue_joints = pm.duplicate(tongue_joints, parentOnly=True)
    rigutils.safe_parent(tongue_fk_group, fk_tongue_joints[0])
    for source_joint, dup_joint in zip(tongue_joints, fk_tongue_joints):
        dup_name = '{0}{1}'.format(ue_rig.RIG_FK_PREFIX, source_joint.nodeName())
        dup_joint.rename(dup_name)
    tongue_fk_controls, tongue_fk_loc_oris, tongue_fk_cons = rigutils.make_fk_controls(fk_tongue_joints, parent=tongue_controls_group)
    for fk_controller, fk_joint in zip(tongue_fk_controls, fk_tongue_joints):
        pm.scaleConstraint(fk_controller, fk_joint)
    for bind_joint, fk_joint in zip(tongue_joints, fk_tongue_joints):
        rigutils.parent_constraint_shortest(fk_joint, bind_joint)
        pm.scaleConstraint(fk_joint, bind_joint)
    # tongue_fk_loc_oris[0].setParent(spine_rig.rig_components.fk_controls[-1])
    # rigutils.parent_constraint_shortest(spine_rig.rig_components.joints_driver.head, tongue_fk_loc_oris[0])
    # rigutils.parent_constraint_shortest(spine_rig.rig_components.joints_driver.head, tongue_fk_loc_oris[0])
    rigutils.parent_constraint_shortest(fk_jaw_joint, tongue_fk_loc_oris[0])

    #seaweed
    seaweed_module_group, seaweed_controls_group, seaweed_components_group, _, seaweed_fk_group = ue_rig.setup_module_groups(
        'seaweed', side='', module_group=None, ik_parent=ue_rig.SKIP_SENTINEL)
    seaweed_module_group.setParent(frog_group)
    names = ['sweaweed_01', 'sweaweed_02']
    seaweed_controls = []
    seaweed_loc_oris = []
    for side in ['', ue_rig.SIDE_SUFFIX_LEFT, ue_rig.SIDE_SUFFIX_RIGHT]:
        seaweed_joints = [ue_rig.get_joint_by_name(name + side) for name in names]
        fk_seaweed_joints = pm.duplicate(seaweed_joints, parentOnly=True)
        rigutils.safe_parent(seaweed_fk_group, fk_seaweed_joints[0])
        for source_joint, dup_joint in zip(seaweed_joints, fk_seaweed_joints):
            dup_name = '{0}{1}'.format(ue_rig.RIG_FK_PREFIX, source_joint.nodeName())
            dup_joint.rename(dup_name)
        seaweed_fk_controls, seaweed_fk_loc_oris, seaweed_fk_cons = rigutils.make_fk_controls(fk_seaweed_joints, side=side, parent=seaweed_controls_group)
        for fk_controller, fk_joint in zip(seaweed_fk_controls, fk_seaweed_joints):
            pm.scaleConstraint(fk_controller, fk_joint)
        for bind_joint, fk_joint in zip(seaweed_joints, fk_seaweed_joints):
            rigutils.parent_constraint_shortest(fk_joint, bind_joint)
            pm.scaleConstraint(fk_joint, bind_joint)
        rigutils.parent_constraint_shortest(spine_rig.rig_components.joints_driver.spine_01, seaweed_fk_loc_oris[0])
        seaweed_controls.extend(seaweed_fk_controls)
        seaweed_loc_oris.extend(seaweed_fk_controls)

    #jigglers
    jiggle_module_group, jiggle_controls_group, jiggle_components_group, _, jiggle_fk_group = ue_rig.setup_module_groups(
        'jiggle', side='', module_group=None, ik_parent=ue_rig.SKIP_SENTINEL)
    jiggle_module_group.setParent(frog_group)
    names = ['belly_jiggle_r', 'belly_jiggle_c', 'belly_jiggle_l', 'throat_jiggle_c', 'throat_jiggle_r', 'throat_jiggle_l']
    jiggle_joints = [ue_rig.get_joint_by_name(name) for name in names]
    fk_jiggle_joints = pm.duplicate(jiggle_joints, parentOnly=True)
    rigutils.safe_parent(jiggle_fk_group, fk_jiggle_joints[0])
    for source_joint, dup_joint in zip(jiggle_joints, fk_jiggle_joints):
        dup_name = '{0}{1}'.format(ue_rig.RIG_FK_PREFIX, source_joint.nodeName())
        dup_joint.rename(dup_name)
    stuff = [rigutils.create_controller_and_constrain_joint(fk_joint) for fk_joint in fk_jiggle_joints]
    jiggle_fk_controls, jiggle_loc_oris, _ = zip(*stuff)
    # rigutils.safe_parent(jiggle_controls_group, jiggle_loc_oris[0])
    # rigutils.safe_parent(jiggle_controls_group, jiggle_loc_oris[3])
    [rigutils.safe_parent(jiggle_controls_group, jlo) for jlo in jiggle_loc_oris]
    for fk_controller, fk_joint in zip(jiggle_fk_controls, fk_jiggle_joints):
        pm.scaleConstraint(fk_controller, fk_joint)
    for bind_joint, fk_joint in zip(jiggle_joints, fk_jiggle_joints):
        rigutils.parent_constraint_shortest(fk_joint, bind_joint)
        pm.scaleConstraint(fk_joint, bind_joint)
    [rigutils.parent_constraint_shortest(spine_rig.rig_components.joints_driver.spine_01, lo)
     for lo in jiggle_loc_oris[:3]]
    [rigutils.parent_constraint_shortest(spine_rig.rig_components.joints_driver.head, lo)
     for lo in jiggle_loc_oris[3:]]

    #eyes
    bind_cons = []
    fk_cons = []

    names = ['eye_root', 'eye', 'eyelid_upper', 'eyelid_lower']
    for side in [ue_rig.SIDE_SUFFIX_LEFT, ue_rig.SIDE_SUFFIX_RIGHT]:
        eye_controllers = []
        eye_loc_ori = []
        eye_module_group, eye_controls_group, eye_components_group, _, eye_fk_group = ue_rig.setup_module_groups(
            'eye', side=side, module_group=None, ik_parent=ue_rig.SKIP_SENTINEL)
        eye_module_group.setParent(frog_group)
        # eye_root = rigutils.create_group_node('eye_root{}'.format(side))
        # rigutils.safe_parent(eye_controls_group, eye_root)
        eye_joints = [ue_rig.get_joint_by_name(name + side) for name in names]
        # xformutils.match_worldspace_position_orientation(eye_root, eye_joints[0])
        fk_eye_joints = pm.duplicate(eye_joints, parentOnly=True)
        [rigutils.safe_parent(eye_fk_group, fkej) for fkej in fk_eye_joints]
        # fk_cons = [rigutils.parent_constraint_shortest(fkj, bj) for fkj, bj in zip(eye_joints, fk_eye_joints)]
        for bind_joint, fk_joint in zip(eye_joints, fk_eye_joints):
            dup_name = '{0}{1}'.format(ue_rig.RIG_FK_PREFIX, bind_joint.nodeName())
            fk_joint.rename(dup_name)
            bind_cons.extend([rigutils.parent_constraint_shortest(fk_joint, bind_joint)])
            bind_cons.extend([pm.scaleConstraint(fk_joint, bind_joint)])
            controller, loc_ori_node, constraint = rigutils.create_controller_and_constrain_joint(fk_joint, side=side, name=dup_name+rigutils.SUFFIX_CONTROL)
            pm.scaleConstraint(controller, fk_joint)
            eye_controllers.append(controller)
            eye_loc_ori.append(loc_ori_node)
            # rigutils.safe_parent(eye_root, loc_ori_node)
        for each_loc_ori in eye_loc_ori[1:]:
            rigutils.safe_parent(eye_controllers[0], each_loc_ori)
        # pm.parentConstraint(eye_controllers[0], eye_loc_ori[1], skipRotate=['x', 'y', 'z'])
        # pm.parentConstraint(eye_controllers[0], eye_loc_ori[2], skipRotate=['x', 'y', 'z'])
        rigutils.safe_parent(eye_controls_group, eye_loc_ori[0])
        rigutils.parent_constraint_shortest(spine_rig.rig_components.joints_driver.head, eye_loc_ori[0])
            
    return FrogRigComponents(module_group, frog_joints, fk_joints, root_controller, left_arm, right_arm,
                              left_leg, right_leg, left_foot, right_foot, spine_rig)


def duplicate_frog_joints(frog_joints: FrogJoints, prefix, parent=None):
    dup_joints = pm.duplicate(frog_joints, parentOnly=True)
    new_frog_joints = FrogJoints(*dup_joints)
    if parent:
        new_frog_joints.root.setParent(parent)
    for source_joint, dup_joint in zip(frog_joints, new_frog_joints):
        dup_name = '{0}{1}'.format(prefix, source_joint.nodeName())
        dup_joint.rename(dup_name)
    return new_frog_joints


def frog_get_controllers_to_bake(biped_rig_components: FrogRigComponents):
    controllers = [biped_rig_components.controller_root]
    return controllers


def frog_constrain_bind_joints_to_rig(biped_rig_components: FrogRigComponents):
    controllers = [biped_rig_components.controller_root]
    constraints = []
    for controller, bind_joint in zip(controllers, biped_rig_components.joints_bind):
        constraints.append(rigutils.parent_constraint_shortest(controller, bind_joint))
    return constraints


def frog_constrain_rig_to_bind_joints(biped_rig_components: FrogRigComponents):
    controllers = [biped_rig_components.controller_root]
    constraints = []
    for bind_joint, controller in zip(biped_rig_components.joints_bind, controllers):
        constraints.append(rigutils.parent_constraint_shortest(bind_joint, controller))
    return constraints
