import random

import maya.api.OpenMaya as om
import pymel.core as pm

import SSEMaya.Utilities.openmayautils as omutils

NO_VERTEX_COLOR = om.MColor((-1, -1, -1, -1))


def get_meshes_from_scene():
    meshes = list(set([m.getParent() for m in pm.ls(type=pm.nt.Mesh)]))
    return meshes


def get_meshes_in_list(nodes):
    shapes = []
    for node in nodes:
        if isinstance(node, pm.nt.Shape):
            shapes.append(node)
        else:
            try:
                shape = node.getShapes()
                if shape:
                    shapes.append(shape)
            except AttributeError:
                pass
    meshes = []
    for mesh in pm.ls(shapes, type=pm.nt.Mesh):
        parent = mesh.getParent()
        if parent not in meshes:
            meshes.append(parent)
    return meshes


def get_mesh_nodes(node):
    if isinstance(node, pm.nt.Mesh):
        return [node]
    else:
        try:
            shapes = node.getShapes()
            return pm.ls(shapes, type=pm.nt.Mesh)
        except AttributeError:
            pass
    return []


def get_ngons(node):
    mesh_nodes = get_mesh_nodes(node)
    ngons = []
    for mesh_node in mesh_nodes:
        ngons.extend(get_ngons_from_mesh_node(mesh_node))
    return ngons


def get_ngons_from_mesh_node(mesh_node):
    face_names = get_ngons_from_mesh_name(mesh_node.name())
    faces = [pm.PyNode(v) for v in face_names]
    return faces


def get_ngons_from_mesh_name(mesh_node_name):
    ngons = []
    dag_path = omutils.get_dagpath_or_dependnode_from_name(mesh_node_name)
    faceIt = om.MItMeshPolygon(dag_path)
    objectName = dag_path.getPath()
    while not faceIt.isDone():
        numOfEdges = faceIt.getEdges()
        if len(numOfEdges) > 4:
            faceIndex = faceIt.index()
            componentName = str(objectName) + '.f[' + str(faceIndex) + ']'
            ngons.append(componentName)
        else:
            pass
        faceIt.next()
    return ngons


def get_overlapping_vertices(node, decimal_place_accuracy=5):
    mesh_nodes = get_mesh_nodes(node)
    overlapping_vertices = []
    for mesh_node in mesh_nodes:
        overlapping_vertices.extend(get_overlapping_vertices_from_mesh_node(mesh_node, decimal_place_accuracy))
    return overlapping_vertices


def get_overlapping_vertices_from_mesh_node(mesh_node, decimal_place_accuracy=5):
    vert_names = get_overlapping_vertices_from_mesh_name(mesh_node.name(), decimal_place_accuracy)
    vertices = [pm.PyNode(v) for v in vert_names]
    return vertices


def get_overlapping_vertices_from_mesh_name(mesh_node_name, decimal_place_accuracy=5):
    # warning
    overlapping_verts = []
    positions = []
    vertex_indices = []
    used_indices = []
    dag_path = omutils.get_dagpath_or_dependnode_from_name(mesh_node_name)
    vertexIt = om.MItMeshVertex(dag_path)
    object_name = dag_path.getPath()
    while not vertexIt.isDone():
        position = om.MVector(vertexIt.position())
        rounded_position = [round(n, decimal_place_accuracy) for n in position]
        vertex_index = vertexIt.index()
        try:
            i = positions.index(rounded_position)
            other_index = vertex_indices[i]
            if other_index not in used_indices:
                other_vertex_name = '{0}.vtx[{1}]'.format(str(object_name), str(other_index))
                overlapping_verts.append(other_vertex_name)
                used_indices.append(other_index)
            vertex_name = '{0}.vtx[{1}]'.format(str(object_name), str(vertex_index))
            overlapping_verts.append(vertex_name)
        except ValueError:
            pass
        vertex_indices.append(vertex_index)
        positions.append(rounded_position)
        vertexIt.next()
    return overlapping_verts


def get_faces_with_missing_uvs(node):
    mesh_nodes = get_mesh_nodes(node)
    faces_missing_uvs = []
    for mesh_node in mesh_nodes:
        faces_missing_uvs.extend(get_faces_with_missing_uvs_from_mesh_node(mesh_node))
    return faces_missing_uvs


def get_faces_with_missing_uvs_from_mesh_node(mesh_node):
    face_names = get_faces_with_missing_uvs_from_mesh_name(mesh_node.name())
    faces = [pm.PyNode(v) for v in face_names]
    return faces


def get_faces_with_missing_uvs_from_mesh_name(mesh_node_name):
    # error
    missing_uvs = []
    dag_path = omutils.get_dagpath_or_dependnode_from_name(mesh_node_name)
    face_iterator = om.MItMeshPolygon(dag_path)
    object_name = dag_path.getPath()
    while not face_iterator.isDone():
        if not face_iterator.hasUVs():
            component_name = '{0}.f[{1}]'.format(object_name, face_iterator.index())
            missing_uvs.append(component_name)
        face_iterator.next()
    return missing_uvs


def get_vertex_colors_from_mesh_name(mesh_node_name, skip_color_values=(NO_VERTEX_COLOR,)):
    vert_index_to_color = {}
    dag_path = omutils.get_dagpath_or_dependnode_from_name(mesh_node_name)
    vertex_iterator = om.MItMeshVertex(dag_path)
    while not vertex_iterator.isDone():
        m_color = vertex_iterator.getColor()
        if m_color not in skip_color_values:
            # PyMel doesn't seem to like MColor. So convert it to tuple to use in PyMel later.
            vert_index_to_color[vertex_iterator.index()] = tuple(m_color)
        vertex_iterator.next()
    return vert_index_to_color


def get_vertex_colors_from_node(node, skip_color_values=(NO_VERTEX_COLOR,)):
    mesh_nodes = get_mesh_nodes(node)
    mesh_node_to_index_to_color = {}
    for mesh_node in mesh_nodes:
        index_to_color = get_vertex_colors_from_mesh_node(mesh_node, skip_color_values=skip_color_values)
        if index_to_color:
            mesh_node_to_index_to_color[mesh_node] = index_to_color
    return mesh_node_to_index_to_color


def get_vertex_colors_from_mesh_node(mesh_node, skip_color_values=(NO_VERTEX_COLOR,)):
    skip_color_values = list(skip_color_values)
    for i, color_value in enumerate(skip_color_values):
        if not isinstance(color_value, om.MColor):
            skip_color_values[i] = om.MColor(color_value)
    return get_vertex_colors_from_mesh_name(mesh_node.name(), skip_color_values=skip_color_values)


def get_mesh_pairs_by_name(meshes_a, meshes_b):
    pairs = []
    # copy meshes_b, so we can pop members of it for optimization without mutating meshes_b
    meshes_b_copy = meshes_b[:]
    for mesh_a in meshes_a:
        mesh_a_name = mesh_a.nodeName(stripNamespace=True)
        for i, mesh_b in enumerate(meshes_b_copy):
            if mesh_a_name == mesh_b.nodeName(stripNamespace=True):
                pairs.append((mesh_a, mesh_b))
                meshes_b_copy.pop(i)
                continue
    return pairs
