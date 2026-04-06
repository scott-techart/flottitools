import sys
import inspect

import maya.mel as mel
import pymel.core as pm

import flottitools.animation.anim_exporter_ui as anim_exporter_ui
import flottitools.fix_paths as fix_paths
import flottitools.environment.export_env as export_env
import flottitools.skinmesh.copyskin.copy_skin_ui as copyskin_ui
import flottitools.skinmesh.averageweights.averageweights_ui as avgwts_ui
import flottitools.validation.validator as validator


GMAIN_WINDOW_SINGLETON = None


def get_gmain_window():
    global GMAIN_WINDOW_SINGLETON
    if GMAIN_WINDOW_SINGLETON is None:
        try:
            GMAIN_WINDOW_SINGLETON = mel.eval('$temp1=$gMainWindow')
        except RuntimeError as e:
            print(e)
            print("Could not get Maya's main window. Likely, because Maya's UI has not loaded or is running in batch mode.")
    return GMAIN_WINDOW_SINGLETON


class FlottiToolsMenu:
    """
    Create Flotti Tools menu in the main Maya toolbar.

    On initialize FlottiToolsMenu parses flottitools.menu for any class that
      inherits from MenuItem and adds it the Flotti Tools menu.
    """
    top_menu_name = "flotti_tools_menu"
    top_menu_label = "Flotti Tools"

    top_menu = 'menu_flottitools'
    character = 'Character'
    environment = 'Environment'
    animation = 'Animation'
    modelling = 'Modelling'
    rigging = 'Rigging'
    skinning = 'Skinning'
    perforce = 'Perforce'
    preferences = 'Preferences'

    def __init__(self):
        try:
            pm.deleteUI(self.top_menu_name)
        except RuntimeError:
            pass

        self.menu_flottitools = pm.menu(self.top_menu_name, parent=get_gmain_window(), tearOff=True, label=self.top_menu_label)
        self.menu_label_to_menu = {}

        def make_sub_menu(label):
            menu_string = pm.menuItem(parent=self.menu_flottitools, label=label, subMenu=True, tearOff=True)
            self.menu_label_to_menu[label] = menu_string
            return menu_string

        menus_by_topic = [self.character, self.environment]
        [make_sub_menu(menu_label) for menu_label in menus_by_topic]
        pm.menuItem(parent=self.menu_flottitools, divider=True)
        menus_by_craft = [self.animation, self.rigging, self.skinning]
        [make_sub_menu(menu_label) for menu_label in menus_by_craft]
        pm.menuItem(parent=self.menu_flottitools, divider=True)
        menus_by_misc = [self.preferences]
        [make_sub_menu(menu_label) for menu_label in menus_by_misc]
        pm.menuItem(parent=self.menu_flottitools, divider=True)


        # Classes that inherit from MenuItem are added to menu_flotti_tools in the order that they appear in this file.
        menu_items = _get_menu_item_classes()
        for menu_item in menu_items:
            menu_item(self)


def _get_menu_item_classes():
    """Get list of classes in this module that inherit from MenuItem.
    MenuItems are returned in the order that they are defined in this module.
    """
    source_lines = inspect.getsourcelines(sys.modules[__name__])[0]
    indices_and_classes = []
    for menu_item_name, menu_item in _get_menu_item_names_and_classes_alphabetical():
        item_base_class_name = menu_item.__bases__[0].__name__
        class_def_as_string = 'class {0}({1}):\n'.format(menu_item_name, item_base_class_name)
        line_index = source_lines.index(class_def_as_string)
        indices_and_classes.append((line_index, menu_item))
    indices_and_classes.sort()
    _, menu_items = zip(*indices_and_classes)
    return menu_items


def _get_menu_item_names_and_classes_alphabetical():
    """Get list of classes in this module that inherit from MenuItem.
    MenuItems are returned in alphabetical order.
    """
    def is_menu_item_class(x):
        menu_item_classes = [MenuItem, Divider]
        return any([inspect.isclass(x) and (issubclass(x, y) and x is not y) for y in menu_item_classes])
    return inspect.getmembers(sys.modules[__name__], is_menu_item_class)


class MenuItem:
    parent_menu = None
    label = None
    image = None

    def __init__(self, flotti_menu_instance):
        parent = flotti_menu_instance.menu_label_to_menu.get(self.parent_menu, flotti_menu_instance.menu_flottitools)
        menu_item = pm.menuItem(parent=parent, label=self.label, command=self.command)
        if self.image:
            menu_item.setImage(self.image)

    def command(self):
        msg = 'Menu item {} has no command defined. A tech artist probably forgot to write it.'.format(self.label)
        raise NotImplementedError(msg)


class Divider:
    parent_menu = None

    def __init__(self, flotti_menu_instance):
        parent = flotti_menu_instance.menu_label_to_menu.get(self.parent_menu, flotti_menu_instance.menu_flottitools)
        pm.menuItem(parent=parent, divider=True)


# Root menu items  -- start
class BatchToolMenuItem(MenuItem):
    parent_menu = FlottiToolsMenu.top_menu
    label = "Batch Tool.."
    
    def command(self, *args):
        import flottitools.batchtool.batch_tool_ui as batch_tool_ui
        batch_tool_ui.batcher_launch()

class ValidatorMenuItem(MenuItem):
    parent_menu = FlottiToolsMenu.top_menu
    label = "Validator.."

    def command(self, *args):
        validator.validator_launch()


class FixPathsMenuItem(MenuItem):
    parent_menu = FlottiToolsMenu.top_menu
    label = "Fix Paths"

    def command(self, *args):
        fix_paths.fix_paths()
		
# Root menu items  -- end


# Character menu items  -- start
class CharacterExporterMenuItem(MenuItem):
    parent_menu = FlottiToolsMenu.character
    label = "Character Exporter..."

    def command(self, *args):
        import flottitools.character.character_exporter_ui as char_exporter
        char_exporter.character_exporter_launch()

# Character menu items  -- end


# Environment menu items  -- start
class ExportEnvironmentMeshesMenuItem(MenuItem):
    parent_menu = FlottiToolsMenu.environment
    label = "Export Selected Meshes"

    def command(self, *args):
        export_env.export_selected_meshes_with_prompt()

# Environment menu items  -- end


# Animation menu items -- start
class AnimExporterMenuItem(MenuItem):
    parent_menu = FlottiToolsMenu.animation
    label = "Animation Exporter.."

    def command(self, *args):
        anim_exporter_ui.anim_exporter_launch()

# Animation menu items -- end


# Rigging menu items -- start
class OrientJointsMenuItem(MenuItem):
    parent_menu = FlottiToolsMenu.rigging
    label = "Orient Joints.."

    def command(self, *args):
        import flottitools.rigging.orient_joints.orient_joints_ui as orient_joints_ui
        orient_joints_ui.orient_joints_launch()

# Rigging menu items -- end


# Skinning tools menu items  -- start
class CopySkinMenuItem(MenuItem):
    parent_menu = FlottiToolsMenu.skinning
    label = "Copy Skin Weights..."

    def command(self, *args):
        copyskin_ui.copy_skin_launch()


class AverageWeightsMenuItem(MenuItem):
    parent_menu = FlottiToolsMenu.skinning
    label = "Average Weights..."

    def command(self, *args):
        avgwts_ui.average_weights()


class CreateFallbackSKWMeshMenuItem(MenuItem):
    parent_menu = FlottiToolsMenu.skinning
    label = "Create Merged Skinned Mesh"

    def command(self, *args):
        import flottitools.utils.skinutils as skinutils
        skinned_meshes = skinutils.get_skinned_meshes_from_selection()
        if not skinned_meshes:
            skinned_meshes = skinutils.get_skinned_meshes_from_scene()
        if not skinned_meshes:
            pm.error('Select one or more skinned meshes to be duplicated and merged into a merged skinned mesh.')
            return
        print(skinutils.combine_skinned_meshes(skinned_meshes, new_name=skinutils.FALLBACK_MESH_NAME, do_duplicate=True))
# Skinning tools menu items  -- end


# Preferences menu items  -- start
class UninstallMenuItem(MenuItem):
    parent_menu = FlottiToolsMenu.preferences
    label = "Uninstall"

    def command(self, *args):
        import flottitools.drag_to_maya_scene_setup as flotti_setup
        flotti_setup.remove_flotti_from_userprefs()
        flotti_setup.remove_menu()
# Preferences menu items  -- end