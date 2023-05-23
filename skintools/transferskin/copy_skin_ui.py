import os

import pymel.core as pm
import PySide2.QtWidgets as QtWidgets
import PySide2.QtGui as QtGui

import flottitools.ui as flottiui
import flottitools.utils.skinutils as skinutils
import flottitools.utils.skeletonutils as skelutils


COPYSKIN_UI = None


def copy_skin_launch():
    global COPYSKIN_UI
    if COPYSKIN_UI:
        COPYSKIN_UI.deleteLater()
    COPYSKIN_UI = CopySkinWeightsMayaWindow()
    COPYSKIN_UI.show()


class CopySkinWeightsMayaWindow(flottiui.FlottiMayaWindowDesignerUI):
    window_title = "Copy Skin Weights"
    dir_path = os.path.abspath(os.path.dirname(__file__))
    ui_designer_file_path = os.path.abspath(os.path.join(dir_path, 'copy_skin.ui'))

    def __init__(self):
        super(CopySkinWeightsMayaWindow, self).__init__()
        self.resize(0, 0)
        self.ui.target_mesh_remove_button.setEnabled(False)

        self.source_mesh = None
        self.target_meshes = []
        self.use_selection = False

        self.grey_arrow = QtGui.QPixmap(os.path.join(self.dir_path, 'arrow_grey.png'))
        self.green_arrow = QtGui.QPixmap(os.path.join(self.dir_path, 'arrow_green.png'))
        self.arrow = self.grey_arrow
        self.ui.arrow_label.setPixmap(self.arrow)

        self.button_to_method_map = {self.ui.surface_vertorder_radio_button: self._copy_vert_order,
                                     self.ui.surface_ws_radio_button: self._copy_worldspace,
                                     self.ui.surface_raycast_radio_button: self._copy_raycast,
                                     self.ui.surface_closestcomp_radio_button: self._copy_closest_component,
                                     self.ui.surface_uv_radio_button: self._copy_uv_space}

        self.inf_index_to_method_map = {0: skelutils.update_inf_map_by_closest_inf,
                                        1: skelutils.update_inf_map_by_label,
                                        2: skelutils.update_inf_map_by_name,
                                        3: None}
        self.inf_index_to_args_map = {0: 'closestJoint',
                                      1: 'label',
                                      2: 'name',
                                      3: None}

        self.ui.source_mesh_lineEdit.returnPressed.connect(self._source_line_edit)
        self.ui.source_mesh_button.clicked.connect(self._source_load_button_clicked)
        self.ui.target_mesh_load_button.clicked.connect(self._target_add_button_clicked)
        self.ui.target_mesh_remove_button.clicked.connect(self._target_remove_button_clicked)
        self.ui.target_mesh_use_selection_button.clicked.connect(self._use_selection_clicked)
        self.ui.target_mesh_listWidget.itemSelectionChanged.connect(self._on_target_sel_changed)

        self.ui.copy_and_close_button.clicked.connect(self.copy_and_closed_clicked)
        self.ui.copy_button.clicked.connect(self.copy_clicked)
        self.ui.close_button.clicked.connect(self.close_clicked)

    def copy_clicked(self):
        self._copy()

    def copy_and_closed_clicked(self):
        self._copy()
        self.close()

    def close_clicked(self):
        self.close()

    def _copy(self):
        checked_button = self.ui.surface_buttonGroup.checkedButton()
        copy_method = self.button_to_method_map[checked_button]
        copy_method()

    def _copy_vert_order(self):
        mapping_methods = self._get_inf_mapping_methods()
        target_meshes = self.target_meshes
        if self.use_selection:
            target_meshes = skinutils.get_skinned_meshes_from_selection()
        for target_mesh in target_meshes:
            if target_mesh == self.source_mesh:
                pm.warning('Skipping target mesh {}. Target mesh must be a different mesh than the source mesh.'.format(
                    target_mesh.shortName()))
                continue
            skinutils.copy_weights_vert_order(self.source_mesh, target_mesh, mapping_methods=mapping_methods)

    def _copy_worldspace(self):
        self._copy_with_surface_association('closestPoint')

    def _copy_raycast(self):
        # copySkinWeights - noMirror - surfaceAssociation rayCast - influenceAssociation label - influenceAssociation name - influenceAssociation closestJoint - normalize;
        self._copy_with_surface_association('rayCast')

    def _copy_closest_component(self):
        self._copy_with_surface_association('closestComponent')

    def _copy_uv_space(self):
        # copySkinWeights -noMirror -surfaceAssociation closestPoint -uvSpace UVChannel_1 map1 -influenceAssociation label -influenceAssociation name -influenceAssociation closestJoint -normalize;
        copy_kwargs = {'surfaceAssociation': 'closestPoint'}
        copy_kwargs.update(self._get_inf_association_kwarg())
        source_uvset = self.source_mesh.getCurrentUVSetName()
        target_meshes = self.target_meshes
        if self.use_selection:
            target_meshes = skinutils.get_skinned_meshes_from_selection()
        for target_mesh in target_meshes:
            if target_mesh == self.source_mesh:
                pm.warning('Skipping target mesh {}. Target mesh must be a different mesh than the source mesh.'.format(
                    target_mesh.shortName()))
                continue
            target_uvset = target_mesh.getCurrentUVSetName()
            copy_kwargs['uvSpace'] = (source_uvset, target_uvset)
            skinutils.copy_weights(self.source_mesh, target_mesh, **copy_kwargs)
            print('Copied weights from {0} to {1} via UV Space: from {2} to {3}'.format(
                self.source_mesh.nodeName, target_mesh.nodeName(), source_uvset, target_uvset))

    def _copy_with_surface_association(self, surface_association):
        copy_kwargs = {'surfaceAssociation': surface_association}
        copy_kwargs.update(self._get_inf_association_kwarg())
        target_meshes = self.target_meshes
        if self.use_selection:
            sel = pm.selected()
            try:
                if isinstance(sel[0], pm.MeshVertex):
                    skinutils.copy_weights(self.source_mesh, sel, **copy_kwargs)
                    print('Copied weights from {0} to {1} via {2}'.format(
                        self.source_mesh.nodeName(), sel, surface_association))
                else:
                    target_meshes = skinutils.get_skinned_meshes_from_selection()
            except IndexError:
                pm.warning('Nothing selected. Select a skinned mesh or skinned vertices to copy weights with "Use Selection" enabled.')
                return
        for target_mesh in target_meshes:
            if target_mesh == self.source_mesh:
                pm.warning('Skipping target mesh {}. Target mesh must be a different mesh than the source mesh.'.format(
                    target_mesh.shortName()))
                continue
            skinutils.copy_weights(self.source_mesh, target_mesh, **copy_kwargs)
            print('Copied weights from {0} to {1} via {2}'.format(
                self.source_mesh.nodeName(), target_mesh.nodeName(), surface_association))

    def _source_line_edit(self):
        text = self.ui.source_mesh_lineEdit.text()
        skinned_meshes = skinutils.get_skinned_meshes_from_scene()
        names = [x.nodeName() for x in skinned_meshes]
        node = None
        for mesh, name in zip(skinned_meshes, names):
            if text.lower() == name.lower():
                node = mesh
                break
        if not node and text != '':
            for mesh, name in zip(skinned_meshes, names):
                if text.lower() in name.lower():
                    node = mesh
                    break
        self.source_mesh = node
        self._do_source_line_edit_background_color()
        self._refresh_arrow_color()

    def _do_source_line_edit_background_color(self):
        if self.source_mesh:
            self.ui.source_mesh_lineEdit.setText(self.source_mesh.nodeName())
            self.ui.source_mesh_lineEdit.setStyleSheet("background-color: green")
        else:
            self.source_mesh = None
            self.ui.source_mesh_lineEdit.setStyleSheet("")

    def _on_target_sel_changed(self):
        stuff = self.ui.target_mesh_listWidget.selectedItems()
        QtWidgets.QListWidget(self.ui.target_mesh_listWidget)
        if stuff:
            self.ui.target_mesh_remove_button.setEnabled(True)
        else:
            self.ui.target_mesh_remove_button.setEnabled(False)

    def _use_selection_clicked(self):
        self.use_selection = self.ui.target_mesh_use_selection_button.isChecked()
        self._refresh_arrow_color()

    def _source_load_button_clicked(self):
        try:
            sel = pm.selected()[0]
            self.source_mesh = sel
            if not skinutils.get_skincluster(sel):
                pm.warning('Selected node is not a skinned mesh. Please select a skinned mesh.')
                self.source_mesh = None
        except IndexError:
            pm.warning('Please select a skinned mesh in the scene.')
            self.source_mesh = None
        self._do_source_line_edit_background_color()
        self._refresh_arrow_color()

    def _target_add_button_clicked(self):
        skinned_meshes = skinutils.get_skinned_meshes_from_selection()
        [self.target_meshes.append(sm) for sm in skinned_meshes if sm not in self.target_meshes]
        self._refresh_target_list()

    def _refresh_target_list(self):
        self.ui.target_mesh_listWidget.clear()
        [self.ui.target_mesh_listWidget.addItem(node.shortName()) for node in self.target_meshes]
        self._refresh_arrow_color()

    def _refresh_arrow_color(self):
        self.arrow = self.grey_arrow
        if self.use_selection:
            if self.source_mesh:
                self.arrow = self.green_arrow
        else:
            if self.target_meshes and self.source_mesh:
                self.arrow = self.green_arrow
                if len(self.target_meshes) == 1:
                    if self.target_meshes[0] == self.source_mesh:
                        self.arrow = self.grey_arrow
        self.ui.arrow_label.setPixmap(self.arrow)

    def _target_remove_button_clicked(self):
        selected_target_indexes = self.ui.target_mesh_listWidget.selectedIndexes()
        selected_target_indexes = [i.row() for i in selected_target_indexes]
        selected_target_indexes.sort()
        selected_target_indexes.reverse()
        [self.target_meshes.pop(i) for i in selected_target_indexes]
        self._refresh_target_list()

    def _get_inf_mapping_methods(self):
        indices = self._get_inf_indices()
        mapping_methods = [self.inf_index_to_method_map[i] for i in indices]
        mapping_methods = [x for x in mapping_methods if x is not None]
        return mapping_methods

    def _get_inf_association_kwarg(self):
        indices = self._get_inf_indices()
        args = [self.inf_index_to_args_map[i] for i in indices]
        args = [a for a in args if a is not None]
        inf_kwarg = {'influenceAssociation': args}
        return inf_kwarg
        # 'influenceAssociation': ('label', 'name', 'closestJoint')

    def _get_inf_indices(self):
        return [x.currentIndex() for x in [self.ui.inf_first_comboBox,
                                           self.ui.inf_second_comboBox,
                                           self.ui.inf_third_comboBox]]





