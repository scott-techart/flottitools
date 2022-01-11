from contextlib import contextmanager

import pymel.core as pm


@contextmanager
def preserve_selection():
    """Store user's selection on enter and restore user's selection on exit."""
    sel = pm.selected(fl=True)
    try:
        yield
    finally:
        pm.select(sel, replace=True)


def convert_selection_to_verts(sel=None):
    sel = sel or pm.selected(fl=True)
    selected_verts = pm.polyListComponentConversion(
        sel, fromVertex=True, fromEdge=True, fromFace=True, fromVertexFace=True, toVertex=True)
    pm.select(selected_verts, replace=True)
    return pm.selected(fl=True)