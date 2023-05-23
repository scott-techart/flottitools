import maya.api.OpenMaya as om


def get_dagpath_or_dependnode(node):
    return get_dagpath_or_dependnode_from_name(node.name())


def get_dagpath_or_dependnode_from_name(name):
    sellist = om.MGlobal.getSelectionListByName(name)
    try:
        return sellist.getDagPath(0)
    except TypeError:
        return sellist.getDependNode(0)
