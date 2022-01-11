import os

import pymel.core as pm

import flottitools.utils.namespaceutils as nsutils
import flottitools.utils.selectionutils as selutils
import flottitools.utils.skinutils as skinutils


NAMESPACE_SKINCOPY_EXPORT = 'FlottiCopySkinWeightsExport'
NAMESPACE_SKINCOPY_IMPORT = 'FlottiCopySkinWeightsImport'


def export_skinned_mesh(skinned_mesh, output_path, go_to_bind_pose=True):
    with pm.UndoChunk():
        if go_to_bind_pose:
            bind_pose = skinutils.get_bind_pose_from_skinned_mesh(skinned_mesh)
            pm.dagPose(bind_pose, restore=True, g=True)
        with selutils.preserve_selection():
            dup_mesh, dup_root, dup_cluster = skinutils.duplicate_skinned_mesh_and_skeleton(
                skinned_mesh, dup_namespace=NAMESPACE_SKINCOPY_EXPORT, dup_parent=nsutils.PARENT_WORLD)
            pm.select((dup_mesh, dup_root), replace=True)
            pm.exportSelected(output_path, constraints=False, expressions=False, shader=False, preserveReferences=False,
                              type='mayaAscii', constructionHistory=True, force=True)
    pm.undo()


def import_skinning(skinned_mesh, skinweights_path, copy_weights_method=None, go_to_bindpose=True):
    with selutils.preserve_selection():
        copy_weights_method = copy_weights_method or skinutils.copy_weights
        new_nodes = pm.importFile(skinweights_path, loadReferenceDepth='none',
                                  namespace=NAMESPACE_SKINCOPY_IMPORT, returnNewNodes=True)
        source_skinmesh = _get_skinned_mesh_from_import(new_nodes, skinweights_path, skinned_mesh.nodeName())
        if go_to_bindpose:
            bind_pose = skinutils.get_bind_pose_from_skinned_mesh(skinned_mesh)
            pm.dagPose(bind_pose, restore=True, g=True)
        copy_weights_method(source_skinmesh, skinned_mesh)
        import_namespace = nsutils.get_namespace_as_pynode(NAMESPACE_SKINCOPY_IMPORT)
        import_namespace.remove()
        # evaluate all nodes
        pm.mel.eval('doEnableNodeItems true all;')


def _get_skinned_mesh_from_import(imported_nodes, skinweights_path, name_to_match=None):
    skinned_meshes = skinutils.get_skinnned_meshes_in_list(imported_nodes)
    try:
        skinned_mesh = skinned_meshes[0]
        if len(skinned_meshes) > 1 and name_to_match:
            for sm in skinned_meshes:
                if sm.nodeName(stripNamespace=True) == name_to_match:
                    skinned_mesh = sm
                    break
        return skinned_mesh
    except IndexError:
        raise MissingSkinnedMesh(skinweights_path)


def get_skindata_path():
    scene_path = pm.sceneName()
    dir_path = os.path.dirname(scene_path)
    return dir_path


def get_skindata_path_from_dialogue(start_dir=None, file_mode=0):
    start_dir = start_dir or get_skindata_path()
    try:
        return pm.fileDialog2(fileMode=file_mode,
                              fileFilter="Maya Files (*.ma);;Maya ASCII (*.ma)",
                              startingDirectory=start_dir)[0]
    except IndexError:
        return


def export_selected_skinning_as():
    skinned_meshes = skinutils.get_skinned_meshes_from_selection()
    for skinned_mesh in skinned_meshes:
        output_path = get_skindata_path_from_dialogue()
        export_skinned_mesh(skinned_mesh, output_path)


def import_selected_skinning_as():
    skinned_mesh = skinutils.get_first_skinned_mesh_from_selection()
    import_path = get_skindata_path_from_dialogue(file_mode=1)
    import_skinning(skinned_mesh, import_path)


class MissingSkinnedMesh(ValueError):
    def __init__(self, skin_file_path):
        super(MissingSkinnedMesh, self).__init__('No skinned mesh detected in {}.'.format(skin_file_path))
