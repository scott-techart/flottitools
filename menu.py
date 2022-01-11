import sys
import inspect

import maya.mel as mel
import pymel.core as pm

import flottitools.skintools.transferskin.copy_skin_ui as copyskin_ui
import flottitools.ui.averageweights_ui as avgwts_ui
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
    modelling = 'menu_modelling'
    rigging = 'menu_rigging'
    developer = 'menu_developer'

    def __init__(self):
        if pm.menu(self.top_menu_name, exists=True):
            pm.deleteUI(self.top_menu_name)

        self.menu_flottitools = pm.menu(self.top_menu_name, parent=get_gmain_window(), tearOff=True, label=self.top_menu_label)

        def make_sub_menu(label):
            return pm.menuItem(parent=self.menu_flottitools, label=label, subMenu=True, tearOff=True)
        self.menu_rigging = make_sub_menu("Rigging")

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

    def __init__(self, flotti_menu_instance):
        self.label = self.label
        parent = getattr(flotti_menu_instance, self.parent_menu)
        pm.menuItem(parent=parent, label=self.label, command=self.command)

    def command(self):
        msg = 'Menu item {} has no command defined. A tech artist probably forgot to write it.'.format(self.label)
        raise NotImplementedError(msg)


class Divider:
    parent_menu = None

    def __init__(self, flotti_menu_instance):
        parent = getattr(flotti_menu_instance, self.parent_menu)
        pm.menuItem(parent=parent, divider=True)


# Root menu items  -- start

class ValidatorMenuItem(MenuItem):
    parent_menu = FlottiToolsMenu.top_menu
    label = "Validator.."

    def command(self, *args):
        validator.validator_launch()


class UninstallMenuItem(MenuItem):
    parent_menu = FlottiToolsMenu.top_menu
    label = "Uninstall"

    def command(self, *args):
        import flottitools.drag_to_maya_scene_setup as foo
        foo.remove_flotti_from_userprefs()
        foo.remove_menu()

# Root menu items  -- end


# Rigging tools menu items  -- start
class CopySkinMenuItem(MenuItem):
    parent_menu = FlottiToolsMenu.rigging
    label = "Copy Skin Weights..."

    def command(self, *args):
        copyskin_ui.copy_skin_launch()


class AverageWeightsMenuItem(MenuItem):
    parent_menu = FlottiToolsMenu.rigging
    label = "Average Weights..."

    def command(self, *args):
        avgwts_ui.average_weights()

# Rigging tools menu items  -- end
