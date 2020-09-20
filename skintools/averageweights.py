import pymel.core as pm

import flottitools.utils.selectionutils as selectionutils
import flottitools.utils.transformutils as xformutils
import flottitools.utils.skinutils as skinutils


class AverageWeights(object):
    def __init__(self):
        self.sample_skincluster = None
        self.sampled_verts = []

    def set_sample_verts(self):
        self.sampled_verts = selectionutils.convert_selection_to_verts()

    def apply_average_weights(self):
        shape_to_skincl, vert_to_infs_wts = get_shape_to_skincl_and_vert_to_infs_wts(self.sampled_verts)
        if not self.sampled_verts:
            return

        inf_to_wt_totals = get_influence_to_weight_totals(vert_to_infs_wts)
        pruned_inf_to_weight = get_pruned_influences_to_weights(inf_to_wt_totals, float(len(self.sampled_verts)))

        target_verts = selectionutils.convert_selection_to_verts()
        target_skincl = skinutils.get_skincluster(target_verts[0])
        with pm.UndoChunk():
            with skinutils.max_influences_normalize_weights_disabled(target_skincl):
                pm.skinPercent(target_skincl, target_verts, transformValue=pruned_inf_to_weight.items())
            # Normalize weights after modifying them just our changes didn't equal exactly 1.0.
            pm.skinPercent(target_skincl, target_verts, normalize=True)

    def apply_proximity_weights(self):
        shape_to_skincl, svert_to_infs_wts = get_shape_to_skincl_and_vert_to_infs_wts(
            self.sampled_verts)
        if not self.sampled_verts:
            return

        target_verts = selectionutils.convert_selection_to_verts()
        target_skincl = skinutils.get_skincluster(target_verts[0])
        with pm.UndoChunk():
            with skinutils.max_influences_normalize_weights_disabled(target_skincl):
                for target_vert in target_verts:
                    infs_to_weights = get_scaled_influence_to_weight_totals(svert_to_infs_wts, target_vert)
                    pruned_infs_to_weights = get_pruned_influences_to_weights(infs_to_weights)
                    pm.skinPercent(target_skincl, target_vert, transformValue=pruned_infs_to_weights.items())
            pm.skinPercent(target_skincl, target_verts, normalize=True)


def get_shape_to_skincl_and_vert_to_infs_wts(verts):
    shape_nodes = pm.ls(verts, objectsOnly=True)
    shapes_no_dups = set(shape_nodes)
    shape_to_skincl = {}
    for shape in shapes_no_dups:
        skincl = skinutils.get_skincluster(shape)
        shape_to_skincl[shape] = skincl

    vert_to_infs_wts = {}
    for shape_node, vert in zip(shape_nodes, verts):
        skincl = shape_to_skincl[shape_node]
        influences = pm.skinPercent(skincl, vert, query=True, transform=None)
        weights = pm.skinPercent(skincl, vert, query=True, value=True)
        vert_to_infs_wts[vert] = influences, weights

    return shape_to_skincl, vert_to_infs_wts


def get_influence_to_weight_totals(vert_to_infs_wts):
    influence_to_weight_totals = {}
    for influences, weights in vert_to_infs_wts.values():
        for inf, wt in zip(influences, weights):
            current_weight_total = influence_to_weight_totals.get(inf, 0)
            influence_to_weight_totals[inf] = current_weight_total + wt
    return influence_to_weight_totals


def get_scaled_influence_to_weight_totals(vert_to_infs_wts, target_vert):
    target_pos = xformutils.get_worldspace_vector(target_vert)
    sampled_verts, sampled_positions = zip(*[(v, xformutils.get_worldspace_vector(v)) for v in vert_to_infs_wts.keys()])
    scalers = xformutils.get_distance_scalers(target_pos, sampled_positions)
    sampled_vert_to_scaler = dict(zip(sampled_verts, scalers))

    infs_to_weights = {}
    for vert, infs_and_weights in vert_to_infs_wts.items():
        scaler = sampled_vert_to_scaler[vert]
        for inf, wt in zip(*infs_and_weights):
            scaled_weight = wt * scaler
            current_weight = infs_to_weights.get(inf, 0.0)
            infs_to_weights[inf] = current_weight + scaled_weight
    return infs_to_weights


def get_pruned_influences_to_weights(inf_to_wt_totals, divisor=1.0):
    to_sort = inf_to_wt_totals.values()
    to_sort.sort(reverse=True)
    try:
        prune_val = to_sort[3]
        if to_sort[3] == to_sort[4]:
            prune_val = to_sort[2]
    except IndexError:
        prune_val = -1.0
    pruned_inf_to_weight = {}
    for inf, wt_total in inf_to_wt_totals.items():
        if wt_total < prune_val:
            pruned_inf_to_weight[inf] = 0.0
        else:
            pruned_inf_to_weight[inf] = (wt_total / divisor)
    return pruned_inf_to_weight
