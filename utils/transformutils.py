import maya.api.OpenMaya as om
import pymel.core as pm


def get_worldspace_vector(pynode):
    return om.MVector(pm.xform(pynode, q=True, worldSpace=True, translation=True))


def match_worldspace_position(dag_node, target_dag_node):
    target_vector = get_worldspace_vector(target_dag_node)
    move_node_to_worldspace_position(dag_node, target_vector)


def nodes_almost_match_worldspace_position(dag1, dag2, tolerance=0.001):
    ws_pos1 = get_worldspace_vector(dag1)
    ws_pos2 = get_worldspace_vector(dag2)
    distance = ws_pos1 - ws_pos2
    return abs(distance.length()) < tolerance


def move_node_to_worldspace_position(dag_node, worldspace_vector):
    pm.move(dag_node, worldspace_vector, absolute=True)


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


def get_extra_root_joints_from_root_joint(root_joint):
    all_children = root_joint.getChildren(allDescendents=True)
    extra_nodes = [x for x in all_children if x.type() != 'joint']
    extra_roots = []
    for extra_node in extra_nodes:
        extra_joints = extra_node.getChildren(allDescendents=True, type=pm.nt.Joint)
        try:
            extra_roots.append(extra_joints[-1])
        except IndexError:
            pass
    return extra_roots
