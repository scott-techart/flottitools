import pymel.core as pm


def convert_selection_to_verts(sel=None):
    sel = sel or pm.selected(fl=True)
    selected_verts = pm.polyListComponentConversion(
        sel, fromVertex=True, fromEdge=True, fromFace=True, fromVertexFace=True, toVertex=True)
    pm.select(selected_verts, replace=True)
    return pm.selected(fl=True)