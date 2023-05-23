import os
import pathlib

import pymel.core as pm


def get_scene_path():
    scene_path = pm.sceneName()
    # If the current scene is new and unsaved pm.sceneName() returns pm.Path().
    if pm.Path() == scene_path:
        return
    full_path = pathlib.Path(scene_path)
    return full_path


def format_path_for_mel(path):
    if isinstance(path, pathlib.Path):
        path = path.__str__()
    path = path.replace('\\', '/')
    return path


def get_path_relative_to_folder_name(path, folder_name):
    lower_case_parts = [p.lower() for p in path.parts]
    lower_case_parts.reverse()
    try:
        index = lower_case_parts.index(folder_name.lower()) - 1
    except ValueError:
        return
    relative_root = path.parents[index]
    relative_path = path.relative_to(relative_root)
    return relative_path


def get_mel_formatted_path(file_path):
    file_path_mel_formatted = os.path.abspath(file_path)
    file_path_mel_formatted = file_path_mel_formatted.replace('\\', '/')
    return file_path_mel_formatted
