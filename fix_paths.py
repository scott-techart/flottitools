from pathlib import Path

import maya.api.OpenMaya as om
import pymel.core as pm

import flottitools.path_consts as path_consts
import flottitools.utils.pathutils as pathutils


def fix_paths():
    retarget_reference_paths_to_users_disk()
    retarget_file_texture_paths_to_users_disk()


def retarget_file_texture_paths_to_users_disk(file_nodes=None):
    file_nodes = file_nodes or pm.ls(type=pm.nt.File)
    for file_node in file_nodes:
        initial_texture_path = file_node.fileTextureName.get()
        mel_abs_retargeted_path = _retarget_path_if_contains_names(
            initial_texture_path, file_node, [])
        if mel_abs_retargeted_path:
            file_node.fileTextureName.set(mel_abs_retargeted_path)
            print('{0} path retargeted to: {1}'.format(file_node, mel_abs_retargeted_path))


def retarget_reference_paths_to_users_disk():
    references = pm.listReferences()
    for reference in references:
        initial_unresolved_path = reference.unresolvedPath()
        mel_abs_retargeted_path = _retarget_path_if_contains_names(
            initial_unresolved_path, reference.refNode.name(), [])
        if mel_abs_retargeted_path:
            reference.replaceWith(mel_abs_retargeted_path)
            print('{0} path retargeted to: {1}'.format(reference.refNode.name(), mel_abs_retargeted_path))


def _retarget_path_if_contains_names(path, node, folder_names):
    relative_path = None
    for folder_name in folder_names:
        _, relative_path = pathutils.get_path_relative_to_folder_name(Path(path), folder_name)
        if relative_path is not None:
            break
    if relative_path is None:
        pm.warning(
            '{0} found in node {1} cannot be converted to relative path because {2} is not found in the path.'.format(
                path, node, folder_names))
        return
    abs_content_source_path = Path(path_consts.RAS_CONTENTSOURCE_DIR)
    abs_path = abs_content_source_path.joinpath(relative_path)
    mel_formatted_abs_path = pathutils.get_mel_formatted_path(abs_path)
    mel_formatted_ras_dir = pathutils.format_path_for_mel(path_consts.RAS_DIR)
    mel_abs_path_relative_indicator = mel_formatted_abs_path.replace(
        '{}/'.format(mel_formatted_ras_dir), '{}//'.format(mel_formatted_ras_dir))
    if mel_abs_path_relative_indicator != str(path):
        return mel_abs_path_relative_indicator


def _callback_on_check_file(file_object: om.MFileObject, client_data=None):
    # client_data is needed or the callback won't work. It can catch any user variables you want to pass
    # Return False to suppress the missing reference popup, however this also removes the reference entirely
    original_file_path = Path(file_object.rawFullName())
    _, relative_path = pathutils.get_path_relative_to_folder_name(original_file_path, path_consts.CONTENTSOURCE_FOLDER_NAME)
    if not relative_path:
        print("- Unable to find filepath -", original_file_path)
        return True
    
    local_file_path = Path(path_consts.FLOTTITOOLS_DIR).joinpath(relative_path)
    if local_file_path.exists() and local_file_path != original_file_path:
        file_object.setRawFullName(str(local_file_path))
        print("Original reference path changed\n"
              "{0}\n"
              "{1}".format(original_file_path, local_file_path))
        return True
    
    else:
        print("- Unable to change filepath -", original_file_path)
        return True
