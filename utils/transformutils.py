import maya.api.OpenMaya as om
import pymel.core as pm


def get_worldspace_vector(pynode):
    try:
        return om.MVector(pynode.getTranslation(space='world'))
    except AttributeError:
        return om.MVector(pm.pointPosition(pynode))
    # return om.MVector(pm.xform(pynode, q=True, worldSpace=True, rotatePivot=True))


def get_worldspace_orientation_quaternion(node):
    return node.getRotation(quaternion=True, space='world')


def get_worldspace_euler_rotation(transform_node):
    return pm.xform(transform_node, rotation=True, worldSpace=True, q=True)


def match_worldspace_position(dag_node, target_dag_node):
    target_vector = get_worldspace_vector(target_dag_node)
    move_node_to_worldspace_position(dag_node, target_vector)


def match_worldspace_position_orientation(transform_node, destination_node):
    transform_node.setTranslation(destination_node.getTranslation(space='world'), space='world')
    transform_node.setRotation(destination_node.getRotation(space='world'), space='world')


def aim_node_at_node(aimed_node, target_node, aim_axis=om.MVector().kXaxisVector):
    aim_axis = aim_axis
    aimed_location = get_worldspace_vector(aimed_node)
    target_location = get_worldspace_vector(target_node)
    orientation_quaternion = get_quaternion_aimed_at_vector(aimed_location, target_location, aim_axis)
    aimed_node.setRotation(orientation_quaternion)


def get_quaternion_aimed_at_vector(start_vector, target_vector, aim_axis=om.MVector().kXaxisVector):
    aim_vector = target_vector - start_vector
    aim_vector.normalize()
    orientation_quaternion = om.MQuaternion(aim_axis, aim_vector)
    return orientation_quaternion



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
            # Return early if there no distance between the source_vector and one of the target_vectors.
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



