import maya.api.OpenMaya as om
import maya.cmds as cmds
import sys

from flottitools import path_consts


def load_flotti_tools():
    try:
        print("\nLoading Flotti Tools\n")
        import flottitools.menu as flotti_menu
        flotti_menu.FlottiToolsMenu()
        cmds.evalDeferred("flottitools.run_after_initialised()", lowestPriority=True)
        print("\nFlotti Tools Loaded\n")

    except Exception as e:
        msg = 'Flotti Tools failed to load. Try restarting Maya.'
        for arg in e.args:
            msg += str(arg)
        print(msg)
        raise RuntimeError(msg)


def run_after_initialised():
    # Add callbacks
    import flottitools.fix_paths as fix_paths
    import flottitools.utils.mayautils as mayautils
    mayautils.Callbacks.add(name="Check reference path",
                            callback=om.MSceneMessage.addCheckFileCallback(om.MSceneMessage.kBeforeCreateReferenceCheck,
                                                                           fix_paths._callback_on_check_file))
