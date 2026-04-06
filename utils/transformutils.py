import maya.api.OpenMaya as om
import pymel.core as pm
import maya.cmds as cmds
import math


def get_worldspace_vector(pynode):
    try:
        return om.MVector(pynode.getTranslation(space='world'))
    except AttributeError:
        return om.MVector(pm.pointPosition(pynode))
    # try:
    #     return om.MVector(pm.xform(pynode, q=True, worldSpace=True, rotatePivot=True))
    #     # return om.MVector(pynode.getTranslation(space='world'))
    # except AttributeError:
    #     return om.MVector(pm.pointPosition(pynode))
    # return om.MVector(pm.xform(pynode, q=True, worldSpace=True, rotatePivot=True))


def get_worldspace_orientation_quaternion(node):
    return node.getRotation(quaternion=True, space='world')


def get_worldspace_euler_rotation(transform_node):
    return pm.xform(transform_node, rotation=True, worldSpace=True, q=True)


def match_worldspace_position(dag_node, target_dag_node):
    target_vector = get_worldspace_vector(target_dag_node)
    move_node_to_worldspace_position(dag_node, target_vector)


def match_worldspace_position_orientation(transform_node, destination_node):
    # transform_node.setTranslation(destination_node.getTranslation(space='world'), space='world')
    # transform_node.setRotation(destination_node.getRotation(space='world'), space='world')
    transform_node.setTranslation(get_worldspace_vector(destination_node), space='world')
    transform_node.setRotation(destination_node.getRotation(space='world'), space='world')


def get_quaternion_aimed_at_vector(start_vector, target_vector, aim_axis=om.MVector().kXaxisVector):
    aim_vector = target_vector - start_vector
    aim_vector.normalize()
    orientation_quaternion = om.MQuaternion(aim_axis, aim_vector)
    return orientation_quaternion


def aim_node_transform_matrix(node, aim_target_vec, up_target_vec):
    node_vec = get_worldspace_vector(node)
    aim_vec = aim_target_vec - node_vec
    side_vec = get_perpendicular_vector_from_three_points(node_vec, aim_target_vec, up_target_vec)
    side_vec *= -1
    up_vec = aim_vec ^ side_vec
    matrix = pm.xform(node, matrix=True, worldSpace=True, q=True)
    transform_matrix = [aim_vec[0], aim_vec[1], aim_vec[2], matrix[3],
                        up_vec[0], up_vec[1], up_vec[2], matrix[7],
                        side_vec[0], side_vec[1], side_vec[2], matrix[11],
                        matrix[12], matrix[13], matrix[14], matrix[15]]
    pm.xform(node, matrix=transform_matrix, worldSpace=True)
    return transform_matrix


def get_aimed_matrix(node, aim_target_vec, up_target_vec):
    start_vec = get_worldspace_vector(node)
    aim_vec = aim_target_vec - start_vec
    side_vec = get_perpendicular_vector_from_three_points(start_vec, aim_target_vec, up_target_vec)
    side_vec *= -1
    up_vec = aim_vec ^ side_vec
    transform_matrix = [aim_vec[0], aim_vec[1], aim_vec[2], 0.0,
                        up_vec[0], up_vec[1], up_vec[2], 0.0,
                        side_vec[0], side_vec[1], side_vec[2], 0.0,
                        start_vec[0], start_vec[1], start_vec[2], 1.0]
    pm.xform(node, matrix=transform_matrix, worldSpace=True)
    return transform_matrix


def aim_node_at_node2(aimed_node, target_node, up_target_vec=om.MVector().kYaxisVector, mirror=False,
                     aim_axis_index=0, up_axis_index=1):
    aimed_vec = get_worldspace_vector(aimed_node)
    target_vec = get_worldspace_vector(target_node)
    aimed_quaternion = get_aimed_quaternion(aimed_vec, target_vec, up_target_vec, mirror=mirror,
                                            aim_axis_index=aim_axis_index, up_axis_index=up_axis_index)
    aimed_node.setRotation(aimed_quaternion, space='world')
    return aimed_node


def aim_node_at_node(aimed_node, target_node, up_target_vec=om.MVector().kYaxisVector, mirror=False,
                     aim_axis_index=0, up_axis_index=1):
    initial_rotate_order = aimed_node.rotateOrder.get()
    aimed_node.rotateOrder.set(0)
    start_vec = get_worldspace_vector(aimed_node)
    aim_target_vec = get_worldspace_vector(target_node)
    # aimed_quaternion = get_aimed_quaternion(aimed_vec, target_vec, up_target_vec, mirror=mirror,
    #                                         aim_axis_index=aim_axis_index, up_axis_index=up_axis_index)
    # aimed_node.setRotation(aimed_quaternion, space='world')
    side_axis_index = 2
    axis_indicies = [aim_axis_index, up_axis_index]
    for i in range(3):
        if i not in axis_indicies:
            side_axis_index = i
    aim_vec = aim_target_vec - start_vec
    side_vec = get_perpendicular_vector_from_three_points(start_vec, aim_target_vec, up_target_vec)
    up_vec = up_target_vec
    if mirror:
        aim_vec *= -1
        side_vec *= -1
    index_to_axis_vector = {0: (1.0, 0, 0),
            1: (0, 1.0, 0),
            2: (0, 0, 1.0)}
    aim_axis_vector = index_to_axis_vector[aim_axis_index]
    if aim_vec[0] < 0.0:
        aim_axis_vector = (-1.0, 0, 0)
    con = pm.aimConstraint(target_node, aimed_node, aimVector=aim_axis_vector, maintainOffset=False, upVector=index_to_axis_vector[up_axis_index], worldUpVector=up_vec)
    pm.delete(con)
    aimed_node.rotateOrder.set(initial_rotate_order)
    return aimed_node


def get_aimed_quaternion(start_vec, aim_target_vec, up_target_vec, mirror=False, aim_axis_index=0, up_axis_index=1):
    side_axis_index = 2
    axis_indicies = [aim_axis_index, up_axis_index]
    for i in range(3):
        if i not in axis_indicies:
            side_axis_index = i
    aim_vec = aim_target_vec - start_vec
    side_vec = get_perpendicular_vector_from_three_points(start_vec, aim_target_vec, up_target_vec)
    up_vec = up_target_vec
    if mirror:
        aim_vec *= -1
        side_vec *= -1
    aim_vec.normalize()
    up_vec.normalize()
    side_vec.normalize()
    aim_matrix_component = [aim_vec[0], aim_vec[1], aim_vec[2], 0.0]
    up_matrix_component = [up_vec[0], up_vec[1], up_vec[2], 0.0]
    side_matrix_component = [side_vec[0], side_vec[1], side_vec[2], 0.0]
    scale_matrix_component = [0.0, 0.0, 0.0, 1.0]
    matrix_index_to_component = {aim_axis_index: aim_matrix_component,
                                 up_axis_index: up_matrix_component,
                                 side_axis_index: side_matrix_component,
                                 3: scale_matrix_component}
    aimed_transform_matrix = []
    for i in range(4):
        aimed_transform_matrix.extend(matrix_index_to_component[i])
    aimed_transform_matrix = om.MMatrix(aimed_transform_matrix)
    aimed_transform_matrix = om.MTransformationMatrix(aimed_transform_matrix)
    aimed_quaternion = aimed_transform_matrix.rotation(asQuaternion=True)
    return aimed_quaternion


def get_perpendicular_vector_from_three_points(vec1, vec2, vec3):
    v1 = vec1 - vec2
    v2 = vec1 - vec3
    cross_product = v1 ^ v2
    # perpendicular_vector = cross_product.normalize()
    # return perpendicular_vector
    return cross_product


def nodes_almost_match_worldspace_position(dag1, dag2, tolerance=0.001):
    ws_pos1 = get_worldspace_vector(dag1)
    ws_pos2 = get_worldspace_vector(dag2)
    return positions_almost_match(ws_pos1, ws_pos2, tolerance)


def node_almost_matches_worldspace_position(node, position_vector, tolerance=0.001):
    node_position = get_worldspace_vector(node)
    return positions_almost_match(node_position, position_vector, tolerance)


def positions_almost_match(position_vec1, position_vec2, tolerance=0.001):
    distance = position_vec1 - position_vec2
    return abs(distance.length()) < tolerance


def move_node_to_worldspace_position(dag_node, worldspace_vector):
    pm.move(dag_node, worldspace_vector, absolute=True)


def get_axis_as_worldspace_vector(transform_node, axis=om.MVector.kXaxisVector):
    quat_ws = om.MQuaternion(transform_node.getRotation(quaternion=True, space='world'))
    matrix = quat_ws.asMatrix()

    vector = (axis * matrix).normal()
    return vector


def get_axis_as_worldspace_vector2(transform_node, axis='x'):
    matrix = pm.xform(transform_node, matrix=True, worldSpace=True, q=True)
    axes = {'x': matrix[:3],
            'y': matrix[4:7],
            'z': matrix[8:11]}
    return om.MVector(axes[axis])


def get_vector_translated_along_axis(transform_node, translate_amount, axis='x', start_vector=None):
    try:
        axis = om.MVector(axis)
    except ValueError:
        axes_dict = {'x': om.MVector.kXaxisVector,
                     'y': om.MVector.kYaxisVector,
                     'z': om.MVector.kZaxisVector}
        axis = axes_dict.get(axis.lower())
    if not axis:
        raise ValueError('Invalid axis provided. Supported arguments: "x", "y", "z" or a vector.')
    start_vector = start_vector or get_worldspace_vector(transform_node)
    local_axis = get_axis_as_worldspace_vector(transform_node, axis)
    translate_on_axis_amount = local_axis * translate_amount
    new_worldspace_pos = start_vector + translate_on_axis_amount
    return new_worldspace_pos


def get_distance_scalers(source_vector, target_vectors):
    """Returns a list of floats of equal length as target_vectors.
    These scaler floats are the normalized distances from source_vector to each target_vector.
    """
    distances = []
    total_distance = 0.0
    for target_vector in target_vectors:
        dist = (source_vector - target_vector).length()
        distances.append(dist)
        total_distance += dist

    distance_scalers = []
    for i, dist in enumerate(distances):
        try:
            val = 1/dist
        except ZeroDivisionError:
            # Return early if there is no distance between the source_vector and one of the target_vectors.
            # i.e. One of the target_vectors shares the same location as the source_vector
            # return a scaler of 1.0 for that target_vector and 0.0 for the remaining target_vectors.
            fake_scalers = [0.0] * len(distances)
            fake_scalers[i] = 1.0
            return fake_scalers
        distance_scalers.append(val)

    scalers_total = 0.0
    for scaler in distance_scalers:
        scalers_total += scaler
    normalized_scalers = []
    for scaler in distance_scalers:
        normalized_scalers.append(scaler/scalers_total)
    return normalized_scalers


def get_distance_between_nodes(node_a, node_b) -> float:
    pos_a = cmds.xform(str(node_a), q=True, worldSpace=True, translation=True)
    pos_b = cmds.xform(str(node_b), q=True, worldSpace=True, translation=True)
    
    vector_difference = [pos_a[0] - pos_b[0], pos_a[1] - pos_b[1], pos_a[2] - pos_b[2]]
    squared = [num ** 2 for num in vector_difference]
    distance = math.sqrt(squared[0] + squared[1] + squared[2])
    
    return distance
