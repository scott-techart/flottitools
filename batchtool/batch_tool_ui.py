import os
import pathlib
import shutil
import stat

import pymel.core as pm
import PySide2.QtCore as QtCore
import PySide2.QtWidgets as QtWidgets
import PySide2.QtGui as QtGui

import flottitools.path_consts as path_consts
import flottitools.ui as flottiui
import flottitools.utils.ioutils as ioutils
import flottitools.utils.materialutils as matutils
import flottitools.utils.meshutils as meshutils
import flottitools.utils.pathutils as pathutils


BATCHTOOL_UI = None


def batcher_launch():
    global BATCHTOOL_UI
    if BATCHTOOL_UI:
        BATCHTOOL_UI.deleteLater()
    BATCHTOOL_UI = BatcherMayaWindow()
    BATCHTOOL_UI.show()


class BatcherMayaWindow(flottiui.FlottiMayaWindowDesignerUI):
    window_title = "Batcher"
    dir_path = os.path.abspath(os.path.dirname(__file__))
    ui_designer_file_path = os.path.abspath(os.path.join(dir_path, 'batch_tool.ui'))

    def __init__(self):
        super(BatcherMayaWindow, self).__init__()
        self.start_dir_string = path_consts.FLOTTITOOLS_DIR
        self.default_filter_string = '*.ma, *.mb'
        self.files_list_paths = []

        export_fbx_name = 'Export Mesh as .fbx'
        rename_mesh_name = 'Rename Mesh to Texture Name'
        self.operation_names = [export_fbx_name,
                                rename_mesh_name]
        self.operation_name_to_method = {export_fbx_name: export_mesh_as_fbx,
                                         rename_mesh_name: rename_mesh_to_texture_name}
        self.operation_name_to_default_filter = {rename_mesh_name: '*.ma, *.mb'}

        self.icon_provider = QtWidgets.QFileIconProvider()
        self.system_model = QtWidgets.QFileSystemModel()

        # type hints for variables defined in batch_tool.ui
        self.ui.start_dir_lineEdit: QtWidgets.QLineEdit
        self.ui.start_dir_browse_button: QtWidgets.QPushButton
        self.ui.browse_dir_treeView: QtWidgets.QTreeView

        self.ui.filter_lineEdit: QtWidgets.QLineEdit
        self.ui.start_dir_browse_button: QtWidgets.QPushButton
        self.ui.browse_files_listWidget: QtWidgets.QListWidget

        self.ui.filelist_add_button: QtWidgets.QPushButton
        self.ui.filelist_remove_button: QtWidgets.QPushButton

        self.ui.files_replace_list_checkBox: QtWidgets.QCheckBox
        self.ui.files_load_list_button: QtWidgets.QPushButton
        self.ui.files_save_list_button: QtWidgets.QPushButton
        self.ui.files_listWidget: QtWidgets.QListWidget

        self.ui.operation_comboBox: QtWidgets.QComboBox
        self.ui.operation_execute_button: QtWidgets.QPushButton

        self.init_ui_states()
        self.init_ui_connections()

        self.show()

    def init_ui_states(self):
        self.system_model.setFilter(QtCore.QDir.Dirs | QtCore.QDir.NoDotAndDotDot)
        self.ui.browse_dir_treeView.setModel(self.system_model)
        [self.ui.browse_dir_treeView.hideColumn(i) for i in range(self.system_model.columnCount()) if i > 0]
        self.ui.start_dir_lineEdit.setText(self.start_dir_string)
        self.start_dir_set(self.start_dir_string)

        self.ui.operation_comboBox.addItems(self.operation_names)

        refresh_icon = QtGui.QPixmap(os.path.join(path_consts.ICONS_DIR, 'refresh.svg'))
        self.ui.filter_refresh_button.setIcon(refresh_icon)
        options_icon = QtGui.QPixmap(os.path.join(path_consts.ICONS_DIR, 'browse.svg'))
        self.ui.start_dir_browse_button.setIcon(options_icon)

        self.files_list_remove_button_enabled_refresh()
        self.files_list_add_button_enabled_refresh()

        self.filter_set_default()

    def init_ui_connections(self):
        self.ui.start_dir_browse_button.clicked.connect(self.browse_dir)
        self.ui.start_dir_lineEdit.returnPressed.connect(self.start_dir_edited)
        self.ui.filter_refresh_button.clicked.connect(self.filter_set_default)
        self.ui.filter_lineEdit.returnPressed.connect(self.browse_files_list_refresh)
        self.ui.browse_dir_treeView.selectionModel().selectionChanged.connect(self.browse_files_list_refresh)
        self.ui.browse_files_listWidget.itemSelectionChanged.connect(self.files_list_add_button_enabled_refresh)
        self.ui.filelist_add_button.clicked.connect(self.files_list_add)
        self.ui.filelist_remove_button.clicked.connect(self.files_list_remove)
        self.ui.files_save_list_button.clicked.connect(self.files_list_save)
        self.ui.files_load_list_button.clicked.connect(self.files_list_load)
        self.ui.files_listWidget.itemSelectionChanged.connect(self.files_list_remove_button_enabled_refresh)
        self.ui.operation_execute_button.clicked.connect(self.execute_batch_operation)
        self.ui.operation_comboBox.currentIndexChanged.connect(self.operation_combo_box_changed)

    def execute_batch_operation(self):
        operation_name = self.ui.operation_comboBox.currentText()
        operation_method = self.operation_name_to_method[operation_name]
        logger = Logger(self.files_list_paths, operation_name)
        result = None
        try:
            p4_instance = None
            if self.p4_instance:
                if self.p4_instance.connected():
                    p4_instance = self.p4_instance
            result = operation_method(self.files_list_paths, logger, p4_instance)
        except Exception as e:
            logger.log(operation_name, e)
        logger.finish()
        print('Finished {0} with the following result:\n    {1}'.format(operation_name, result))
        print('Log file saved to:\n    {}'.format(logger.log_file_path))
        return result

    def browse_files_list_refresh(self):
        self.ui.browse_files_listWidget.clear()
        filter_text = self.ui.filter_lineEdit.text()
        file_paths_in_selected_dirs = []
        for selected_index in self.ui.browse_dir_treeView.selectedIndexes():
            path_string = self.system_model.filePath(selected_index)
            path = pathlib.Path(path_string)
            file_paths = get_all_file_paths_in_dir(path)
            if filter_text:
                file_paths = path_match_multiple(file_paths, filter_text)
            file_paths_in_selected_dirs.extend(file_paths)
        # remove duplicates and sort list
        file_paths_in_selected_dirs = list(set(file_paths_in_selected_dirs))
        file_paths_in_selected_dirs.sort()
        for file_path in file_paths_in_selected_dirs:
            new_list_item = self._get_list_item_from_path(file_path)
            self.ui.browse_files_listWidget.addItem(new_list_item)
            new_list_item.path = file_path

    def files_list_add(self):
        selected_items = self.ui.browse_files_listWidget.selectedItems()
        for selected_item in selected_items:
            if selected_item.path not in self.files_list_paths:
                self.files_list_paths.append(selected_item.path)
        self.files_list_refresh()

    def files_list_remove(self):
        selected_items = self.ui.files_listWidget.selectedItems()
        for selected_item in selected_items:
            self.files_list_paths.remove(selected_item.path)
        self.files_list_refresh()

    def files_list_refresh(self):
        self.ui.files_listWidget.clear()
        self.files_list_paths.sort()
        for path in self.files_list_paths:
            new_item = self._get_list_item_from_path(path)
            self.ui.files_listWidget.addItem(new_item)

    def files_list_add_button_enabled_refresh(self):
        self._button_enabled_refresh(self.ui.filelist_add_button, self.ui.browse_files_listWidget)

    def files_list_remove_button_enabled_refresh(self):
        self._button_enabled_refresh(self.ui.filelist_remove_button, self.ui.files_listWidget)

    def browse_dir(self):
        browser_dialog = QtWidgets.QFileDialog(self)
        browser_dialog.setWindowTitle('Choose a root directory to search for files from.')
        browser_dialog.setDirectory(path_consts.FLOTTITOOLS_DIR)
        browser_dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
        dir_was_selected = browser_dialog.exec()
        if dir_was_selected:
            selected_dir = browser_dialog.selectedFiles()[0]
            self.ui.start_dir_lineEdit.setText(selected_dir)
            self.start_dir_set(selected_dir)

    def start_dir_set(self, path_string):
        self.start_dir_string = path_string
        root_index = self.system_model.setRootPath(self.start_dir_string)
        self.ui.browse_dir_treeView.setRootIndex(root_index)
        self.ui.browse_files_listWidget.clear()

    def start_dir_edited(self):
        dir_text = self.ui.start_dir_lineEdit.text()
        if os.path.exists(dir_text):
            self.start_dir_set(dir_text)

    def filter_set_default(self, current_operation_name=None):
        current_operation_name = current_operation_name or self.ui.operation_comboBox.currentText()
        filter_string = self.operation_name_to_default_filter.get(current_operation_name, self.default_filter_string)
        # if not filter_string:
        #     filter_string = self.default_filter_string
        self.ui.filter_lineEdit.setText(filter_string)
        self.browse_files_list_refresh()

    def operation_combo_box_changed(self):
        current_operation_name = self.ui.operation_comboBox.currentText()
        self.filter_set_default(current_operation_name)
        start_dir = self.operation_name_to_start_dir.get(current_operation_name, path_consts.FLOTTITOOLS_DIR)
        self.ui.start_dir_lineEdit.setText(start_dir)
        self.start_dir_edited()

    def files_list_save(self):
        print('Saving and loading lists has not been implemented yet.')

    def files_list_load(self):
        print('Saving and loading lists has not been implemented yet.')

    @staticmethod
    def _button_enabled_refresh(button, list_widget):
        items_are_selected = bool(list_widget.selectedItems())
        button.setEnabled(items_are_selected)

    def _get_list_item_from_path(self, path):
        file_info = QtCore.QFileInfo(str(path))
        file_icon = self.icon_provider.icon(file_info)
        new_list_item = ListWidgetItemWithPath()
        new_list_item.path = path
        n = path.name
        new_list_item.setText(n)
        new_list_item.setIcon(file_icon)
        return new_list_item


def path_match_multiple(paths, match_string):
    if ',' not in match_string:
        return [p for p in paths if p.match(match_string)]
    parts = match_string.split(',')
    match_strings = [p.strip() for p in parts]
    matched_paths = []
    for match_string in match_strings:
        matched_paths.extend([p for p in paths if p.match(match_string)])
    return matched_paths


def get_all_file_paths_in_dir(dir_path):
    all_paths = []
    for dir_path, sub_dir_names, file_names in os.walk(dir_path):
        for file_name in file_names:
            file_path = pathlib.Path(os.path.join(dir_path, file_name))
            all_paths.append(file_path)
    return all_paths


class ListWidgetItemWithPath(QtWidgets.QListWidgetItem):
    # would have used a dict but QListWidgetItems aren't hashable and can't be stored in a dict
    path = None


def export_mesh_as_fbx(file_paths, logger):
    results = []
    for file_path in file_paths:
        try:
            on_open_error = open_file_and_ignore_errors(file_path)
            if on_open_error:
                logger.log(file_path, on_open_error)
            fbx_path = pathlib.Path(file_path)
            fbx_path = fbx_path.with_suffix('.fbx')
            fbx_abs_path = os.path.abspath(fbx_path)
            mesh = meshutils.get_meshes_from_scene()[0]
            ioutils.export_fbx(fbx_abs_path, nodes=mesh)
            ioutils.ensure_file_is_writable(file_path)
            pm.saveFile()
            logger.log(file_path, 'Exported {0} to {1}'.format(mesh, fbx_abs_path))
        except Exception as e:
            logger.log(file_path, e)
    return results


def rename_mesh_to_texture_name(file_paths, logger):
    results = []
    for file_path in file_paths:
        try:
            on_open_error = open_file_and_ignore_errors(file_path)
            if on_open_error:
                logger.log(file_path, on_open_error)
            rename_mesh_in_scene_to_match_texture()
            ioutils.ensure_file_is_writable(file_path)
            pm.saveFile()
            logger.log(file_path, 'Mesh successfully renamed!')
        except Exception as e:
            logger.log(file_path, e)
    return results


def rename_mesh_in_scene_to_match_texture():
    mesh = meshutils.get_meshes_from_scene()[0]
    material = matutils.get_materials_assigned_to_nodes(mesh)[0]
    try:
        texture_file_node = material.color.inputs()[0]
    except IndexError:
        return mesh
    texture_path = pathlib.Path(texture_file_node.fileTextureName.get())
    mesh.rename(texture_path.stem)
    return mesh


def open_file_and_ignore_errors(file_path):
    error = None
    try:
        pm.openFile(file_path, force=True)
    except Exception as e:
        error = e
    return error


class Logger:
    def __init__(self, file_list, operation_name):
        self.operation_name = operation_name
        self.log_file_path = self.get_log_file_path()
        self.log_data = ['Performing {} on files: \n'.format(operation_name)]

        stuff = ['    {}\n'.format(str(p)) for p in file_list]
        self.log_data.extend(stuff)

    def log(self, file_path, result):
        self.log_data.append('{0} :  {1}\n'.format(str(file_path), result))

    def finish(self):
        with open(self.log_file_path, 'w') as f:
            f.writelines(self.log_data)

    def get_log_file_path(self):
        log_file_base_name = 'Batch {} Log'.format(self.operation_name)
        next_log_file_name = '{}01.txt'.format(log_file_base_name)
        log_dir = pathlib.Path(path_consts.FLOTTITOOLS_DIR)
        existing_log_files = []
        for each in os.listdir(log_dir):
            if each.lower().startswith(log_file_base_name.lower()):
                existing_log_files.append(each)
        if existing_log_files:
            existing_log_files.sort()
            name, ext = os.path.splitext(existing_log_files[-1])
            number = int(name[-2:])
            number += 1
            next_log_file_name = '{0}{1}.txt'.format(log_file_base_name, str(number).zfill(2))
        log_file_path = log_dir.joinpath(next_log_file_name)
        return log_file_path
