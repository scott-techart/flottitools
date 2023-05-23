import os

import pymel.core as pm
import PySide2.QtWidgets as QtWidgets
import PySide2.QtCore as QtCore
import PySide2.QtGui as QtGui

import flottitools.path_consts as path_consts
import flottitools.ui as flottiui
import flottitools.utils.materialutils as matutils
import flottitools.utils.meshutils as meshutils
import flottitools.utils.skinutils as skinutils
import flottitools.validation.materials as val_mats
import flottitools.validation.meshes as val_mesh
import flottitools.validation.skinmesh as val_skmesh


VALIDATOR_UI = None
# categories
CATEGORY_SKMESH = 'skinned mesh'
CATEGORY_MESH = 'static mesh'
CATEGORY_MAT = 'materials'

# presets
PRESET_ALL = 'All'
PRESET_NONE = 'None'
PRESET_MATERIALS_ONLY = 'Materials Only'
PRESET_SKINNED_MESHES = 'Skinned Meshes'
PRESET_MESHES = 'Meshes'

# severity
SEVERITY_ERROR = 0
SEVERITY_WARNING = 1
SEVERITY_PASS = 2

# colors
COLOR_ERROR = 'maroon'
COLOR_WARNING = 'darkgoldenrod'
COLOR_PASS = 'green'
COLOR_UNKNOWN = 'indigo'

SEVERITY_COLOR_MAP = {
    SEVERITY_ERROR: COLOR_ERROR,
    SEVERITY_WARNING: COLOR_WARNING,
    SEVERITY_PASS: COLOR_PASS,
    None: COLOR_UNKNOWN
}


def validator_launch(parent_to_notify=None, launch_hidden=False):
    global VALIDATOR_UI
    if VALIDATOR_UI:
        VALIDATOR_UI.deleteLater()
    VALIDATOR_UI = ValidatorMayaWindow(parent_to_notify)
    if not launch_hidden:
        VALIDATOR_UI.show()
    return VALIDATOR_UI


class ValidatorMayaWindow(flottiui.FlottiMayaWindowDesignerUI):
    window_title = "Validator"
    ui_designer_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'ui', 'validator.ui'))

    def __init__(self, parent_to_notify=None):
        super(ValidatorMayaWindow, self).__init__()
        self.resize(0, 390)
        self.parent_to_notify = parent_to_notify
        self.initialized_issues = []
        self.category_to_widget_map = {CATEGORY_SKMESH: self.ui.issues_skinnedmesh_viswidget,
                                       CATEGORY_MESH: self.ui.issues_staticmesh_viswidget,
                                       CATEGORY_MAT: self.ui.issues_materials_viswidget}
        self.nodes_whitelist = []
        self.nodes_blacklist = []

        self.issues = [ExceedingVertsIssueWidget,
                       NonNormalizedVertsIssueWidget,
                       ExceedingJointsIssueWidget,
                       ExtraRootJointsIssueWidget,
                       JointsWithDuplicatedNamesIssueWidget,
                       MissingUVsIssueWidget,
                       MultipleShapeNodesIssueWidget,
                       DirtyHistoryMeshIssueWidget,
                       OverlappingVerticesIssueWidget,
                       VertexColorIssueWidget]

        self.ui.scene_extras_vis_widget.setVisible(False)
        self.ui.pbar_vis_widget.setVisible(False)
        self.ui.progress_bar = flottiui.ProgressBarWithLabel()
        self.ui.pbar_vis_widget.layout().addWidget(self.ui.progress_bar)

        self._add_issues()
        self._init_presets()
        self._init_scene_nodes()
        self._init_ui_connections()
        self._rotated_buttons_setup()

    def validate_scene(self):
        progress_bars = [self.ui.progress_bar]
        if self.parent_to_notify:
            progress_bars.append(self.parent_to_notify.progress_bar)
        issues_to_validate = self._get_all_issues_to_validate()
        pm.waitCursor(state=True)
        try:
            self.ui.pbar_vis_widget.setVisible(True)
            for pb in progress_bars:
                pb.reset()
                pb.set_maximum(len(issues_to_validate))
            for issue in issues_to_validate:
                for pb in progress_bars:
                    pb.update_label_and_iter_val('Validating {}'.format(issue.label))
                self._scroll_issues_to_issue(issue)
                issue.validate_issue(update_parent_ui=False)
            self.ui.pbar_vis_widget.setVisible(False)
            self.update_ui_elements_based_on_issue_results()
        except Exception as e:
            pm.waitCursor(state=False)
            raise e
        pm.waitCursor(state=False)

    def fix_all(self):
        issues_to_fix = [i for i in self.get_dirty_issues() if i.has_fix_method]
        [issue.fix_issue() for issue in issues_to_fix]
        self.validate_scene()

    def refresh_nodes_lists(self, white_list_nodes=None):
        all_val_nodes = self._get_all_nodes_to_validate()
        if white_list_nodes:
            self.nodes_whitelist = white_list_nodes
        else:
            self.nodes_whitelist = []
            self.nodes_blacklist =[]
            for node in all_val_nodes:
                self.nodes_whitelist.append(node)

        self._refresh_nodes_list_widgets()

    def refresh_presets_list(self):
        self.ui.presets_listWidget.clear()
        [self.ui.presets_listWidget.addItem(n) for n in self.preset_names]
        self.ui.presets_listWidget.setCurrentRow(0)

    def preset_selection_changed(self):
        selected_items = self.ui.presets_listWidget.selectedItems()
        selected_names = [x.text() for x in selected_items]
        self.set_issue_checked_states_to_presets(selected_names)
        self.refresh_nodes_lists()

    def set_issue_checked_states_to_presets(self, preset_names):
        selected_preset_states = [self.preset_name_to_issue_state[n] for n in preset_names]
        combined_selected_preset_states = [sum(x) for x in zip(*selected_preset_states)]
        first_checked_issue = None
        for issue, val in zip(self.initialized_issues, combined_selected_preset_states):
            issue.ui.issue_checkBox.setChecked(val)
            if first_checked_issue is None:
                if val:
                    first_checked_issue = issue
        first_checked_issue = first_checked_issue or self.initialized_issues[0]
        self._scroll_issues_to_issue(first_checked_issue)

    def set_preset_selection(self, preset_names):
        indices = [self.preset_names.index(x) for x in preset_names]
        for i in range(self.ui.presets_listWidget.count()):
            state = False
            if i in indices:
                state = True
            self.ui.presets_listWidget.item(i).setSelected(state)

    def blacklist_selected_items(self):
        selected_whitelist_indexes = self.ui.objects_val_listWidget.selectedIndexes()
        selected_whitelist_indexes = [i.row() for i in selected_whitelist_indexes]
        self._move_nodes_and_sort(self.nodes_whitelist, self.nodes_blacklist, selected_whitelist_indexes)
        self._refresh_nodes_list_widgets()

    def blacklist_all_items(self):
        self._move_nodes_and_sort(self.nodes_whitelist, self.nodes_blacklist, list(range(len(self.nodes_whitelist))))
        self._refresh_nodes_list_widgets()

    def whitelist_selected_items(self):
        selected_blacklist_indexes = self.ui.objects_skip_listWidget.selectedIndexes()
        selected_blacklist_indexes = [i.row() for i in selected_blacklist_indexes]
        self._move_nodes_and_sort(self.nodes_blacklist, self.nodes_whitelist, selected_blacklist_indexes)
        self._refresh_nodes_list_widgets()

    def set_parent_to_notify(self, parent_to_notify):
        self.parent_to_notify = parent_to_notify

    def update_ui_elements_based_on_issue_results(self):
        dirty_issues = self.get_dirty_issues()
        if not dirty_issues:
            scroll_area_stylesheet = "QScrollArea {}"
            self.ui.scrollArea.setStyleSheet(scroll_area_stylesheet)
            self.ui.scene_extras_vis_widget.setVisible(False)
            if not self._all_issues_not_checked_yet() and self.parent_to_notify:
                self.parent_to_notify.update_validation_severity(SEVERITY_PASS)
            return
        self.ui.scene_extras_vis_widget.setVisible(True)
        self._scroll_issues_to_issue(dirty_issues[0])

        max_severity = SEVERITY_WARNING
        for issue in dirty_issues:
            if issue.severity == SEVERITY_ERROR:
                max_severity = issue.severity
                break
        color = SEVERITY_COLOR_MAP[max_severity]
        scroll_area_stylesheet = "QScrollArea { border: 5px solid "+color+"; }"
        self.ui.scrollArea.setStyleSheet(scroll_area_stylesheet)
        color_style_sheet_string = get_style_sheet_string_from_severity(max_severity)
        self.ui.all_fix_button.setStyleSheet(color_style_sheet_string)
        self.ui.all_results_button.setStyleSheet(color_style_sheet_string)
        fixable_issues = [x for x in dirty_issues if x.has_fix_method]
        tool_tip = None
        if not fixable_issues:
            tool_tip = 'No automatic fixes available for current issues. Please fix manually.'
        self.ui.all_fix_button.setEnabled(bool(fixable_issues))
        self.ui.all_fix_button.setToolTip(tool_tip)
        if self.parent_to_notify:
            self.parent_to_notify.update_validation_severity(max_severity)

    def _scroll_issues_to_issue(self, issue):
        i = self.initialized_issues.index(issue)
        self._scroll_issues_to_index(i)

    def _scroll_issues_to_index(self, index):
        scroll_bar = self.ui.scrollArea.verticalScrollBar()
        issue_height = 44
        scroll_to_val = index * issue_height
        scroll_bar.setValue(scroll_to_val)

    def copy_all_reports(self):
        dirty_issues = self.get_dirty_issues()
        lines = ''
        for issue in dirty_issues:
            lines += 'Nodes with {}:\n    '.format(issue.label)
            error_node_labels = [x.node_label for x in issue.validation_results]
            lines += ', '.join(error_node_labels)
            lines += '\n'
        clipboard = QtGui.QGuiApplication.clipboard()
        clipboard.clear()
        clipboard.setText(lines)

    def _refresh_nodes_list_widgets(self):
        self.ui.objects_val_listWidget.clear()
        self.ui.objects_skip_listWidget.clear()
        [self.ui.objects_val_listWidget.addItem(node.name()) for node in self.nodes_whitelist]
        [self.ui.objects_skip_listWidget.addItem(node.name()) for node in self.nodes_blacklist]

    def _get_all_issues_to_validate(self):
        issues_to_validate = []
        for issue in self.initialized_issues:
            if issue.ui.issue_checkBox.isChecked():
                issues_to_validate.append(issue)
        return issues_to_validate

    def get_dirty_issues(self, issues_to_validate=None):
        issues_to_validate = issues_to_validate or self._get_all_issues_to_validate()
        dirty_issues = [x for x in issues_to_validate if x.dirty is True]
        return dirty_issues

    def _all_issues_not_checked_yet(self, issues_to_validate=None):
        issues_to_validate = issues_to_validate or self._get_all_issues_to_validate()
        n = [True for x in issues_to_validate if x.dirty is None]
        if n:
            return all(n)
        return False

    def _add_issue(self, issue):
        new_issue = issue(self)
        self.initialized_issues.append(new_issue)
        category_widget = self.category_to_widget_map[new_issue.category]
        category_widget.layout().addWidget(new_issue)
        category_widget.layout().addWidget(flottiui.QHLine())

    def _add_issues(self):
        for issue in self.issues:
            self._add_issue(issue)

    def _get_all_nodes_to_validate(self):
        all_val_nodes = []
        for issue in self._get_all_issues_to_validate():
            all_val_nodes.extend(issue.get_nodes_to_validate())
        all_val_nodes = list(set(all_val_nodes))
        all_val_nodes.sort()
        return all_val_nodes

    def _init_ui_connections(self):
        self.ui.validate_scene_button.clicked.connect(self.validate_scene)
        self.ui.all_results_button.clicked.connect(self.copy_all_reports)
        self.ui.all_fix_button.clicked.connect(self.fix_all)
        self.ui.objects_refresh_button.clicked.connect(self.refresh_nodes_lists)
        self.ui.objects_skipall_button.clicked.connect(self.blacklist_all_items)
        self.ui.objects_skip_button.clicked.connect(self.blacklist_selected_items)
        self.ui.objects_val_button.clicked.connect(self.whitelist_selected_items)
        self.ui.presets_listWidget.itemSelectionChanged.connect(self.preset_selection_changed)

    def _init_presets(self):
        self.ui.presets_groupBox.setVisible(False)
        self.preset_names = [PRESET_ALL, PRESET_SKINNED_MESHES, PRESET_MESHES, PRESET_MATERIALS_ONLY, PRESET_NONE]
        self.preset_name_to_issue_state = {}
        for preset_name in self.preset_names:
            self.preset_name_to_issue_state.setdefault(preset_name, [])
            for issue in self.issues:
                val = False
                if preset_name in issue.presets:
                    val = True
                self.preset_name_to_issue_state[preset_name].append(val)
        self.refresh_presets_list()

    def _init_scene_nodes(self):
        self.ui.objects_groupBox.setVisible(False)
        self.refresh_nodes_lists()

    def _rotated_buttons_setup(self):
        self.ui.presets_toggle_button.deleteLater()
        self.ui.objects_toggle_button.deleteLater()

        new_presets_button = flottiui.RotatedButton('Presets')
        new_presets_button.setMaximumWidth(24)
        new_presets_button.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        new_presets_button.setCheckable(True)
        new_presets_button.setChecked(False)
        new_presets_button.toggled.connect(lambda x: self.ui.presets_groupBox.setVisible(x))
        self.ui.presets_toggle_button = new_presets_button
        new_nodes_button = flottiui.RotatedButton('Nodes')
        new_nodes_button.setMaximumWidth(24)
        new_nodes_button.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        new_nodes_button.setCheckable(True)
        new_nodes_button.setChecked(False)
        new_nodes_button.toggled.connect(lambda x: self.ui.objects_groupBox.setVisible(x))

        vertical_font = new_nodes_button.font()
        vertical_font.setStretch(QtGui.QFont.Expanded)
        new_nodes_button.setFont(vertical_font)

        new_presets_button.setFont(vertical_font)
        self.ui.objects_toggle_button = new_nodes_button
        self.ui.verticalLayout_9.addWidget(new_presets_button)
        self.ui.verticalLayout_9.addWidget(new_nodes_button)

    @staticmethod
    def _move_nodes_and_sort(origin_list, dest_list, indexes):
        [dest_list.append(origin_list[i]) for i in indexes]
        dest_list.sort()
        indexes.sort()
        indexes.reverse()
        [origin_list.pop(i) for i in indexes]


class ValidationIssueWidget(flottiui.FlottiMayaWindowDesignerUI):
    window_title = "Validation Issue"
    ui_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'ui'))
    ui_designer_file_path = os.path.abspath(os.path.join(ui_path, 'validation_issue.ui'))

    preval_path = os.path.abspath(os.path.join(ui_path, 'icon_val_preval.png'))
    success_path = os.path.abspath(os.path.join(ui_path, 'icon_val_success.png'))
    warning_path = os.path.abspath(os.path.join(ui_path, 'icon_val_warning.png'))
    error_path = os.path.abspath(os.path.join(ui_path, 'icon_val_error.png'))
    unknown_path = os.path.abspath(os.path.join(ui_path, 'icon_val_unknown.png'))

    severity_icon_map = {SEVERITY_ERROR: error_path,
                         SEVERITY_WARNING: warning_path,
                         None: unknown_path}

    report_widget = None
    category = None
    label = None
    description = None
    issue_report_label = 'Error in {}'
    severity = None
    has_fix_method = True

    error_msg = 'This button does not work yet. If you would like this button to work please contact Scott.\n'
    error_msg += 'Or better yet, contact your PO and tell them how much time it would save you if Scott made this work.'

    def __init__(self, validator_instance):
        super(ValidationIssueWidget, self).__init__()
        self.validator_instance = validator_instance
        self.dirty = None
        self.ui.issue_label.setText(self.description)
        self.ui.issue_icon_label.setPixmap(self.preval_path)
        self.report_widget = self.report_widget or IssueReportWidget
        self.validation_results = None

        self.ui.issue_report_pushButton.clicked.connect(self.get_info)
        self.ui.validate_button.clicked.connect(self.validate_issue)
        self.ui.issue_fix_pushButton.clicked.connect(self.fix_issue)
        self._init_progress_bar()

    def validate_issue(self, update_parent_ui=True):
        nodes_to_validate = self.get_whitelisted_nodes_to_validate()
        result = None
        if nodes_to_validate:
            self.ui.pbar_vis_widget.setVisible(True)
            result = self.validate(nodes_to_validate)
            self.ui.pbar_vis_widget.setVisible(False)

        if result:
            self.dirty = True
            self.ui.actions_enabled_hbox.setEnabled(True)
            [val_node.assess_severity() for val_node in result]
            severity = min([val_node.severity for val_node in result])
            severity_color = SEVERITY_COLOR_MAP.get(severity, COLOR_UNKNOWN)
            self._set_buttons_color(severity_color)
            icon_path = self.severity_icon_map.get(severity, COLOR_UNKNOWN)
            self.ui.issue_icon_label.setPixmap(icon_path)
            if not self.has_fix_method:
                self.ui.issue_fix_pushButton.setEnabled(self.has_fix_method)
                self.ui.issue_fix_pushButton.setToolTip(
                    'No automatic fix available for this issue. Please fix manually.')
            print('Attention! {} encountered errors to report.'.format(self.label))
        else:
            self.ui.actions_enabled_hbox.setEnabled(False)
            self.dirty = False
            self.ui.issue_icon_label.setPixmap(self.success_path)
            self._set_buttons_color('green')
            if not self.has_fix_method:
                self.ui.issue_fix_pushButton.setToolTip(None)
            print('Success! {} did not encounter any errors to report.'.format(self.label))
        if update_parent_ui:
            self.validator_instance.update_ui_elements_based_on_issue_results()
        self.validator_instance.update_ui_elements_based_on_issue_results()

    def validate(self, nodes_to_validate=None):
        raise NotImplementedError(self.error_msg)

    @staticmethod
    def validation_method(white_listed_nodes=None):
        return None

    def get_info(self):
        report_widget_instance = self.report_widget(self)
        report_widget_instance.show()

    def fix(self):
        raise NotImplementedError(self.error_msg)

    def get_nodes_to_validate(self):
        raise NotImplementedError(self.error_msg)

    def get_whitelisted_nodes_to_validate(self):
        all_nodes = self.get_nodes_to_validate()
        if not self.all_whitelist_nodes_exist():
            self.validator_instance.refresh_nodes_lists()
        nodes_to_validate = [x for x in all_nodes if x in self.validator_instance.nodes_whitelist]
        return nodes_to_validate

    def all_whitelist_nodes_exist(self):
        return not any([not x.exists() for x in self.validator_instance.nodes_whitelist])

    def fix_issue(self):
        print('Performing: ' + self.fix.__name__)
        self.fix()
        self.validate_issue()

    def _set_buttons_color(self, color):
        color_string = "background-color: {}".format(color)
        self.ui.validate_button.setStyleSheet(color_string)
        self.ui.issue_fix_pushButton.setStyleSheet(color_string)
        self.ui.issue_report_pushButton.setStyleSheet(color_string)

    def _init_progress_bar(self):
        self.ui.pbar_vis_widget.setVisible(False)
        self.ui.progress_bar.deleteLater()
        self.ui.progress_bar = flottiui.ProgressBarWithLabel()
        self.ui.pbar_vis_widget.layout().addWidget(self.ui.progress_bar)

    @staticmethod
    def format_validation_results(validation_results, issue_label=None, severity=None):
        """
        Default behavior for wrapping validation data in ValidatedNodeUIContainer() and IssueDataUIContainer().
        validation_results should be a dict with the validated node as key and its issues as values.

        Overwrite method if your validation data is formatted differently.
        """
        issue_label = issue_label or 'Error in {}'
        val_nodes_with_issues = []
        for validated_node, issues in validation_results.items():
            val_node = ValidatedNodeUIContainer(validated_node)
            issue_label = issue_label.format(val_node.node_label)
            issue_data = IssueDataUIContainer(issues, val_node, issue_label, severity=severity)
            val_node.append_issue(issue_data)
            val_node.assess_severity()
            val_nodes_with_issues.append(val_node)
        return val_nodes_with_issues


class ValidatedNodeUIContainer:
    node = None
    severity = None
    issues = []
    node_label = None
    node_label_background_color = None

    def __init__(self, dag_node, issues=None, node_label=None):
        self.node_label = node_label or dag_node.nodeName()
        self.node = dag_node
        self.issues = issues or []

    def assess_severity(self):
        try:
            self.severity = min([issue.severity for issue in self.issues])
        except ValueError:
            # if there are no issues min() will provoke a ValueError
            pass
        self.node_label_background_color = SEVERITY_COLOR_MAP.get(self.severity, COLOR_UNKNOWN)
        return self.severity

    def append_issue(self, issue):
        self.issues.append(issue)


class IssueDataUIContainer:
    issue_label = None
    issue_group_box = None
    issue_color = None
    data = None
    parent_val_data = None
    severity = None

    def __init__(self, issue_data, parent_val_node=None, issue_label=None, issue_group_box=None, severity=None):
        self.data = issue_data
        self.parent_val_data = parent_val_node
        self.issue_label = issue_label
        self.issue_group_box = issue_group_box
        self.set_severity(severity)

    def set_severity(self, severity):
        self.severity = severity
        self.issue_color = SEVERITY_COLOR_MAP.get(self.severity, COLOR_UNKNOWN)


class IssueReportWidget(flottiui.FlottiMayaWindowDesignerUI):
    window_title = "Validation Issues Report"
    ui_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'ui'))
    ui_designer_file_path = os.path.abspath(os.path.join(ui_path, 'error_report.ui'))

    def __init__(self, issue_instance):
        super(IssueReportWidget, self).__init__()
        self.issue_instance = issue_instance
        self.validation_results = self.issue_instance.validation_results
        self.validation_data = self._get_validation_data()
        self.item_label_to_node_data = {}
        self.group_box_title_to_issue_data = {}

        self.refresh_error_list()
        self.select_all()
        self.refresh_details_list()
        self.ui.report_errorlist_listWidget.itemSelectionChanged.connect(self._error_selection_changed)
        self.ui.nodes_selectall_button.clicked.connect(self.select_all)
        self.ui.nodes_deselectall_button.clicked.connect(self.deselect_all)
        self.ui.details_copytocb_button.clicked.connect(self.copy_all_to_clipboard)
        self.ui.details_copyselectedtocb_button.clicked.connect(self.copy_selected_to_clipboard)

    def _get_validation_data(self):
        to_sort = []
        for val_node in self.validation_results:
            for i, issue in enumerate(val_node.issues):
                if not issue.issue_label:
                    issue.issue_label = '{0} Error #{1}'.format(val_node.node_label, i+1)
            to_sort.append((val_node.node_label, val_node))
        # sort alphabetically by node name
        try:
            to_sort.sort()
        except TypeError:
            pass
        _, sorted_validation_data = zip(*to_sort)
        return sorted_validation_data

    def refresh_error_list(self):
        self.ui.report_errorlist_listWidget.clear()
        for val_data in self.validation_data:
            list_item = QtWidgets.QListWidgetItem(val_data.node_label)
            list_item.setBackground(QtGui.QColor(val_data.node_label_background_color))
            self.item_label_to_node_data[val_data.node_label] = val_data
            self.ui.report_errorlist_listWidget.addItem(list_item)

    def refresh_details_list(self, selected_item_labels=None):
        selected_item_labels = selected_item_labels or self.ui.report_errorlist_listWidget.selectedItems()
        # clear the report details scroll area layout.
        details_layout = self.ui.reportdetails_contents_vbox.layout()
        self.clear_layout(details_layout)

        # fill it back up with latest stuff
        selected_val_data = []
        for item_label in selected_item_labels:
            val_node_data = self.item_label_to_node_data[item_label.text()]
            selected_val_data.append(val_node_data)

        for val_data in selected_val_data:
            for issue in val_data.issues:
                gbox_vis = flottiui.GroupBoxVisibilityToggle(issue.issue_label)
                gb_stylesheet = "QGroupBox { border: 5px solid " + issue.issue_color + "; }"
                gbox_vis.setStyleSheet(gb_stylesheet)
                details_layout.addWidget(gbox_vis)
                issue.issue_group_box = gbox_vis
                self.format_issue_and_add_to_group_box(issue, gbox_vis.visibility_widget.layout())
                self.group_box_title_to_issue_data[gbox_vis.title()] = issue

    def select_all(self):
        self.ui.report_errorlist_listWidget.selectAll()

    def deselect_all(self):
        self.ui.report_errorlist_listWidget.clearSelection()

    def copy_all_to_clipboard(self):
        issues = []
        for val_data in self.validation_data:
            issues.extend(val_data.issues)
        data_for_clipboard = self.format_issues_for_clipboard(issues)
        clipboard = QtGui.QGuiApplication.clipboard()
        clipboard.clear()
        clipboard.setText(data_for_clipboard)

    def copy_selected_to_clipboard(self):
        details_layout = self.ui.reportdetails_contents_vbox.layout()
        stuff = []
        for i in range(details_layout.count()):
            group_box = details_layout.itemAt(i).widget()
            if group_box.isChecked():
                issue_data = self.group_box_title_to_issue_data.get(group_box.title())
                if issue_data:
                    stuff.append(issue_data)
        if stuff:
            data_for_clipboard = self.format_issues_for_clipboard(stuff)
            clipboard = QtGui.QGuiApplication.clipboard()
            clipboard.clear()
            clipboard.setText(data_for_clipboard)

    def _error_selection_changed(self):
        selected_item_labels = self.ui.report_errorlist_listWidget.selectedItems()
        self.refresh_details_list(selected_item_labels)
        selected_item_nodes = [self.item_label_to_node_data[x.text()].node for x in selected_item_labels]
        pm.select(selected_item_nodes, r=True)

    @staticmethod
    def format_issue_and_add_to_group_box(issue_data, issue_layout):
        """
        Overwrite this method with a widget that displays your validation data nice user-friendly format.

        Add your widget to issue_layout with issue_layout.addWidget(your_widget)
        """
        lazy_issue_widget = QtWidgets.QTextEdit()
        lazy_issue_widget.append(str(issue_data.data))
        lazy_issue_widget.setReadOnly(True)
        issue_layout.addWidget(lazy_issue_widget)

    @staticmethod
    def format_issues_for_clipboard(issues):
        """
        Overwrite this method with your own that formats the validation issue report data
          into a nice human-readable message that will be copied to the user's clipboard.
        """
        lines = 'Validation report:\n'
        for issue in issues:
            lines += 'Errors encountered in {0}: \n    {1}\n'.format(
                issue.parent_val_data.node_label, issue.data)
        return lines


class ExceedingVertsIssueReportWidget(IssueReportWidget):
    window_title = "Validate >4 Influences Per Vert Report"

    @staticmethod
    def format_issue_and_add_to_group_box(issue, issue_layout):
        skinned_mesh = issue.parent_val_data.node
        vert_indexes_and_value_pairs = [(skinned_mesh.vtx[x], len(y.keys())) for x, y in issue.data.items()]
        _setup_simple_vert_table(vert_indexes_and_value_pairs, 'Influence Count', issue_layout)

    @staticmethod
    def format_issues_for_clipboard(issues):
        lines = 'Validation report:\n'
        for issue in issues:
            parent_node_label = issue.parent_val_data.node_label
            skinned_mesh = issue.parent_val_data.node
            lines += '{0} has verts with more than four influences. Total bad verts in mesh: {1} \n'.format(
                parent_node_label, len(issue.data))
            for vert_index, infs_to_wts in issue.data.items():
                lines += '    {0}  total influences {1}:\n'.format(
                    skinned_mesh.vtx[vert_index].name(), len(infs_to_wts))
                for influence, weight in infs_to_wts.items():
                    lines += '        {0} : {1}\n'.format(influence.name(), weight)
        return lines


class ExceedingVertsIssueWidget(ValidationIssueWidget):
    category = CATEGORY_SKMESH
    presets = [PRESET_ALL, PRESET_SKINNED_MESHES]
    label = 'Exceeding Verts'
    description = 'Vertices with more than four influences.'
    issue_report_label = 'Vertices in {} with more than four influences'
    severity = SEVERITY_ERROR

    report_widget = ExceedingVertsIssueReportWidget

    def validate(self, skinned_meshes=None):
        meshes_to_bad_verts = val_skmesh.get_exceeding_verts_from_scene(
            skinned_meshes, self.ui.progress_bar)
        self.validation_results = self.format_validation_results(meshes_to_bad_verts,
                                                                 self.issue_report_label,
                                                                 severity=self.severity)
        return self.validation_results

    def fix(self):
        self.ui.pbar_vis_widget.setVisible(True)
        exceeding_meshes_dict = self._format_val_results_for_fix()
        val_skmesh.prune_exceeding_influences_from_scene_validation(exceeding_meshes_dict, self.ui.progress_bar)
        self.ui.pbar_vis_widget.setVisible(False)

    def get_nodes_to_validate(self):
        return skinutils.get_skinned_meshes_from_scene()

    def _format_val_results_for_fix(self):
        exceeding_meshes_dict = {}
        for val_node in self.validation_results:
            issue_data = val_node.issues[0].data
            exceeding_meshes_dict[val_node.node] = issue_data
        return exceeding_meshes_dict


class NonNormalizedVertsIssueReportWidget(IssueReportWidget):
    window_title = "Validate Non-normalized Vertices Report"

    @staticmethod
    def format_issue_and_add_to_group_box(issue, issue_layout):
        skinned_mesh = issue.parent_val_data.node
        vert_and_data_pairs = [(skinned_mesh.vtx[x], y) for x, y in issue.data.items()]
        _setup_simple_vert_table(vert_and_data_pairs, 'Total Weight', issue_layout)

    @staticmethod
    def format_issues_for_clipboard(issues):
        lines = 'Validation report:\n'
        for issue in issues:
            parent_node_label = issue.parent_val_data.node_label
            skinned_mesh = issue.parent_val_data.node
            lines += '{0} has non-normalized verts. Total bad verts in mesh: {1} \n'.format(
                parent_node_label, len(issue.data))
            for vert_index, weight_total in issue.data.items():
                lines += '    {0}  total weight: {1}\n'.format(skinned_mesh.vtx[vert_index].name(), weight_total)
        return lines


class NonNormalizedVertsIssueWidget(ValidationIssueWidget):
    category = CATEGORY_SKMESH
    presets = [PRESET_ALL, PRESET_SKINNED_MESHES]
    label = 'Non-normalized Verts'
    description = 'Vertices with non normalized weights.'
    issue_report_label = 'Vertices in {} with non-normalized weights'
    severity = SEVERITY_ERROR
    report_widget = NonNormalizedVertsIssueReportWidget

    def validate(self, skinned_meshes=None):
        validation_results = val_skmesh.get_non_normalized_verts_from_scene(
            skinned_meshes, progress_bar=self.ui.progress_bar)
        self.validation_results = self.format_validation_results(validation_results,
                                                                 self.issue_report_label,
                                                                 severity=self.severity)
        return self.validation_results

    def fix(self):
        self.ui.pbar_vis_widget.setVisible(True)
        formatted_val_results = self.format_val_nodes_for_fix_method()
        val_skmesh.normalize_skinned_meshes(formatted_val_results, self.ui.progress_bar)
        self.ui.pbar_vis_widget.setVisible(False)

    def format_val_nodes_for_fix_method(self):
        skinned_meshes = [v.node for v in self.validation_results]
        return skinned_meshes

    def get_nodes_to_validate(self):
        return skinutils.get_skinned_meshes_from_scene()


class ExceedingJointsIssueReportWidget(IssueReportWidget):
    window_title = "Validate >64 Weighted Influences Report"

    @staticmethod
    def format_issue_and_add_to_group_box(issue, issue_layout):
        count = len(issue.data)
        influence_and_value_pairs = [(x, count) for x in issue.data]
        _setup_simple_vert_table(influence_and_value_pairs, 'Total Influences', issue_layout)

    @staticmethod
    def format_issues_for_clipboard(issues):
        lines = 'Validation report:\n'
        for issue in issues:
            lines += '{0} has greater than 0.0 skinning on more than 64 joints. Influence Count: {1} \n    {2}\n'.format(
                issue.parent_val_data.node_label, len(issue.data), issue.data)
        return lines


class ExceedingJointsIssueWidget(ValidationIssueWidget):
    category = CATEGORY_SKMESH
    presets = [PRESET_ALL, PRESET_SKINNED_MESHES]
    label = 'Too Many Joints'
    description = 'Meshes skinned to more than 64 joints.'
    issue_report_label = '{} is skinned to more than 64 joints'
    severity = SEVERITY_ERROR
    report_widget = ExceedingJointsIssueReportWidget
    has_fix_method = False

    def validate(self, skinned_meshes=None):
        meshes_to_joint_count = val_skmesh.get_joint_counts_from_scene(
            skinned_meshes, progress_bar=self.ui.progress_bar)
        self.validation_results = self.format_validation_results(meshes_to_joint_count,
                                                                 self.issue_report_label,
                                                                 severity=self.severity)
        return self.validation_results

    def get_nodes_to_validate(self):
        return skinutils.get_skinned_meshes_from_scene()


class ExtraRootJointsIssueReportWidget(IssueReportWidget):
    window_title = "Validate extra root joints report."

    @staticmethod
    def format_issue_and_add_to_group_box(issue, issue_layout):
        list_widget = QtWidgets.QListWidget()
        list_widget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        widget_items = [QtWidgets.QListWidgetItem(str(x)) for x in issue.data]
        [list_widget.addItem(x) for x in widget_items]

        def on_sel_changed():
            selected_indexes = list_widget.selectedIndexes()
            selected_nodes = [issue.data[i.row()] for i in selected_indexes]
            pm.select(selected_nodes)
        list_widget.itemSelectionChanged.connect(on_sel_changed)
        issue_layout.addWidget(list_widget)

    @staticmethod
    def format_issues_for_clipboard(issues):
        lines = 'Validation report:\n'
        for issue in issues:
            lines += "{0}'s skeleton has more than one root joint. This may be due to a joint parented to a group node. Extra root joints:\n".format(
                issue.parent_val_data.node_label)
            for extra_root in issue.data:
                lines += '    {0}\n'.format(extra_root.name())
        return lines


class ExtraRootJointsIssueWidget(ValidationIssueWidget):
    category = CATEGORY_SKMESH
    presets = [PRESET_ALL, PRESET_SKINNED_MESHES]
    label = 'Extra Root Joints'
    description = 'Skeletons that have more than one root.'
    issue_report_label = '{} has more than one root joint in its skeleton.'
    severity = SEVERITY_ERROR
    report_widget = ExtraRootJointsIssueReportWidget
    has_fix_method = False

    def validate(self, skinned_meshes=None):
        meshes_to_extra_roots = val_skmesh.get_extra_skeleton_roots_from_scene(
            skinned_meshes, progress_bar=self.ui.progress_bar)
        self.validation_results = self.format_validation_results(meshes_to_extra_roots,
                                                                 self.issue_report_label,
                                                                 severity=self.severity)
        return self.validation_results

    def get_nodes_to_validate(self):
        return skinutils.get_skinned_meshes_from_scene()


class MediaNotInTexturePathsIssueReportWidget(IssueReportWidget):
    window_title = "Validate Materials Report"

    @staticmethod
    def format_issue_and_add_to_group_box(issue, issue_layout):
        mat_node = issue.parent_val_data.node
        connected_meshes = mat_node.outColor.outputs()[0].listConnections(type='mesh')
        friendly_meshes_string = ''
        for mesh in connected_meshes:
            if friendly_meshes_string:
                friendly_meshes_string += ', '
            friendly_meshes_string += mesh.nodeName()

        table = QtWidgets.QTableWidget()
        table.setColumnCount(len(issue.data))
        table.setRowCount(4)
        table.setMinimumHeight(5 * 24)
        issue_layout.addWidget(table)

        # Set the table headers
        table.setVerticalHeaderLabels(["Bad File Nodes", "Bad Paths", "Assigned to Meshes", "Long Description"])

        cell_index_to_method = {}
        for y, bad_file_node in enumerate(issue.data):
            bad_path = bad_file_node.fileTextureName.get()
            file_tableitem = QtWidgets.QTableWidgetItem(bad_file_node.nodeName())
            badpath_tableitem = QtWidgets.QTableWidgetItem(bad_path)
            meshes_tableitem = QtWidgets.QTableWidgetItem(friendly_meshes_string)
            description_tableitem = QtWidgets.QTableWidgetItem(
                "Texture paths should point to a texture in your branch's media folder.")

            for x, each in enumerate([file_tableitem, badpath_tableitem, meshes_tableitem, description_tableitem]):
                each.setFlags(QtCore.Qt.ItemIsEnabled)
                table.setItem(x, y, each)

            # connect the file and meshes cells on clicked to select their dag nodes
            def get_uncalled_select_file_node(file_node):
                return lambda: pm.select(file_node, r=True)

            def get_uncalled_select_meshes(meshes):
                return lambda: pm.select(meshes, r=True)
            cell_index_to_method[(0, y)] = get_uncalled_select_file_node(bad_file_node)
            cell_index_to_method[(2, y)] = get_uncalled_select_meshes(connected_meshes)

            def on_cell_clicked(cell_column_index, cell_row_index):
                uncalled_func = cell_index_to_method.get((cell_column_index, cell_row_index))
                if uncalled_func:
                    uncalled_func()
        table.cellClicked.connect(on_cell_clicked)

        table.resizeColumnsToContents()
        table.resizeRowsToContents()


class MediaNotInTexturePathsIssueWidget(ValidationIssueWidget):
    category = CATEGORY_MAT
    presets = [PRESET_ALL, PRESET_MATERIALS_ONLY]
    label = 'Bad Texture Paths'
    description = '"Media" not in texture paths.'
    issue_report_label = '{} uses a texture that does not contain "media" in the file path.'
    severity = SEVERITY_WARNING
    report_widget = MediaNotInTexturePathsIssueReportWidget
    has_fix_method = False

    def validate(self, material_nodes=None):
        mats_to_file_nodes = val_mats.get_materials_with_bad_texture_paths_from_scene(
            material_nodes, progress_bar=self.ui.progress_bar)
        self.validation_results = self.format_validation_results(mats_to_file_nodes,
                                                                 self.issue_report_label,
                                                                 severity=self.severity)
        return self.validation_results

    def get_nodes_to_validate(self):
        return matutils.get_used_materials_in_scene()


class JointsWithDuplicatedNamesIssueReportWidget(IssueReportWidget):
    window_title = "Check for duplicated joint names report"

    @staticmethod
    def format_issue_and_add_to_group_box(issue, issue_layout):
        list_widget = QtWidgets.QListWidget()
        list_widget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        widget_items = [QtWidgets.QListWidgetItem(str(x)) for x in issue.data]
        [list_widget.addItem(x) for x in widget_items]

        def on_sel_changed():
            selected_indexes = list_widget.selectedIndexes()
            selected_nodes = [issue.data[i.row()] for i in selected_indexes]
            pm.select(selected_nodes)
        list_widget.itemSelectionChanged.connect(on_sel_changed)
        issue_layout.addWidget(list_widget)


class JointsWithDuplicatedNamesIssueWidget(ValidationIssueWidget):
    category = CATEGORY_SKMESH
    presets = [PRESET_ALL, PRESET_SKINNED_MESHES]
    label = 'Joints with non unique names'
    description = 'Joints with non unique names'
    issue_report_label = '{} is sharing its name with another joint.'
    severity = SEVERITY_ERROR
    report_widget = JointsWithDuplicatedNamesIssueReportWidget
    has_fix_method = False

    def validate(self, skinned_meshes=None):
        joints_dict = val_skmesh.get_dup_joint_names_from_scene(skinned_meshes)

        self.validation_results = self.format_validation_results(joints_dict,
                                                                 self.issue_report_label,
                                                                 severity=self.severity)
        return self.validation_results

    def get_nodes_to_validate(self):
        return skinutils.get_skinned_meshes_from_scene()


class MissingUVsIssueReportWidget(IssueReportWidget):
    window_title = "Validate Missing UVs Report"

    @staticmethod
    def format_issue_and_add_to_group_box(issue, issue_layout):
        _setup_simple_report_list_widget(issue.data, issue_layout)

    @staticmethod
    def format_issues_for_clipboard(issues):
        lines = 'Validation report:\n'
        for issue in issues:
            lines += '{0} has unmapped faces. {1} faces missing UVs: \n    {2}\n'.format(
                issue.parent_val_data.node_label, len(issue.data), issue.data)
        return lines


class MissingUVsIssueWidget(ValidationIssueWidget):
    category = CATEGORY_MESH
    presets = [PRESET_ALL, PRESET_MESHES, PRESET_SKINNED_MESHES]
    label = 'Missing UVs'
    description = 'Meshes with unmapped faces.'
    issue_report_label = '{} has faces that are missing UVs.'
    severity = SEVERITY_ERROR
    report_widget = MissingUVsIssueReportWidget
    has_fix_method = False

    def validate(self, meshes=None):
        meshes_to_bad_faces = val_mesh.get_missing_uvs_from_scene(meshes, progress_bar=self.ui.progress_bar)
        self.validation_results = self.format_validation_results(meshes_to_bad_faces,
                                                                 self.issue_report_label,
                                                                 severity=self.severity)
        return self.validation_results

    def get_nodes_to_validate(self):
        return val_mesh.get_missing_uvs_from_scene()


class MultipleShapeNodesIssueReportWidget(IssueReportWidget):
    window_title = "Validate Too Many Shape Nodes Report"

    @staticmethod
    def format_issue_and_add_to_group_box(issue, issue_layout):
        _setup_simple_report_list_widget(issue.data, issue_layout)

    @staticmethod
    def format_issues_for_clipboard(issues):
        lines = 'Validation report:\n'
        for issue in issues:
            lines += '{0} has {1} shape nodes but should only have one: \n    {2}\n'.format(
                issue.parent_val_data.node_label, len(issue.data), issue.data)
        return lines


class MultipleShapeNodesIssueWidget(ValidationIssueWidget):
    category = CATEGORY_MESH
    presets = [PRESET_ALL, PRESET_MESHES, PRESET_SKINNED_MESHES]
    label = 'Multiple shape nodes'
    description = 'Meshes with too many shape nodes.'
    issue_report_label = '{} has too many shape nodes.'
    severity = SEVERITY_ERROR
    report_widget = MultipleShapeNodesIssueReportWidget
    has_fix_method = False

    def validate(self, meshes=None):
        meshes_to_shapes = val_mesh.get_meshes_with_multiple_shapes_from_scene(
            meshes, progress_bar=self.ui.progress_bar)
        self.validation_results = self.format_validation_results(meshes_to_shapes,
                                                                 self.issue_report_label,
                                                                 severity=self.severity)
        return self.validation_results

    def get_nodes_to_validate(self):
        return meshutils.get_meshes_from_scene()


class DirtyHistoryMeshIssueReportWidget(IssueReportWidget):
    window_title = "Validate Dirty History Report"

    @staticmethod
    def format_issue_and_add_to_group_box(issue, issue_layout):
        _setup_simple_report_list_widget(issue.data, issue_layout)

    @staticmethod
    def format_issues_for_clipboard(issues):
        lines = 'Validation report:\n'
        for issue in issues:
            lines += '{0} has dirty construction history: \n    {1}\n'.format(
                issue.parent_val_data.node_label, issue.data)
        return lines


class DirtyHistoryMeshIssueWidget(ValidationIssueWidget):
    category = CATEGORY_MESH
    presets = [PRESET_ALL, PRESET_MESHES, PRESET_SKINNED_MESHES]
    label = 'Dirty construction history'
    description = 'Meshes with dirty construction history.'
    issue_report_label = '{} has dirty construction history.'
    severity = SEVERITY_WARNING
    report_widget = DirtyHistoryMeshIssueReportWidget

    def validate(self, meshes=None):
        meshes_to_shapes = val_mesh.get_meshes_with_dirty_history_from_scene(
            meshes, progress_bar=self.ui.progress_bar)
        self.validation_results = self.format_validation_results(meshes_to_shapes,
                                                                 self.issue_report_label,
                                                                 severity=self.severity)
        return self.validation_results

    def get_nodes_to_validate(self):
        return meshutils.get_meshes_from_scene()

    def fix(self):
        meshes = [v.node for v in self.validation_results]
        val_mesh.fix_meshes_with_dirty_history(meshes)


class OverlappingVerticesIssueReportWidget(IssueReportWidget):
    window_title = "Validate Overlapping Vertices"

    @staticmethod
    def format_issue_and_add_to_group_box(issue, issue_layout):
        _setup_simple_report_list_widget(issue.data, issue_layout)

    @staticmethod
    def format_issues_for_clipboard(issues):
        lines = 'Validation report:\n'
        for issue in issues:
            lines += '{0} has {1} overlapping vertices: \n    {2}\n'.format(
                issue.parent_val_data.node_label, len(issue.data), issue.data)
        return lines


class OverlappingVerticesIssueWidget(ValidationIssueWidget):
    category = CATEGORY_MESH
    presets = [PRESET_ALL, PRESET_MESHES, PRESET_SKINNED_MESHES]
    label = 'Overlapping Vertices'
    description = 'Meshes with overlapping vertices.'
    issue_report_label = '{} has overlapping vertices.'
    severity = SEVERITY_WARNING
    report_widget = OverlappingVerticesIssueReportWidget
    has_fix_method = False

    def validate(self, meshes=None):
        meshes_to_bad_verts = val_mesh.get_meshes_with_overlapping_verts_from_scene(
            meshes, progress_bar=self.ui.progress_bar)
        self.validation_results = self.format_validation_results(meshes_to_bad_verts,
                                                                 self.issue_report_label,
                                                                 severity=self.severity)
        return self.validation_results

    def get_nodes_to_validate(self):
        return meshutils.get_meshes_from_scene()


class VertexColorIssueReportWidget(IssueReportWidget):
    window_title = "Validate Overlapping Vertices"

    @staticmethod
    def format_issue_and_add_to_group_box(issue, issue_layout):
        node_and_value_pairs = []
        for vert_index, vert_color in issue.data.items():
            node_and_value_pairs.append((issue.parent_val_data.node.vtx[vert_index], vert_color))
        _setup_simple_vert_table(node_and_value_pairs, 'Vert Color', issue_layout)

    @staticmethod
    def format_issues_for_clipboard(issues):
        lines = 'Validation report:\n'
        for issue in issues:
            lines += '{0} has {1} vertices with invalid vert color: \n    {2}\n'.format(
                issue.parent_val_data.node_label, len(issue.data), issue.data)
        return lines


class VertexColorIssueWidget(ValidationIssueWidget):
    category = CATEGORY_MESH
    presets = [PRESET_ALL, PRESET_MESHES, PRESET_SKINNED_MESHES]
    label = 'Invalid Vertex Color'
    description = 'Meshes with invalid vertex color.'
    issue_report_label = '{} has vertices with invalid color.'
    severity = SEVERITY_WARNING
    report_widget = VertexColorIssueReportWidget
    has_fix_method = True

    def fix(self):
        self.ui.pbar_vis_widget.setVisible(True)
        meshes_and_verts = []
        for val_node in self.validation_results:
            issue_data = val_node.issues[0].data
            verts = [val_node.node.vtx[i] for i in issue_data.keys()]
            meshes_and_verts.append((val_node.node, verts))
        val_mesh.remove_vert_color(meshes_and_verts)
        self.ui.pbar_vis_widget.setVisible(False)

    def validate(self, meshes=None):
        meshes_to_bad_verts = val_mesh.get_invalid_vertex_colors_from_scene(
            meshes, progress_bar=self.ui.progress_bar)
        self.validation_results = self.format_validation_results(meshes_to_bad_verts,
                                                                 self.issue_report_label,
                                                                 severity=self.severity)
        return self.validation_results

    def get_nodes_to_validate(self):
        return meshutils.get_meshes_from_scene()


class ValidatorEmbedded(QtWidgets.QWidget):
    validator_presets = [PRESET_SKINNED_MESHES, PRESET_MESHES]

    def __init__(self, parent_layout):
        super().__init__()
        self.nodes = []
        self.validation_severity = None
        self.validator_instance = None
        v_box = QtWidgets.QVBoxLayout()
        v_box.setContentsMargins(0, 0, 0, 0)
        h_box = QtWidgets.QHBoxLayout()
        h_box.setContentsMargins(0, 0, 0, 0)
        self.validate_button = QtWidgets.QPushButton('Validate')
        self.validate_open_button = QtWidgets.QPushButton()
        self.validate_open_button.setMaximumWidth(23)
        options_icon = QtGui.QPixmap(os.path.join(path_consts.ICONS_DIR, 'options.svg'))
        self.validate_open_button.setIcon(options_icon)

        h_box.addWidget(self.validate_button)
        h_box.addWidget(self.validate_open_button)
        v_box.addLayout(h_box)

        self.pbar_vis_widget = flottiui.VisibilityToggleWidget()
        self.progress_bar = flottiui.ProgressBarWithLabel()
        self.pbar_vis_widget.layout().addWidget(self.progress_bar)
        self.pbar_vis_widget.setVisible(False)
        v_box.addWidget(self.pbar_vis_widget)
        self.setLayout(v_box)

        parent_layout.insertWidget(0, self)
        self.validate_button.clicked.connect(self.validate_scene)
        self.validate_open_button.clicked.connect(self.show_validator)

    def validate_scene(self):
        self.get_validator_instance()
        self.pbar_vis_widget.setVisible(True)
        self.validator_instance.set_preset_selection(self.validator_presets)
        self.validator_instance.refresh_nodes_lists(self.nodes)
        self.validator_instance.validate_scene()
        self.pbar_vis_widget.setVisible(False)
        self.validator_instance.update_ui_elements_based_on_issue_results()
        if self.validator_instance.get_dirty_issues():
            self.validator_instance.show()

    def show_validator(self):
        self.get_validator_instance()
        self.validator_instance.update_ui_elements_based_on_issue_results()
        self.validator_instance.show()

    def get_validator_instance(self):
        if self.validator_instance:
            return self.validator_instance
        if VALIDATOR_UI:
            if VALIDATOR_UI.isVisible():
                self.validator_instance = VALIDATOR_UI
                self.validator_instance.set_parent_to_notify(self)
                self.validator_instance.update_ui_elements_based_on_issue_results()
                self.validator_instance.setFocus()
                return self.validator_instance
        self.validator_instance = validator_launch(self, launch_hidden=True)
        return self.validator_instance

    def update_validation_severity(self, severity=None):
        self.validation_severity = severity
        style_sheet_string = get_style_sheet_string_from_severity(self.validation_severity)
        self.validate_button.setStyleSheet(style_sheet_string)
        self.validate_open_button.setStyleSheet(style_sheet_string)


def _setup_simple_vert_table(node_and_value_pairs, column_label, parent_layout):
    table = QtWidgets.QTableWidget()
    table.setColumnCount(1)
    table.setRowCount(len(node_and_value_pairs))
    table.setMinimumHeight(5 * 24)
    parent_layout.addWidget(table)

    table.setHorizontalHeaderLabels([column_label])
    cell_index_to_vert = {}
    vert_labels = []
    for i, (node, influences_to_weights) in enumerate(node_and_value_pairs):
        cell_index_to_vert[i] = node
        vert_labels.append(node.name())
        infcount_tableitem = QtWidgets.QTableWidgetItem(str(influences_to_weights))
        table.setItem(0, i, infcount_tableitem)
    table.setVerticalHeaderLabels(vert_labels)

    def on_sel_change():
        row_indexes = [cell_index_to_vert[row_index.row()] for row_index in table.selectionModel().selectedRows()]
        pm.select(row_indexes, r=True)

    table.itemSelectionChanged.connect(on_sel_change)
    table.resizeColumnsToContents()


def _setup_simple_report_list_widget(nodes, parent_layout):
    list_widget = QtWidgets.QListWidget()
    list_widget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
    parent_layout.addWidget(list_widget)
    for node in nodes:
        list_item = QtWidgets.QListWidgetItem(node.name())
        list_widget.addItem(list_item)

    def on_sel_change():
        to_select = [nodes[i.row()] for i in list_widget.selectedIndexes()]
        pm.select(to_select, r=True)
    list_widget.itemSelectionChanged.connect(on_sel_change)


def get_style_sheet_string_from_severity(severity):
    style_sheet_string = "background-color: {}"
    if severity is not None:
        color = SEVERITY_COLOR_MAP[severity]
        style_sheet_string = "background-color: {}".format(color)
    return style_sheet_string
