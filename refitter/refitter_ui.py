import os

import pymel.core as pm
import PySide2.QtWidgets as QtWidgets
import PySide2.QtGui as QtGui

import path_consts
import flottitools.refitter.refitter as refitter
import flottitools.ui as flottiui
import flottitools.utils.deformerutils as defutils


REFITTER_UI = None


def refitter_launch():
    global REFITTER_UI
    if REFITTER_UI:
        REFITTER_UI.deleteLater()
    REFITTER_UI = RefitterMayaWindow()
    REFITTER_UI.show()


class RefitterMayaWindow(flottiui.FlottiMayaWindowDesignerUI):
    window_title = "Refitter"
    dir_path = os.path.abspath(os.path.dirname(__file__))
    ui_designer_file_path = os.path.abspath(os.path.join(dir_path, 'refitter.ui'))

    def __init__(self):
        super(RefitterMayaWindow, self).__init__()
        self.ui.tri_options_vis_widget.setVisible(False)
        self.resize(0, 0)
        # init class variables
        self.default_parent_sentinel = object()
        self.refitter_instance = refitter.Refitter()
        self.blend_mesh = None
        self.target_meshes = []
        self.use_selection = False
        self.variations = []
        self.tri_orig_parent_name = refitter.DEFAULT_ORIGINAL_MESHES_PARENT_NAME
        self.refitted_parent_name = 'refitted_meshes'
        self.tri_orig_parent = None

        self.scroll_area_layout = self.ui.scrollAreaWidgetContents.layout()
        self.grey_arrow = QtGui.QPixmap(os.path.join(path_consts.ICONS_DIR, 'arrow_grey.png'))
        self.green_arrow = QtGui.QPixmap(os.path.join(path_consts.ICONS_DIR, 'arrow_green.png'))
        self.arrow = self.grey_arrow
        self.ui.arrow_label.setPixmap(self.arrow)

        self._init_ui_connections()

        self.add_variation()

    def _init_ui_connections(self):
        self.ui.blend_mesh_lineEdit.returnPressed.connect(self._blend_line_edit)
        self.ui.blend_mesh_button.clicked.connect(self._blend_load_button_clicked)
        self.ui.target_mesh_load_button.clicked.connect(self._target_add_button_clicked)
        self.ui.target_mesh_remove_button.clicked.connect(self._target_remove_button_clicked)
        self.ui.target_mesh_listWidget.itemSelectionChanged.connect(self._on_target_sel_changed)
        self.ui.target_mesh_remove_button.setEnabled(False)

        self.ui.variation_add_button.clicked.connect(self.add_variation)
        self.ui.variation_remove_button.clicked.connect(self.remove_variation)

        self.ui.tri_orig_add_button.clicked.connect(self._set_selected_tri_orig_parent)
        self.ui.tri_orig_default_button.clicked.connect(self._default_tri_orig_parent)
        self.ui.tri_orig_parent_lineEdit.returnPressed.connect(self._on_tri_orig_line_edit)

        self.ui.refit_and_close_button.clicked.connect(self.refit_and_closed_clicked)
        self.ui.refit_button.clicked.connect(self.refit_clicked)
        self.ui.close_button.clicked.connect(self.close_clicked)

    def refit_clicked(self):
        self._refit()

    def refit_and_closed_clicked(self):
        self._refit()
        self.close()

    def close_clicked(self):
        self.close()

    def _refit(self):
        with pm.UndoChunk():
            blend_attrs_values_and_suffixes = []
            for variation_widget in self.variations:
                blend_index = variation_widget.ui.targets_comboBox.currentIndex()
                blend_target = variation_widget.blend_nodes[0].weight[blend_index]
                blend_value = variation_widget.ui.value_spinBox.value()
                suffix = variation_widget.ui.suffix_lineEdit.text()
                if not suffix.startswith('_'):
                    suffix = '_{}'.format(suffix)
                blend_attrs_values_and_suffixes.append((blend_target, blend_value, suffix))
            tri_orig_parent = None
            do_triangulate = self.ui.tri_groupBox.isChecked()
            if do_triangulate:
                preserve_source_meshes = self.ui.tri_keeporig_checkBox.isChecked()
                if preserve_source_meshes:
                    if self.ui.tri_orig_parent_checkBox.isChecked():
                        tri_orig_parent = self.tri_orig_parent
                        if tri_orig_parent == self.default_parent_sentinel:
                            tri_orig_parent = None
                tri_meshes, all_refitted_meshes = refitter.triangulate_and_refit_meshes(
                    self.blend_mesh, self.target_meshes, blend_attrs_values_and_suffixes=blend_attrs_values_and_suffixes,
                    preserve_source_meshes=preserve_source_meshes, tri_orig_parent=tri_orig_parent)
            else:
                tri_meshes = []
                all_refitted_meshes = refitter.refit_meshes(self.blend_mesh, self.target_meshes,
                                                            blend_attrs_values_and_suffixes)
        return tri_meshes, all_refitted_meshes

    def add_variation(self):
        row_count = self.scroll_area_layout.count()
        str_count = defutils.make_string_double_digit(row_count)
        default_suffix = '_variation{}'.format(str_count)
        new_variation = RefitterVariationWidget(self.blend_mesh, default_suffix)
        self.scroll_area_layout.insertWidget(row_count - 1, new_variation)
        self.variations.append(new_variation)

    def remove_variation(self):
        last_widget = self.variations.pop(-1)
        self.scroll_area_layout.removeWidget(last_widget)
        last_widget.deleteLater()

    def _blend_line_edit(self):
        text = self.ui.blend_mesh_lineEdit.text()
        meshes = [x.getParent() for x in pm.ls(type='mesh')]
        matching_mesh = self._get_matching_node_to_text(text, meshes)
        self.blend_mesh = matching_mesh
        self._validate_blend_mesh()
        self._refresh_arrow_color()

    def _do_blend_line_edit_background_color(self):
        if self.blend_mesh:
            self.ui.blend_mesh_lineEdit.setText(self.blend_mesh.nodeName())
            self.ui.blend_mesh_lineEdit.setStyleSheet("background-color: green")
            self.ui.variations_groupBox.setEnabled(True)
        else:
            self.blend_mesh = None
            self.ui.blend_mesh_lineEdit.setStyleSheet("")
            self.ui.variations_groupBox.setEnabled(False)

    def _validate_blend_mesh(self):
        self.blend_mesh_valid = 0
        if self.blend_mesh:
            self.blend_mesh_valid = 2
            blend_nodes = defutils.get_blendshape_nodes(self.blend_mesh)
            if blend_nodes:
                self.blend_mesh_valid = 1
        else:
            self.blend_mesh = None
            self.ui.blend_mesh_lineEdit.setStyleSheet("")
            self.ui.variations_groupBox.setEnabled(False)

        if self.blend_mesh_valid == 0:
            self.blend_mesh = None
            self.ui.refit_and_close_button.setEnabled(False)
            self.ui.refit_button.setEnabled(False)
            self.ui.blend_mesh_lineEdit.setStyleSheet("")
            self.ui.variations_groupBox.setEnabled(False)
        elif self.blend_mesh_valid == 1:
            self.ui.refit_and_close_button.setEnabled(True)
            self.ui.refit_button.setEnabled(True)
            self.ui.blend_mesh_lineEdit.setText(self.blend_mesh.nodeName())
            self.ui.blend_mesh_lineEdit.setStyleSheet("background-color: green")
            self.ui.variations_groupBox.setEnabled(True)
            [x.refresh_target(self.blend_mesh) for x in self.variations]
        elif self.blend_mesh_valid == 2:
            self.ui.refit_and_close_button.setEnabled(False)
            self.ui.refit_button.setEnabled(False)
            self.ui.blend_mesh_lineEdit.setText(self.blend_mesh.nodeName())
            self.ui.blend_mesh_lineEdit.setStyleSheet("background-color: darkgoldenrod")
            self.ui.variations_groupBox.setEnabled(False)
        self.refitter_instance.blend_mesh = self.blend_mesh

    def _blend_load_button_clicked(self):
        sel = pm.selected()
        meshes = [x for x in sel if defutils.get_blendshape_nodes(x)]
        try:
            self.blend_mesh = meshes[0]
        except IndexError:
            pm.warning('Please select a mesh with blendshapes in the scene to use as a source mesh.')
            self.blend_mesh = None
            if len(sel):
                self.ui.blend_mesh_lineEdit.setText(sel[0].name())
            else:
                self.ui.blend_mesh_lineEdit.setText('')
        self._validate_blend_mesh()
        self._refresh_arrow_color()

    def _refresh_arrow_color(self):
        self.arrow = self.grey_arrow
        if self.use_selection:
            if self.blend_mesh:
                self.arrow = self.green_arrow
        else:
            if self.target_meshes and self.blend_mesh:
                self.arrow = self.green_arrow
                if len(self.target_meshes) == 1:
                    if self.target_meshes[0] == self.blend_mesh:
                        self.arrow = self.grey_arrow
        self.ui.arrow_label.setPixmap(self.arrow)

    def _target_add_button_clicked(self):
        sel = pm.selected()
        meshes = [x for x in sel if x.getShape()]
        [self.target_meshes.append(sm) for sm in meshes if sm not in self.target_meshes]
        self._refresh_target_list()

    def _refresh_target_list(self):
        self.ui.target_mesh_listWidget.clear()
        [self.ui.target_mesh_listWidget.addItem(node.shortName()) for node in self.target_meshes]
        self._refresh_arrow_color()

    def _target_remove_button_clicked(self):
        selected_target_indexes = self.ui.target_mesh_listWidget.selectedIndexes()
        selected_target_indexes = [i.row() for i in selected_target_indexes]
        selected_target_indexes.sort()
        selected_target_indexes.reverse()
        [self.target_meshes.pop(i) for i in selected_target_indexes]
        self._refresh_target_list()

    def _on_target_sel_changed(self):
        stuff = self.ui.target_mesh_listWidget.selectedItems()
        QtWidgets.QListWidget(self.ui.target_mesh_listWidget)
        if stuff:
            self.ui.target_mesh_remove_button.setEnabled(True)
        else:
            self.ui.target_mesh_remove_button.setEnabled(False)

    def _default_tri_orig_parent(self):
        self.tri_orig_parent = self._default_tri_parent(self.tri_orig_parent_name, self.ui.tri_orig_parent_lineEdit)

    # def _default_tri_mesh_parent(self):
    #     self.tri_mesh_parent = self._default_tri_parent(self.tri_mesh_parent_name, self.ui.tri_mesh_parent_lineEdit)

    def _default_tri_parent(self, parent_name, line_edit):
        line_edit.setText(parent_name)
        stuff = pm.ls(parent_name, type='transform')
        if stuff:
            parent_node = stuff[0]
        else:
            parent_node = self.default_parent_sentinel
        self._validate_line_edit_node(line_edit, parent_node, parent_name)
        return parent_node

    def _set_selected_tri_orig_parent(self):
        self._set_selected_parent(self.ui.tri_orig_parent_lineEdit, self.tri_orig_parent)

    # def _set_selected_tri_mesh_parent(self):
    #     self._set_selected_parent(self.ui.tri_mesh_parent_lineEdit, self.tri_mesh_parent)

    def _set_selected_parent(self, line_edit, parent_var):
        sel = pm.selected(type='transform')
        try:
            parent_node = sel[0]
        except IndexError:
            parent_node = None
            pm.warning('Please select a transform node in the scene to use as a parent.')
            line_edit.setText('')
        self._validate_line_edit_node(line_edit, parent_node, parent_var)

    def _on_tri_orig_line_edit(self):
        self.tri_orig_parent = self._on_tri_line_edit(self.ui.tri_orig_parent_lineEdit, self.tri_orig_parent_name)

    # def _on_tri_mesh_line_edit(self):
    #     self.tri_mesh_parent = self._on_tri_line_edit(self.ui.tri_mesh_parent_lineEdit, self.tri_mesh_parent_name)

    def _on_tri_line_edit(self, line_edit, parent_var_name):
        text = line_edit.text()
        parent_node = self._get_matching_node_to_text(text)
        self._validate_line_edit_node(line_edit, parent_node, parent_var_name)
        return parent_node

    def _validate_line_edit_node(self, line_edit, parent_node, parent_var_name):
        if parent_node:
            if parent_node == self.default_parent_sentinel:
                line_edit.setText(parent_var_name + ' (New Node)')
                line_edit.setStyleSheet("background-color: green")
            else:
                line_edit.setText(parent_node.nodeName())
                line_edit.setStyleSheet("background-color: green")
        else:
            line_edit.setStyleSheet("")

    @staticmethod
    def _get_matching_node_to_text(text, node_list=None):
        node_list = node_list or pm.ls(type='transform')
        names = [x.nodeName() for x in node_list]
        matching_node = None
        for node, name in zip(node_list, names):
            if text.lower() == name.lower():
                matching_node = node
                break
        if not matching_node and text != '':
            for node, name in zip(node_list, names):
                if text.lower() in name.lower():
                    matching_node = node
                    break
        return matching_node


class RefitterVariationWidget(flottiui.FlottiMayaWindowDesignerUI):
    window_title = "Refitter Variation"
    dir_path = os.path.abspath(os.path.dirname(__file__))
    ui_designer_file_path = os.path.abspath(os.path.join(dir_path, 'refitter_variation_widget.ui'))

    def __init__(self, blend_mesh=None, variation_suffix=None):
        super(RefitterVariationWidget, self).__init__()
        variation_suffix = variation_suffix or '_variation01'
        self.ui.suffix_lineEdit.setText(variation_suffix)
        self.blend_nodes = []
        self.refresh_target(blend_mesh)

    def refresh_target(self, blend_mesh):
        if not blend_mesh:
            return
        self.blend_nodes = defutils.get_blendshape_nodes(blend_mesh)
        target_names = pm.listAttr(self.blend_nodes[0].weight, m=True)
        self.ui.targets_comboBox.clear()
        # for t_name, blend_node in zip(target_names, self.blend_nodes):
        for t_name in target_names:
            item = self.ui.targets_comboBox.addItem(t_name)