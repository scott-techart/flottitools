import os

import flottitools.skintools.averageweights as avgwts
import flottitools.ui as flottiui


AVERAGE_WEIGHTS_UI = None


def average_weights():
    global AVERAGE_WEIGHTS_UI
    if AVERAGE_WEIGHTS_UI is None:
        AVERAGE_WEIGHTS_UI = AverageWeightsMayaWindow()
    AVERAGE_WEIGHTS_UI.hide()
    AVERAGE_WEIGHTS_UI.show()


class AverageWeightsMayaWindow(flottiui.FlottiMayaWindowDesignerUI):
    window_title = "Average Weights"
    ui_designer_file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'averageweights.ui'))

    def __init__(self):
        super(AverageWeightsMayaWindow, self).__init__()
        self.ui.sampled_verts_visibility_widget.setVisible(False)
        self.avgwts_instance = avgwts.AverageWeights()

        self.ui.sample_verts_button.clicked.connect(self.sample_verts)
        self.ui.average_button.clicked.connect(self.apply_average_weights)
        self.ui.proximity_button.clicked.connect(self.apply_proximity_weights)

    def sample_verts(self):
        self.avgwts_instance.set_sample_verts()
        self.refresh_sample_verts_list()

    def apply_average_weights(self):
        self.avgwts_instance.apply_average_weights()

    def apply_proximity_weights(self):
        self.avgwts_instance.apply_proximity_weights()

    def refresh_sample_verts_list(self):
        vert_names = [v.name() for v in self.avgwts_instance.sampled_verts]
        self.ui.sampled_verts_listwidget.clear()
        self.ui.sampled_verts_listwidget.addItems(vert_names)