import os

import pymel.core as pm
import maya.api.OpenMaya as om

import flottitools.ui as flottiui
import flottitools.utils.skeletonutils as skelutils
import flottitools.utils.transformutils as xformutils


ORIENT_JOINTS_UI = None


def orient_joints_launch():
    global ORIENT_JOINTS_UI
    if ORIENT_JOINTS_UI:
        ORIENT_JOINTS_UI.deleteLater()
    ORIENT_JOINTS_UI = OrientJointsMayaWindow()
    ORIENT_JOINTS_UI.show()


class OrientJointsMayaWindow(flottiui.FlottiMayaWindowDesignerUI):
    window_title = "Orient Joints"
    dir_path = os.path.abspath(os.path.dirname(__file__))
    ui_designer_file_path = os.path.abspath(os.path.join(dir_path, 'orient_joints.ui'))

    def __init__(self):
        super().__init__()
        self.coplanar_nodes = []
        self.aim_up_vector = None
        self.node_to_copy_from = None
        self.mirror_side_vector = None

        #consts
        self.side_vector_to_text = {(1, 0, 0): '+X (1, 0, 0)',
                                    (0, 1, 0): '+Y (0, 1, 0)',
                                    (0, 0, 1): '+Z (0, 0, 1)',
                                    (-1, 0, 0): '-X (-1, 0, 0)',
                                    (0, -1, 0): '-Y (0, -1, 0)',
                                    (0, 0, -1): '-Z (0, 0, -1)'}
        self.side_index_to_vector = {0: (1, 0, 0),
                                     1: (0, 1, 0),
                                     2: (0, 0, 1)}
        self.mirror_button_to_index = {self.ui.mirror_forward_x_button: 0,
                                       self.ui.mirror_forward_y_button: 1,
                                       self.ui.mirror_forward_z_button: 2,
                                       self.ui.mirror_up_x_button: 0,
                                       self.ui.mirror_up_y_button: 1,
                                       self.ui.mirror_up_z_button: 2}
        self.aim_button_to_index = {self.ui.aim_x_button: 0,
                                    self.ui.aim_y_button: 1,
                                    self.ui.aim_z_button: 2,
                                    self.ui.up_x_button: 0,
                                    self.ui.up_y_button: 1,
                                    self.ui.up_z_button: 2}

        self.ui.nodes_load_button.clicked.connect(self._node_add_button_clicked)
        self.ui.nodes_remove_button.clicked.connect(self._node_remove_button_clicked)

        self._refresh_axes_buttons()
        self._refresh_mirror_buttons()
        axes_buttons = [self.ui.aim_x_button, self.ui.aim_y_button, self.ui.aim_z_button,
                        self.ui.up_x_button, self.ui.up_y_button, self.ui.up_z_button]
        [b.clicked.connect(self._refresh_axes_buttons) for b in axes_buttons]
        mirror_buttons = [self.ui.mirror_forward_x_button, self.ui.mirror_forward_y_button, self.ui.mirror_forward_z_button,
                          self.ui.mirror_up_x_button, self.ui.mirror_up_y_button, self.ui.mirror_up_z_button]
        [b.clicked.connect(self._refresh_mirror_buttons) for b in mirror_buttons]

        self.ui.up_copy_button.clicked.connect(self._on_copy_button_clicked)
        self.ui.up_vector_group_box.toggled.connect(self._refresh_up_vector)
        self.button_to_axis = {self.ui.aim_x_button: om.MVector.kXaxisVector,
                               self.ui.aim_y_button: om.MVector.kYaxisVector,
                               self.ui.aim_z_button: om.MVector.kZaxisVector,
                               self.ui.up_x_button: om.MVector.kXaxisVector,
                               self.ui.up_y_button: om.MVector.kYaxisVector,
                               self.ui.up_z_button: om.MVector.kZaxisVector}
        self.ui.mirror_groupBox.toggled.connect(self._refresh_mirror_side)
        self.ui.mirror_flip_side_checkbox.toggled.connect(self._refresh_mirror_side)

        self.ui.orient_button.clicked.connect(self.orient_selected)
        self.ui.up_flip_check_box.toggled.connect(self._refresh_up_vector)

    def orient_selected(self):
        self._refresh_up_vector()
        aim_axis_index = self.aim_button_to_index[self.ui.axis_aim_buttonGroup.checkedButton()]
        up_axis_index = self.aim_button_to_index[self.ui.axis_up_buttonGroup.checkedButton()]
        if self.aim_up_vector:
            skelutils.orient_selected_joints(
                up_target_vec=self.aim_up_vector, mirror_side_vector=self.mirror_side_vector,
                aim_axis_index=aim_axis_index, up_axis_index=up_axis_index)
        else:
            skelutils.orient_selected_joints(
                mirror_side_vector=self.mirror_side_vector, aim_axis_index=aim_axis_index, up_axis_index=up_axis_index)

    def _on_copy_button_clicked(self):
        try:
            self.node_to_copy_from = pm.selected(type=pm.nt.Transform)[0]
            self.ui.up_vector_group_box.setChecked(False)
            self._refresh_up_vector()
        except IndexError:
            pm.error('No transform node selected. Select a transform node to copy up vector from.')

    def _refresh_up_vector(self):
        up_vector = None
        if self.ui.up_vector_group_box.isChecked():
            if len(self.coplanar_nodes) == 3:
                node_positions = [xformutils.get_worldspace_vector(n) for n in self.coplanar_nodes]
                up_vector = skelutils.get_perpendicular_vector_from_three_points(*node_positions)
        elif self.node_to_copy_from:
            checked_up_axis = self.button_to_axis[self.ui.axis_up_buttonGroup.checkedButton()]
            up_vector = xformutils.get_axis_as_worldspace_vector(self.node_to_copy_from, axis=checked_up_axis)
        if self.ui.up_flip_check_box.isChecked():
            up_vector = up_vector * -1
        self.aim_up_vector = up_vector
        up_vec_str = 'Cannot determine up vector.'
        if up_vector:
            up_vec_str = '({0}, {1}, {2})'.format(self.aim_up_vector[0], self.aim_up_vector[1], self.aim_up_vector[2])
        self.ui.up_line_edit.setText(up_vec_str)

    def _node_add_button_clicked(self):
        selected_nodes = pm.selected(type=pm.nt.Transform)
        transform_nodes = [sn for sn in selected_nodes if sn not in self.coplanar_nodes]
        all_nodes = self.coplanar_nodes + transform_nodes
        if len(all_nodes) > 3:
            all_nodes = all_nodes[-3:]
            pm.warning('Maximum three nodes to calculate up vector. Using last three added.')
        self.coplanar_nodes = all_nodes
        self._refresh_nodes_list()

    def _refresh_nodes_list(self):
        self.ui.nodes_listWidget.clear()
        [self.ui.nodes_listWidget.addItem(node.shortName()) for node in self.coplanar_nodes]
        self._refresh_up_vector()

    def _node_remove_button_clicked(self):
        selected_nodes_indexes = self.ui.nodes_listWidget.selectedIndexes()
        selected_nodes_indexes = [i.row() for i in selected_nodes_indexes]
        selected_nodes_indexes.sort()
        selected_nodes_indexes.reverse()
        [self.coplanar_nodes.pop(i) for i in selected_nodes_indexes]
        self._refresh_nodes_list()
        self._refresh_up_vector()

    def _refresh_axes_buttons(self):
        aim_buttons = [self.ui.aim_x_button, self.ui.aim_y_button, self.ui.aim_z_button]
        up_buttons = [self.ui.up_x_button, self.ui.up_y_button, self.ui.up_z_button]
        self._refresh_button_groups(aim_buttons, up_buttons)
        self._refresh_up_vector()

    def _refresh_mirror_buttons(self):
        forward_buttons = [self.ui.mirror_forward_x_button,
                           self.ui.mirror_forward_y_button,
                           self.ui.mirror_forward_z_button]
        up_buttons = [self.ui.mirror_up_x_button, self.ui.mirror_up_y_button, self.ui.mirror_up_z_button]
        self._refresh_button_groups(forward_buttons, up_buttons)
        self._refresh_mirror_side()

    def _refresh_mirror_side(self):
        if not self.ui.mirror_groupBox.isChecked():
            self.mirror_side_vector = None
            self.ui.mirror_side_label.setText('')
            return
        checked_forward_button = self.ui.mirror_forward_buttonGroup.checkedButton()
        checked_up_button = self.ui.mirror_up_buttonGroup.checkedButton()

        axis_indices = [self.mirror_button_to_index[b] for b in [checked_forward_button, checked_up_button]]
        side_index = 0
        for i in range(3):
            if i not in axis_indices:
                side_index = i
                continue
        side_vector = self.side_index_to_vector[side_index]
        side_modifier = -1
        if self.ui.mirror_flip_side_checkbox.isChecked():
            side_modifier = 1

        side_vector = (side_vector[0]*side_modifier, side_vector[1]*side_modifier, side_vector[2]*side_modifier)
        self.mirror_side_vector = om.MVector(side_vector)

        side_vector_text = self.side_vector_to_text[side_vector]
        self.ui.mirror_side_label.setText(side_vector_text)

    @staticmethod
    def _refresh_button_groups(buttons1, buttons2):
        for i, (aim_b, up_b) in enumerate(zip(buttons1, buttons2)):
            aim_checked = aim_b.isChecked()
            up_checked = up_b.isChecked()
            aim_b.setEnabled(not up_checked)
            up_b.setEnabled(not aim_checked)
