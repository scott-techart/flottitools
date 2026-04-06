from typing import NamedTuple

import pymel.core as pm

import flottitools.rigging.ue_rig_modules as ue_rig
import flottitools.utils.rigutils as rigutils
import flottitools.utils.skinutils as skinutils
import flottitools.utils.stringutils as stringutils


class SpineJoints(NamedTuple):
    pelvis: pm.nt.Joint
    spine_01: pm.nt.Joint
    spine_02: pm.nt.Joint
    spine_03: pm.nt.Joint
    neck_01: pm.nt.Joint
    head: pm.nt.Joint


class SpineRigComponents(NamedTuple):
    module_group: pm.nt.Transform
    joints_bind: SpineJoints
    joints_ik: SpineJoints
    joints_fk: SpineJoints
    joints_driver: SpineJoints

    upper_body_ctr: pm.nt.Transform
    pelvis_ctr: pm.nt.Transform
    neck_ctr: pm.nt.Transform
    head_ctr: pm.nt.Transform

    fk_controls: pm.nt.Transform

    spline_start_ctr: pm.nt.Transform
    spline_mid_ctr: pm.nt.Transform
    spline_end_ctr: pm.nt.Transform
    spline_neck_joint: pm.nt.Joint
    ik_handle: pm.nt.IkHandle
    ik_spline: pm.nt.Transform
    spline_control_joints: pm.nt.Joint

    parent_blend_attr: pm.Attribute
    # (bind_spine_joints, ik_joints, fk_joints, upper_body_ctr, pelvis_ctr, fk_controls, head_ctr, spline_start_ctr,
    #  spline_mid_ctr, spline_end_ctr,
    #  ik_handle, parent_blend_attr, spline_control_joints, ik_spline)


class SpineRig(ue_rig.RigModule):
    side_suffix = ''
    bind_joints: SpineJoints = None
    rig_components: SpineRigComponents = None
    rig_to_bind_constraints = []
    bind_to_rig_constraints = []
    controllers_to_bake = []
    pole_vector_to_transforms = {}
    parent_node = None
    module_name = 'spine'

    def __init__(self, module_name='', parent_node=None):
        side_suffix = ''
        super().__init__(side_suffix, module_name=module_name, parent_node=parent_node)

    def get_joints_from_scene(self):
        self.bind_joints = get_spine_joints_from_scene()
        return self.bind_joints

    def build_rig(self):
        self.rig_components = build_spine_rig(self.bind_joints)
        self.rig_components.module_group.setParent(self.parent_node)

    def constrain_rig_to_bind_joints(self):
        constraints = spine_constrain_rig_to_bind_skeleton(self.rig_components)
        self.rig_to_bind_constraints = constraints
        return constraints

    def constrain_bind_joints_to_rig(self):
        rig_constraints = spine_constrain_bind_joints_to_rig(self.rig_components)
        self.bind_to_rig_constraints = rig_constraints
        return rig_constraints

    def get_controllers_to_bake(self):
        self.controllers_to_bake = spine_get_controllers_to_bake(self.rig_components)
        return self.controllers_to_bake

    def get_pole_vector_to_transforms(self):
        self.pole_vector_to_transforms = {}
        return self.pole_vector_to_transforms

    def tear_down(self):
        pm.delete(self.rig_components.module_group)


def build_spine_rig(bind_spine_joints: SpineJoints, module_name='spine', side=''):
    'circleRaised'
    'circleSunken'
    side = side or ue_rig.get_side_from_name(bind_spine_joints[0].nodeName())
    module_group, controls_group, components_group, ik_group, fk_group = ue_rig.setup_module_groups(
        module_name, side)

    fk_controls, head_ctr, ik_handle, ik_spline, neck_ctr, parent_blend_attr, pelvis_ctr, spline_control_joints, spline_end_ctr, spline_mid_ctr, spline_neck_joint, spline_start_ctr, upper_body_ctr, ik_joints, fk_joints, driver_joints = rig_spine_ik_fk(
        bind_spine_joints, controls_group, ik_group, fk_group, module_name, components_group)

    return SpineRigComponents(module_group, bind_spine_joints, ik_joints, fk_joints, driver_joints, upper_body_ctr, pelvis_ctr,
                              neck_ctr, head_ctr, fk_controls, spline_start_ctr, spline_mid_ctr, spline_end_ctr,
                              spline_neck_joint, ik_handle, ik_spline, spline_control_joints, parent_blend_attr)


def rig_spine_ik_fk(bind_spine_joints, controls_group, ik_group, fk_group, module_name, components_group):
    ik_joints = duplicate_spine_joints(bind_spine_joints, ue_rig.RIG_IK_PREFIX, ik_group)
    fk_joints = duplicate_spine_joints(bind_spine_joints, ue_rig.RIG_FK_PREFIX, fk_group)
    driver_joints = duplicate_spine_joints(bind_spine_joints, ue_rig.RIG_DRIVER_PREFIX, components_group)

    upper_body_name = '{}_{}'.format('upper_body', rigutils.SUFFIX_CONTROL)
    upper_body_ctr, upper_body_loc_ori = rigutils.create_controller_from_joint(
        bind_spine_joints.pelvis, name=upper_body_name, shape_scale=(-20, 20, -20), shape_type='circleRaised')
    upper_body_loc_ori.setParent(controls_group)
    pelvis_name = '{}_{}'.format(ue_rig.JOINT_NAME_PELVIS, rigutils.SUFFIX_CONTROL)
    pelvis_ctr, pelvis_loc_ori = rigutils.create_controller_from_joint(bind_spine_joints.pelvis, name=pelvis_name,
                                                                       shape_scale=(-18, 18, -18),
                                                                       shape_type='circleSunken')
    pelvis_loc_ori.setParent(upper_body_ctr)
    fk_controls, fk_loc_oris, fk_cons = rigutils.make_fk_controls(fk_joints[:-2], parent=controls_group)
    # spline_neck_ctr_name = '{}_{}'.format(bind_spine_joints.neck_01.nodeName(), rigutils.SUFFIX_CONTROL)
    neck_ctr, neck_loc_ori, neck_con = rigutils.create_controller_and_constrain_joint(fk_joints[-2], name='neck_CTR')
    neck_loc_ori.setParent(controls_group)
    # head_ctrs, head_loc_oris, head_cons = rigutils.make_fk_controls([fk_joints[-1]], parent=controls_group)
    # head_ctr, head_loc_ori, head_con = list(zip(head_ctrs, head_loc_oris, head_cons))[0]
    head_ctr, head_loc_ori, head_con = rigutils.create_controller_and_constrain_joint(fk_joints[-1], name='head_CTR')
    head_loc_ori.setParent(controls_group)
    # head_parent_grp = rigutils.make_parent_group(head_ctr)
    spline_name = 'ik_{}_spline'.format(module_name)
    ik_spline = rigutils.create_spline_for_joint_chain(ik_joints.pelvis, ik_joints.neck_01)
    ik_spline.setParent(ik_group)
    # ikHandle - sol ikSplineSolver - ccv false - pcv false;
    ik_handle, ik_effector = rigutils.create_ik_chain(ik_joints.pelvis, ik_joints.neck_01,
                                                      name=spline_name, solver='ikSplineSolver',
                                                      curve=ik_spline, createCurve=False, parentCurve=False)
    ik_handle.setParent(ik_group)
    spline_rig_group = rigutils.create_group_node('{}_spline_{}'.format(module_name, rigutils.SUFFIX_COMP_GROUP))
    spline_rig_group.setParent(ik_group)
    spline_control_joints = pm.duplicate([ik_joints.pelvis, ik_joints.spine_02, ik_joints.neck_01], parentOnly=True)
    spline_joint_names = ['base', 'mid', 'top']
    for joint, joint_name in zip(spline_control_joints, spline_joint_names):
        joint.setParent(spline_rig_group)
        joint.rename('{0}_spline_{1}_{2}'.format(module_name, joint_name, rigutils.SUFFIX_IK))
    spline_skincl = skinutils.bind_mesh_to_joints(ik_spline, spline_control_joints)

    def make_spline_controller(joint):
        spline_ctr, spline_loc_ori, spline_con = rigutils.create_controller_and_constrain_joint(joint, shape_scale=(
        10, 10, 10))
        spline_parent_grp = rigutils.make_parent_group(spline_ctr)
        return spline_ctr, spline_parent_grp, spline_loc_ori, spline_con

    spline_start_ctr, spline_start_parent_grp, spline_start_loc_ori, spline_start_con = make_spline_controller(
        spline_control_joints[0])
    spline_mid_ctr, spline_mid_parent_grp, spline_mid_loc_ori, spline_mid_con = make_spline_controller(
        spline_control_joints[1])
    spline_end_ctr, spline_end_parent_grp, spline_end_loc_ori, spline_end_con = make_spline_controller(
        spline_control_joints[2])
    [lo.setParent(controls_group) for lo in [spline_start_loc_ori, spline_mid_loc_ori, spline_end_loc_ori]]
    rigutils.parent_constraint_shortest(pelvis_ctr, spline_start_parent_grp)
    rigutils.parent_constraint_shortest(upper_body_ctr, spline_mid_parent_grp)
    rigutils.parent_constraint_shortest(upper_body_ctr, spline_end_parent_grp)
    parent_blend_attr = rigutils.make_parent_switch_attr(upper_body_ctr, 'ikFkBlend')
    # head_parent_grp = rigutils.make_parent_group(head_ctr)
    spline_neck_joint = pm.duplicate(ik_joints.neck_01, parentOnly=True)[0]
    spline_neck_joint.setParent(ik_group)
    spline_neck_joint_name = '{}_spline_{}'.format(ue_rig.RIG_IK_PREFIX, ue_rig.JOINT_NAME_NECK01)
    spline_neck_joint.rename(spline_neck_joint_name)
    # pm.pointConstraint(ik_joints.neck_01, spline_neck_joint, maintainOffset=False)
    # pm.orientConstraint(spline_end_ctr, spline_neck_joint, maintainOffset=False)
    pm.parentConstraint(neck_ctr, spline_neck_joint, maintainOffset=True)
    spine_end_dummy = pm.createNode('transform')
    spine_dummy_name = stringutils.replace_suffix(neck_ctr.nodeName(), rigutils.SUFFIX_OFFSET_GROUP)
    spine_end_dummy.setParent(ik_group)
    spine_end_dummy.rename(spine_dummy_name)
    pm.pointConstraint(ik_joints.neck_01, spine_end_dummy, maintainOffset=False)
    pm.orientConstraint(spline_end_ctr, spine_end_dummy, maintainOffset=False)
    neck_parent_cons, neck_one_minus = rigutils.set_up_parent_switch(
        neck_loc_ori, [spine_end_dummy, fk_controls[-1]], parent_blend_attr)
    head_parent_cons, head_one_minus = rigutils.set_up_parent_switch(
        head_loc_ori, [neck_ctr, fk_joints.neck_01], parent_blend_attr)
    # skinPercent - tv spine_spline_top_IKJ 1 skinCluster2 ikj_pelvis_spline.cv[4:6];
    pm.skinPercent(spline_skincl, ik_spline.cv[-3:], tv=(spline_control_joints[2], 1.0))
    ik_handle.dWorldUpType.set(4)
    pelvis_ctr.worldMatrix[0].connect(ik_handle.dWorldUpMatrix)
    spline_end_ctr.worldMatrix[0].connect(ik_handle.dWorldUpMatrixEnd)
    ik_handle.dTwistControlEnable.set(True)
    rigutils.set_up_visibility_switch(fk_loc_oris[0], parent_blend_attr)
    ik_controls = (spline_start_loc_ori, spline_mid_loc_ori, spline_end_loc_ori)
    [rigutils.set_up_visibility_switch(ikc, parent_blend_attr, use_one_minus=True) for ikc in ik_controls]

    constraints = []
    fake_ik_joints = list(ik_joints[:-2])
    fake_ik_joints.append(spline_neck_joint)
    for driver_joint, ik_joint, fk_joint in zip(driver_joints, fake_ik_joints, fk_joints):
        parent_cons, one_minus = rigutils.set_up_parent_switch(driver_joint, [ik_joint, fk_joint],
                                                               parent_blend_attr)
        for p_con in parent_cons:
            p_con.interpType.set(2)
        constraints.extend(parent_cons)
    constraints.append(rigutils.parent_constraint_shortest(fk_joints[-1], driver_joints[-1]))

    return fk_controls, head_ctr, ik_handle, ik_spline, neck_ctr, parent_blend_attr, pelvis_ctr, spline_control_joints, spline_end_ctr, spline_mid_ctr, spline_neck_joint, spline_start_ctr, upper_body_ctr, ik_joints, fk_joints, driver_joints


def get_spine_joints_from_scene():
    names = [ue_rig.JOINT_NAME_PELVIS, ue_rig.JOINT_NAME_SPINE01, ue_rig.JOINT_NAME_SPINE02, ue_rig.JOINT_NAME_SPINE03,
             ue_rig.JOINT_NAME_NECK01, ue_rig.JOINT_NAME_HEAD]
    joints = [ue_rig.get_joint_by_name(j_name) for j_name in names]
    spine_joints = SpineJoints(*joints)
    return spine_joints


def duplicate_spine_joints(spine_joints: SpineJoints, prefix, parent=None):
    dup_joints = pm.duplicate(spine_joints, parentOnly=True)
    new_spine_joints = SpineJoints(*dup_joints)
    rigutils.safe_parent(new_spine_joints.pelvis, new_spine_joints.spine_01)
    rigutils.safe_parent(new_spine_joints.spine_01, new_spine_joints.spine_02)
    rigutils.safe_parent(new_spine_joints.spine_02, new_spine_joints.spine_03)
    rigutils.safe_parent(new_spine_joints.spine_03, new_spine_joints.neck_01)
    rigutils.safe_parent(new_spine_joints.neck_01, new_spine_joints.head)
    if parent:
        new_spine_joints.pelvis.setParent(parent)
    for source_joint, dup_joint in zip(spine_joints, new_spine_joints):
        dup_name = '{0}{1}'.format(prefix, source_joint.nodeName())
        dup_joint.rename(dup_name)
    return new_spine_joints


def spine_constrain_rig_to_bind_skeleton(spine_rig_components: SpineRigComponents):
    fk_controls = spine_rig_components.fk_controls[:]
    fk_controls.append(spine_rig_components.neck_ctr)
    fk_controls.append(spine_rig_components.head_ctr)
    constraints = []
    for bind_joint, fk_control in zip(spine_rig_components.joints_bind, fk_controls):
        constraints.append(pm.parentConstraint(bind_joint, fk_control, maintainOffset=True))

    fk_drivers = [spine_rig_components.fk_controls[0], spine_rig_components.fk_controls[2]]
                  # spine_rig_components.fk_controls[4]]
    ik_driven = [spine_rig_components.spline_start_ctr, spine_rig_components.spline_mid_ctr]
                # spine_rig_components.spline_end_ctr]
    constraints.extend([pm.parentConstraint(fkd, ikd, maintainOffset=True) for fkd, ikd in zip(fk_drivers, ik_driven)])
    constraints.append(pm.parentConstraint(spine_rig_components.joints_bind.neck_01, spine_rig_components.spline_end_ctr, maintainOffset=True))
    # constraints.append(pm.orientConstraint(spine_rig_components.neck_ctr, spine_rig_components.spline_neck_ctr, maintainOffset=True))
    constraints.extend([pm.parentConstraint(spine_rig_components.joints_bind.pelvis, ctr, maintainOffset=True) for ctr in (spine_rig_components.pelvis_ctr, spine_rig_components.upper_body_ctr)])
    return constraints


def spine_constrain_bind_joints_to_rig(spine_rig: SpineRigComponents):
    constraints = []
    # constraints.append(pm.parentConstraint(spine_rig.joints_fk.head, spine_rig.joints_bind.head))
    bind_joints = spine_rig.joints_bind
    # ik_joints = list(spine_rig.joints_ik[:-2])
    # ik_joints.append(spine_rig.spline_neck_joint)
    fk_joints = spine_rig.joints_fk
    driver_joints = spine_rig.joints_driver
    # for bind_joint, ik_joint, fk_joint in zip(bind_joints, ik_joints, fk_joints):
    #     parent_cons, one_minus = rigutils.set_up_parent_switch(bind_joint, [ik_joint, fk_joint],
    #                                                            spine_rig.parent_blend_attr)
    #     for p_con in parent_cons:
    #         p_con.interpType.set(2)
    #     constraints.extend(parent_cons)
    for bind_joint, driver_joint in zip(bind_joints, driver_joints):
        constraints.extend(rigutils.parent_constraint_shortest(driver_joint, bind_joint))
    return constraints


def spine_get_controllers_to_bake(spine_rig: SpineRigComponents):
    controllers_to_bake = [spine_rig.upper_body_ctr, spine_rig.pelvis_ctr, spine_rig.head_ctr,
                           spine_rig.spline_start_ctr, spine_rig.spline_mid_ctr, spine_rig.spline_end_ctr,
                           spine_rig.neck_ctr]
    controllers_to_bake.extend(spine_rig.fk_controls)
    return controllers_to_bake
