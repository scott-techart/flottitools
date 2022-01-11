import os

import flottitools.utils.materialutils as matutils


def get_materials_with_bad_texture_paths_from_scene(material_nodes=None, progress_bar=None):
    material_nodes = material_nodes or matutils.get_used_materials_in_scene()
    if progress_bar:
        progress_bar.reset()
        progress_bar.set_maximum(len(material_nodes))
    mat_to_filenodes = {}
    for mat in material_nodes:
        bad_file_nodes = get_file_nodes_with_bad_texture_paths(mat)
        if bad_file_nodes:
            mat_to_filenodes[mat] = bad_file_nodes
        if progress_bar:
            progress_bar.update_iterate_value()
    return mat_to_filenodes


def get_file_nodes_with_workfiles_texture_paths(materials):
    file_nodes = []
    for mat in materials:
        attrs_and_filenodes = matutils.get_attrs_and_file_nodes_from_mat(mat)
        file_nodes.extend([f for a, f in attrs_and_filenodes if 'media' not in os.path.normpath(f.fileTextureName).lower()])


def get_file_nodes_with_bad_texture_paths(material):
    attrs_and_filenodes = matutils.get_attrs_and_file_nodes_from_mat(material)
    file_nodes = [f for a, f in attrs_and_filenodes if 'media' not in os.path.normpath(f.fileTextureName.get()).lower()]
    return file_nodes
