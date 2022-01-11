import os
import stat
import sys

import maya.cmds as cmds
import maya.mel as mel
import pymel.core as pm

FLOTTI_ARTTOOLS_VERSION = 'v1.0'
FLOTTI_DIR = os.path.dirname(os.path.dirname(__file__))
FLOTTI_SHELF_NAME = 'FlottiTools'
FLOTTI_END_TAG = '# <<< End FlottiTools startup'
FLOTTI_START_TAG = '# >>> Start FlottiTools startup'
FLOTTI_VERSION_IDENTIFIER = ' :: '


def onMayaDroppedPythonFile(*args):
    setup_flottitools()


def setup_flottitools():
    make_flottitools_shelf()
    usersetup_path = get_maya_usersetup_path()
    usersetup_lines = get_usersetup_lines()
    inject_flottisetup_to_maya_usersetup(usersetup_path, usersetup_lines)

    if FLOTTI_DIR not in sys.path:
        sys.path.append(r'D:/git_repos')
    remove_menu()
    import maya.utils as mayautils
    mayautils.executeDeferred('import flottitools; flottitools.load_flotti_tools()')


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

def get_maya_usersetup_path():
    scripts_dir = os.path.abspath(cmds.internalVar(userScriptDir=True))
    usersetup_path = os.path.join(scripts_dir, 'userSetup.py')
    return usersetup_path


def get_usersetup_lines():
    flottitools_dir = os.path.dirname(os.path.dirname(__file__))
    lines = ['import sys\n',
             'sys.path.append(r\'{0}\')\n\n'.format(flottitools_dir),
             'import flottitools\n'
             'import maya.utils as mayautils\n',
             'mayautils.executeDeferred(\'flottitools.load_flotti_tools()\')\n']
    return lines


def inject_flottisetup_to_maya_usersetup(usersetup_path, flotti_setup_lines=None, version=FLOTTI_ARTTOOLS_VERSION,
                                         start_tag=None, end_tag=None):
    flotti_setup_lines = flotti_setup_lines or []
    start_tag = start_tag or FLOTTI_START_TAG
    end_tag = end_tag or FLOTTI_END_TAG
    if not os.path.exists(usersetup_path):
        open(usersetup_path, 'w').close()
    # set usersetup file to writeable in case it's read only
    os.chmod(usersetup_path, stat.S_IWRITE)
    with open(usersetup_path, 'r+') as usersetup_file:
        usersetup_lines = usersetup_file.readlines()
        new_lines = _update_flotti_setup_lines(usersetup_lines, flotti_setup_lines, start_tag, end_tag, version)

    if new_lines != usersetup_lines:
        with open(usersetup_path, 'w') as usersetup_file:
            usersetup_file.writelines(new_lines)


def _update_flotti_setup_lines(current_lines, flotti_setup_lines, start_tag, end_tag, version,
                               version_identifier=FLOTTI_VERSION_IDENTIFIER):
    new_start_line = _get_flotti_setup_line(start_tag, version_identifier, version)
    new_end_line = _get_flotti_setup_line(end_tag, version_identifier, version)

    start_index, end_index = _get_flotti_start_and_end_indices(current_lines, start_tag, end_tag)
    if start_index is None or end_index is None:
        new_lines = current_lines[:]
        # new_lines.extend(['\n', '\n', '\n'])
        new_lines.append(new_start_line)
        new_lines.extend(flotti_setup_lines)
        new_lines.append(new_end_line)
        return new_lines

    current_start_version = _get_flotti_version_from_index(current_lines, start_index, version_identifier)
    current_end_version = _get_flotti_version_from_index(current_lines, end_index, version_identifier)
    if version == current_start_version and version == current_end_version:
        return current_lines

    before_flottisetup_chunk = current_lines[:start_index]
    after_flottisetup_chunk = current_lines[end_index + 1:]

    new_flottisetup_lines = [new_start_line]
    new_flottisetup_lines.extend(flotti_setup_lines)
    new_flottisetup_lines.append(new_end_line)

    new_lines = before_flottisetup_chunk + new_flottisetup_lines + after_flottisetup_chunk

    return new_lines


def _get_flotti_setup_line(tag, version_identifier, version):
    return ''.join([tag, version_identifier, version, '\n'])


def _get_flotti_start_and_end_indices(lines_to_parse, start_tag, end_tag):
    start_line_index = _get_index_startswith_value(lines_to_parse, start_tag)
    end_line_index = _get_index_startswith_value(lines_to_parse, end_tag)
    return start_line_index, end_line_index


def _get_index_startswith_value(list_to_parse, value):
    index = None
    for i, existing_line in enumerate(list_to_parse):
        if existing_line.startswith(value):
            index = i
    return index


def _get_flotti_version_from_index(lines_to_parse, line_index, version_identifier):
    line_split = lines_to_parse[line_index].rsplit(version_identifier, 1)
    version = None
    if len(line_split) > 1:
        version = line_split[-1].strip('\n')
    return version


def remove_flotti_from_userprefs():
    usersetup_path = get_maya_usersetup_path()
    with open(usersetup_path, 'r+') as usersetup_file:
        usersetup_lines = usersetup_file.readlines()
        start_index, end_index = _get_flotti_start_and_end_indices(usersetup_lines, FLOTTI_START_TAG, FLOTTI_END_TAG)
        before_flottisetup_chunk = usersetup_lines[:start_index]
        after_flottisetup_chunk = usersetup_lines[end_index + 1:]
        new_lines = before_flottisetup_chunk + after_flottisetup_chunk

    if new_lines != usersetup_lines:
        with open(usersetup_path, 'w') as usersetup_file:
            usersetup_file.writelines(new_lines)


def remove_menu():
    import flottitools.menu as flotti_menu
    if pm.menu(flotti_menu.FlottiToolsMenu.top_menu_name, exists=True):
        pm.deleteUI(flotti_menu.FlottiToolsMenu.top_menu_name)
