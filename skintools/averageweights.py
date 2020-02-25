import pymel.core as pm


class AverageWeights(object):
    def __init__(self):
        self.sample_skincluster = None
        self.sample_verts = []

    def set_sample_verts(self):
        sample_verts = pm.selected(fl=True)
        self.sample_skincluster =



def get_verts_to_infuence_weight_pairs(verts):
    pass