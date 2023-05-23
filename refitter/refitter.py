import pymel.core as pm

import flottitools.utils.deformerutils as deformerutils
import flottitools.utils.skinutils as skinutils

DEFAULT_ORIGINAL_MESHES_PARENT_NAME = 'original_nontriangulated_meshes'


class Refitter:
    def __init__(self, blend_mesh=None):
        self.blend_mesh = blend_mesh
        self.trash_node = None
        self.refitted_group_node = None

    def set_selected_blend_mesh(self):
        self.blend_mesh = pm.selected()[0]

    def refit_and_skin_selected_meshes(self, blend_values=None):
        source_meshes = pm.selected()
        all_refitted_meshes = deformerutils.create_refit_meshes(source_meshes, self.blend_mesh, blend_values)
        for refitted_meshes in all_refitted_meshes:
            for source_mesh, refitted_mesh in zip(source_meshes, refitted_meshes):
                source_skincluster = skinutils.get_skincluster(source_mesh)
                if source_skincluster is None:
                    continue
                target_skincluster = skinutils.bind_mesh_like_mesh(source_mesh, refitted_mesh, source_skincluster)
                skinutils.copy_weights_vert_order_inf_order(source_mesh, refitted_mesh,
                                                            source_skincluster, target_skincluster)

    def triangulate_and_refit_selected_meshes(self, blend_values=None):
        source_meshes = pm.selected()
        return self.triangulate_and_refit_meshes(source_meshes, blend_values)

    def triangulate_and_refit_meshes(self, source_meshes, blend_attrs_values_and_suffixes=None, group_node=None):
        triangulate_and_refit_meshes(self.blend_mesh, source_meshes,
                                     blend_attrs_values_and_suffixes=blend_attrs_values_and_suffixes,
                                     preserve_source_meshes=False, tri_orig_parent=None, tri_mesh_parent=None,
                                     refitted_parent=None)


def refit_meshes(blend_mesh, source_meshes, blend_attrs_values_and_suffixes=None, refitted_parent=None):
    blend_attrs_values_and_suffixes = blend_attrs_values_and_suffixes or (None, None, None)
    all_refitted_meshes = []
    for blend_attr, blend_value, suffix in blend_attrs_values_and_suffixes:
        refitted_meshes = deformerutils.create_refitted_meshes(source_meshes, blend_mesh, blend_value, blend_attr, suffix)
        all_refitted_meshes.append(refitted_meshes)
        if refitted_parent is not None:
            pm.parent(refitted_meshes, refitted_parent)
    for refitted_meshes in all_refitted_meshes:
        _copy_skinning_to_refitted_meshes(source_meshes, refitted_meshes)

    return all_refitted_meshes


def triangulate_and_refit_meshes(blend_mesh, source_meshes, blend_attrs_values_and_suffixes=None,
                                 preserve_source_meshes=False,
                                 tri_orig_parent=None, tri_mesh_parent=None, refitted_parent=None):
    blend_attrs_values_and_suffixes = blend_attrs_values_and_suffixes or (None, None, None)
    if preserve_source_meshes and tri_orig_parent is None:
        tri_orig_parent = pm.createNode('transform')
        tri_orig_parent.rename(DEFAULT_ORIGINAL_MESHES_PARENT_NAME)

    tri_meshes = []
    for source_mesh in source_meshes:
        tri_mesh, _ = skinutils.duplicate_triangulate_mesh(source_mesh)
        if preserve_source_meshes:
            source_mesh.setParent(tri_orig_parent)
        else:
            pm.delete(source_mesh)
        if tri_mesh_parent is not None:
            tri_mesh.setParent(tri_mesh_parent)
        tri_mesh.rename(source_mesh.nodeName())
        tri_meshes.append(tri_mesh)

    all_refitted_meshes = refit_meshes(blend_mesh, source_meshes, blend_attrs_values_and_suffixes, refitted_parent)

    return tri_meshes, all_refitted_meshes


def _copy_skinning_to_refitted_meshes(source_meshes, refitted_meshes):
    for source_mesh, refitted_mesh in zip(source_meshes, refitted_meshes):
        source_skincluster = skinutils.get_skincluster(source_mesh)
        if source_skincluster is None:
            break
        target_skincluster = skinutils.bind_mesh_like_mesh(source_mesh, refitted_mesh, source_skincluster)
        skinutils.copy_weights_vert_order_inf_order(source_mesh, refitted_mesh,
                                                    source_skincluster, target_skincluster)


def refit_player2_mesh(source_mesh, blend_mesh):
    blend_node = deformerutils.get_blendshape_nodes(blend_mesh)[0]
    blend_attr_names = pm.listAttr(blend_node.weight, multi=True)
    # suffixes = [x.replace('GC2', '') for x in blend_attr_names]
    suffixes = ['_{}'.format(x.rsplit('_', 1)[1]) for x in blend_attr_names]
    blend_attrs = [blend_node.attr(x) for x in blend_attr_names]
    current_blend_values = blend_node.weight.get()
    zero_blend_values = [0.0 for _ in range(len(current_blend_values))]
    one_blend_values = [1.0 for _ in range(len(current_blend_values))]
    [ba.set(bv) for ba, bv in zip(blend_attrs, zero_blend_values)]
    tri_meshes, all_refitted_meshes = triangulate_and_refit_meshes(blend_mesh, [source_mesh], zip(blend_attrs, one_blend_values, suffixes))
    [ba.set(bv) for ba, bv in zip(blend_attrs, current_blend_values)]
    return tri_meshes, all_refitted_meshes
