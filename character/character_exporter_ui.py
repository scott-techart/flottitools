import os
from pathlib import Path

import flottitools.path_consts as path_consts
import flottitools.ui as flotti_ui
import flottitools.utils.ioutils as ioutils
import flottitools.utils.pathutils as pathutils

import flottitools.character.character_exporter as char_exporter

QtGui = flotti_ui.QtGui

FBX_FILE_EXTENSION = '.fbx'
MAYA_FILE_EXTENSIONS = ['.ma', '.mb']
SKMESH_PREFIX = 'SK_'
SKEL_FILE_PREFIX = 'SKEL_'
SKINWEIGHTS_FILE_PREFIX = 'SKW_'

CHAR_EXPORTER_UI = None


def character_exporter_launch():
    global CHAR_EXPORTER_UI
    if CHAR_EXPORTER_UI:
        CHAR_EXPORTER_UI.deleteLater()
    CHAR_EXPORTER_UI = CharacterExporterMayaWindow()
    CHAR_EXPORTER_UI.show()


class CharacterExporterMayaWindow(flotti_ui.FlottiMayaWindowDesignerUI):
    window_title = "Character Exporter"
    dir_path = os.path.abspath(os.path.dirname(__file__))
    ui_designer_file_path = os.path.abspath(os.path.join(dir_path, 'character_exporter.ui'))

    def __init__(self):
        super(CharacterExporterMayaWindow, self).__init__()
        self.scene_path = None
        self.export_file_path = None
        self.skeleton_path = None
        self.skin_weights_path = None
        
        self.ui.debug_vis_widget.setVisible(False)
        
        self._init_button_images()
        self._init_ui_signals()
        self._refresh_scene_path()

    def _init_button_images(self):
        refresh_icon = QtGui.QPixmap(os.path.join(path_consts.ICONS_DIR, 'refresh.svg'))
        self.ui.current_file_refresh_button.setIcon(refresh_icon)
        self.ui.steps_skel_refresh_button.setIcon(refresh_icon)
        self.ui.steps_skw_refresh_button.setIcon(refresh_icon)
        self.ui.export_refresh_button.setIcon(refresh_icon)
        browse_icon = QtGui.QPixmap(os.path.join(path_consts.ICONS_DIR, 'browse.svg'))
        self.ui.steps_skel_browse_button.setIcon(browse_icon)
        self.ui.steps_skw_browse_button.setIcon(browse_icon)
        self.ui.export_browse_button.setIcon(browse_icon)
    def _init_ui_signals(self):
        self.ui.current_file_refresh_button.clicked.connect(self._refresh_scene_path)
        self.ui.steps_skel_refresh_button.clicked.connect(self._refresh_skel_path)
        self.ui.steps_skw_refresh_button.clicked.connect(self._refresh_skin_weights_path)
        self.ui.export_refresh_button.clicked.connect(self._refresh_export_path)
        self.ui.steps_skel_browse_button.clicked.connect(self.browse_skeleton_file)
        self.ui.steps_skw_browse_button.clicked.connect(self.browse_skin_weights_file)
        self.ui.export_browse_button.clicked.connect(self.browse_export_fbx_file)
        self.ui.steps_skel_lineedit.textEdited.connect(self._steps_skel_edited)
        self.ui.steps_skw_lineedit.textEdited.connect(self._steps_skinweights_edited)
        self.ui.export_path_lineedit.textEdited.connect(self._export_line_edited)
        self.ui.export_button.clicked.connect(self.export)

    def export(self):
        if not self.export_file_path:
            raise AssertionError('Aborting Export. Invalid export file path.')
        char_exporter.export_sk_meshes_from_scene(self.export_file_path, self.skeleton_path, self.skin_weights_path)
    def _refresh_scene_path(self):
        scene_path = pathutils.get_scene_path()
        if not scene_path:
            self.scene_path = None
            self.ui.current_file_line_edit.setText('')
            self.ui.current_file_line_edit.setStyleSheet(flotti_ui.COLOR_BG_CS_STRING_WARNING)
        else:
            self.scene_path = scene_path
            self.ui.current_file_line_edit.setText(os.path.normpath(scene_path))
            self.ui.current_file_line_edit.setStyleSheet("")
        self._update_based_on_scene_path()

    def _update_based_on_scene_path(self):
        if not self.scene_path:
            return
        self._refresh_skel_path()
        self._refresh_skin_weights_path()
        self._refresh_export_path()
    
    def _refresh_skel_path(self):
        skel_path = char_exporter.get_skeleton_path_from_static_mesh_path(self.scene_path)
        self.ui.steps_skel_lineedit.setText(os.path.normpath(skel_path))
        self._steps_skel_edited()
        
    def _refresh_skin_weights_path(self):
        skw_path = char_exporter.get_skin_weights_path_from_static_mesh_path(self.scene_path)
        self.ui.steps_skw_lineedit.setText(os.path.normpath(skw_path))
        self._steps_skinweights_edited()
    
    def _refresh_export_path(self):
        export_path = char_exporter.get_sk_mesh_export_path(self.scene_path)
        self.ui.export_path_lineedit.setText(os.path.normpath(export_path))
        self._export_line_edited()

    def _steps_skel_edited(self):
        self.skeleton_path = self._path_line_edit(self.ui.steps_skel_lineedit, SKEL_FILE_PREFIX, MAYA_FILE_EXTENSIONS)

    def _steps_skinweights_edited(self):
        self.skin_weights_path = self._path_line_edit(self.ui.steps_skw_lineedit, SKINWEIGHTS_FILE_PREFIX, MAYA_FILE_EXTENSIONS)
    
    def _export_line_edited(self):
        text = self.ui.export_path_lineedit.text()
        path = Path(text)
        path = path.with_suffix(FBX_FILE_EXTENSION)
        if path.suffix.lower() != FBX_FILE_EXTENSION:
            self.export_file_path = None
            self.ui.export_button.setEnabled(False)
            self.ui.export_path_lineedit.setStyleSheet("")
            return
        if not path.name.lower().startswith(SKMESH_PREFIX.lower()) or not path.is_relative_to(path_consts.FLOTTITOOLS_DIR):
            self.export_file_path = None
            self.ui.export_button.setEnabled(False)
            self.ui.export_path_lineedit.setStyleSheet(flotti_ui.COLOR_BG_CS_STRING_WARNING)
            self.ui.export_button.setEnabled(True)
            return
        self.export_file_path = path
        new_path_text = os.path.normpath(path)
        if new_path_text != text:
            self.ui.export_path_lineedit.setText(new_path_text)
        self.ui.export_button.setEnabled(True)
        self.ui.export_path_lineedit.setStyleSheet(flotti_ui.COLOR_BG_CS_STRING_PASS)
    
    def browse_skeleton_file(self):
        self._browse_maya_file(self.ui.steps_skel_lineedit)
        self._steps_skel_edited()
    
    def browse_skin_weights_file(self):
        self._browse_maya_file(self.ui.steps_skw_lineedit)
        self._steps_skinweights_edited()
    
    def browse_export_fbx_file(self):
        dir_path = None
        if self.scene_path:
            dir_path = self.scene_path.parents[1]
        fbx_file_path = Path(ioutils.get_path_from_dialogue(file_mode=0, file_filter='Fbx (*.fbx *.FBX)', start_dir=dir_path))
        self.ui.export_path_lineedit.setText(os.path.normpath(fbx_file_path))
        self._export_line_edited()
    def _browse_maya_file(self, line_edit):
        dir_path = None
        if self.scene_path:
            dir_path = self.scene_path.parent
        maya_filters = "Maya Files (*.ma *.mb);;Maya ASCII (*.ma);;Maya Binary (*.mb)"
        maya_file_path = ioutils.get_path_from_dialogue(file_mode=1, file_filter=maya_filters, start_dir=dir_path)
        if not maya_file_path:
            return
        maya_file_path = Path(maya_file_path)
        line_edit.setText(os.path.normpath(maya_file_path))
    
    @staticmethod
    def _path_line_edit(path_line_edit, name_prefix, file_extensions):
        text = path_line_edit.text()
        path = Path(text)
        file_extensions = [f.lower() for f in file_extensions]
        if path.suffix.lower() not in file_extensions:
            path_line_edit.setStyleSheet("")
            return
        if not path.name.lower().startswith(name_prefix.lower()):
            path_line_edit.setStyleSheet("")
            return
        CharacterExporterMayaWindow._do_path_line_edit_background_color(path, path_line_edit)
        return path

    @staticmethod
    def _do_path_line_edit_background_color(path, line_edit):
        if path.exists():
            line_edit.setText(os.path.normpath(path))
            line_edit.setStyleSheet("background-color: green")
        else:
            line_edit.setStyleSheet("")