from typing import NamedTuple

import pymel.core as pm

import apmaya.utils.rigutils as rigutils
import apmaya.utils.transformutils as transformutils
import apmaya.rigging.ue_rig_modules as ue_rig


DEFAULT_SPIDERLEG_MODULE_NAME = 'spiderLeg'


class SpiderLegJoints(NamedTuple):
    clavicle: pm.nt.Joint
    hip: pm.nt.Joint
    knee: pm.nt.Joint
    ankle: pm.nt.Joint
    end: pm.nt.Joint


class SpiderLegRigComponents(NamedTuple):
    module_group: pm.nt.Transform
    joints_bind: SpiderLegJoints
    joints_ik: SpiderLegJoints
    joints_fk: SpiderLegJoints

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
    
    toe_roll_controller = pm.nt.Transform
    toe_ik_handle = pm.nt.Transform


class SpiderLegRig(ue_rig.RigModule):
    side_suffix = ''
    bind_joints: SpiderLegJoints = None
    rig_components: SpiderLegRigComponents = None
    rig_to_bind_constraints = []
    bind_to_rig_constraints = []
    controllers_to_bake = []
    pole_vector_to_transforms = {}
    parent_node = None
    module_name = DEFAULT_SPIDERLEG_MODULE_NAME
    
    def __init__(self, parent_node=None):
        self.bind_joints = get_spider_leg_joints_from_scene()
        parts = self.bind_joints.clavicle.nodeName(stripNamespace=True).split('_')
        module_name = parts[1]
        side_suffix = '_{}'.format(parts[2])
        super().__init__(side_suffix, module_name=module_name, parent_node=parent_node)
        self.spider_leg_ik_joints = None
        self.spider_leg_fk_joints = None
        self.parent_blend_attr = None

    def build_rig(self):
        self.spider_leg_ik_joints, self.spider_leg_fk_joints, self.parent_blend_attr = build_spider_leg_rig(self.bind_joints, module_name=self.module_name, side=self.side_suffix)

    def constrain_bind_joints_to_rig(self):
        rig_constraints = leg_constrain_bind_joints_to_rig(self.bind_joints, self.spider_leg_ik_joints, self.spider_leg_fk_joints, self.parent_blend_attr)


def get_spider_leg_joints_from_scene():
    clavicle = pm.selected()[0]
    joints = [j for j in clavicle.getChildren(allDescendents=True) if isinstance(j, pm.nt.Joint)]
    joints.append(clavicle)
    joints.reverse()
    spider_leg_joints = SpiderLegJoints(*joints)
    return spider_leg_joints


def do_it():
    rig = SpiderLegRig()
    rig.build_rig()
    rig.constrain_bind_joints_to_rig()
    return rig


def leg_constrain_bind_joints_to_rig(buffer_joints, ik_joints, fk_joints, parent_blend_attr):
    rig_constraints = []
    for bind_joint, ik_joint, fk_joint in zip(buffer_joints, ik_joints, fk_joints):
        parent_cons, one_minus = rigutils.set_up_parent_switch(bind_joint, [ik_joint, fk_joint], parent_blend_attr)
        for p_con in parent_cons:
            p_con.interpType.set(2)
        rig_constraints.extend(parent_cons)
    return rig_constraints

def build_spider_leg_rig(buffer_spider_leg_joints: SpiderLegJoints, module_name=DEFAULT_SPIDERLEG_MODULE_NAME, module_group=None, side=None):
    side = side or ue_rig.get_side_from_name(buffer_spider_leg_joints[0].nodeName())
    module_group, controls_group, components_group, ik_group, fk_group = ue_rig.setup_module_groups(
        module_name, side, module_group)

    ik_joints_struct = duplicate_spider_leg_joints(buffer_spider_leg_joints, ue_rig.RIG_IK_PREFIX, ik_group)
    ik_joints = list(ik_joints_struct)
    fake_shoulder = pm.duplicate(ik_joints[1], parentOnly=True)[0]
    fake_shoulder_name = '{}_iktarget'.format(ik_joints[1].nodeName())
    fake_shoulder.rename(fake_shoulder_name)
    ik_joints[1].setParent(ik_group)
    fk_joints_struct = duplicate_spider_leg_joints(buffer_spider_leg_joints, ue_rig.RIG_FK_PREFIX, fk_group)

    ik_ctrs_grp = rigutils.create_group_node('{0}{1}_{2}_{3}'.format(module_name, side, 'ikCTRs', rigutils.SUFFIX_GROUP))
    rigutils.safe_parent(controls_group, ik_ctrs_grp)
    fk_ctrs_grp = rigutils.create_group_node('{0}{1}_{2}_{3}'.format(module_name, side, 'fkCTRs', rigutils.SUFFIX_GROUP))
    rigutils.safe_parent(controls_group, fk_ctrs_grp)

    clav_name = '{}{}_root_{}'.format(module_name, side, rigutils.SUFFIX_CONTROL)
    clavicle_ctr, clavicle_loc_ori, clavicle_con = rigutils.create_controller_and_constrain_joint(
        fk_joints_struct.clavicle, name=clav_name, side=side, shape_type='halfCircleBiDirIndicator', shape_rotation=(0, 0, 90), shape_scale=(3, 3, 3))
    rigutils.safe_parent(controls_group, clavicle_loc_ori)
    parent_blend_attr = rigutils.make_parent_switch_attr(clavicle_ctr, 'ikFkBlend')


    (fk_controls, ik_upperarm_loc_ori, ik_upperarm_ctr, ik_hand_ctr, pole_vector_ctr,
     ik_handle, switch_ctr, parent_blend_attr) = ue_rig.rig_limb_no_twist_joints(
        buffer_spider_leg_joints[1:], fk_joints_struct[1:], ik_joints_struct[1:], controls_group, ik_group, clavicle_ctr, module_name, side, stuff=(0, 0, 50), parent_blend_attr=parent_blend_attr, ik_ctrs_grp=ik_ctrs_grp, fk_ctrs_grp=fk_ctrs_grp)

    ik_kwargs = {'solver': "ikSCsolver"}
    ik_handle_name = '{0}_{1}_{2}'.format(module_name, 'shoulderPivot', rigutils.SUFFIX_IK_HANDLE)
    shoulder_pivot_handle, shoulder_pivot_effector = rigutils.create_ik_chain(ik_joints[0], fake_shoulder, ik_handle_name, **ik_kwargs)
    rigutils.safe_parent(ik_group, shoulder_pivot_handle)

    ik_handle_name = '{0}{1}_{2}_{3}'.format(module_name, side, 'toePivot', rigutils.SUFFIX_IK_HANDLE)
    toe_pivot_handle, toe_pivot_effector = rigutils.create_ik_chain(ik_joints[-2], ik_joints[-1], ik_handle_name, **ik_kwargs)
    rigutils.safe_parent(ik_group, toe_pivot_handle)

    toe_roll_name = '{0}{1}_{2}_{3}'.format(module_name, side, 'toeRoll', rigutils.SUFFIX_CONTROL)
    toe_roll_controller, toe_roll_loc_ori_node = rigutils.create_controller_from_joint(
        ik_joints[-1], toe_roll_name, side=side, shape_type='cube', shape_scale=(1, 1, 1), shape_rotation=(0, 0, 0))
    rigutils.safe_parent(ik_ctrs_grp, toe_roll_loc_ori_node)

    con = [c for c in ik_joints[1].getChildren() if isinstance(c, pm.nt.Constraint)][0]
    pm.delete(con)
    pm.pointConstraint(fake_shoulder, ik_joints[1], maintainOffset=True)

    rigutils.parent_constraint_shortest(clavicle_ctr, ik_upperarm_loc_ori)
    rigutils.parent_constraint_shortest(ik_upperarm_ctr, shoulder_pivot_handle)
    rigutils.parent_constraint_shortest(clavicle_ctr, fk_controls[0].getParent())
    pm.parentConstraint(ik_hand_ctr, ik_joints_struct.ankle, maintainOffset=True, skipTranslate=['x', 'y', 'z'])
    rigutils.parent_constraint_shortest(ik_hand_ctr, toe_pivot_handle)
    rigutils.parent_constraint_shortest(toe_roll_controller, ik_hand_ctr.getParent())

    return ik_joints, fk_joints_struct, parent_blend_attr


def duplicate_spider_leg_joints(spider_leg_joints: SpiderLegJoints, prefix, parent=None):
    dup_joints = pm.duplicate(spider_leg_joints, parentOnly=True)
    new_leg_joints_struct = SpiderLegJoints(*dup_joints)
    if parent:
        new_leg_joints_struct.clavicle.setParent(parent)
    for source_joint, dup_joint in zip(spider_leg_joints, new_leg_joints_struct):
        source_name = source_joint.nodeName()
        if source_name.lower().startswith('buffer_'):
            source_name = source_name.replace('buffer_', '')
            source_name = source_name.replace('Buffer_', '')
        dup_name = '{0}{1}'.format(prefix, source_name)
        dup_joint.rename(dup_name)
    return new_leg_joints_struct


def trash(leggrp, thoraxctr, rootctr):
    parts = leggrp.split('_')
    name = '{}_{}'.format(parts[0], parts[1])
    ikcomp = pm.PyNode('{}_ik_components_GRP'.format(name))
    clavctr = pm.PyNode('{}_root_CTR'.format(name))
    clavloc = pm.PyNode('{}_root_loc_ori_GRP'.format(name))
    toectr = pm.PyNode('{}_toeRoll_CTR'.format(name))
    pvctr = pm.PyNode('{}_poleVector_CTR'.format(name))
    pvloc = pm.PyNode('{}_poleVector_loc_ori_GRP'.format(name))

    aimthingy_name = '{}_aim_GRP'.format(name)
    claviori_name = '{}_aimRootOri_GRP'.format(name)
    aimthingy_target_name = '{}_aimTarget_GRP'.format(name)
    aimthingy = rigutils.create_group_node(aimthingy_name)
    aimtarget = rigutils.create_group_node(aimthingy_target_name)
    clavori = rigutils.create_group_node(claviori_name)
    aimthingy.setParent(ikcomp)
    aimtarget.setParent(ikcomp)
    clavori.setParent(ikcomp)
    transformutils.match_worldspace_position_orientation(aimthingy, clavloc)
    transformutils.match_worldspace_position_orientation(aimtarget, clavloc)
    transformutils.match_worldspace_position_orientation(clavori, clavloc)
    pm.move(aimtarget, (0, 10, 0), relative=True)
    pm.parentConstraint(thoraxctr, clavori, mo=True)
    pm.parentConstraint(thoraxctr, aimtarget, mo=True)
    pm.pointConstraint(thoraxctr, aimthingy, mo=True)
    pm.aimConstraint(aimtarget, aimthingy, aimVector=(0, 1, 0), upVector=(1, 0, 0), worldUpType='object', worldUpObject=toectr)

    pm.delete([c for c in pvloc.getChildren() if isinstance(c, pm.nt.Constraint)][0])
    pm.delete([c for c in clavloc.getChildren() if isinstance(c, pm.nt.Constraint)][0])
    pm.pointConstraint(thoraxctr, clavloc, mo=True)
    clav_con0 = pm.parentConstraint(clavori, clavloc, mo=True, skipTranslate=('x', 'y', 'z'))
    clav_con1 = pm.parentConstraint(aimthingy, clavloc, mo=True, skipTranslate=('x', 'y', 'z'))
    
    switch_attr = rigutils.make_parent_switch_attr(clavctr, attr_name='followToe')
    one_minus_node = pm.shadingNode('plusMinusAverage', asUtility=True, name='{}_oneMinusNode'.format(clavctr.nodeName()))
    subtract_operation_index = 2
    one_minus_node.operation.set(subtract_operation_index)
    one_minus_node.input1D[0].set(1.0)
    switch_attr.connect(one_minus_node.input1D[1], force=True)
    clav_con0.interpType.set(2)
    clav_con1.interpType.set(2)
    p_con_attr0 = [x for x in clav_con0.listAttr() if clavori.nodeName() in x.name()][0]
    p_con_attr1 = [x for x in clav_con1.listAttr() if aimthingy.nodeName() in x.name()][0]
    switch_attr.connect(p_con_attr1)
    one_minus_node.output1D.connect(p_con_attr0)
    switch_attr.set(1)
    
    pv_con0 = pm.parentConstraint(rootctr, pvloc, mo=True)
    pv_con1 = pm.parentConstraint(aimthingy, pvloc, mo=True)
    pv_switch_attr = rigutils.make_parent_switch_attr(pvctr, attr_name='followToe')
    one_minus_node = pm.shadingNode('plusMinusAverage', asUtility=True, name='{}_oneMinusNode'.format(pvctr.nodeName()))
    subtract_operation_index = 2
    one_minus_node.operation.set(subtract_operation_index)
    one_minus_node.input1D[0].set(1.0)
    pv_switch_attr.connect(one_minus_node.input1D[1], force=True)
    pv_con0.interpType.set(2)
    pv_con1.interpType.set(2)
    p_con_attr0 = [x for x in pv_con0.listAttr() if rootctr.nodeName() in x.name()][0]
    p_con_attr1 = [x for x in pv_con1.listAttr() if aimthingy.nodeName() in x.name()][0]
    pv_switch_attr.connect(p_con_attr1)
    one_minus_node.output1D.connect(p_con_attr0)
    pv_switch_attr.set(1)