from typing import NamedTuple
import math

import maya.api.OpenMaya as om
import pymel.core as pm

import flottitools.rigging.ue_rig_modules as ue_rig
import flottitools.rigging.ue_rig_modules.leg as leg
import flottitools.utils.rigutils as rigutils
import flottitools.utils.skeletonutils as skelutils
import flottitools.utils.stringutils as stringutils
import flottitools.utils.transformutils as xformutils


class FootJoints(NamedTuple):
    foot: pm.nt.Joint
    ball: pm.nt.Joint


class FootRigComponents(NamedTuple):
    module_group: pm.nt.Transform
    joints_bind: FootJoints
    joints_ik: FootJoints
    joints_fk: FootJoints

    controller_foot: pm.nt.Transform
    controller_fk_ball: pm.nt.Transform
    controller_heel: pm.nt.Transform
    controller_roll_ball: pm.nt.Transform
    controller_roll_toes: pm.nt.Transform
    controller_toes: pm.nt.Transform

    ik_handle_ankle: pm.nt.IkHandle
    ik_handle_toe: pm.nt.IkHandle
    ik_joint_toes: pm.nt.Joint

    attribute_parent_blend: pm.Attribute


class FootRig(ue_rig.RigModule):
    side_suffix = ''
    bind_joints: FootJoints = None
    rig_components: FootRigComponents = None
    rig_to_bind_constraints = []
    bind_to_rig_constraints = []
    controllers_to_bake = []
    pole_vector_to_transforms = {}
    parent_node = None
    module_name = 'foot'

    def __init__(self, side_suffix, leg_rig_components: leg.LegRigComponents, module_name='foot', parent_node=None):
        super().__init__(side_suffix, module_name=module_name, parent_node=parent_node)
        self.leg_rig_components = leg_rig_components

    def get_joints_from_scene(self):
        self.bind_joints = get_foot_joints_from_scene(self.side_suffix)
        return self.bind_joints

    def build_rig(self):
        self.rig_components = build_foot_rig(self.bind_joints, self.leg_rig_components, module_name=self.module_name,
                                             side=self.side_suffix)
        self.rig_components.module_group.setParent(self.parent_node)

    def constrain_rig_to_bind_joints(self):
        constraints = foot_constrain_rig_to_bind_skeleton(self.rig_components)
        self.rig_to_bind_constraints = constraints
        return constraints

    def constrain_bind_joints_to_rig(self):
        rig_constraints = foot_constrain_bind_joints_to_rig(self.rig_components)
        self.bind_to_rig_constraints = rig_constraints
        return rig_constraints

    def get_controllers_to_bake(self):
        self.controllers_to_bake = foot_get_controllers_to_bake(self.rig_components)
        return self.controllers_to_bake

    def get_pole_vector_to_transforms(self):
        return {}

    def tear_down(self):
        pm.delete(self.rig_components.module_group)


def build_foot_rig(bind_foot_joints: FootJoints, leg_rig_components: leg.LegRigComponents, module_name='foot', side=''):
    start_joint = bind_foot_joints.foot
    # bind_joints = skelutils.get_hierarchy_from_root(start_joint, joints_only=True)
    side = side or rigutils.get_side_from_name(bind_foot_joints.foot.nodeName())
    module_group, controls_group, components_group, ik_group, fk_group = ue_rig.setup_module_groups(module_name, side)
    # fk_joints = get_duped_joints_for_three_joint_chain(start_joint, SUFFIX_FK, fk_parent)
    ik_foot_joints, fk_foot_joints = duplicate_foot_joints(bind_foot_joints, leg_rig_components, side)
    # ik_foot_joints = duplicate_foot_joints(*bind_foot_joints, leg_rig_components)
    # fk_foot_joints.foot.setParent(leg_rig_components.joints_fk.foot)
    fk_ball_ctr, fk_ball_loc_ori, _ = rigutils.create_controller_and_constrain_joint(fk_foot_joints.ball, side=side)
    fk_ball_loc_ori.setParent(leg_rig_components.controller_fk_foot)
    # ik_joints
    # ik_ball = pm.duplicate(bind_foot_joints.ball)[0]
    # ik_toe = ik_ball.getChildren()[0]
    # ik_foot_joints.ball.setParent(leg_rig_components.joints_fk.foot)
    # new_name = stringutils.replace_suffix(ik_ball, rigutils.SUFFIX_IK)
    # ik_ball.rename(new_name)
    # ik_foot_joints = [leg_rig_components.ankle_joint_ik, ik_ball]

    foot_dir = 1
    if side == ue_rig.SIDE_SUFFIX_LEFT:
        foot_dir = -1
    # make foot controller - start
    foot_name = rigutils.get_control_name_from_module_name('foot', side)
    # foot_shape_loc, foot_shape_ori = get_foot_loc_ori(*ik_foot_joints[:2])
    # foot_shape_loc = xformutils.get_worldspace_vector(ik_foot_joints.foot)
    # foot_shape_loc, foot_shape_ori = get_foot_pos(leg_rig_components.joints_bind.calf, bind_foot_joints.foot, bind_foot_joints.ball)
    ankle_loc = xformutils.get_worldspace_vector(bind_foot_joints.foot)
    foot_shape_loc_vec, foot_ori, heel_loc_vec = get_foot_and_heel_loc_ori(bind_foot_joints.foot, bind_foot_joints.ball)
    # foot_shape_ori = ik_foot_joints.foot.getRotation(quaternion=True, space='world')
    # foot_ctr, foot_loc_ori = rigutils.make_controller_node(foot_name, side, shape_name='wedge', mirror=(1, 1, 1),
    #                                                        shape_rotation=(0, -180, 0), shape_scale=(-14, -10, -20),
    #                                                        location=ankle_loc, rotation=foot_ori,
    #                                                        move_cv_x=8)
    # foot_loc_ori.setParent(controls_group)
    foot_ctr = leg_rig_components.controller_ik_foot
    foot_loc_ori = foot_ctr.getParent()
    # foot_ctr, foot_loc_ori = rigutils.make_controller_node(foot_name, side, shape_name='wedge',
    #                                                        shape_rotation=(0, 0, 0), shape_scale=(1, 1, 1),
    #                                                        location=foot_shape_loc)
    # aim_target_vec = xformutils.get_worldspace_vector(bind_foot_joints.ball)
    # up_target_vec = xformutils.get_worldspace_vector(bind_foot_joints.foot)
    # floor_cvs(foot_ctr)
    # amount = 12 * foot_dir
    # move_cvs(foot_ctr, foot_shape_loc)

    heel_name = rigutils.get_control_name_from_module_name('heel', side)
    # heel_loc, heel_ori = get_heel_loc_ori(*ik_foot_joints[:2])
    ball_loc = xformutils.get_worldspace_vector(bind_foot_joints.ball)
    # heel_loc, heel_ori = get_heel_loc_ori(foot_shape_loc, ball_loc, ankle_loc)
    heel_ctr, heel_loc_ori = rigutils.make_controller_node(heel_name, side, shape_name='halfCircleBiDir',
                                                           shape_rotation=(90, 0, 45), shape_scale=(3, 3, 3),
                                                           location=heel_loc_vec, rotation=foot_ori)

    roll_ball_name = rigutils.get_control_name_from_module_name('roll_ball', side)
    roll_ball_loc = ik_foot_joints.ball.getTranslation(space='world')
    roll_ball_ori = ik_foot_joints.ball.getRotation(quaternion=True, space='world')
    roll_ball_ctr, roll_ball_loc_ori = rigutils.make_controller_node(roll_ball_name, side,
                                                                     shape_name='halfCircleBiDirIndicator',
                                                                     mirror=(-1, -1, -1),
                                                                     shape_rotation=(90, 0, 270), shape_scale=(3, 3, 3),
                                                                     location=roll_ball_loc, rotation=roll_ball_ori)

    toe_dir = 1
    if side == ue_rig.SIDE_SUFFIX_RIGHT:
        toe_dir = -1
    move_scaler = toe_dir * 0.5
    # move_scaler = toe_dir * 1.1
    roll_toes_loc = get_toe_worldspace_position(ik_foot_joints.foot, ik_foot_joints.ball, move_scaler=move_scaler)
    roll_toes_ori = ik_foot_joints.ball.getRotation(quaternion=True, space='world')
    roll_toes_name = rigutils.get_control_name_from_module_name('roll_toes', side)

    # roll_toes_loc = toes_loc
    # roll_toes_loc[1] = 0.0

    roll_toes_ctr, roll_toes_loc_ori = rigutils.make_controller_node(roll_toes_name, side, shape_name='halfCircleBiDir',
                                                                     mirror=(-1, -1, -1),
                                                                     shape_rotation=(90, 180, 30), shape_scale=(2, 2, 2),
                                                                     location=roll_toes_loc, rotation=roll_toes_ori)

    toes_name = rigutils.get_control_name_from_module_name('toes', side)
    # toes_loc = ik_foot_joints[1].getTranslation(space='world')
    toes_joint = pm.duplicate(ik_foot_joints.ball, parentOnly=True)[0]
    toes_joint.setParent(ik_foot_joints.ball)
    toes_joint.rename('{0}{1}'.format(ue_rig.JOINT_NAME_IK_TOE, side))
    xformutils.move_node_to_worldspace_position(toes_joint, roll_toes_loc)
    toes_loc = ik_foot_joints.ball.getTranslation(space='world')
    toes_ori = ik_foot_joints.ball.getRotation(quaternion=True, space='world')
    toes_ctr, toes_loc_ori = rigutils.make_controller_node(toes_name, side, shape_name='circleDirectional',
                                                           mirror=(-1, -1, -1),
                                                           shape_rotation=(270, 0, 180), shape_scale=(3, 3, 3),
                                                           location=toes_loc, rotation=toes_ori)
    # make foot controller - end

    ankle_ik_name = 'ankle_to_ball{0}{1}'.format(side, rigutils.SUFFIX_IK_HANDLE)
    ankle_handle, ankle_effector = rigutils.create_ik_chain(ik_foot_joints[0], ik_foot_joints[1], ankle_ik_name)
    toe_ik_name = 'ball_to_toe{0}{1}'.format(side, rigutils.SUFFIX_IK_HANDLE)
    toe_handle, toe_effector = rigutils.create_ik_chain(ik_foot_joints[1], toes_joint, toe_ik_name)

    # parent stuff
    toe_handle.setParent(toes_ctr)

    ankle_handle.setParent(roll_ball_ctr)
    roll_ball_parent_grp, roll_ball_constraint = rigutils.constrain_controller(roll_toes_ctr, roll_ball_ctr)
    toes_parent_grp, toes_constraint = rigutils.constrain_controller(roll_toes_ctr, toes_ctr)
    roll_toes_parent_grp, roll_toes_constraint = rigutils.constrain_controller(heel_ctr, roll_toes_ctr)
    # heel_parent_grp, heel_constraint = constrain_controller(foot_ctr, heel_ctr)
    [lo.setParent(foot_ctr) for lo in [heel_loc_ori, roll_ball_loc_ori, roll_toes_loc_ori, toes_loc_ori]]

    # joint_constraint = pm.parentConstraint(roll_ball_ctr, leg_rig_components.ik_handle, maintainOffset=True)
    # joint_constraint = pm.orientConstraint(foot_ctr, leg_controls_struct.ankle_joint_ik, maintainOffset=True)
    # print(bind_joints[1], [ik_foot_joints[1], fk_joints[1]], leg_controls_struct.parent_blend_attr)
    # rigutils.set_up_parent_switch(bind_foot_joints.ball, [ik_foot_joints.ball, fk_foot_joints.ball],
    #                               leg_rig_components.parent_blend_attr)
    # for b_joint, ik_joint, fk_joint in zip(bind_joints[:2], ik_foot_joints[:2], fk_joints):
    #     set_up_parent_switch(b_joint, [ik_joint, fk_joint], leg_controls_struct.parent_blend_attr)
    blend_attr = leg_rig_components.attribute_parent_blend

    rigutils.set_up_visibility_switch(fk_ball_loc_ori, blend_attr)

    # for ik_loc_ori in [heel_loc_ori, roll_ball_loc_ori, roll_toes_loc_ori, toes_loc_ori, foot_loc_ori]:
    #     rigutils.set_up_visibility_switch(ik_loc_ori, blend_attr, use_one_minus=True)
    for ik_loc_ori in [heel_loc_ori, roll_ball_loc_ori, roll_toes_loc_ori, toes_loc_ori]:
        rigutils.set_up_visibility_switch(ik_loc_ori, blend_attr, use_one_minus=True)

    pm.delete(leg_rig_components.ik_handle.translateX.listConnections())
    rigutils.parent_constraint_shortest(roll_ball_ctr, leg_rig_components.ik_handle)

    return FootRigComponents(module_group, bind_foot_joints, ik_foot_joints, fk_foot_joints, foot_ctr, fk_ball_ctr,
                             heel_ctr, roll_ball_ctr, roll_toes_ctr, toes_ctr, ankle_handle, toe_handle, toes_joint,
                             blend_attr)


def get_foot_joints_from_scene(side_suffix):
    foot = ue_rig.get_joint_by_name(ue_rig.JOINT_NAME_FOOT, side_suffix)
    ball = ue_rig.get_joint_by_name(ue_rig.JOINT_NAME_BALL, side_suffix)
    return FootJoints(foot, ball)


def get_foot_pos(knee_joint, ankle_joint, ball_joint):
    knee_pos = xformutils.get_worldspace_vector(knee_joint)
    ankle_pos = xformutils.get_worldspace_vector(ankle_joint)
    ball_pos = xformutils.get_worldspace_vector(ball_joint)
    knee_to_ankle = ankle_pos - knee_pos
    ankle_to_ball = ball_pos - ankle_pos
    angle = 1.15
    side_a = math.sin(angle) * ankle_to_ball
    a_length = side_a.length()
    ankle_to_ball_length = ankle_to_ball.length()
    b_length = math.sqrt((ankle_to_ball_length * ankle_to_ball_length) - (a_length * a_length))
    foot_pos = knee_to_ankle.normalize() * b_length * 1.4
    foot_pos += ankle_pos
    foot_ori = xformutils.get_aimed_quaternion(foot_pos, ball_pos, ankle_pos)

    return foot_pos, foot_ori


def get_foot_and_heel_loc_ori(foot_joint, ball_joint):
    foot_vec = xformutils.get_worldspace_vector(foot_joint)
    ball_vec = xformutils.get_worldspace_vector(ball_joint)
    ball_to_foot_vec = foot_vec - ball_vec
    ball_to_floor_angle = 0.5747367866192552
    rotate_ball_to_foot = om.MQuaternion(-0.28306629557448720336, 2.8755406425248517685e-06,
                                         0.014344452939599171629, 0.95899307034583514131)
    floor_vec = ball_to_foot_vec.rotateBy(rotate_ball_to_foot)
    floor_vec_norm = floor_vec.normalize()

    floor_length = math.cos(ball_to_floor_angle) * ball_to_foot_vec
    floor_length = floor_length.length()

    foot_shape_loc_vec = (floor_vec_norm * floor_length) + ball_vec
    aim_vec = ball_vec - foot_shape_loc_vec
    side_vec = xformutils.get_perpendicular_vector_from_three_points(foot_shape_loc_vec, ball_vec, foot_vec)
    up_vec = aim_vec ^ side_vec
    up_vec *= -1
    foot_ori = xformutils.get_aimed_quaternion(foot_shape_loc_vec, ball_vec, up_vec)
    heel_loc_vec = (floor_vec_norm * floor_length)*0.4 + foot_shape_loc_vec
    # heel_loc_vec = (floor_vec_norm * floor_length) * 0.004 + foot_shape_loc_vec

    return foot_shape_loc_vec, foot_ori, heel_loc_vec


def floor_cvs(curve_node):
    pm.move(curve_node.cv, moveY=True, absolute=True, worldSpace=True)


def move_cvs(curve_node, loc_vec):
    pm.move(curve_node.cv, loc_vec, relative=True, worldSpace=True)


def get_toe_worldspace_position(foot_joint, ball_joint, move_scaler=0.319):
    foot_pos = xformutils.get_worldspace_vector(foot_joint)
    ball_pos = xformutils.get_worldspace_vector(ball_joint)
    foot_to_ball = ball_pos - foot_pos
    foot_to_ball_distance = foot_to_ball.length()
    toe_offset = foot_to_ball_distance * move_scaler
    return xformutils.get_vector_translated_along_axis(ball_joint, toe_offset)


def duplicate_foot_joints(foot_joints: FootJoints, leg_rig_components: leg.LegRigComponents, side_prefix):
    dup_name = foot_joints.ball.nodeName()
    ik_name = ue_rig.RIG_IK_PREFIX + dup_name
    ik_ball = pm.duplicate(foot_joints.ball, parentOnly=True)[0]
    ik_ball.setParent(leg_rig_components.joints_ik.end)
    ik_ball.rename(ik_name)
    fk_ball = pm.duplicate(foot_joints.ball, parentOnly=True)[0]
    fk_ball.setParent(leg_rig_components.joints_fk.end)
    fk_name = ue_rig.RIG_FK_PREFIX + dup_name
    fk_ball.rename(fk_name)
    ik_foot_joints = FootJoints(leg_rig_components.joints_ik.end, ik_ball)
    fk_foot_joints = FootJoints(leg_rig_components.joints_fk.end, fk_ball)
    return ik_foot_joints, fk_foot_joints


def foot_constrain_rig_to_bind_skeleton(foot_rig_components: FootRigComponents):
    constraints = []
    bind_to_foot = [foot_rig_components.controller_foot, foot_rig_components.controller_heel,
                    foot_rig_components.controller_roll_ball]
    for child in bind_to_foot:
        constraints.append(rigutils.parent_constraint_shortest(foot_rig_components.joints_bind.foot, child))
    bind_to_ball = [foot_rig_components.controller_fk_ball, foot_rig_components.controller_toes,
                    foot_rig_components.controller_roll_toes]
    for child in bind_to_ball:
        constraints.append(rigutils.parent_constraint_shortest(foot_rig_components.joints_bind.ball, child))
    return constraints


def foot_constrain_bind_joints_to_rig(foot_rig_components: FootRigComponents):
    rig_constraints = []
    parent_cons, one_minus = rigutils.set_up_parent_switch(
        foot_rig_components.joints_bind.ball, [foot_rig_components.joints_ik.ball, foot_rig_components.joints_fk.ball],
        foot_rig_components.attribute_parent_blend)
    rig_constraints.extend(parent_cons)
    return rig_constraints


def foot_get_controllers_to_bake(foot_rig_components: FootRigComponents):
    controllers_to_bake = [foot_rig_components.controller_foot,
                           foot_rig_components.controller_fk_ball,
                           foot_rig_components.controller_heel,
                           foot_rig_components.controller_roll_ball,
                           foot_rig_components.controller_roll_toes,
                           foot_rig_components.controller_toes]
    return controllers_to_bake
