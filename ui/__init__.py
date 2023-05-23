import os

from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
import pymel.core as pm
import PySide2.QtCore as QtCore
import PySide2.QtGui as QtGui
import PySide2.QtUiTools as QtUiTools
import PySide2.QtWidgets as QtWidgets

import flottitools.path_consts as path_consts


CANCEL_STRING = 'Cancel'
SAVE_STRING = 'Save'
DONT_SAVE_STRING = "Don't Save"

RED_LABEL_CS_STRING = "QLabel{ color: rgb(255, 50, 50); }"
GREEN_LABEL_CS_STRING = "QLabel{ color: rgb(50, 255, 50); }"


class FlottiWindow(QtWidgets.QDialog):
    window_title = "SSE Window"
    object_name = None

    def __init__(self, parent=None):
        super(FlottiWindow, self).__init__(parent=parent)
        if self.object_name is not None:
            self.setObjectName(self.object_name)
        self.setWindowTitle(self.window_title)
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

    @staticmethod
    def clear_layout(layout):
        for i in reversed(range(layout.count())):
            widget = layout.itemAt(i).widget()
            widget.setParent(None)
            widget.deleteLater()


class FlottiMayaWindow(MayaQWidgetDockableMixin, FlottiWindow):
    window_title = "FlottiTools Maya Window"
    object_name = None
    
    def __init__(self, parent=None):
        super(FlottiMayaWindow, self).__init__(parent=parent)


class FlottiWindowDesignerUI(FlottiWindow):
    ui_designer_file_path = None

    def __init__(self, parent=None):
        super(FlottiWindowDesignerUI, self).__init__(parent=parent)
        if self.ui_designer_file_path is None:
            raise NotImplementedError()
        loader = QtUiTools.QUiLoader()
        uifile = QtCore.QFile(self.ui_designer_file_path)
        uifile.open(QtCore.QFile.ReadOnly)
        self.ui = loader.load(uifile)
        uifile.close()

        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(self.ui)
        # set window to minimize size when it launches
        self.resize(0, 0)


class FlottiMayaWindowDesignerUI(MayaQWidgetDockableMixin, FlottiWindowDesignerUI):
    window_title = "FlottiTools Maya Window"
    object_name = None


class QHLine(QtWidgets.QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QtWidgets.QFrame.HLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)


class QVLine(QtWidgets.QFrame):
    def __init__(self):
        super(QVLine, self).__init__()
        self.setFrameShape(QtWidgets.QFrame.VLine)
        self.setFrameShadow(QtWidgets.QFrame.Sunken)


class NonScrollFocusedQComboBox(QtWidgets.QComboBox):
    def __init__(self, *args, **kwargs):
        super(NonScrollFocusedQComboBox, self).__init__(*args, **kwargs)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

    def wheelEvent(self, *args, **kwargs):
        pass


class RotatedButton(QtWidgets.QPushButton):
    def paintEvent(self, event):
        painter = QtWidgets.QStylePainter(self)
        painter.rotate(270)
        painter.translate(-1 * self.height(), 0)
        painter.drawControl(QtWidgets.QStyle.CE_PushButton, self.getSyleOptions())

    def getSyleOptions(self):
        options = QtWidgets.QStyleOptionButton()
        options.initFrom(self)
        size = options.rect.size()
        size.transpose()
        options.rect.setSize(size)
        options.features = QtWidgets.QStyleOptionButton.None_
        if self.isFlat():
            options.features |= QtWidgets.QStyleOptionButton.Flat
        if self.menu():
            options.features |= QtWidgets.QStyleOptionButton.HasMenu
        if self.autoDefault() or self.isDefault():
            options.features |= QtWidgets.QStyleOptionButton.AutoDefaultButton
        if self.isDefault():
            options.features |= QtWidgets.QStyleOptionButton.DefaultButton
        if self.isDown() or (self.menu() and self.menu().isVisible()):
            options.state |= QtWidgets.QStyle.State_Sunken
        if self.isChecked():
            options.state |= QtWidgets.QStyle.State_On
        if not self.isFlat() and not self.isDown():
            options.state |= QtWidgets.QStyle.State_Raised

        options.text = self.text()
        options.icon = self.icon()
        options.iconSize = self.iconSize()
        return options


class GroupBoxVisibilityToggle(QtWidgets.QGroupBox):
    def __init__(self, *group_box_args):
        super(GroupBoxVisibilityToggle, self).__init__(*group_box_args)
        self.setCheckable(True)
        self.setChecked(True)
        gbox_layout = QtWidgets.QVBoxLayout()
        self.setLayout(gbox_layout)
        self.visibility_widget = VisibilityToggleWidget()
        gbox_layout.addWidget(self.visibility_widget)
        self.toggled.connect(lambda x: self.visibility_widget.setVisible(self.isChecked()))


class VisibilityToggleWidget(QtWidgets.QWidget):
    def __init__(self):
        super(VisibilityToggleWidget, self).__init__()
        vw_layout = QtWidgets.QVBoxLayout()
        self.setLayout(vw_layout)
        self.layout().setContentsMargins(0, 0, 0, 0)


class MayaProgressBar(QtWidgets.QProgressBar):
    def __init__(self):
        super(MayaProgressBar, self).__init__()
        self.chunks = []
        self.current_chunk_index = 0

    def reset(self):
        super(MayaProgressBar, self).reset()
        self.chunks = []
        self.current_chunk_index = 0
        pm.refresh()

    def update_value(self, value):
        self.setValue(value)
        pm.refresh()

    def iterate_value(self, step_size=1):
        self.setValue(self.value()+step_size)

    def iterate_chunk(self):
        self.setValue(self.value() + self.chunks[self.current_chunk_index])
        self.current_chunk_index += 1

    def update_iterate_value(self, step_size=1):
        self.update_value(self.value()+step_size)

    def update_iterate_chunk(self):
        self.iterate_chunk()
        pm.refresh()

    def set_chunks(self, chunk_max_values):
        chunks = [0.01]  # This gets our progress bar started reading 0% rather than just blank
        chunks.extend(chunk_max_values)
        self.chunks = chunks
        self.setMaximum(sum(chunk_max_values))


class ProgressBarWithLabel(QtWidgets.QWidget):
    def __init__(self):
        super(ProgressBarWithLabel, self).__init__()
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.progress_bar = MayaProgressBar()
        self.label = QtWidgets.QLabel()
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.label)

    def reset(self):
        self.label.setText('')
        self.progress_bar.reset()

    def set_maximum(self, maximum):
        self.progress_bar.setMaximum(maximum)

    def update_value(self, value):
        self.progress_bar.update_value(value)

    def iterate_value(self, step_size=1):
        self.progress_bar.iterate_value(step_size)

    def update_iterate_value(self, step_size=1):
        self.progress_bar.update_iterate_value(step_size)

    def update_label_and_iter_val(self, text):
        self.progress_bar.setValue(self.progress_bar.value()+1)
        self.label.setText(text)
        pm.refresh()

    def update_label_and_add_val(self, text, value):
        self.progress_bar.setValue(self.progress_bar.value()+value)
        self.label.setText(text)
        pm.refresh()

    def update_label(self, text):
        self.label.setText(text)
        pm.refresh()

    def update_label_and_value(self, text, value):
        self.progress_bar.setValue(value)
        self.label.setText(text)
        pm.refresh()

    def iterate_chunk(self):
        self.progress_bar.iterate_chunk()

    def set_chunks(self, chunk_max_values):
        self.progress_bar.set_chunks(chunk_max_values)

    def update_iterate_chunk(self):
        self.iterate_chunk()
        pm.refresh()

    def update_label_and_iter_chunk(self, text):
        self.iterate_chunk()
        self.label.setText(text)
        pm.refresh()


def unsaved_changes_prompt():
    if not pm.isModified():
        return True
    scene_path = pm.sceneName()
    path_string = 'unsaved file'
    if scene_path != pm.Path():
        path_string = str(scene_path).replace(os.sep, '/')

    result = pm.confirmDialog(title='Save Changes', message='Save changes to {}?'.format(path_string),
                              button=[SAVE_STRING, DONT_SAVE_STRING, CANCEL_STRING],
                              defaultButton=SAVE_STRING, cancelButton=CANCEL_STRING, dismissString=CANCEL_STRING)
    if result == SAVE_STRING:
        pm.saveFile()
        return True
    elif result == DONT_SAVE_STRING:
        return True
    return False



class RefreshButton(QtWidgets.QPushButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        refresh_icon = QtGui.QPixmap(os.path.join(path_consts.ICONS_DIR, 'refresh.svg'))
        self.setIcon(refresh_icon)
