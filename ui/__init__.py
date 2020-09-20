from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
import PySide2.QtCore as QtCore
import PySide2.QtUiTools as QtUiTools
import PySide2.QtWidgets as QtWidgets


class FlottiWindow(QtWidgets.QDialog):
    window_title = "FlottiTools Window"
    object_name = None

    def __init__(self, parent=None):
        super(FlottiWindow, self).__init__(parent=parent)
        if self.object_name is not None:
            self.setObjectName(self.object_name)
        self.setWindowTitle(self.window_title)
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)


class FlottiMayaWindow(MayaQWidgetDockableMixin, FlottiWindow):
    window_title = "FlottiTools Maya Window"
    object_name = None


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


class FlottiMayaWindowDesignerUI(MayaQWidgetDockableMixin, FlottiWindowDesignerUI):
    window_title = "FlottiTools Maya Window"
    object_name = None