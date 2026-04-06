from typing import NamedTuple

import pymel.core as pm

import flottitools.utils.rigutils as rigutils
import flottitools.utils.skeletonutils as skelutils
import flottitools.utils.transformutils as xformutils


SKIP_SENTINEL = object()

RIG_IK_PREFIX = 'ikj_'
RIG_FK_PREFIX = 'fkj_'
RIG_DRIVER_PREFIX = 'driver_'

SIDE_SUFFIX_LEFT = '_l'
SIDE_SUFFIX_RIGHT = '_r'
COLOR_RED = 13
COLOR_GREEN = 14
COLOR_YELLOW = 17
SIDE_TO_COLOR_MAP = {SIDE_SUFFIX_LEFT: COLOR_RED,
                     SIDE_SUFFIX_RIGHT: COLOR_GREEN}

MODULE_TYPE_THUMB_FINGER = 'thumb'
MODULE_TYPE_INDEX_FINGER = 'index'
MODULE_TYPE_MIDDLE_FINGER = 'middle'
MODULE_TYPE_RING_FINGER = 'ring'
MODULE_TYPE_PINKY_FINGER = 'pinky'
MODULE_TYPE_DEFAULT_FINGER = 'finger'

SHAPE_CIRCLE = 'circle'
SHAPE_SPHERE = 'sphere'
SHAPE_HALF_CIRCLE = 'halfCircle'
SHAPE_HALF_CIRCLE_QUA_DIR = 'halfCircleQuaDir'
SHAPE_CIRCLE_DIRECTIONAL = 'circleDirectional'
SHAPE_FOUR_DIRECTIONAL = 'rootMotion'

JOINT_NAME_ROOT = 'root'
JOINT_NAME_PELVIS = 'pelvis'
JOINT_NAME_SPINE01 = 'spine_01'
JOINT_NAME_SPINE02 = 'spine_02'
JOINT_NAME_SPINE03 = 'spine_03'
JOINT_NAME_NECK01 = 'neck_01'
JOINT_NAME_HEAD = 'head'
JOINT_NAME_CLAVICLE = 'clavicle'
JOINT_NAME_UPPERARM = 'upperarm'
JOINT_NAME_UPPERARMTWIST = 'upperarm_twist_01'
JOINT_NAME_LOWERARM = 'lowerarm'
JOINT_NAME_LOWERARMTWIST = 'lowerarm_twist_01'
JOINT_NAME_HAND = 'hand'
JOINT_NAME_INDEX = 'index'
JOINT_NAME_INDEX01 = 'index_01'
JOINT_NAME_INDEX02 = 'index_02'
JOINT_NAME_INDEX03 = 'index_03'
JOINT_NAME_MIDDLE = 'middle'
JOINT_NAME_MIDDLE01 = 'middle_01'
JOINT_NAME_MIDDLE02 = 'middle_02'
JOINT_NAME_MIDDLE03 = 'middle_03'
JOINT_NAME_RING = 'ring'
JOINT_NAME_RING01 = 'ring_01'
JOINT_NAME_RING02 = 'ring_02'
JOINT_NAME_RING03 = 'ring_03'
JOINT_NAME_PINKY = 'pinky'
JOINT_NAME_PINKY01 = 'pinky_01'
JOINT_NAME_PINKY02 = 'pinky_02'
JOINT_NAME_PINKY03 = 'pinky_03'
JOINT_NAME_THUMB = 'thumb'
JOINT_NAME_THUMB01 = 'thumb_01'
JOINT_NAME_THUMB02 = 'thumb_02'
JOINT_NAME_THUMB03 = 'thumb_03'
JOINT_NAME_THIGH = 'thigh'
JOINT_NAME_THIGHTWIST = 'thigh_twist_01'
JOINT_NAME_CALF = 'calf'
JOINT_NAME_CALFTWIST = 'calf_twist_01'
JOINT_NAME_FOOT = 'foot'
JOINT_NAME_BALL = 'ball'
JOINT_NAME_IK_FOOTROOT = 'ik_foot_root'
JOINT_NAME_IK_FOOT = 'ik_foot'
JOINT_NAME_IK_HANDROOT = 'ik_hand_root'
JOINT_NAME_IK_HANDGUN = 'ik_hand_gun'
JOINT_NAME_IK_HAND = 'ik_hand'
JOINT_NAME_IK_TOE = 'toe'
FINGER_NAMES = [JOINT_NAME_PINKY, JOINT_NAME_RING, JOINT_NAME_MIDDLE, JOINT_NAME_INDEX, JOINT_NAME_THUMB]

SKELETON_JOINT_NAMES = [JOINT_NAME_ROOT,
                        JOINT_NAME_PELVIS,
                        JOINT_NAME_SPINE01,
                        JOINT_NAME_SPINE02,
                        JOINT_NAME_SPINE03,
                        JOINT_NAME_NECK01,
                        JOINT_NAME_HEAD,
                        JOINT_NAME_CLAVICLE,
                        JOINT_NAME_UPPERARM,
                        JOINT_NAME_UPPERARMTWIST,
                        JOINT_NAME_LOWERARM,
                        JOINT_NAME_LOWERARMTWIST,
                        JOINT_NAME_HAND,
                        JOINT_NAME_INDEX01,
                        JOINT_NAME_INDEX02,
                        JOINT_NAME_INDEX03,
                        JOINT_NAME_MIDDLE01,
                        JOINT_NAME_MIDDLE02,
                        JOINT_NAME_MIDDLE03,
                        JOINT_NAME_RING01,
                        JOINT_NAME_RING02,
                        JOINT_NAME_RING03,
                        JOINT_NAME_PINKY01,
                        JOINT_NAME_PINKY02,
                        JOINT_NAME_PINKY03,
                        JOINT_NAME_THUMB01,
                        JOINT_NAME_THUMB02,
                        JOINT_NAME_THUMB03,
                        JOINT_NAME_THIGH,
                        JOINT_NAME_THIGHTWIST,
                        JOINT_NAME_CALF,
                        JOINT_NAME_CALFTWIST,
                        JOINT_NAME_FOOT,
                        JOINT_NAME_IK_FOOTROOT,
                        JOINT_NAME_IK_FOOT,
                        JOINT_NAME_IK_HANDROOT,
                        JOINT_NAME_IK_HANDGUN,
                        JOINT_NAME_IK_HAND]


class RigModule(object):
    side_suffix = ''
    bind_joints = None
    rig_components = None
    rig_to_bind_constraints = []
    bind_to_rig_constraints = []
    controllers_to_bake = []
    pole_vector_to_transforms = {}
    parent_node = None
    module_name = ''

    def __init__(self, side_suffix, module_name='', parent_node=None):
        self.side_suffix = side_suffix
        if self.module_name:
            self.module_name = module_name
        self.parent_node = parent_node
        self.get_joints_from_scene()

    def get_joints_from_scene(self):
        raise NotImplementedError

    def build_rig(self):
        raise NotImplementedError

    def constrain_rig_to_bind_joints(self):
        raise NotImplementedError

    def constrain_bind_joints_to_rig(self):
        raise NotImplementedError

    def get_controllers_to_bake(self):
        raise NotImplementedError

    def get_pole_vector_to_transforms(self):
        raise NotImplementedError

    def get_bind_joints_in_rig(self):
        raise NotImplementedError

    def bake_animation_to_rig(self):
        start_frame = int(pm.playbackOptions(minTime=True, q=True))
        end_frame = int(pm.playbackOptions(maxTime=True, q=True))
        controllers_to_bake = self.get_controllers_to_bake()
        pv_to_transforms = self.get_pole_vector_to_transforms()
        bake_animation_to_nodes(controllers_to_bake, start_frame, end_frame)
        key_pv_every_frame(pv_to_transforms, start_frame, end_frame)
        pm.delete(self.rig_to_bind_constraints)

    def bake_animation_to_bind_joints(self):
        bind_joints = self.get_bind_joints_in_rig()
        bake_animation_to_nodes(bind_joints)

    def tear_down(self):
        raise NotImplementedError


def get_joint_by_name(joint_name, side_suffix=None):
    name = '::{0}'.format(joint_name)
    if side_suffix:
        name += side_suffix
    return pm.ls(name, type=pm.nt.Joint)[0]


def bake_animation_to_nodes(nodes, start_frame=None, end_frame=None):
    start_frame = start_frame or int(pm.playbackOptions(minTime=True, q=True))
    end_frame = end_frame or int(pm.playbackOptions(maxTime=True, q=True))
    pm.bakeResults(nodes, simulation=True, time=str(start_frame) + ":" + str(end_frame), sampleBy=1,
                   oversamplingRate=1, disableImplicitControl=True, preserveOutsideKeys=False,
                   sparseAnimCurveBake=False, removeBakedAttributeFromLayer=True, removeBakedAnimFromLayer=False,
                   bakeOnOverrideLayer=False, minimizeRotation=False, controlPoints=False, shape=True)


def key_pv_every_frame(pv_to_transforms, start_frame, end_frame):
    pm.setKeyframe(list(pv_to_transforms.keys()), at='translate')
    for i in range(start_frame, end_frame+1):
        pm.currentTime(i)
        for pvc, fkc in pv_to_transforms.items():
            pv_loc = get_pv_controller_position(*fkc)
            pvc.setTranslation(pv_loc, space='world')
            pm.setKeyframe(pvc, at='translate')


def get_pv_controller_position(start_joint, mid_joint, end_joint, scalar=40.0):
    start_pos = xformutils.get_worldspace_vector(start_joint)
    mid_pos = xformutils.get_worldspace_vector(mid_joint)
    end_pos = xformutils.get_worldspace_vector(end_joint)
    start_mid = mid_pos - start_pos
    mid_end = end_pos - mid_pos
    start_end = end_pos - start_pos
    cross1 = start_mid ^ mid_end
    new_pv_vector = start_end ^ cross1
    new_pv_vector.normalize()
    new_pv_pos = (new_pv_vector * scalar) + mid_pos
    return new_pv_pos


def get_side_from_name(name):
    side_suffix = ''
    if name.lower().endswith(SIDE_SUFFIX_RIGHT):
        side_suffix = SIDE_SUFFIX_RIGHT
    elif name.lower().endswith(SIDE_SUFFIX_LEFT):
        side_suffix = SIDE_SUFFIX_LEFT
    return side_suffix


def setup_module_groups(module_name, side, module_group=None, controls_group=None,
                        components_group=None, ik_parent=None, fk_parent=None):
    module_group = _setup_module_group_node(module_name, side, rigutils.SUFFIX_MODULE, module_group)
    controls_group = _setup_module_group_node(module_name, side, rigutils.SUFFIX_CONTROLS, controls_group, module_group)
    components_group = _setup_module_group_node(module_name, side, rigutils.SUFFIX_COMP_GROUP, components_group, module_group)
    components_group.visibility.set(0)
    ik_parent = _setup_module_group_node(module_name, side, rigutils.SUFFIX_IK_GROUP, ik_parent, components_group)
    fk_parent = _setup_module_group_node(module_name, side, rigutils.SUFFIX_FK_GROUP, fk_parent, components_group)
    return module_group, controls_group, components_group, ik_parent, fk_parent


def _setup_module_group_node(module_name, side, suffix, group_node, parent=None):
    if group_node is SKIP_SENTINEL:
        return
    group_node = group_node or rigutils.create_group_node('{}{}_{}'.format(module_name, side, suffix))
    if parent:
        rigutils.safe_parent(parent, group_node)
    return group_node


class LimbJoints(NamedTuple):
    start: pm.nt.Joint
    upper_twist: pm.nt.Joint
    middle: pm.nt.Joint
    lower_twist: pm.nt.Joint
    end: pm.nt.Joint


class LimbJointsSimple(NamedTuple):
    start: pm.nt.Joint
    middle: pm.nt.Joint
    end: pm.nt.Joint


def rig_limb(bind_joints: LimbJoints, fk_joints: LimbJoints, ik_joints: LimbJoints, controls_group,
             ik_parent, fk_parent, module_name, side, ik_ctr_start_name='shoulder', ik_ctr_end_name='hand'):
    ik_chain_joints = [ik_joints.start, ik_joints.middle, ik_joints.end]
    ik_twist_joints = [ik_joints.upper_twist, ik_joints.lower_twist]
    pm.parent(ik_twist_joints, world=True)
    pv_loc_ori, ik_handle = rigutils.set_up_ik_rig(ik_chain_joints, ik_parent, module_name, side)
    for ik_twist_j, ik_twist_p in zip(ik_twist_joints, [ik_joints.start, ik_joints.middle]):
        ik_twist_j.setParent(ik_twist_p)
        # ik_twist_j.translate.set((0, 0, 0))
        # ik_twist_j.rotate.set((0, 0, 0))
        # ik_twist_j.jointOrient.set((0, 0, 0))
    pole_vector_ctr = pv_loc_ori.getChildren()[0]
    pv_loc_ori.setParent(controls_group)
    ik_handle.setParent(ik_parent)

    ik_shoulder_controller_name = rigutils.get_control_name_from_module_name(ik_ctr_start_name, side)
    shoulder_loc = ik_joints.start.getTranslation(space='world')
    shoulder_ori = ik_joints.start.getRotation(space='world')
    ik_start_ctr, ik_start_loc_ori = rigutils.make_controller_node(
        ik_shoulder_controller_name, side, shape_name='cube', mirror=(-1, -1, -1),
        shape_rotation=(0, 0, 0), shape_scale=(3, 3, 3), location=shoulder_loc, rotation=shoulder_ori)
    ik_start_loc_ori.setParent(controls_group)
    pm.parentConstraint(ik_start_ctr, ik_joints.start, maintainOffset=True)
    # fk_chain_joints = [fk_joints.clavicle, fk_joints_struct.upperarm, fk_joints_struct.lowerarm, fk_joints_struct.hand]
    fk_chain_joints = [fk_joints.start, fk_joints.middle, fk_joints.end]
    fk_controls, fk_loc_oris, cons = rigutils.make_fk_controls(fk_chain_joints, side)
    fk_loc_oris[0].setParent(fk_parent)
    # pm.parentConstraint(fk_controls[0], ik_shoulder_loc_ori, maintainOffset=True)

    ik_foot_controller_name = rigutils.get_control_name_from_module_name(ik_ctr_end_name, side)
    foot_loc = ik_joints.end.getTranslation(space='world')
    foot_ori = ik_joints.end.getRotation(space='world')
    ik_end_ctr, ik_end_loc_ori = rigutils.make_controller_node(
        ik_foot_controller_name, side, shape_name='cube', mirror=(-1, -1, -1),
        shape_rotation=(0, 0, 0), shape_scale=(3, 3, 3), location=foot_loc, rotation=foot_ori)
    ik_end_loc_ori.setParent(controls_group)
    pm.parentConstraint(ik_end_ctr, ik_handle, maintainOffset=True)
    pm.orientConstraint(ik_end_ctr, ik_joints.end, maintainOffset=True)

    def orient_x_constraint(parent_node, child_node):
        return pm.orientConstraint(parent_node, child_node, skip=['y', 'z'], weight=1.0, maintainOffset=True)

    def parent_constraint(parent_node, child_node):
        return pm.parentConstraint(parent_node, child_node, skipRotate=['x'], weight=1.0, maintainOffset=True)

    def set_up_twist_controller(twist_joint, ik_child, ik_parents, fk_child, fk_parents):
        twist_control, twist_loc_ori, twist_cons = rigutils.make_fk_controls(
            [twist_joint], side, shape_type=SHAPE_CIRCLE_DIRECTIONAL, shape_scale=(6, 6, 6))
        pm.delete(twist_cons)
        twist_control = twist_control[0]
        twist_loc_ori = twist_loc_ori[0]
        twist_loc_ori.setParent(controls_group)
        twist_strength_attr = rigutils.make_parent_switch_attr(twist_control, 'twistStrength')
        ik_cons, _ = rigutils.set_up_parent_switch(ik_child,
                                      ik_parents, twist_strength_attr,
                                      constraint_method=orient_x_constraint)
        fk_cons, _ = rigutils.set_up_parent_switch(fk_child,
                                      fk_parents, twist_strength_attr,
                                      constraint_method=orient_x_constraint)
        # [c.interpType.set(1) for c in ik_cons]
        # [c.interpType.set(1) for c in fk_cons]
        # pm.parentConstraint(ik_parents[0], ik_child, skipRotate=['x'], weight=1.0, maintainOffset=True)
        # pm.parentConstraint(fk_parents[0], fk_child, skipRotate=['x'], weight=1.0, maintainOffset=True)
        twist_strength_attr.set(0.6)
        return twist_control

    lower_twist_ctr = set_up_twist_controller(bind_joints.lower_twist,
                                                  ik_joints.lower_twist,
                                                  (bind_joints.middle, bind_joints.end),
                                                  fk_joints.lower_twist,
                                                  (bind_joints.middle, bind_joints.end))
    upper_twist_ctr = set_up_twist_controller(bind_joints.upper_twist,
                                                  ik_joints.upper_twist,
                                                  (bind_joints.start, bind_joints.middle),
                                                  fk_joints.upper_twist,
                                                  (bind_joints.start, bind_joints.middle))
    switch_control_name = '{0}_{1}_{2}_{3}'.format(module_name, 'switch', rigutils.SUFFIX_CONTROL, side)
    switch_ctr, switch_loc_ori, parent_blend_attr = rigutils.set_up_ikfk_blend_controller(
        bind_joints.end, side, switch_control_name)
    switch_loc_ori.setParent(controls_group)
    rigutils.set_up_visibility_switch(ik_end_loc_ori, parent_blend_attr, use_one_minus=True)
    rigutils.set_up_visibility_switch(fk_loc_oris[0], parent_blend_attr)
    rigutils.set_up_visibility_switch(pv_loc_ori, parent_blend_attr, use_one_minus=True)

    rigutils.set_up_visibility_switch(ik_start_loc_ori, parent_blend_attr, use_one_minus=True)
    return (fk_controls, ik_start_loc_ori, ik_start_ctr, ik_end_ctr, pole_vector_ctr, ik_handle,
            upper_twist_ctr, lower_twist_ctr, switch_ctr, parent_blend_attr)


def rig_limb_no_twist_joints(bind_joints, fk_joints, ik_joints, controls_group,
                             ik_parent, fk_parent, module_name, side, stuff=(0, 0, 50)):
    ik_chain_joints = [ik_joints[0], ik_joints[1], ik_joints[2]]
    pv_loc_ori, ik_handle = rigutils.set_up_ik_rig(ik_chain_joints, ik_parent, module_name, side)
    pole_vector_ctr = pv_loc_ori.getChildren()[0]
    pv_loc_ori.setParent(controls_group)
    rigutils.safe_parent(ik_parent, ik_handle)
    # ik_handle.setParent(ik_parent)

    ik_shoulder_controller_name = rigutils.get_control_name_from_module_name('shoulder', side)
    shoulder_loc = ik_joints[0].getTranslation(space='world')
    shoulder_ori = ik_joints[0].getRotation(space='world')
    ik_start_ctr, ik_start_loc_ori = rigutils.make_controller_node(
        ik_shoulder_controller_name, side, shape_name='cube', mirror=(-1, -1, -1),
        shape_rotation=(0, 0, 0), shape_scale=(3, 3, 3), location=shoulder_loc, rotation=shoulder_ori)
    ik_start_loc_ori.setParent(controls_group)
    pm.parentConstraint(ik_start_ctr, ik_joints[0], maintainOffset=True)

    ik_foot_controller_name = rigutils.get_control_name_from_module_name('foot', side)
    foot_loc = ik_joints[2].getTranslation(space='world')
    foot_ori = ik_joints[2].getRotation(space='world')
    ik_end_ctr, ik_end_loc_ori = rigutils.make_controller_node(
        ik_foot_controller_name, side, shape_name='cube', mirror=(-1, -1, -1),
        shape_rotation=(0, 0, 0), shape_scale=(3, 3, 3), location=foot_loc, rotation=foot_ori)
    ik_end_loc_ori.setParent(controls_group)
    pm.parentConstraint(ik_end_ctr, ik_handle, maintainOffset=True)
    # fk_chain_joints = [fk_joints.clavicle, fk_joints_struct.upperarm, fk_joints_struct.lowerarm, fk_joints_struct.hand]
    fk_chain_joints = [fk_joints[0], fk_joints[1], fk_joints[2]]
    fk_controls, fk_loc_oris, cons = rigutils.make_fk_controls(fk_chain_joints, side)
    fk_loc_oris[0].setParent(fk_parent)
    # pm.parentConstraint(fk_controls[0], ik_shoulder_loc_ori, maintainOffset=True)

    switch_control_name = '{0}_{1}_{2}_{3}'.format(module_name, 'switch', rigutils.SUFFIX_CONTROL, side)
    switch_ctr, switch_loc_ori, parent_blend_attr = rigutils.set_up_ikfk_blend_controller(
        bind_joints[2], side, switch_control_name, ctr_loc_offset_vec3=stuff)
    switch_loc_ori.setParent(controls_group)
    rigutils.set_up_visibility_switch(fk_loc_oris[0], parent_blend_attr)
    rigutils.set_up_visibility_switch(pv_loc_ori, parent_blend_attr, use_one_minus=True)
    rigutils.set_up_visibility_switch(ik_end_loc_ori, parent_blend_attr, use_one_minus=True)

    rigutils.set_up_visibility_switch(ik_start_loc_ori, parent_blend_attr, use_one_minus=True)
    return (fk_controls, ik_start_loc_ori, ik_start_ctr, ik_end_ctr, pole_vector_ctr, ik_handle,
            switch_ctr, parent_blend_attr)


def do_root_motion_stuff():
    names = [JOINT_NAME_ROOT, JOINT_NAME_PELVIS]
    # joints = [get_joint_by_name(j_name) for j_name in names]
    joints = _get_root_joint_things(names=names)
    locators = [pm.spaceLocator(name='{}_locator'.format(j.nodeName())) for j in joints]
    constraints = [pm.parentConstraint(j, l, maintainOffset=False) for j, l in zip(joints, locators)]
    bake_animation_to_nodes(locators)
    pm.delete(constraints)
    constraints = []
    for locator, joint in zip(locators, joints):
        constraints.append(pm.parentConstraint(locator, joint, maintainOffset=False))
    return locators, joints, constraints


def do_root_motion_stuff2(names=None):
    names = names or [JOINT_NAME_ROOT]
    # joints = [get_joint_by_name(j_name) for j_name in names]
    joints = _get_root_joint_things(names=names)
    locators = [pm.spaceLocator(name='{}_locator'.format(j.nodeName())) for j in joints]
    constraints = [pm.parentConstraint(j, l, maintainOffset=False) for j, l in zip(joints, locators)]
    bake_animation_to_nodes(locators)
    pm.delete(constraints)
    constraints = []
    for locator, joint in zip(locators, joints):
        constraints.append(pm.parentConstraint(locator, joint, maintainOffset=False))
    fix_root_bs2(locators[0])
    # locs, js, cs = do_root_motion_stuff2(names=[JOINT_NAME_PELVIS])
    # locators.extend(locs)
    # joints.extend(js)
    # constraints.extend(cs)
    return locators, joints, constraints


def bake_root_locators(locators=None, joints=None):
    joints = joints or _get_root_joint_things()
    locators = locators or [pm.ls('{}_locator'.format(j.nodeName()), type=pm.nt.Transform)[0] for j in joints]
    bake_animation_to_nodes(joints)
    pm.delete(locators)
    return joints


def _get_root_joint_things(names=None):
    names = names or [JOINT_NAME_ROOT, JOINT_NAME_PELVIS, JOINT_NAME_IK_FOOTROOT, JOINT_NAME_IK_HANDROOT]
    joints = [get_joint_by_name(j_name) for j_name in names]
    return joints


def fix_root_bs():
    start_frame = int(pm.playbackOptions(minTime=True, q=True))
    end_frame = int(pm.playbackOptions(maxTime=True, q=True))
    root_locator = pm.ls('root_locator', type=pm.nt.Transform)[0]
    root_locator.rotateX.disconnect()
    root_locator.rotateY.disconnect()
    root_locator.rotateZ.disconnect()
    root_locator.rotate.set((-90, 0, 0))
    pm.currentTime(start_frame)
    pm.setKeyframe(root_locator, at='rotate')
    pm.currentTime(end_frame)
    pm.setKeyframe(root_locator, at='rotate')

def fix_root_bs2(locator):
    start_frame = int(pm.playbackOptions(minTime=True, q=True))
    end_frame = int(pm.playbackOptions(maxTime=True, q=True))
    # root_locator = pm.ls('root_locator', type=pm.nt.Transform)[0]
    root_locator = locator
    root_locator.rotateX.disconnect()
    root_locator.rotateY.disconnect()
    root_locator.rotateZ.disconnect()
    root_locator.translateX.disconnect()
    root_locator.translateY.disconnect()
    root_locator.translateZ.disconnect()
    root_locator.rotate.set((0, 0, 0))
    root_locator.translate.set((0, 0, 0))
    pm.currentTime(start_frame)
    pm.setKeyframe(root_locator, at=['rotate', 'translate'])
    pm.currentTime(end_frame)
    pm.setKeyframe(root_locator, at=['rotate', 'translate'])


def set_time_slider():
    root_joint = get_joint_by_name('root')
    skel = skelutils.get_hierarchy_from_root(root_joint, joints_only=True)
    start_frame = 0
    end_frame = int(max(pm.keyframe(skel, q=True)))
    pm.playbackOptions(animationStartTime=start_frame, animationEndTime=end_frame, min=start_frame, max=end_frame)
    return start_frame, end_frame

