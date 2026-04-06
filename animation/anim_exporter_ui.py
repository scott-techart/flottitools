from contextlib import contextmanager
import json
import os
from pathlib import Path

import pymel.core as pm

import flottitools.path_consts as path_consts
import flottitools.ui as flotti_ui
import flottitools.utils.ioutils as ioutils
import flottitools.utils.pathutils as pathutils

import flottitools.animation.anim_exporter as anim_exporter

QtCore = flotti_ui.QtCore
QtGui = flotti_ui.QtGui
QtUiTools = flotti_ui.QtUiTools

ANIM_EXPORTER_UI = None


def anim_exporter_launch():
    global ANIM_EXPORTER_UI
    if ANIM_EXPORTER_UI:
        ANIM_EXPORTER_UI.deleteLater()
    ANIM_EXPORTER_UI = AnimExporterMayaWindow()
    ANIM_EXPORTER_UI.show()


class AnimExporterMayaWindow(flotti_ui.FlottiWindowDesignerUI):
    window_title = "Animation Exporter"
    dir_path = os.path.abspath(os.path.dirname(__file__))
    ui_designer_file_path = os.path.abspath(os.path.join(dir_path, 'anim_exporter.ui'))

    def __init__(self):
        super(AnimExporterMayaWindow, self).__init__()
        self.metadata_path = None
        self.metadata = None
        self.clips = []
        self.auto_save = True
        self.relative_root = Path(path_consts.FLOTTITOOLS_DIR)
        self.clip_color_alternator = False

        self.ui.clips_widgets_vlayout.setAlignment(QtCore.Qt.AlignTop)
        self._init_connections()
        self._init_icons()
        self.auto_save_toggled()
        self.ui.rel_root_lineEdit.setText(os.path.normpath(self.relative_root))
        self.metadata_path_refresh()
        self._update_ui_elements_based_on_metadata_path()

    def _init_connections(self):
        self.ui.metadata_path_lineedit.returnPressed.connect(self.enter_pressed)
        self.ui.metadata_path_lineedit.textEdited.connect(self.metadata_path_edited)
        self.ui.metadata_autosave_checkbox.toggled.connect(self.auto_save_toggled)
        self.ui.metadata_save_button.clicked.connect(self.save)
        self.ui.metadata_open_button.clicked.connect(self.open)
        self.ui.metadata_refresh_button.clicked.connect(self.metadata_path_refresh)
        self.ui.metadata_saveas_button.clicked.connect(self.save_as)
        self.ui.select_all_checkbox.toggled.connect(self._select_all_checkbox_toggled)
        self.ui.clips_subtract_button.clicked.connect(self.delete_last_clip)
        self.ui.clips_add_button.clicked.connect(self.add_button_clicked)
        self.ui.clips_deleteselected_button.clicked.connect(self.delete_selected_clips)
        self.ui.export_selected_button.clicked.connect(self.export_selected)

    def _init_icons(self):
        refresh_icon = QtGui.QPixmap(os.path.join(path_consts.ICONS_DIR, 'refresh.svg'))
        self.ui.metadata_refresh_button.setIcon(refresh_icon)
        browse_icon = QtGui.QPixmap(os.path.join(path_consts.ICONS_DIR, 'browse.svg'))
        self.ui.metadata_open_button.setIcon(browse_icon)

    def auto_save_toggled(self):
        self.auto_save = bool(self.ui.metadata_autosave_checkbox.isChecked())
        self.ui.metadata_save_button.setEnabled(not self.auto_save)

    def save(self):
        self._save(self.metadata_path)

    def _save(self, metadata_path):
        metadata_path = sanitize_metadata_path_strong(metadata_path)
        abs_metadata_path = os.path.abspath(metadata_path)
        clips_data = self.get_all_clips_data()
        with open(abs_metadata_path, 'w', encoding='utf-8') as f:
            json.dump(clips_data, f, ensure_ascii=False, indent=4)

    def open(self):
        start_dir = anim_exporter.get_metadata_start_dir()
        dest_path = get_metadata_path_from_open_dialogue(start_dir=start_dir)
        if not dest_path:
            return
        dest_path = os.path.abspath(dest_path)
        self.ui.metadata_path_lineedit.setText(dest_path)
        self._update_ui_elements_based_on_metadata_path()
        self.metadata_path_edited()

    def save_as(self):
        dest_path = get_metadata_path_from_save_as_dialogue()
        if not dest_path:
            return
        self._save(dest_path)
        dest_path = os.path.abspath(dest_path)
        self.ui.metadata_path_lineedit.setText(dest_path)
        self.metadata_path_edited()
        self._update_ui_elements_based_on_metadata_path()

    def get_all_clips_data(self):
        datas = [x.get_data() for x in self.clips]
        return datas

    def load_clip_data(self):
        if self.metadata_path.is_file():
            abs_metadata_path = os.path.abspath(self.metadata_path)
            with open(abs_metadata_path) as f:
                self.metadata = json.load(f)
            self.clips = []
            self.clear_layout(self.ui.clips_widgets_vlayout)
            for each in self.metadata:
                self.add_clip(clip_dict=each)

    def metadata_path_edited(self):
        self.metadata_path = None
        metadata_path_input = self.ui.metadata_path_lineedit.text()
        metadata_path = Path(metadata_path_input)
        if is_valid_metadata_path(metadata_path):
            if metadata_path.is_file():
                # .is_file() checks if file exists
                self.metadata_path = metadata_path
                self.load_clip_data()
            else:
                parent_dir = metadata_path.parent
                if parent_dir.is_dir() and parent_dir != Path('.'):
                    self.metadata_path = metadata_path
                    self.clear_layout(self.ui.clips_widgets_vlayout)
                    self.clips = []
        self._update_ui_elements_based_on_metadata_path()
        return self.metadata_path

    def enter_pressed(self):
        try:
            metadata_path_input = self.ui.metadata_path_lineedit.text()
            metadata_path = Path(metadata_path_input)
            self.metadata_path = sanitize_metadata_path_strong(metadata_path)
            if self.metadata_path is None:
                return
            self.ui.metadata_path_lineedit.setText(str(self.metadata_path))
            if self.metadata_path.is_file():
                self.load_clip_data()
            else:
                self.save()
        except ValueError:
            pass
        self._update_ui_elements_based_on_metadata_path()

    def metadata_path_refresh(self):
        metadata_path = anim_exporter.get_metadata_default_path()
        if metadata_path:
            # metadata_name = path.name.replace(anim_exporter.ANIM_SEQUENCE_PREFIX.lower(), anim_exporter.METADATA_PREFIX)
            # metadata_name = metadata_name.replace(anim_exporter.ANIM_SEQUENCE_PREFIX, anim_exporter.METADATA_PREFIX)
            # metadata_path = path.parent.joinpath(metadata_name)
            self.ui.metadata_path_lineedit.setText(os.path.normpath(metadata_path))
            self.metadata_path_edited()

    def _update_ui_elements_based_on_metadata_path(self):
        if self.metadata_path:
            line_edit_color = flotti_ui.COLOR_BG_CS_STRING_WARNING
            if self.metadata_path.is_file():
                line_edit_color = flotti_ui.COLOR_BG_CS_STRING_PASS
            self.ui.metadata_autosave_checkbox.setEnabled(True)
            self.ui.metadata_path_lineedit.setStyleSheet(line_edit_color)
            self.ui.metadata_autosave_checkbox.setEnabled(True)
            if self.ui.metadata_autosave_checkbox.isChecked():
                self.auto_save = True
            else:
                self.ui.metadata_save_button.setEnabled(True)
        else:
            self.ui.metadata_autosave_checkbox.setEnabled(False)
            self.ui.metadata_path_lineedit.setStyleSheet("")
            self.ui.metadata_autosave_checkbox.setEnabled(False)
            self.auto_save = False
            self.ui.metadata_save_button.setEnabled(False)
            self.clear_layout(self.ui.clips_widgets_vlayout)
            self.clips = []

    def add_button_clicked(self):
        self.add_clip(clip_dict=None)
        if self.auto_save:
            self.save()

    def add_clip(self, clip_dict=None):
        if not clip_dict:
            scene_path = pathutils.get_scene_path()
            default_clip_name = scene_path.stem
            default_file_name = scene_path.with_suffix(anim_exporter.EXTENSION_FBX).name
            default_dir = scene_path.parents[1]
            default_clip_export_path = default_dir.joinpath(default_file_name)
            clip_dict = {anim_exporter.CLIP_NAME: default_clip_name,
                         anim_exporter.CLIP_EXPORT_PATH: os.path.normpath(default_clip_export_path)}
        
        color = (0, 149, 182, 20)
        if self.clip_color_alternator:
            color = (40, 60, 70, 140)
            self.clip_color_alternator = False
        else:
            self.clip_color_alternator = True
        clip = AnimClipWidget(clip_dict=clip_dict, exporter_instance=self, background_color=color)
        self.clips.append(clip)
        self.ui.clips_widgets_vlayout.addWidget(clip.ui)

    def delete_clip(self, index):
        widget = self.ui.clips_widgets_vlayout.itemAt(index).widget()
        widget.setParent(None)
        widget.deleteLater()
        self.clips.pop(index)

    def delete_last_clip(self):
        self.delete_clip(len(self.clips)-1)
        if self.auto_save:
            self.save()

    def delete_selected_clips(self):
        indices = [i for i, clip in enumerate(self.clips) if clip.is_checked()]
        indices.reverse()
        for index in indices:
            self.delete_clip(index)
        if self.auto_save:
            self.save()

    def export_all_clips(self):
        for clip in self.clips:
            self._export_clip(clip)

    def export_selected(self):
        indices = [i for i, clip in enumerate(self.clips) if clip.is_checked()]
        for index in indices:
            self._export_clip(self.clips[index])

    def _export_clip(self, clip):
        result = clip.export()
        return result

    def _select_all_checkbox_toggled(self):
        if self.ui.select_all_checkbox.isChecked():
            [clip.check() for clip in self.clips]
        else:
            [clip.uncheck() for clip in self.clips]

class AnimClipWidget:
    def __init__(self, clip_dict=None, parent=None, exporter_instance=None, background_color=None):
        dir_path = os.path.abspath(os.path.dirname(__file__))
        ui_designer_file_path = os.path.abspath(os.path.join(dir_path, 'anim_clip_widget.ui'))
        self.ui = flotti_ui.load_qt_ui_from_path(ui_designer_file_path)
        if background_color:
            self.ui.setAutoFillBackground(True)
            palette = self.ui.palette()
            palette.setColor(QtGui.QPalette.Window, QtGui.QColor(*background_color))
            self.ui.setPalette(palette)

        self.exporter_instance = exporter_instance
        self.auto_save = True

        self.clip_dict_init = clip_dict
        self.clip_name = None
        self.frame_start = None
        self.frame_end = None
        self.export_path = None
        self.references_current_scene = pm.listReferences()
        self.current_reference = None

        self.refresh_rig_references()

        self._init_icons()
        self._init_data()
        self._init_connections()

    def _init_data(self):
        self.load_clip_dict(self.clip_dict_init)

    def load_clip_dict(self, clip_dict):
        with self.auto_save_disabled():
            self.ui.clipname_lineedit.setText(str(clip_dict.get(anim_exporter.CLIP_NAME, anim_exporter.CLIP_DEFAULT_NAME)))
            self.frame_start = int(clip_dict.get(anim_exporter.CLIP_FRAME_START, 0))
            self.frame_end = int(clip_dict.get(anim_exporter.CLIP_FRAME_END, 10))
            self.ui.frame_start_spinbox.setValue(self.frame_start)
            self.ui.frame_end_spinbox.setValue(self.frame_end)
            path_string = str(clip_dict.get(anim_exporter.CLIP_EXPORT_PATH, ''))
            self.export_path = None
            self.ui.export_lineedit.setText('')
            if path_string:
                export_path = Path(path_string)
                _, relative_path = self.get_rel_path_parts_and_update_ui(export_path)
                if relative_path:
                    self.export_path = self.exporter_instance.relative_root.joinpath(relative_path)
                    self.ui.export_lineedit.setText(os.path.normpath(self.export_path))
            rig_ref_ns = clip_dict.get(anim_exporter.CLIP_RIG_NAMESPACE, '')
            if rig_ref_ns:
                self.current_reference = anim_exporter.get_matching_reference(rig_ref_ns, self.references_current_scene)
                if self.current_reference:
                    self.ui.rigref_combobox.setCurrentIndex(self.references_current_scene.index(self.current_reference))
                else:
                    self.references_current_scene.append(anim_exporter.RIG_REF_INVALID)
                    self.ui.rigref_combobox.addItem('Invalid - No matching rig referenced in scene!')
                    self.ui.rigref_combobox.setCurrentIndex(len(self.references_current_scene) - 1)

    def _init_connections(self):
        self.ui.clipname_lineedit.textEdited.connect(self.clip_name_edited)
        self.ui.frame_start_spinbox.valueChanged.connect(self._auto_save_default_method)
        self.ui.frame_end_spinbox.valueChanged.connect(self._auto_save_default_method)
        self.ui.frame_set_button.clicked.connect(self.frame_range_set_from_scene)
        self.ui.frame_jump_button.clicked.connect(self.frame_range_browse_to)
        self.ui.rigref_combobox.currentIndexChanged.connect(self._auto_save_default_method)
        # self.ui.rigref_refresh_button.clicked.connect(self.refresh_rig_references)
        self.ui.export_lineedit.textEdited.connect(self.export_path_edited)
        self.ui.export_button.clicked.connect(self.export)
        self.ui.export_browse_button.clicked.connect(self.export_path_browse)

    def _init_icons(self):
        # refresh_icon = QtGui.QPixmap(os.path.join(path_consts.ICONS_DIR, 'refresh.svg'))
        browse_icon = QtGui.QPixmap(os.path.join(path_consts.ICONS_DIR, 'browse.svg'))
        frame_browse_icon = QtGui.QPixmap(os.path.join(path_consts.ICONS_DIR, 'range_browse.svg'))
        frame_set_icon = QtGui.QPixmap(os.path.join(path_consts.ICONS_DIR, 'range_set.svg'))
        # self.ui.export_default_button.setIcon(refresh_icon)
        self.ui.export_browse_button.setIcon(browse_icon)
        self.ui.frame_set_button.setIcon(frame_set_icon)
        self.ui.frame_jump_button.setIcon(frame_browse_icon)
        # self.ui.rigref_refresh_button.setIcon(refresh_icon)

    def _auto_save_default_method(self):
        self.current_reference = self.references_current_scene[self.ui.rigref_combobox.currentIndex()]
        if self.exporter_instance.auto_save:
            if self.auto_save:
                self.exporter_instance.save()



    def is_checked(self):
        return self.ui.checked_checkbox.isChecked()

    def check(self):
        self.ui.checked_checkbox.setChecked(True)

    def uncheck(self):
        self.ui.checked_checkbox.setChecked(False)

    def get_data(self):
        self.clip_name = self.ui.clipname_lineedit.text()
        self.frame_start = int(self.ui.frame_start_spinbox.value())
        self.frame_end = int(self.ui.frame_end_spinbox.value())
        self.export_path = self.ui.export_lineedit.text()
        data_dict = {anim_exporter.CLIP_NAME: self.clip_name, anim_exporter.CLIP_FRAME_START: self.frame_start, 
                     anim_exporter.CLIP_FRAME_END: self.frame_end, anim_exporter.CLIP_EXPORT_PATH: self.export_path, 
                     anim_exporter.CLIP_RIG_NAMESPACE: self.current_reference.namespace}
        return data_dict

    def refresh_rig_references(self):
        with self.auto_save_disabled():
            self.ui.rigref_combobox.clear()
            self.references_current_scene = pm.listReferences(recursive=True, loaded=True)
            new_index = None
            for i, reference in enumerate(self.references_current_scene):
                ns = reference.namespace
                self.ui.rigref_combobox.addItem(ns)
                if self.current_reference:
                    if self.current_reference.namespace == ns:
                        new_index = i
                else:
                    new_index = 0
            if new_index is None:
                self.references_current_scene.append(anim_exporter.RIG_REF_INVALID)
                new_index = len(self.references_current_scene) - 1
            else:
                self.ui.rigref_combobox.setCurrentIndex(new_index)
            self.current_reference = self.references_current_scene[new_index]

    def frame_range_browse_to(self):
        pm.playbackOptions(minTime=self.frame_start, edit=True)
        pm.playbackOptions(maxTime=self.frame_end, edit=True)

    def frame_range_set_from_scene(self):
        self.frame_start = int(pm.playbackOptions(minTime=True, query=True))
        self.frame_end = int(pm.playbackOptions(maxTime=True, query=True))
        self.ui.frame_start_spinbox.setValue(self.frame_start)
        self.ui.frame_end_spinbox.setValue(self.frame_end)
        self._auto_save_default_method()

    def clip_name_edited(self):
        self.clip_name = self.ui.clipname_lineedit.text()
        self.update_export_path()

    def export_path_edited(self):
        text = self.ui.export_lineedit.text()
        dir_path = Path(text)
        if dir_path.suffix:
            dir_path = dir_path.parent
        if dir_path.is_dir() and dir_path != Path('.'):
            self.export_path = dir_path
            self.update_export_path(dir_path=dir_path)
        self.get_rel_path_parts_and_update_ui(self.export_path)

    def update_export_path(self, dir_path=None):
        dir_path = dir_path or self.export_path
        if dir_path is None:
            return
        dir_path = Path(dir_path)
        if not self.clip_name:
            return
        if dir_path.suffix:
            dir_path = dir_path.parent
        dest_path = anim_exporter.get_clip_export_default_path(self.clip_name, dir_path=dir_path)
        self.ui.export_lineedit.setText(str(dest_path))
        self.export_path = dest_path
        self._auto_save_default_method()

    def export_path_browse(self):
        start_dir = anim_exporter.get_metadata_start_dir()
        dir_path = ioutils.get_dir_path_from_dialogue(start_dir=start_dir)
        if not dir_path:
            return
        self.update_export_path(dir_path=dir_path)

    def export(self):
        data = self.get_data()
        export_path = Path(data.get(anim_exporter.CLIP_EXPORT_PATH))
        result = anim_exporter.export_animation(export_path, data.get(anim_exporter.CLIP_FRAME_START), data.get(anim_exporter.CLIP_FRAME_END),
                                                rig_reference=self.current_reference)
        return result

    def get_rel_path_parts_and_update_ui(self, path):
        if path:
            relative_root, relative_path = pathutils.get_path_relative_to_folder_name(path, path_consts.FLOTTITOOLS_DIR)
            if not relative_root:
                return None, None    
            self.ui.export_saved_root_lineEdit.setText(os.path.normpath(relative_root))
            self.ui.export_saved_rel_lineEdit.setText(os.path.normpath(relative_path))
            return relative_root, relative_path
        return None, None

    @contextmanager
    def auto_save_disabled(self):
        buffer_auto_save = self.auto_save
        self.auto_save = False
        try:
            yield
        finally:
            self.auto_save = buffer_auto_save
    



def get_widget():
    dir_path = os.path.abspath(os.path.dirname(__file__))
    ui_designer_file_path = os.path.abspath(os.path.join(dir_path, 'anim_clip_widget.ui'))
    loader = QtUiTools.QUiLoader()
    uifile = QtCore.QFile(ui_designer_file_path)
    uifile.open(QtCore.QFile.ReadOnly)
    ui = loader.load(uifile)
    uifile.close()
    return ui


def get_metadata_path_from_open_dialogue(start_dir=None, file_mode=1):
    start_dir = start_dir or anim_exporter.get_metadata_start_dir()
    try:
        path = pm.fileDialog2(fileMode=file_mode,
                              fileFilter=anim_exporter.FILE_FILTER_METADATA,
                              startingDirectory=start_dir)[0]
        return sanitize_metadata_path_weak(Path(path))
    except (TypeError, IndexError):
        return


def get_metadata_path_from_save_as_dialogue(start_dir=None):
    start_dir = start_dir or pathutils.get_scene_path()
    if start_dir.suffix:
        start_dir = start_dir.with_suffix(anim_exporter.EXTENSION_METADATA)
        start_dir_name = start_dir.stem.replace(anim_exporter.ANIM_SEQUENCE_PREFIX.lower(), anim_exporter.METADATA_PREFIX)
        start_dir_name = start_dir_name.replace(anim_exporter.ANIM_SEQUENCE_PREFIX, anim_exporter.METADATA_PREFIX)
        start_dir = start_dir.parent.joinpath(start_dir_name)
    path = ioutils.get_save_as_path_from_dialogue(start_dir=start_dir, file_filter=anim_exporter.FILE_FILTER_METADATA)
    return sanitize_metadata_path_strong(path)


def sanitize_metadata_path_strong(path):
    valid_extensions = [anim_exporter.EXTENSION_METADATA]
    return _sanitize_metadata_path(path, valid_extensions)


def sanitize_metadata_path_weak(path):
    valid_extensions = [anim_exporter.EXTENSION_METADATA, '.json']
    return _sanitize_metadata_path(path, valid_extensions)


def _sanitize_metadata_path(path, valid_extensions):
    if path is None:
        return
    path: Path
    path = Path(path)
    parent_dir = path.parent
    if parent_dir.is_dir() and parent_dir != Path('.'):
        if not path.suffix:
            return path.with_suffix(anim_exporter.EXTENSION_METADATA)
        if path.suffix.lower() not in valid_extensions:
            raise ValueError('"{0}" is an invalid animation metadata extension. Choose a file with a "{1}" extension.'.format(
                path.suffix, anim_exporter.EXTENSION_METADATA))
        return path


def is_valid_metadata_path(path):
    path = Path(path)
    if path.suffix.lower() != anim_exporter.EXTENSION_METADATA:
        return False
    return True
