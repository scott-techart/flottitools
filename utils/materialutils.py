import pymel.core as pm


def get_all_materials_in_scene():
    # return pm.ls(type=pm.nt.ShadingDependNode)
    return pm.ls(materials=True)


def get_used_materials_in_scene():
    used_materials = []
    for shading_engine in pm.ls(type=pm.nt.ShadingEngine):
        if shading_engine.members():
            used_materials.extend(shading_engine.surfaceShader.listConnections())
    return used_materials


def create_material(mat_name, mat_type='lambert'):
    material = pm.shadingNode(mat_type, asShader=1, name=mat_name)
    shading_group = pm.sets(renderable=1, noSurfaceShader=1, empty=1, name='{}SG'.format(material.nodeName()))
    material.outColor.connect(shading_group.surfaceShader, force=True)
    return material, shading_group


def assign_material(pynode, material=None, shading_group=None):
    assert material or shading_group
    shading_group = shading_group or get_shading_groups_from_pynode(material)[0]
    shading_group.forceElement(pynode)


def assign_material_to_shapes(pynode, material=None, shading_group=None):
    for shape in pynode.getShapes():
        if "Orig" not in str(shape):
            assign_material(shape, material, shading_group)


def get_shading_groups_from_pynode(pynode):
    try:
        return pynode.shadingGroups()
    except AttributeError:
        pynode.node().shadingGroups()


def get_attrs_and_file_nodes_from_mat(material):
    return material.listConnections(type=pm.nt.File, connections=True)
