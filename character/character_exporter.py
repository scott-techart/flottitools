import os

import pymel.core as pm

import flottitools.mayafbx as mayafbx
import flottitools.skinmesh.skinio as skinio
import flottitools.utils.ioutils as ioutils
import flottitools.utils.meshutils as meshutils
import flottitools.utils.skeletonutils as skelutils
import flottitools.utils.skinutils as skinutils

STATIC_MESH_PREFIX = 'SM_'
SKELETAL_MESH_PREFIX = 'SK_'
SKELETON_PREFIX = 'SKEL_'
SKIN_WEIGHTS_PREFIX = 'SKW_'

MAYA_BINARY_EXTENSION = '.mb'
MAYA_ASCII_EXTENSION = '.ma'
MAYA_FILE_EXTENSIONS = [MAYA_ASCII_EXTENSION, MAYA_BINARY_EXTENSION]
FBX_EXTENSION = '.fbx'


def export_sk_meshes_from_scene(export_fbx_path, skeleton_path, skin_weights_path):
    if not skeleton_path.exists():
        raise AssertionError('Aborting SKMesh export. No skeleton file exists at path: {}'.format(os.path.normpath(skeleton_path)))
    if not skin_weights_path.exists():
        raise AssertionError('Aborting SKMesh export. No skin weights file exists at path: {}'.format(os.path.normpath(skin_weights_path)))
    skel_nodes = pm.importFile(skeleton_path, loadReferenceDepth='none', defaultNamespace=True, returnNewNodes=True)
    first_joint = None
    for skel_node in skel_nodes:
        if isinstance(skel_node, pm.nt.Joint):
            first_joint = skel_node
            continue
    root_joint = skelutils.get_root_joint_from_child(first_joint)
    skeleton = skelutils.get_hierarchy_from_root(root_joint, joints_only=True)
    static_meshes = meshutils.get_meshes_from_scene()
    skin_clusters = [skinutils.bind_mesh_to_joints(static_mesh, skeleton) for static_mesh in static_meshes]
    skinio.import_skinning_on_meshes(static_meshes, skin_weights_path)
    
    options = mayafbx.FbxExportOptions()
    options.smoothing_groups = True
    options.hard_edges = False
    options.triangulate = True
    options.animation = False
    options.cameras = False
    options.lights = False
    options.audio = False
    options.automatic_units = True
    options.file_version = mayafbx.FileVersion.FBX_2020
    
    ioutils.ensure_file_is_writable(export_fbx_path)
    pm.select(static_meshes, replace=True)
    pm.select(root_joint, add=True)
    mayafbx.export_fbx(export_fbx_path, options, selection=True)
    return static_meshes, skeleton, skin_clusters


def get_sk_mesh_export_path(static_mesh_path):
    source_dir = static_mesh_path.parents[1]
    new_file_name = static_mesh_path.stem
    if not new_file_name.lower().startswith(STATIC_MESH_PREFIX.lower()):
        return
    new_file_name = new_file_name.replace(STATIC_MESH_PREFIX.lower(), SKELETAL_MESH_PREFIX)
    new_file_name = new_file_name.replace(STATIC_MESH_PREFIX, SKELETAL_MESH_PREFIX)
    new_path = source_dir.joinpath(new_file_name).with_suffix(FBX_EXTENSION)
    return new_path

def get_skeleton_path_from_static_mesh_path(static_mesh_path):
    skel_path = get_path_from_static_mesh_path(static_mesh_path, SKELETON_PREFIX)
    return skel_path


def get_skin_weights_path_from_static_mesh_path(static_mesh_path):
    skw_path = get_path_from_static_mesh_path(static_mesh_path, SKIN_WEIGHTS_PREFIX)
    return skw_path


def get_path_from_static_mesh_path(static_mesh_path, prefix):
    source_dir = static_mesh_path.parent
    new_file_name = static_mesh_path.stem
    if not new_file_name.lower().startswith(STATIC_MESH_PREFIX.lower()):
        return
    new_file_name = new_file_name.replace(STATIC_MESH_PREFIX.lower(), prefix)
    new_file_name = new_file_name.replace(STATIC_MESH_PREFIX, prefix)
    new_path = source_dir.joinpath(new_file_name).with_suffix(MAYA_ASCII_EXTENSION)
    if new_path.exists():
        return new_path
    new_path = source_dir.joinpath(new_file_name).with_suffix(MAYA_BINARY_EXTENSION)
    return new_path
