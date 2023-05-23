import os

import pymel.core as pm

import flottitools.utils.meshutils as meshutils
import flottitools.utils.namespaceutils as nsutils
import flottitools.utils.selectionutils as selutils
import flottitools.utils.skinutils as skinutils


NAMESPACE_SKINCOPY_EXPORT = 'FlottiCopySkinWeightsExport'
NAMESPACE_SKINCOPY_IMPORT = 'FlottiCopySkinWeightsImport'

SKINNING_METHOD_BEST_GUESS = object()


def export_skinned_mesh(skinned_mesh, output_path, go_to_bind_pose=True):
    export_skinned_meshes([skinned_mesh], output_path, go_to_bind_pose=go_to_bind_pose)


def export_skinned_meshes(skinned_meshes, output_path, go_to_bind_pose=True):
    with pm.UndoChunk():
        if go_to_bind_pose:
            try:
                bind_poses = [skinutils.get_bind_pose_from_skinned_mesh(skm) for skm in skinned_meshes]
                # remove duplicate bind poses
                bind_poses = set(bind_poses)
                [pm.dagPose(bp, restore=True, g=True) for bp in bind_poses]
            except:
                pass
        with selutils.preserve_selection():
            to_select = []
            dup_meshes_roots_and_clusters = skinutils.duplicate_skinned_meshes_and_skeleton(
                skinned_meshes, dup_namespace=NAMESPACE_SKINCOPY_EXPORT, dup_parent=nsutils.PARENT_WORLD)
            dup_meshes, dup_roots, dup_clusters = zip(*dup_meshes_roots_and_clusters)
            dup_roots = set(dup_roots)
            to_select.extend(dup_meshes)
            to_select.extend(dup_roots)
            pm.select(to_select, replace=True)
            pm.exportSelected(output_path, constraints=False, expressions=False, shader=False, preserveReferences=False,
                              type='mayaAscii', constructionHistory=True, force=True)
    pm.undo()


def import_skinning(target_mesh, skinweights_path, copy_weights_method=None, go_to_bindpose=True, bind_unskinned=True, get_mesh_pairs_method=None):
    if copy_weights_method == SKINNING_METHOD_BEST_GUESS:
        copy_weights_method = None
    import_skinning_on_meshes([target_mesh], skinweights_path, copy_weights_method=copy_weights_method,
                              go_to_bindpose=go_to_bindpose, bind_unskinned=bind_unskinned, get_mesh_pairs_method=get_mesh_pairs_method)


def import_skinning_on_meshes_in_scene(skinweights_path, copy_weights_method=None, go_to_bindpose=True, bind_unskinned=True, get_mesh_pairs_method=None):
    meshes = meshutils.get_meshes_from_scene()
    import_skinning_on_meshes(meshes, skinweights_path, copy_weights_method=copy_weights_method,
                              go_to_bindpose=go_to_bindpose, bind_unskinned=bind_unskinned, get_mesh_pairs_method=get_mesh_pairs_method)


def import_skinning_on_meshes(target_meshes, skinweights_path, copy_weights_method=None,
                              go_to_bindpose=True, bind_unskinned=True, get_mesh_pairs_method=None):
    get_mesh_pairs_method = get_mesh_pairs_method or meshutils.get_mesh_pairs_by_name
    scene_joints = None
    if bind_unskinned:
        scene_joints = pm.ls(type=pm.nt.Joint)
    with selutils.preserve_selection():
        new_nodes = pm.importFile(skinweights_path, loadReferenceDepth='none',
                                  namespace=NAMESPACE_SKINCOPY_IMPORT, returnNewNodes=True)
        source_skinned_meshes = skinutils.get_skinnned_meshes_in_list(new_nodes)
        import_namespace = nsutils.get_first_namespace_from_node(source_skinned_meshes[0])
        source_target_mesh_pairs = get_mesh_pairs_method(source_skinned_meshes, target_meshes)

        if go_to_bindpose:
            try:
                bind_poses = [skinutils.get_bind_pose_from_skinned_mesh(skm) for skm in target_meshes]
                bind_poses = set(bind_poses)
                [pm.dagPose(bp, restore=True, g=True) for bp in bind_poses]
            except:
                pass

        for source_skinned_mesh, target_mesh in source_target_mesh_pairs:
            if bind_unskinned:
                if not skinutils.get_skincluster(target_mesh):
                    skinutils.bind_mesh_to_similar_joints(source_skinned_mesh, target_mesh, target_joints=scene_joints)
            # if copy_weights_method is None then best guess which weight copy method to use
            print('Copying skinning from mesh: {0} to mesh: {1}'.format(source_skinned_mesh.nodeName(),
                                                                        target_mesh.nodeName()))
            do_copy_weights_methods = copy_weights_method or _get_best_guess_copy_weights_method(source_skinned_mesh,
                                                                                                 target_mesh)
            do_copy_weights_methods(source_skinned_mesh, target_mesh)
        import_namespace.remove()
        # evaluate all nodes
        pm.mel.eval('doEnableNodeItems true all;')


def _get_best_guess_copy_weights_method(source_mesh, target_mesh, vert_order_check_method=None):
    def default_method(source, target):
        return len(source.vtx) == len(target.vtx)

    vert_order_check_method = vert_order_check_method or default_method
    copy_weights_method = skinutils.copy_weights
    if vert_order_check_method(source_mesh, target_mesh):
        copy_weights_method = skinutils.copy_weights_vert_order
    return copy_weights_method


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


def export_selected_skinning_as(output_path=None, go_to_bind_pose=True):
    skinned_meshes = skinutils.get_skinned_meshes_from_selection()
    if not output_path:
        output_path = get_skindata_path_from_dialogue()
    export_skinned_meshes(skinned_meshes, output_path, go_to_bind_pose)


def import_selected_skinning_as(copy_weights_method=None):
    copy_weights_method = copy_weights_method or skinutils.copy_weights
    if not pm.selected():
        raise AssertionError(
            'No skinned mesh currently selected. Select the skinned mesh you would like to copy weights to.')
    skinned_mesh = skinutils.get_first_skinned_mesh_from_selection()
    if skinned_mesh is None:
        raise AssertionError('No skinned mesh currently selected. The current selection does not have a skin cluster.')
    import_path = get_skindata_path_from_dialogue(file_mode=1)
    import_skinning(skinned_mesh, import_path, copy_weights_method=copy_weights_method)


class MissingSkinnedMesh(ValueError):
    def __init__(self, skin_file_path):
        super(MissingSkinnedMesh, self).__init__('No skinned mesh detected in {}.'.format(skin_file_path))
