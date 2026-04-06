import maya.OpenMayaUI as old_omui
import maya.api.OpenMayaUI as omui
import maya.cmds as cmds
import inspect
import sys

from flottitools.ui import QtGui
from flottitools import path_consts


class Callbacks:
    _instance = None
    ids: list[int] = []
    ids_dict: dict[str: int] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def add(cls, name: str, callback: int):
        if callback not in cls.ids:
            cls.ids.append(callback)
            cls.ids_dict[callback] = name


def unload_plugin(plugin: str):
    if cmds.pluginInfo(plugin, q=True, loaded=True):
        cmds.pluginInfo(plugin, e=True, autoload=False)
        cmds.unloadPlugin(plugin, force=True)

        print(f"Unloaded - {plugin}")


def delete_cached_modules(verbose: bool = False):
    modules_to_delete = []
    # Iterate over all the modules that are currently loaded
    for module_key, module_data in sys.modules.items():
        try:
            # Use the "inspect" library to get the moduleFilePath that the current module was loaded from
            module_file_path = inspect.getfile(module_data)

            if module_file_path.startswith(path_consts.FLOTTITOOLS_DIR):
                modules_to_delete.append(module_key)
        except:  # Some random module you can't inspect. It's not relevant to us, so doesn't matter
            pass

    for each_module in modules_to_delete:
        if verbose:
            print(f"Deleting - {each_module}")
        del (sys.modules[each_module])


def set_time_range_to_animation():
    ### TODO This is super slow on big files, try and speed it up
    anim_tl = cmds.ls(type="animCurveTL")
    anim_ta = cmds.ls(type="animCurveTA")
    anim_tu = cmds.ls(type="animCurveTU")
    anim_tt = cmds.ls(type="animCurveTT")

    first_key: float = 0.0
    last_key: float = 10.0

    set_time_range: bool = False

    for each_curve in anim_tl + anim_ta + anim_tu + anim_tt:
        keys = cmds.keyframe(each_curve, q=True, timeChange=True)
        if not keys:
            continue
        else:
            set_time_range = True

        if keys[-1] > last_key:
            last_key = keys[-1]

        if keys[0] < first_key:
            first_key = keys[0]

    if set_time_range:
        cmds.playbackOptions(minTime=first_key, maxTime=last_key)


def save_screenshot(file_path, width: int, height: int):
    current_frame = int(cmds.currentTime(q=True))

    cmds.playblast(frame=current_frame, viewer=False, format="image", compression="png", showOrnaments=False, completeFilename=file_path,
                   widthHeight=[width, height], percent=100)


def delete_display_layers(delete_only_empty: bool = True):
    display_layers = [each_layer for each_layer in cmds.ls(type="displayLayer")]

    default_layer = "defaultLayer"
    if default_layer in display_layers:
        display_layers.remove(default_layer)

    if not display_layers:
        return None

    if delete_only_empty:
        display_layers = [each_layer for each_layer in display_layers if not cmds.editDisplayLayerMembers(each_layer, q=True)]

    if display_layers:
        cmds.delete(display_layers)


def get_active_model_panel(short_name: bool = True) -> str:
    active_panel = omui.M3dView.active3dView()

    widget = active_panel.widget()
    active_panel_name = old_omui.MQtUtil.fullName(widget)

    if short_name:
        active_panel_name = active_panel_name.split("|")[-2]

    return active_panel_name


def get_active_panel_xray_joints() -> bool:
    active_panel = omui.M3dView.active3dView()
    return active_panel.xrayJoints()


def set_active_panel_xray_joints(xray_joints: bool):
    active_panel = get_active_model_panel()
    cmds.modelEditor(active_panel, e=True, jointXray=xray_joints)


def get_cursor_in_active_model_panel() -> bool:
    active_panel = omui.M3dView.active3dView()

    viewport_x, viewport_y = active_panel.getScreenPosition()
    viewport_width, viewport_height = active_panel.viewport()[2:]

    cursor_x = QtGui.QCursor.pos().x()
    cursor_y = QtGui.QCursor.pos().y()

    if viewport_x <= cursor_x <= (viewport_width + viewport_x) and viewport_y <= cursor_y <= (viewport_height + viewport_y):
        return True
    else:
        return False
