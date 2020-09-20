import os

import maya.cmds as cmds
import maya.mel as mel


FLOTTI_SHELF_NAME = 'FlottiTools'


def onMayaDroppedPythonFile(*args):
    make_flottitools_shelf()


def make_flottitools_shelf():
    try:
        flottishelf_fullpath = cmds.shelfLayout(FLOTTI_SHELF_NAME, q=True, fullPathName=True)
        return flottishelf_fullpath
    except RuntimeError:
        flottishelf_shortname = mel.eval('addNewShelfTab \"{0}\";'.format(FLOTTI_SHELF_NAME))
        flottishelf_fullpath = cmds.shelfLayout(flottishelf_shortname, q=True, fullPathName=True)
        user_shelf_dir = os.path.abspath(cmds.internalVar(userShelfDir=True))
        save_shelf_path = os.path.join(user_shelf_dir, "shelf_{0}".format(FLOTTI_SHELF_NAME))
        cmds.saveShelf(flottishelf_fullpath, save_shelf_path)

        flottitools_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        button_cmd = 'import sys\n'
        button_cmd += 'if \'{0}\' not in sys.path: sys.path.append(\'{0}\')\n'.format(flottitools_dir)
        button_cmd += 'import flottitools.ui.averageweights_ui as avgwtsui\n'
        button_cmd += 'avgwtsui.average_weights()'

        icon_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'ui', 'averageweights_icon.png'))
        cmds.setParent(flottishelf_shortname)
        avgwts_shelfbutton = cmds.shelfButton(image1=icon_path, sourceType="python",
                                              label="Average Weights", annotation="Average Weights",
                                              command=button_cmd)