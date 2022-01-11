import pymel.core as pm


def create_wrap_deformer(influence_mesh, target_mesh, **kwargs):
    """
    Ryan Roberts - Wrap Deformer
    rr_wrap.py
    Description:
        Ryan Robers created a simple function to create a wrap deformer.
        The wrap deformer needs a little more than the deform command to get working.
        Michael Clavan
        I wanted to have the function also return the deformer to the user.  So, my contributions are pretty minor.
        I converted the wrap deformer into a pynode object type pm.nt.Wrap.
        Scott Clary
        Converted maya.cmds to pymel code so that we can pass PyNodes into this method.
    """
    influence_shape = influence_mesh.getShape()

    # create wrap deformer
    weight_threshold = kwargs.get('weightThreshold', 0.0)
    max_distance = kwargs.get('maxDistance', 1.0)
    exclusive_bind = kwargs.get('exclusiveBind', False)
    auto_weight_threshold = kwargs.get('autoWeightThreshold', True)
    falloff_mode = kwargs.get('falloffMode', 0)

    wrap_node = pm.deformer(target_mesh, type='wrap')[0]

    wrap_node.weightThreshold.set(weight_threshold)
    wrap_node.maxDistance.set(max_distance)
    wrap_node.exclusiveBind.set(exclusive_bind)
    wrap_node.autoWeightThreshold.set(auto_weight_threshold)
    wrap_node.falloffMode.set(falloff_mode)
    target_mesh = target_mesh.getShape()
    target_mesh.worldMatrix[0].connect(wrap_node.geomMatrix)

    # add influence
    base = pm.duplicate(influence_mesh, name='{0}Base'.format(influence_mesh))[0]
    base_shape = base.getShape()
    base_shape.visibility.set(False)

    def safe_add_attr(node, long_name, keyable=True, **kwargies):
        try:
            # if the attribute already exists, do nothing otherwise create it
            node.attr(long_name).exists()
        except AttributeError:
            node.addAttr(long_name, **kwargies)
            if keyable:
                node.attr(long_name).set(keyable=True)


    # create dropoff attr if it doesn't exist
    safe_add_attr(influence_mesh, 'dropoff', shortName='dr', defaultValue=4.0, min=0.0, max=20.0)

    # if type mesh
    if isinstance(influence_shape, pm.nt.Mesh):
        # create smoothness attr if it doesn't exist
        safe_add_attr(influence_mesh, 'smoothness', shortName='smt', defaultValue=0.0, min=0.0)
        # create the inflType attr if it doesn't exist
        safe_add_attr(influence_mesh, 'inflType', keyable=False,
                      shortName='ift', attributeType='short', defaultValue=2, min=1, max=2)

        influence_shape.worldMesh.connect(wrap_node.driverPoints[0])
        base_shape.worldMesh.connect(wrap_node.basePoints[0])
        influence_mesh.inflType.connect(wrap_node.inflType[0])
        influence_mesh.smoothness.connect(wrap_node.smoothness[0])

    if isinstance(influence_shape, pm.nt.NurbsCurve) or isinstance(influence_shape, pm.nt.NurbsSurface):
        # create the wrapSamples attr if it doesn't exist
        safe_add_attr(influence_mesh, 'wrapSamples', shortName='wsm', attributeType='short', defaultValue=10, min=1)

        influence_shape.ws.connect(wrap_node.driverPoints[0])
        base_shape.ws.connect(wrap_node.basePoints[0])
        influence_mesh.wsm.connect(wrap_node.nurbsSamples[0])

    influence_mesh.dropoff.connect(wrap_node.dropoff[0])

    return wrap_node, base_shape


def refit_mesh(target_mesh, driver_mesh):
    refit_meshes([target_mesh], driver_mesh)


def refit_meshes(target_meshes, driver_mesh):
    with pm.UndoChunk():
        blendshape = [x for x in driver_mesh.getShape().inputs() if isinstance(x, pm.nt.BlendShape)][0]
        initial_weight = blendshape.weight[0].get()
        blendshape.weight[0].set(0.0)
        base_shapes = []
        for target_mesh in target_meshes:
            wrap_node, base_shape = create_wrap_deformer(driver_mesh, target_mesh)
            base_shapes.append(base_shape.getParent())
        blendshape.weight[0].set(1.0)
        # sometimes the target meshes do not get deformed at all until the viewport is refreshed for some reason.
        pm.refresh()
        # clearing the history deleted the wrap deformer nodes, but does not delete the base shapes that were created.
        pm.delete(target_meshes, constructionHistory=True)
        pm.delete(base_shapes)
        blendshape.weight[0].set(initial_weight)


