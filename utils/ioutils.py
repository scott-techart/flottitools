import os
import stat

import pymel.core as pm
import maya.cmds as cmds

import flottitools.path_consts as path_consts
import flottitools.utils.pathutils as pathutils


def get_destination_ma_path_from_dialogue(start_dir=None, file_mode=0):
    start_dir = start_dir or path_consts.FLOTTITOOLS_DIR
    try:
        return pm.fileDialog2(fileMode=file_mode,
                              fileFilter="Maya Files (*.ma);;Maya ASCII (*.ma)",
                              startingDirectory=start_dir)[0]
    except IndexError:
        return


def get_fbx_path_from_dialogue(start_dir=None, file_mode=1):
    start_dir = start_dir or path_consts.FLOTTITOOLS_DIR
    try:
        return pm.fileDialog2(fileMode=file_mode,
                              fileFilter="FBX Files (*.fbx)",
                              startingDirectory=start_dir)[0]
    except IndexError:
        return


def ensure_file_is_writable(path):
    dest_path = os.path.abspath(path)
    if os.path.exists(dest_path):
        if not os.access(dest_path, os.W_OK):
            os.chmod(dest_path, stat.S_IWRITE)


def export_fbx(export_file_path, nodes=None):
    """
    If nodes is None then export the entire scene. Else export only the contents of nodes.
    pm.ExportFile() triggers UI elements.
    The mel command works reliably and does not hang waiting for user input.
    """
    # mel_formatted_file_path = os.path.normpath(export_file_path).replace('\\', '/')
    mel_formatted_file_path = pathutils.format_path_for_mel(export_file_path)
    args = ['FBXExport', '-f', '"{}"'.format(mel_formatted_file_path)]
    if nodes:
        args.append('-s')
        pm.select(nodes, replace=True)
    mel_string = ' '.join(args)
    return pm.mel.eval(mel_string)
