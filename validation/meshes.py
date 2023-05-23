import pymel.core as pm

import flottitools.utils.meshutils as meshutils
import flottitools.utils.transformutils as transformutils


def get_missing_uvs_from_scene(meshes=None, progress_bar=None):
    meshes = meshes or meshutils.get_meshes_from_scene()
    if progress_bar:
        progress_bar.reset()
        chunks = [len(m.f) for m in meshes]
        progress_bar.set_chunks(chunks)
    meshes_with_missing_uvs = {}
    for mesh in meshes:
        if progress_bar:
            progress_bar.update_label_and_iter_chunk('Validating:  {0}'.format(mesh.name()))
        missing_uv_faces = meshutils.get_faces_with_missing_uvs(mesh)
        if missing_uv_faces:
            meshes_with_missing_uvs[mesh] = missing_uv_faces
    return meshes_with_missing_uvs


def get_meshes_with_multiple_shapes_from_scene(meshes=None, progress_bar=None):
    meshes = meshes or meshutils.get_meshes_from_scene()
    if progress_bar:
        progress_bar.reset()
        progress_bar.set_maximum(len(meshes))
    meshes_with_too_many_shapes = {}
    for mesh in meshes:
        # getShapes() returns nodes like Orig nodes in skinned meshes. This method doesn't.
        shapes = mesh.listHistory(type='shape', future=True)
        if len(shapes) > 1:
            meshes_with_too_many_shapes[mesh] = shapes
        if progress_bar:
            progress_bar.update_iterate_value()
    return meshes_with_too_many_shapes


def get_meshes_with_dirty_history_from_scene(meshes=None, progress_bar=None):
    meshes = meshes or meshutils.get_meshes_from_scene()
    if progress_bar:
        progress_bar.reset()
        progress_bar.set_maximum(len(meshes))
    meshes_with_dirty_history = {}
    for mesh in meshes:
        # history = [h for h in mesh.listHistory(pruneDagObjects=True) if not isinstance(h, pm.nt.SkinCluster)]
        history = get_bad_history_nodes(mesh)
        for h in history:
            print(h, h.type(), type(h))
        if history:
            meshes_with_dirty_history[mesh] = history
        if progress_bar:
            progress_bar.update_iterate_value()
    return meshes_with_dirty_history


def fix_meshes_with_dirty_history(meshes):
    for mesh in meshes:
        history = mesh.listHistory(pruneDagObjects=True)
        skin_cl = [h for h in history if isinstance(h, pm.nt.SkinCluster)]
        if skin_cl:
            pm.bakePartialHistory(mesh, prePostDeformers=True)
        else:
            pm.delete(mesh, constructionHistory=True)


def get_meshes_with_overlapping_verts_from_scene(meshes=None, progress_bar=None):
    meshes = meshes or meshutils.get_meshes_from_scene()
    if progress_bar:
        progress_bar.reset()
        chunks = [len(m.f) for m in meshes]
        progress_bar.set_chunks(chunks)
    meshes_with_overlapping_verts = {}
    for mesh in meshes:
        if progress_bar:
            progress_bar.update_label_and_iter_chunk('Validating:  {0}'.format(mesh.name()))
        overlapping_verts = meshutils.get_overlapping_vertices(mesh)
        if overlapping_verts:
            meshes_with_overlapping_verts[mesh] = overlapping_verts
    return meshes_with_overlapping_verts


def get_bad_history_nodes(node):
    def is_acceptable_history_node(history_node):
        node_types = [pm.nt.SkinCluster, pm.nt.GroupId, pm.nt.ShadingEngine,
                      pm.nt.DisplayLayer, pm.nt.Tweak, pm.nt.GroupParts]
        for node_type in node_types:
            if isinstance(history_node, node_type):
                return True
        return False
    return [h for h in node.listHistory(pruneDagObjects=True) if not is_acceptable_history_node(h)]


def get_invalid_vertex_colors_from_scene(meshes=None, progress_bar=None):
    meshes = meshes or meshutils.get_meshes_from_scene()
    meshes_with_invalid_vert_colors = {}
    if progress_bar:
        progress_bar.reset()
        chunks = [len(m.vtx) for m in meshes]
        progress_bar.set_chunks(chunks)
    for mesh in meshes:
        if progress_bar:
            progress_bar.update_label_and_iter_chunk('Validating:  {0}'.format(mesh.name()))
        mesh_node_to_index_to_color = meshutils.get_vertex_colors_from_node(mesh)
        meshes_with_invalid_vert_colors.update(mesh_node_to_index_to_color)
    return meshes_with_invalid_vert_colors


def remove_vert_color(mesh_and_verts, progress_bar=None):
    if progress_bar:
        progress_bar.reset()
        progress_bar.set_maximum(len(mesh_and_verts))
    for mesh, verts in mesh_and_verts:
        if progress_bar:
            progress_bar.update_label_and_iter_val('Fixing:  {0}'.format(mesh.name()))
        pm.polyColorPerVertex(verts, remove=True)
