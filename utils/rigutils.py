import os
import json

import maya.api.OpenMaya as om
import pymel.core as pm

import flottitools.path_consts as path_consts
import flottitools.utils.skeletonutils as skelutils
import flottitools.utils.skinutils as skinutils
import flottitools.utils.stringutils as stringutils
import flottitools.utils.transformutils as xformutils

CONTROL_SHAPES_PATH = os.path.join(path_consts.FLOTTITOOLS_DIR, 'rigging', 'control_shapes')

# SIDE_LEFT = '_L_'
# SIDE_RIGHT = '_R_'
# SIDE_CENTER = '_C_'
SIDE_LEFT = '_l'
SIDE_RIGHT = '_r'
SIDE_CENTER = ''
COLOR_BLUE = 6
COLOR_RED = 13
COLOR_GREEN = 14
COLOR_YELLOW = 17
SIDE_TO_COLOR_MAP = {SIDE_LEFT: COLOR_RED,
                     SIDE_RIGHT: COLOR_BLUE,
                     SIDE_CENTER: COLOR_YELLOW}

PREFIX_JOINT_IK = 'ikj_'
PREFIX_JOINT_FK = 'fkj_'
PREFIX_JOINT_DRIVER = 'driver_'

SUFFIX_IK = 'IKJ'
SUFFIX_FK = 'FKJ'
SUFFIX_BIND = 'JNT'
SUFFIX_CONTROL = 'CTR'
SUFFIX_IK_CONTROL = 'IK_{}'.format(SUFFIX_CONTROL)
SUFFIX_FK_CONTROL = 'FK_{}'.format(SUFFIX_CONTROL)
SUFFIX_META_CONTROL = 'META_{}'.format(SUFFIX_CONTROL)
SUFFIX_AIM_CONTROL = 'AIM_{}'.format(SUFFIX_CONTROL)
SUFFIX_GROUP = 'GRP'
SUFFIX_LOCORI = 'loc_ori_GRP'
SUFFIX_AIM_TARGET = 'aim_target_GRP'
SUFFIX_AIMED = 'aimed_GRP'
SUFFIX_BUFFER = 'buffer_GRP'
SUFFIX_IK_HANDLE = 'IKH'
SUFFIX_IK_EFFECTOR = 'EFFECTOR'
SUFFIX_PARENT = 'parent_GRP'
SUFFIX_MODULE = 'module_GRP'
SUFFIX_CONTROLS = 'controls_GRP'
SUFFIX_IK_GROUP = 'ik_components_GRP'
SUFFIX_FK_GROUP = 'fk_components_GRP'
SUFFIX_DRIVER_GROUP = 'driver_components_GRP'
SUFFIX_COMP_GROUP = 'rig_components_GRP'
SUFFIX_OFFSET_GROUP = 'OFF_GRP'


def get_control_name_from_module_name(name, side, suffix=SUFFIX_CONTROL):
    new_name = '{}{}'.format(name, side)
    new_name = stringutils.append_suffix(new_name, suffix)
    return new_name


def create_ik_chain(start_joint, end_joint, name=None, **kwargs):
    default_kwargs = {'solver': "ikRPsolver"}
    default_kwargs.update(kwargs)
    name = name or start_joint.nodeName()
    new_name = stringutils.replace_suffix(name, SUFFIX_IK_HANDLE)
    eff_name = stringutils.replace_suffix(new_name, SUFFIX_IK_EFFECTOR)
    ik_handle, ik_effector = pm.ikHandle(
        name=new_name, startJoint=start_joint, endEffector=end_joint, **default_kwargs)
    ik_effector.rename(eff_name)
    return ik_handle, ik_effector


def move_node_along_pole_vector(node, ik_handle, magnitude=10):
    pole_vector = ik_handle.poleVector.get()
    pole_vector_normalized = pole_vector.normal()
    distance = pole_vector_normalized * magnitude
    pm.move(node, distance, relative=True)


def set_up_ikfk_blend_controller(anchor_joint, side, controller_name='leg_switch',
                                 ctr_loc_offset_vec3=(14, 0, 0)):
    anchor_joint_location_vec3 = anchor_joint.getTranslation(space='world')
    new_loc_vec3 = []
    for offest_amount, position in zip(ctr_loc_offset_vec3, anchor_joint_location_vec3):
        new_loc_vec3.append(offest_amount + position)
        # if offest_amount == 0:
        #     new_loc_vec3.append(position)
        # else:
    new_loc_vec3 = om.MVector(new_loc_vec3)
    switch_controller_name = get_control_name_from_module_name(controller_name, side)
    switch_ctr, switch_loc_ori = make_controller_node(switch_controller_name, side, shape_name='star8Soft',
                                                      mirror=(1, 1, 1), shape_scale=(3, 3, 3), location=new_loc_vec3)
    parent_blend_attr = make_parent_switch_attr(switch_ctr, 'ikFkBlend')
    pm.parentConstraint(anchor_joint, switch_loc_ori, maintainOffset=True)
    return switch_ctr, switch_loc_ori, parent_blend_attr


def make_parent_switch_attr(node, attr_name='parentBlend', attr_type='double', values=None, default_val=0.0):
    values = values or [0.0, 1.0]
    # addAttr -ln "parentSwitch"  -at double  -min 0 -max 1 -dv 0 thing;
    # addAttr -ln "fooBar"  -at "enum" -en "Green:Blue:"
    # setAttr -e-keyable true thing;
    if attr_type == 'double':
        min_val, max_val = values[:2]
        node.addAttr(attr_name, attributeType=attr_type, min=min_val, max=max_val, defaultValue=default_val)
    newattr = node.attr(attr_name)
    newattr.set(keyable=True)
    return newattr


def set_up_parent_switch(node, parents, switch_attr, constraint_method=None):
    def parent_constraint(parent_node, child_node):
        return pm.parentConstraint(parent_node, child_node, maintainOffset=True, weight=1)

    constraint_method = constraint_method or parent_constraint
    one_minus_node = get_or_make_one_minus_node_from_switch_attr(node, switch_attr)
    parent_cons = []
    for i, parent in enumerate(parents):
        p_con = constraint_method(parent, node)
        p_con.interpType.set(2)
        parent_cons.append(p_con)
        p_con_attr = [x for x in p_con.listAttr() if parent.nodeName() in x.name()][0]
        if i == 1:
            switch_attr.connect(p_con_attr)
        else:
            one_minus_node.output1D.connect(p_con_attr)
    return parent_cons, one_minus_node


def get_or_make_one_minus_node_from_switch_attr(node, switch_attr):
    existing_one_minus_nodes = get_one_minus_node_from_switch_attr(switch_attr)
    if existing_one_minus_nodes:
        one_minus_node = existing_one_minus_nodes[0]
    else:
        one_minus_node = pm.shadingNode('plusMinusAverage', asUtility=True, name='{}_oneMinusNode'.format(node.nodeName()))
        subtract_operation_index = 2
        one_minus_node.operation.set(subtract_operation_index)
        one_minus_node.input1D[0].set(1.0)
        switch_attr.connect(one_minus_node.input1D[1], force=True)
    return one_minus_node


def get_one_minus_node_from_switch_attr(switch_attr):
    nodes = switch_attr.outputs(type=pm.nt.PlusMinusAverage)
    oneminus_nodes = [x for x in nodes if 'oneminus' in x.nodeName().lower()]
    return oneminus_nodes


def set_up_visibility_switch(node, switch_attr, use_one_minus=False):
    if use_one_minus:
        one_minus_node = get_or_make_one_minus_node_from_switch_attr(node, switch_attr)
        one_minus_node.output1D.connect(node.visibility)
    else:
        switch_attr.connect(node.visibility)


def constrain_controller(parent_node, controller, **parent_kwargs):
    default_kwargs = {'maintainOffset': True}
    parent_kwargs.update(default_kwargs)
    parent_group = make_parent_group(controller)
    constraint_node = pm.parentConstraint(parent_node, parent_group, **parent_kwargs)
    return parent_group, constraint_node


def create_scaler_node(input_attr, input_const, output_attr, name=None, input_scaler_attr_name='', const_scaler_attr_name='', output_scaler_attr_name=''):
    name = name or '{0}_direction_scaler'.format(input_attr.node().nodeName())
    input_scaler_attr_name = input_scaler_attr_name or 'input1X'
    const_scaler_attr_name = const_scaler_attr_name or 'input2X'
    output_scaler_attr_name = output_scaler_attr_name or 'outputX'
    scaler_node = pm.shadingNode(
        'multiplyDivide', asUtility=True, name=name)
    input_attr.connect(scaler_node.attr(input_scaler_attr_name))
    scaler_node.attr(const_scaler_attr_name).set(input_const)
    scaler_node.attr(output_scaler_attr_name).connect(output_attr)
    return scaler_node


def create_magnify_node(input_attr, output_attr, name=None):
    name = name or '{0}_magnify'.format(input_attr.node().nodeName())
    magnify_node = pm.shadingNode(
        'multiplyDivide', asUtility=True, name=name)
    input_attr.connect(magnify_node.input1X)
    magnify_node.outputX.connect(output_attr)
    return magnify_node



def create_group_node(name, parent=None):
    group_node = pm.createNode('transform')
    group_node.rename(name)
    if parent:
        group_node.setParent(parent)
    return group_node


def create_offset_group(node, worldspace_location=None, worldspace_orientation=None,
                        new_suffix=SUFFIX_OFFSET_GROUP, suffix_sep_count=1):
    new_name = stringutils.replace_suffix(node.nodeName(), new_suffix, suffix_sep_count=suffix_sep_count)
    parent = node.getParent()
    offset_group = create_group_node(new_name, parent)
    if worldspace_location:
        offset_group.setTranslation(worldspace_location, space='world')
    else:
        xformutils.match_worldspace_position(offset_group, node)
    if worldspace_orientation:
        offset_group.setRotation(worldspace_orientation, space='world')
    else:
        offset_group.setRotation(node.getRotation(space='world'), space='world')
    node.setParent(offset_group)
    return offset_group


def make_parent_group(node):
    p = node.getParent()
    p_group = pm.createNode('transform')
    xformutils.match_worldspace_position_orientation(p_group, node)
    p_group.setParent(p)
    new_name = stringutils.replace_suffix(node.nodeName(), SUFFIX_PARENT)
    p_group.rename(new_name)
    node.setParent(p_group)
    return p_group


def safe_parent(parent, child):
    if child.getParent() != parent:
        child.setParent(parent)


def make_controller_node(controller_name, side, shape_name='circle', mirror=(1, 1, 1),
                         shape_translate=(0, 0, 0), shape_rotation=(90, 0, 0), shape_scale=(1, 1, 1),
                         location=(0, 0, 0), rotation=(0, 0, 0), move_cv_x=0, move_cv_y=0, move_cv_z=0):
    controller = make_shape(shape_name, controller_name)
    stuff = (1, 1, 1)
    if side == SIDE_RIGHT or side == SIDE_CENTER:
        stuff = mirror
    move_cv_x *= stuff[0]
    move_cv_y *= stuff[1]
    move_cv_z *= stuff[2]
    transform_shape(controller, shape_translate, shape_rotation, shape_scale, move_cv_x, move_cv_y, move_cv_z, mirror=stuff)
    set_color(controller, SIDE_TO_COLOR_MAP.get(side, COLOR_YELLOW))
    loc_ori_node = pm.createNode('transform')
    loc_ori_name = stringutils.replace_suffix(controller_name, SUFFIX_LOCORI)
    loc_ori_node.rename(loc_ori_name)
    controller.setParent(loc_ori_node)
    loc_ori_node.setRotation(rotation)
    xformutils.move_node_to_worldspace_position(loc_ori_node, location)
    return controller, loc_ori_node


def transform_shape(shape, translate_vector=(0, 0, 0), rotate_vector=(0, 0, 0), shape_scale=(1, 1, 1),
                    move_cv_x=0, move_cv_y=0, move_cv_z=0, mirror=(1, 1, 1)):
    shape.translate.set(translate_vector)
    pm.rotate(shape, rotate_vector)
    new_scale = shape.scale.get() * shape_scale * mirror
    shape.scale.set(new_scale)
    pm.makeIdentity(apply=True, scale=True, translate=False, rotate=True)
    shapes = shape.getShapes()

    def move_cv(amount, kwarg):
        for shapey in shapes:
            pm.move(shapey.cv, amount, relative=True, worldSpace=True, **kwarg)

    if move_cv_x:
        move_cv(move_cv_x, {'moveX': True})
    if move_cv_y:
        move_cv(move_cv_y, {'moveY': True})
    if move_cv_z:
        move_cv(move_cv_z, {'moveZ': True})


def set_color(node, index):
    shapes = [node]
    try:
        shapes = node.getShapes()
    except AttributeError:
        pass
    for shape in shapes:
        shape.overrideEnabled.set(True)
        shape.overrideColor.set(index)


def sample_all_shapes():
    for i, j in enumerate([f for f in os.listdir(CONTROL_SHAPES_PATH) if f.lower().endswith('.json')]):
        name = os.path.splitext(j)[0]
        x = make_shape(name)
        xformutils.move_node_to_worldspace_position(x, (i * 3, 0, 0))


def make_shape(shape_file_name, name=None):
    name = name or shape_file_name
    shape_path = os.path.join(CONTROL_SHAPES_PATH, '{}.json'.format(shape_file_name))
    shape_data = _load_json_data(shape_path)
    shape_transform_node = pm.createNode('transform', name=name)
    _set_shape_from_shape_data(shape_transform_node, shape_data)
    pm.select(shape_transform_node, r=True)
    return shape_transform_node


def _load_json_data(file_path):
    if os.path.isfile(file_path):
        f = open(file_path, "r")
        data = json.loads(f.read())
        f.close()
        return data
    else:
        pm.error("The file " + file_path + " doesn't exist")


def _set_shape_from_shape_data(transform_node, shape_data):
    for i, crv_shape_dict in enumerate(shape_data):
        new_transform = pm.curve(p=crv_shape_dict["points"], k=crv_shape_dict["knots"],
                                 d=crv_shape_dict["degree"], per=bool(crv_shape_dict["form"]))

        new_shape = pm.listRelatives(new_transform, s=True)[0]
        pm.parent(new_shape, transform_node, s=True, r=True)

        pm.delete(new_transform)
        pm.rename(new_shape, transform_node + "Shape" + str(i + 1).zfill(2))


def get_side_from_name(name):
    side = SIDE_LEFT
    if SIDE_RIGHT in name:
        side = SIDE_RIGHT
    elif SIDE_CENTER in name:
        side = SIDE_CENTER
    return side


def parent_constraint_shortest(parent, child, maintain_offset=True):
    constraint = pm.parentConstraint(parent, child, maintainOffset=maintain_offset)
    constraint.interpType.set(2)
    return constraint


def make_fk_controls(joints, side=None, shape_type='circle',
                     shape_rotation=(0, 0, 90), shape_scale=(8, 8, 8), shape_translation=(0, 0, 0),
                     move_cv_x=0, move_cv_z=0, mirror=(-1, -1, -1), parent=None, 
                     prefixes_to_strip=(PREFIX_JOINT_FK, PREFIX_JOINT_IK, PREFIX_JOINT_DRIVER)):
    side = side or get_side_from_name(joints[0].nodeName())
    controls = []
    loc_oris = []
    cons = []
    last = None
    for joint in joints:
        name = joint.nodeName()
        for prefix in prefixes_to_strip:
            if name.lower().startswith(prefix):
                name = name[len(prefix):]
                continue
        name = f'{name}_{SUFFIX_FK_CONTROL}'
        fk_controller, fk_loc_ori_node = create_controller_from_joint(
            joint, name=name, side=side, mirror=mirror, move_cv_x=move_cv_x, move_cv_z=move_cv_z,
            shape_rotation=shape_rotation, shape_scale=shape_scale, shape_translation=shape_translation,
            shape_type=shape_type, suffix=SUFFIX_FK_CONTROL)
        controls.append(fk_controller)
        loc_oris.append(fk_loc_ori_node)
        cons.append(pm.parentConstraint(fk_controller, joint, maintainOffset=False))
        # pm.scaleConstraint(fk_controller, joint, maintainOffset=False)
        if last:
            fk_loc_ori_node.setParent(last)
        last = fk_controller
    if parent:
        safe_parent(parent, loc_oris[0])
    return controls, loc_oris, cons


def create_controller_from_joint(joint, name='', side=None, shape_type='circle', mirror=(-1, -1, -1),
                                 move_cv_x=0, move_cv_z=0, shape_rotation=(0, 0, 90), shape_scale=(8, 8, 8),
                                 shape_translation=(0, 0, 0), suffix=SUFFIX_CONTROL):
    # name = name or stringutils.replace_suffix(joint.nodeName(), SUFFIX_CONTROL)
    if not name:
        name = joint.nodeName().split('_', 1)[1]
        name = f'{name}_{suffix}'
    loc = joint.getTranslation(space='world')
    ori = joint.getRotation(space='world')
    controller, loc_ori_node = make_controller_node(name, side, shape_name=shape_type, mirror=mirror,
                                                    shape_translate=shape_translation,
                                                    shape_rotation=shape_rotation,
                                                    shape_scale=shape_scale, location=loc, rotation=ori,
                                                    move_cv_x=move_cv_x, move_cv_z=move_cv_z)
    joint_rotation_order = joint.rotateOrder.get()
    controller.rotateOrder.set(joint_rotation_order)
    loc_ori_node.rotateOrder.set(joint_rotation_order)
    return controller, loc_ori_node


def create_controller_and_constrain_joint(joint, name='', side=None, shape_type='circle', mirror=(-1, -1, -1),
                                          move_cv_x=0, move_cv_z=0, shape_rotation=(0, 0, 90), shape_scale=(8, 8, 8),
                                          shape_translation=(0, 0, 0)):
    controller, loc_ori_node = create_controller_from_joint(joint, name=name, side=side, shape_type=shape_type,
                                                            mirror=mirror, move_cv_x=move_cv_x, move_cv_z=move_cv_z,
                                                            shape_rotation=shape_rotation, shape_scale=shape_scale,
                                                            shape_translation=shape_translation)
    constraint = parent_constraint_shortest(controller, joint, maintain_offset=True)
    return controller, loc_ori_node, constraint


def set_up_ik_rig(ik_joints, ik_parent, module_name, side):
    skelutils.orient_three_joints(*ik_joints)
    polevector_controller_name = '{0}{1}_poleVector_{2}'.format(module_name, side, SUFFIX_CONTROL)
    knee_loc = ik_joints[1].getTranslation(space='world')
    knee_pv_ctr, knee_pv_loc_ori = make_controller_node(polevector_controller_name, side, shape_name='pyramid',
                                                        mirror=(1, 1, 1),
                                                        shape_rotation=(0, 0, 0), shape_scale=(3, 3, 3),
                                                        location=knee_loc)
    # setAttr "annotationShape1.overrideDisplayType" 2
    annotation_shape = pm.annotate(knee_pv_ctr, point=knee_loc)
    annotation_shape.overrideEnabled.set(1)
    annotation_shape.overrideDisplayType.set(2)
    annotation_transform = annotation_shape.getParent()
    leg_ik_name = '{0}{1}{2}'.format(module_name, SUFFIX_IK_HANDLE, side)
    leg_ik_handle, leg_ik_effector = create_ik_chain(ik_joints[0], ik_joints[2], leg_ik_name)
    leg_ik_handle.setParent(ik_parent)

    start_mid_v = xformutils.get_worldspace_vector(ik_joints[1]) - xformutils.get_worldspace_vector(ik_joints[0])

    dir_scaler = 1
    magnitude = start_mid_v.length() * dir_scaler * 1.2
    move_node_along_pole_vector(knee_pv_loc_ori, leg_ik_handle, magnitude=magnitude)
    pole_vector = leg_ik_handle.poleVector.get()
    aim_con = pm.aimConstraint(ik_joints[1], knee_pv_ctr)
    pm.delete(aim_con)
    pm.poleVectorConstraint(knee_pv_ctr, leg_ik_handle)

    annotation_transform.setParent(knee_pv_loc_ori)
    annotation_constraint = pm.parentConstraint(ik_joints[1], annotation_transform, maintainOffset=True)
    return knee_pv_loc_ori, leg_ik_handle


def create_spline_for_joint_chain(start_joint, end_joint, name=''):
    name = name or '{}_spline'.format(start_joint.nodeName())
    # (degree + 1) curve points
    # knots = (numberOfPoints + degree - 1)
    # curve - d 3 - p - 3.721481 0 20.510586 - p 1.947096 0 25.152186 - p 13.284251 0 34.435388 - p 41.775453 0 7.151908 - p 56.607885 0 22.04396 - p 64.024101 0 29.489986 - k 0 - k 0 - k 0 - k 1 - k 2 - k 3 - k 3 - k 3;
    all_parents: list = end_joint.getAllParents()
    try:
        start_index = all_parents.index(start_joint)
    except ValueError:
        raise AssertionError('{} is not a parent of {}'.format(start_joint.nodeName(), end_joint.nodeName()))
    joint_chain = [end_joint]
    parent_slice = all_parents[:start_index+1]
    joint_chain.extend(parent_slice)
    joint_chain.reverse()
    # return joint_chain
    rigid_curve = pm.curve(degree=1, point=[xformutils.get_worldspace_vector(j) for j in joint_chain])
    smooth_curve = pm.fitBspline(constructionHistory=False)[0]
    smooth_curve.rename(name)
    pm.delete(rigid_curve)
    return smooth_curve


def convert_static_mesh_anim_to_skinned_mesh(root_mesh, start_frame=None, end_frame=None):
    start_frame = start_frame or int(pm.playbackOptions(minTime=True, q=True))
    end_frame = end_frame or int(pm.playbackOptions(maxTime=True, q=True))
    pm.currentTime(start_frame)
    meshes, joints = _recurse_children(root_mesh)
    constraints = [pm.parentConstraint(m, j, maintainOffset=False) for m, j in zip(meshes, joints)]
    bake_animation_to_nodes(joints, start_frame=start_frame, end_frame=end_frame)
    pm.delete(constraints)
    vert_indices_to_infs_wts = {}
    start_vert_number = 0
    for mesh, joint in zip(meshes, joints):
        vert_count = len(mesh.vtx)
        for vert_index in range(start_vert_number, start_vert_number+vert_count):
            vert_indices_to_infs_wts[vert_index] = {joint: 1.0}
        start_vert_number = vert_count
    new_mesh = combine_meshes(meshes)
    skin_cluster = skinutils.bind_mesh_to_joints(new_mesh, joints)
    skinutils.set_weights(vert_indices_to_infs_wts, skin_cluster=skin_cluster)
    return new_mesh, joints, skin_cluster


def _recurse_children(static_mesh, meshes=None,joints=None, parent=None):
    joints = joints or []
    meshes = meshes or []
    joint = pm.joint()
    joint.rename('{}_joint'.format(static_mesh))
    joint.setParent(parent)
    xformutils.match_worldspace_position_orientation(joint, static_mesh)
    joints.append(joint)
    meshes.append(static_mesh)
    children_meshes = static_mesh.getChildren(type=pm.nt.Transform)
    # if children_meshes:
    for child_mesh in children_meshes:
        _recurse_children(child_mesh, meshes=meshes, joints=joints, parent=joint)
    return meshes, joints


def bake_animation_to_nodes(nodes, start_frame=None, end_frame=None):
    start_frame = start_frame or int(pm.playbackOptions(minTime=True, q=True))
    end_frame = end_frame or int(pm.playbackOptions(maxTime=True, q=True))
    pm.bakeResults(nodes, simulation=True, time=str(start_frame) + ":" + str(end_frame), sampleBy=1,
                   oversamplingRate=1, disableImplicitControl=True, preserveOutsideKeys=False,
                   sparseAnimCurveBake=False, removeBakedAttributeFromLayer=True, removeBakedAnimFromLayer=False,
                   bakeOnOverrideLayer=False, minimizeRotation=False, controlPoints=False, shape=True)


def combine_meshes(meshes, name=''):
    # polyUnite - ch 1 - mergeUVSets 1 - centerPivot - name
    name = name or meshes[0].nodeName()
    new_mesh = pm.polyUnite(meshes, ch=False, mergeUVSets=True, centerPivot=False)[0]
    new_mesh.rename(name)
    return new_mesh


def select_all_controllers():
    controllers = get_all_controllers()
    pm.select(controllers, r=True)
    return controllers


def get_all_controllers():
    all_transforms = pm.ls(type=pm.nt.Transform)
    controller_transform_nodes = [n for n in all_transforms if n.nodeName().lower().endswith('_ctr') or n.nodeName().lower().endswith('_ctrl')]
    set_members = []
    for selection_set in pm.ls(type=pm.nt.ObjectSet):
        # pm.ls(type=pm.nt.ObjectSet) returns a bunch of ShaderEngine nodes because they inherit from ObjectSet
        if not selection_set.type() == 'objectSet':
            continue
        sel_set_name = selection_set.nodeName().lower()
        if 'controllers' not in sel_set_name or 'ctrs' not in sel_set_name:
            continue
        set_members.extend(selection_set.members(flatten=True))
    set_members = set(set_members)
    controller_transform_nodes = set(controller_transform_nodes)
    controllers = list(set_members.union(controller_transform_nodes))
    controllers.sort()
    return controllers


def get_all_curves():
    all_curves = pm.ls(type=pm.nt.NurbsCurve)
    return list(set([c.getParent() for c in all_curves]))