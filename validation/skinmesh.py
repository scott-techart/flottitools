import pymel.core as pm

import flottitools.utils.skeletonutils as skelutils
import flottitools.utils.skinutils as skinutils
import flottitools.utils.transformutils as xformutils


def get_exceeding_verts_from_scene(skinned_meshes=None, progress_bar=None):
    """Checks skinned_meshes for verts with more than four influences.

     If the caller does not provide skinned_meshes all
     skinned meshes detected in the Maya scene will be checked.
    """
    skinned_meshes = skinned_meshes or skinutils.get_skinned_meshes_from_scene()

    exceeding_verts = {}
    if progress_bar:
        progress_bar.reset()
        chunks = [len(skm.vtx) for skm in skinned_meshes]
        progress_bar.set_chunks(chunks)
    for skinned_mesh in skinned_meshes:
        if progress_bar:
            progress_bar.update_label_and_iter_chunk('Validating:  {0}'.format(skinned_mesh.name()))
        exceeding_verts_dict = skinutils.get_vert_indexes_with_exceeding_influences(skinned_mesh)
        if exceeding_verts_dict:
            exceeding_verts[skinned_mesh] = exceeding_verts_dict
    return exceeding_verts


def prune_exceeding_influences_from_scene_validation(exceeding_meshes_dict, progress_bar=None):
    if progress_bar:
        progress_bar.reset()
        chunks = [len(x) for x in exceeding_meshes_dict.values()]
        progress_bar.set_chunks(chunks)
    for skinned_mesh, exceeding_vert_indexes in exceeding_meshes_dict.items():
        if progress_bar:
            progress_bar.update_label_and_iter_chunk('Fixing:  {0}'.format(skinned_mesh.name()))
        skinutils.prune_exceeding_skinned_mesh(skinned_mesh, exceeding_vert_indexes)


def get_non_normalized_verts_from_scene(skinned_meshes=None, progress_bar=None):
    skinned_meshes = skinned_meshes or skinutils.get_skinned_meshes_from_scene()
    if progress_bar:
        progress_bar.reset()
        chunks = [len(x.vtx) for x in skinned_meshes]
        progress_bar.set_chunks(chunks)
    non_normalized_verts = {}
    for skinned_mesh in skinned_meshes:
        if progress_bar:
            progress_bar.update_label_and_iter_chunk('Validating:  {0}'.format(skinned_mesh.name()))
        skin_cluster = skinutils.get_skincluster(skinned_mesh)
        bad_vert_indexes_to_weight = skinutils.get_non_normalized_vert_indexes(skinned_mesh.vtx, skin_cluster)
        bad_verts = [skinned_mesh.vtx[i] for i in bad_vert_indexes_to_weight]
        if bad_verts:
            non_normalized_verts[skinned_mesh] = bad_vert_indexes_to_weight
    return non_normalized_verts


def normalize_skinned_meshes(skinned_meshes, progress_bar=None):
    if progress_bar:
        progress_bar.reset()
        progress_bar.set_maximum(len(skinned_meshes))
    for skinned_mesh in skinned_meshes:
        if progress_bar:
            progress_bar.update_label_and_iter_val('Fixing:  {0}'.format(skinned_mesh.name()))
        skinutils.normalize_skinned_mesh(skinned_mesh)


def get_joint_counts_from_scene(skinned_meshes=None, progress_bar=None):
    skinned_meshes = skinned_meshes or skinutils.get_skinned_meshes_from_scene()
    if progress_bar:
        progress_bar.reset()
        progress_bar.set_maximum(len(skinned_meshes))
    meshes_with_too_many_joints = {}
    for skinned_mesh in skinned_meshes:
        if progress_bar:
            progress_bar.update_label('Validating:  {0}'.format(skinned_mesh.name()))
        skincl = skinutils.get_skincluster(skinned_mesh)
        skinned_influences = pm.skinCluster(skincl, weightedInfluence=True, q=True)
        if len(skinned_influences) > 64:
            meshes_with_too_many_joints[skinned_mesh] = skinned_influences
        if progress_bar:
            progress_bar.update_iterate_value()
    return meshes_with_too_many_joints


def get_extra_skeleton_roots_from_scene(skinned_meshes=None, progress_bar=None):
    skinned_meshes = skinned_meshes or skinutils.get_skinned_meshes_from_scene()
    if progress_bar:
        progress_bar.reset()
        progress_bar.set_maximum(len(skinned_meshes))
    extra_skel_roots = {}
    for skinned_mesh in skinned_meshes:
        if progress_bar:
            progress_bar.update_label('Validating:  {0}'.format(skinned_mesh.name()))
        root_joint = skinutils.get_root_joint_from_skinned_mesh(skinned_mesh)
        extra_roots = skelutils.get_extra_root_joints_from_root_joint(root_joint)
        if extra_roots:
            extra_skel_roots[skinned_mesh] = extra_roots
        if progress_bar:
            progress_bar.update_iterate_value()
    return extra_skel_roots


def iterate_methods_per_vert(vertices, skin_cluster=None, methods=None, progress_bar=None):
    if progress_bar:
        pbar_text = progress_bar.label.text()
    results = []
    for i, vert in enumerate(vertices):
        for method in methods:
            result = method(vert, skin_cluster=skin_cluster)
            results.append(result)
        if progress_bar:
            new_text = '{0}  vtx[{1}]'.format(pbar_text, vert.index())
            progress_bar.update_label_and_iter_val(new_text)


def get_dup_joint_names_from_scene(skinned_meshes=None):
    skinned_meshes = skinned_meshes or skinutils.get_skinned_meshes_from_scene()
    skinned_meshes_to_dup_joints = {}
    for skinned_mesh in skinned_meshes:
        root_joint = skinutils.get_root_joint_from_skinned_mesh(skinned_mesh)
        skeleton = skelutils.get_hierarchy_from_root(root_joint, joints_only=True)
        dup_named_joints = get_nodes_with_same_name_in_list(skeleton)
        if dup_named_joints:
            skinned_meshes_to_dup_joints[skinned_mesh] = dup_named_joints
    return skinned_meshes_to_dup_joints


def get_nodes_with_same_name_in_list(nodes):
    short_names = [n.shortName() for n in nodes]
    short_names_set = set(short_names)
    if len(short_names) == len(short_names_set):
        return []
    dup_indices = find_duplicates_indices(short_names)
    nodes_with_same_names = [nodes[i] for i in dup_indices]
    return nodes_with_same_names


def find_duplicates_indices(lst):
    duplicates = []
    seen = {}
    for i, item in enumerate(lst):
        if item in seen:
            if seen[item] not in duplicates:
                duplicates.append(seen[item])
            duplicates.append(i)
        else:
            seen[item] = i
    return duplicates


def execute_methods_on_each_skin_mesh_in_scene(methods=None):
    methods = methods or [skinutils.prune_exceeding_skinned_mesh, skinutils.normalize_skinned_mesh]
    skinned_meshes = skinutils.get_skinned_meshes_from_scene()
    for skinned_mesh in skinned_meshes:
        for method in methods:
            method(skinned_mesh)

