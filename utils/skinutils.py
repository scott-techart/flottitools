from contextlib import contextmanager

import maya.OpenMaya as OpenMaya
import maya.OpenMayaAnim as OpenMayaAnim
import pymel.core as pm

import flottitools.utils.namespaceutils as nsutils
import flottitools.utils.selectionutils as selutils
import flottitools.utils.skeletonutils as skelutils


DEFAULT_SKINCLUSTER_KWARGS = {'bindMethod': 0,
                              'normalizeWeights': True,
                              'weightDistribution': 0,
                              'maximumInfluences': 4,
                              'obeyMaxInfluences': True,
                              'dropoffRate': 4,
                              'removeUnusedInfluence': False}


def get_skincluster(pynode):
    """Returns the pynode's connected skinCluster.
    Returns None if no skinCluster found.

    :param pynode: Any pynode that has a skinCluster connected to it.
    :return: nt.SkinCluster
    """
    try:
        shape_node = pynode.getShape()
    except AttributeError:
        # shape nodes do not have a .getShape() method. So, if we get an attribute error assume pynode is a shape node.
        shape_node = pynode
    if not shape_node:
        return
    skin = shape_node.listHistory(type='skinCluster', future=False)
    try:
        return skin[0]
    except IndexError:
        return None


@contextmanager
def max_influences_normalize_weights_disabled(skin_cluster, normalize_on_exit=False):
    """Disables normalize weights and maintain max influences
    attributes of a skin cluster on enter and re-enables them on exit.

    Some Maya commands like skinPercent can produce slightly unpredictable
    results when the skinCluster's normalize weights attribute is enabled.
    """
    influence_state = skin_cluster.maintainMaxInfluences.get()
    normalize_state = skin_cluster.setNormalizeWeights(q=True)
    skin_cluster.maintainMaxInfluences.set(False)
    skin_cluster.setNormalizeWeights(0)
    try:
        yield
    finally:
        skin_cluster.maintainMaxInfluences.set(influence_state)
        skin_cluster.setNormalizeWeights(normalize_state)
        if normalize_on_exit:
            skin_cluster.forceNormalizeWeights()


def bind_mesh_to_joints(mesh, joints, **skincluster_kwargs):
    kwargs = DEFAULT_SKINCLUSTER_KWARGS.copy()
    kwargs.update(skincluster_kwargs)
    with selutils.preserve_selection():
        pm.select(joints, r=True)
        skin_cluster = pm.skinCluster(joints, mesh, toSelectedBones=True, **kwargs)
    return skin_cluster


def bind_mesh_like_mesh(source_mesh, target_mesh, source_skincluster=None):
    source_skincluster = source_skincluster or get_skincluster(source_mesh)
    source_influences = source_skincluster.influenceObjects()
    return bind_mesh_to_joints(target_mesh, source_influences)


def bind_mesh_geodesic_voxel(mesh, joints, resolution=None, falloff=1.0, **skinCluster_kwargs):
    """ This cannot be run in Maya standalone or batch mode!
        geomBind() requires a GPU.
    """
    resolution = resolution or (64, 64)
    kwargs = DEFAULT_SKINCLUSTER_KWARGS.copy()
    kwargs.update(skinCluster_kwargs)
    skin_cluster = bind_mesh_to_joints(mesh, joints)
    try:
        # according to the command reference 3 is the only valid bindMethod value for geomBind()
        pm.geomBind(skin_cluster, bindMethod=3, geodesicVoxelParams=resolution,
                    maxInfluences=kwargs.get('maximumInfluences'), falloff=falloff)
        return skin_cluster
    except RuntimeError:
        return skin_cluster


def bind_mesh_delta_mush(mesh, joints, cleanup=False, **skinCluster_kwargs):
    skin_cluster = bind_mesh_to_joints(mesh, joints, **skinCluster_kwargs)
    max_infs = skinCluster_kwargs.get('maximumInfluences', 4)
    skin_cluster = apply_delta_mush_skinning(mesh, skin_cluster, max_influences=max_infs,
                                             sample_existing_skinning=False, cleanup=cleanup)
    return skin_cluster


def get_vert_indexes_with_exceeding_influences(skinned_mesh, skin_cluster=None, max_influences=4):
    skin_cluster = skin_cluster or get_skincluster(skinned_mesh)
    exceeding_verts = {}
    verts_to_weighted_influences = get_vert_indexes_to_weighted_influences(skin_cluster)
    for vert, influences_to_weights in verts_to_weighted_influences.items():
        if len(influences_to_weights.values()) > max_influences:
            exceeding_verts[vert] = influences_to_weights
    return exceeding_verts


def get_skinned_meshes_from_scene():
    skinned_meshes = _get_skinned_meshes()
    return skinned_meshes


def get_skinnned_meshes_in_list(nodes):
    skinned_meshes = _get_skinned_meshes(nodes)
    skinned_meshes_in_nodes = [x for x in skinned_meshes if x in nodes]
    return skinned_meshes_in_nodes


def _get_skinned_meshes(nodes=None):
    if nodes is None:
        skin_clusters = pm.ls(typ='skinCluster')
    else:
        skin_clusters = pm.ls(nodes, typ='skinCluster')

    skinned_meshes = []
    for skincl in skin_clusters:
        shapes = skincl.getGeometry()
        meshes = pm.ls(shapes, type='mesh')
        meshes_xforms = [m.getParent() for m in meshes]
        skinned_meshes.extend(meshes_xforms)
    # make sure there are no duplicates in the list
    skinned_meshes = list(set(skinned_meshes))
    return skinned_meshes


def prune_exceeding_influences(vertex, skin_cluster=None, influences_to_weights=None, max_influences=4):
    skin_cluster = skin_cluster or get_skincluster(vertex)
    influences_to_weights = influences_to_weights or get_weighted_influences(vertex, skin_cluster)
    pruned_infs_to_weights = get_pruned_influences_to_weights(influences_to_weights, max_influences=max_influences)
    pm.skinPercent(skin_cluster, vertex, transformValue=pruned_infs_to_weights.items())


def prune_exceeding_skinned_mesh(skinned_mesh, vert_indexes_to_infs_and_wts=None, skincluster=None, max_influences=4):
    skincluster = skincluster or get_skincluster(skinned_mesh)
    vert_indexes_to_infs_and_wts = vert_indexes_to_infs_and_wts or get_vert_indexes_with_exceeding_influences(skinned_mesh)
    with max_influences_normalize_weights_disabled(skincluster, normalize_on_exit=True):
        for vert_index, infs_to_wts in vert_indexes_to_infs_and_wts.items():
            vert = skinned_mesh.vtx[vert_index]
            prune_exceeding_influences(
                vert, skin_cluster=skincluster, influences_to_weights=infs_to_wts, max_influences=max_influences)


def get_pruned_influences_to_weights(influences_to_weights, max_influences=4, divisor=1.0):
    to_sort = list(influences_to_weights.values())
    to_sort.sort(reverse=True)
    max_index = max_influences - 1
    try:
        prune_val = to_sort[max_index]
        if to_sort[max_index] == to_sort[max_influences]:
            prune_val = to_sort[max_influences - 2]
    except IndexError:
        prune_val = -1.0
    pruned_inf_to_weight = {}
    not_pruned_infs = []
    for inf, weight in influences_to_weights.items():
        if weight < prune_val:
            pruned_inf_to_weight[inf] = 0.0
        else:
            pruned_inf_to_weight[inf] = (weight / divisor)
            not_pruned_infs.append(inf)
    # very rare edge case where all influences have equal weight and exceed max
    if len(not_pruned_infs) > max_influences:
        not_pruned_infs.sort()
        for exceeding_inf in not_pruned_infs[max_influences:]:
            pruned_inf_to_weight[exceeding_inf] = 0.0
    return pruned_inf_to_weight


def get_non_normalized_vert_indexes(vertices, skin_cluster=None, tolerance=.000001):
    skin_cluster = skin_cluster or get_skincluster(vertices[0])
    non_normalized_vert_indexes_to_total_weight = {}
    vert_inf_wts = get_vert_indexes_to_weighted_influences(skin_cluster, vertices)
    for vert_index, infs_wts in vert_inf_wts.items():
        weights = infs_wts.values()
        total_weight = sum(weights)
        if abs(total_weight - 1.0) > tolerance:
            non_normalized_vert_indexes_to_total_weight[vert_index] = total_weight
    return non_normalized_vert_indexes_to_total_weight


def move_weight_to_parent_and_remove_influence(influence_origin, skin_cluster):
    return move_weight_and_remove_influence(influence_origin, influence_origin.getParent(), skin_cluster)


def move_weight_and_remove_influence(influence_origin, influence_destination, skin_cluster):
    pm.select(clear=True)
    skin_cluster.selectInfluenceVerts(influence_origin)
    bad_vertices = [x for x in pm.selected(fl=True) if isinstance(x, pm.MeshVertex)]
    if bad_vertices:
        for bad_vert in bad_vertices:
            # the transformMoveWeights flag in skinPercent does not quite work like you would expect so I wrote my own
            move_weights(skin_cluster, bad_vert, influence_origin, influence_destination)
    skin_cluster.removeInfluence(influence_origin)
    return bad_vertices


def remove_influences_from_skincluster(skin_cluster, influences):
    with max_influences_normalize_weights_disabled(skin_cluster):
        skin_cluster.removeInfluence(influences)


def move_weights(skin_cluster, vertex, origin_inf, destination_inf):
    """Sets origin_inf weight to 0.0 and adds its original weight to destination_inf."""
    infs_to_weights = get_weighted_influences(vertex, skin_cluster)
    initial_origin_weight = infs_to_weights.get(origin_inf, 0.0)
    initial_destination_weight = infs_to_weights.get(destination_inf, 0.0)
    destination_weight = initial_origin_weight + initial_destination_weight
    infs_to_weights[origin_inf] = 0.0
    infs_to_weights[destination_inf] = destination_weight
    pm.skinPercent(skin_cluster, vertex, transformValue=infs_to_weights.items())


def normalize_skinned_meshes(skinned_meshes):
    for skinned_mesh in skinned_meshes:
        normalize_skinned_mesh(skinned_mesh)


def normalize_skinned_mesh(skinned_mesh):
    skin_cluster = get_skincluster(skinned_mesh)
    skin_cluster.forceNormalizeWeights()
    skin_cluster.setNormalizeWeights(1)


def apply_delta_mush_skinning(skinned_mesh, skin_cluster=None, max_influences=4,
                              sample_existing_skinning=True, cleanup=False):
    mush_mesh, mush_skincluster = duplicate_skinned_mesh(skinned_mesh, skin_cluster, sample_existing_skinning)
    mush_node = apply_delta_mush(mush_mesh)
    skin_cluster = bake_deformer_to_skin(mush_mesh, skinned_mesh, max_influences=max_influences, cleanup=cleanup)
    pm.delete([mush_mesh, mush_node])
    return skin_cluster


def duplicate_skinned_mesh(skinned_mesh, skin_cluster=None, copy_skinning=True):
    skin_cluster = skin_cluster or get_skincluster(skinned_mesh)
    influences = skin_cluster.getInfluence()
    return duplicate_skinned_mesh_to_influences(skinned_mesh, influences, copy_skinning=copy_skinning)


def duplicate_skinned_mesh_to_influences(skinned_mesh, influences, copy_skinning=True, bind_method=bind_mesh_to_joints, dup_namespace=None, dup_parent=None):
    dup_namespace = dup_namespace or pm.namespaceInfo(currentNamespace=True)
    with nsutils.preserve_namespace(dup_namespace):
        skinned_mesh_duplicate = nsutils.duplicate_to_namespace(
            skinned_mesh, dup_namespace=dup_namespace, dup_parent=dup_parent)[0]
        skincluster_duplicate = bind_method(skinned_mesh_duplicate, influences)

    if copy_skinning:
        copy_weights(skinned_mesh, skinned_mesh_duplicate)
        # copy_weights_vert_order(skinned_mesh, skinned_mesh_duplicate)
    return skinned_mesh_duplicate, skincluster_duplicate


def duplicate_skinned_mesh_and_skeleton(skinned_mesh, dup_namespace=None, copy_skinning=True, bind_method=bind_mesh_to_joints, dup_parent=None):
    skin_cluster = get_skincluster(skinned_mesh)
    source_influences = skin_cluster.influenceObjects()
    source_skeleton_root = skelutils.get_root_joint_from_child(source_influences[0])
    if dup_namespace:
        nsutils.add_namespace_to_root(dup_namespace)
    dup_root = skelutils.duplicate_skeleton(source_skeleton_root, dup_namespace=dup_namespace, dup_parent=dup_parent)
    dup_skel = skelutils.get_hierarchy_from_root(dup_root, joints_only=True)
    dup_mesh, dup_cluster = duplicate_skinned_mesh_to_influences(skinned_mesh, dup_skel,
                                                                 copy_skinning=copy_skinning, bind_method=bind_method, dup_namespace=dup_namespace, dup_parent=dup_parent)
    return dup_mesh, dup_root, dup_cluster


def apply_delta_mush(mesh, distanceWeight=1.0, displacement=1.0, **deltaMush_kwargs):
    default_deltaMush_kwargs = {'smoothingIterations': 20,
                                'smoothingStep': 1.0,
                                'pinBorderVertices': False,
                                'envelope': 1.0,
                                'inwardConstraint': 0.0,
                                'outwardConstraint': 0.0}
    default_deltaMush_kwargs.update(deltaMush_kwargs)
    delta_mush_node = pm.deltaMush(mesh, **default_deltaMush_kwargs)
    # these are arguments that the Delta Mush UI has but are not valid arguments for the deltaMush() command.
    delta_mush_node.distanceWeight.set(distanceWeight)
    delta_mush_node.displacement.set(displacement)
    return delta_mush_node


def bake_deformer_to_skin(source_mesh, target_mesh, source_skeleton=None, target_skeleton=None,
                          max_influences=4, cleanup=False):
    source_skeleton = source_skeleton or get_skincluster(source_mesh).getInfluence()
    target_skeleton = target_skeleton or get_skincluster(target_mesh).getInfluence()
    source_root = source_skeleton[0]
    target_root = target_skeleton[0]

    pm.bakeDeformer(srcMeshName=source_mesh,
                    srcSkeletonName=source_root,
                    dstMeshName=target_mesh,
                    dstSkeletonName=target_root,
                    maxInfluences=max_influences)
    # bakeDeformer deletes and re-creates the dest mesh's skin cluster
    # so we need to query target_mesh's skin cluster again.
    target_skin_cluster = get_skincluster(target_mesh)
    if cleanup:
        # bakeDeformer does not seem to respect max influences or normalize weights.
        # these cleanup operations are behind a feature flag because they are very slow, but effective.
        prune_exceeding_skinned_mesh(target_mesh, skincluster=target_skin_cluster, max_influences=max_influences)
        target_skin_cluster.forceNormalizeWeights()
    pm.warning("Bake Deformer process complete. You should probably save your work and restart Maya now. This process takes tons of memory and does not give it back when it's done.")
    return target_skin_cluster


def copy_weights(source_mesh, target_nodes, **copySkinWeights_kwargs):
    """Copies weights using pm.copySkinWeights with the most commonly used default kwargs.
    target_nodes can be a single skinned mesh or vertex or it can be a list of vertices.
    """
    default_copySkinWeightsKwargs = {'noMirror': True,
                                     'surfaceAssociation': 'closestPoint',
                                     'influenceAssociation': ('label', 'name', 'closestJoint'),
                                     'normalize': True}
    default_copySkinWeightsKwargs.update(copySkinWeights_kwargs)
    pm.copySkinWeights(source_mesh, target_nodes, **default_copySkinWeightsKwargs)


def get_root_joint_from_skinned_mesh(skinned_mesh):
    skin_cluster = get_skincluster(skinned_mesh)
    influences = skin_cluster.getInfluence()
    return skelutils.get_root_joint_from_child(influences[0])


def get_vert_indexes_to_weighted_influences(skin_cluster, vertices=None):
    """
    Return a dictionary of vertex indices as keys and influence to weights dictionaries as values.
    Only returns influences that have greater-than zero weights.

    Original code from Tyler Thorncok https://www.charactersetup.com/tutorial_skinWeights.html
    Tweaked to use PyNode influences and only check the vertices passed in (or all vertices if None).

    :param skin_cluster: PyNode SkinCluster
    :param vertices: PyNode MeshVertex Return weights for only the vertices provided.
                     If None return values for all vertices.
    :returns: {vert_index: {influence: weight_value}}
    """
    # poly mesh and skinCluster name
    clusterName = skin_cluster.name()

    # get the MFnSkinCluster for clusterName
    selList = OpenMaya.MSelectionList()
    selList.add(clusterName)
    clusterNode = OpenMaya.MObject()
    selList.getDependNode(0, clusterNode)
    skinFn = OpenMayaAnim.MFnSkinCluster(clusterNode)

    # get the MDagPath for all influence
    infDags = OpenMaya.MDagPathArray()
    skinFn.influenceObjects(infDags)

    # Get PyNodes for influences. They are returned in the same order as the OpenMaya commands return influence indices.
    # They have the advantage of containing more information like the influence name.
    # Their index can be derived from the skinCluster using skin_cluster.indexForInfluenceObject(influence)
    influences = skin_cluster.influenceObjects()
    # need a influence index to influences mapping because influence indices can diverge from the order they come from
    # skinCluster.influenceObjects() if methods like removeInfluence() have been used on the skinCluster before.
    inf_index_to_infs = {}
    for influence in influences:
        inf_index = get_influence_index(influence, skin_cluster)
        inf_index_to_infs[inf_index] = influence

    # get the MPlug for the weightList and weights attributes
    weight_list_plug = skinFn.findPlug('weightList')
    weights_plug = skinFn.findPlug('weights')
    wlAttr = weight_list_plug.attribute()
    wAttr = weights_plug.attribute()
    wInfIds = OpenMaya.MIntArray()

    # the weights are stored in dictionary, the key is the vertId,
    # the value is another dictionary whose key is the influence id and
    # value is the weight for that influence
    weights = {}
    if vertices:
        # get influences and weights for only the vertices passed in
        vert_indices = [v.index() for v in vertices]
    else:
        # get influences and weights for all vertices affected by the skin_cluster
        vert_indices = range(weight_list_plug.numElements())
    for vId in vert_indices:
        vWeights = {}
        # tell the weights attribute which vertex id it represents
        weights_plug.selectAncestorLogicalIndex(vId, wlAttr)
        # get the indice of all non-zero weights for this vert
        weights_plug.getExistingArrayAttributeIndices(wInfIds)
        # create a copy of the current wPlug
        infPlug = OpenMaya.MPlug(weights_plug)
        for infId in wInfIds:
            # tell the infPlug it represents the current influence id
            infPlug.selectAncestorLogicalIndex(infId, wAttr)
            # add this influence and its weight to this verts weights
            if infPlug.asDouble() != 0.0:
                try:
                    influence = inf_index_to_infs[infId]
                    vWeights[influence] = infPlug.asDouble()
                except KeyError:
                    # this is super weird Maya BS. It seems as though the weightList sometimes remembers the
                    # weight values of influences that were removed from the skinCluster.
                    # This results in a KeyError in our inf_index_to_infs dict.
                    # I think we can safely catch and ignore these key errors and everything works as intended o.O
                    pass

        weights[vId] = vWeights

    return weights


def get_weighted_influences(vertex, skin_cluster=None):
    skin_cluster = skin_cluster or get_skincluster(vertex)
    vert_to_infs_wts = get_vert_indexes_to_weighted_influences(skin_cluster, [vertex])
    return vert_to_infs_wts[vertex.index()]


def get_influence_index(influence, skin_cluster):
    index = None
    try:
        index = skin_cluster.indexForInfluenceObject(influence)
    except pm.general.MayaNodeError:
        # if influence is passed as a string and there is more than one object in the scene with that same name
        infs = skin_cluster.getInfluence()
        for inf in infs:
            if influence == inf.nodeName():
                index = skin_cluster.indexForInfluenceObject(inf)
                continue
    return index


def _copy_weights_vert_order(source_mesh, target_mesh, influence_map,
                            source_skincluster=None, target_skincluster=None):
    source_skincluster = source_skincluster or get_skincluster(source_mesh)
    target_skincluster = target_skincluster or get_skincluster(target_mesh)

    verts_to_weighted_influences = get_vert_indexes_to_weighted_influences(source_skincluster)
    pm.skinPercent(target_skincluster, target_mesh, normalize=False, pruneWeights=100)
    for vert_index, weighted_infs in verts_to_weighted_influences.items():
        target_vert = target_mesh.vtx[vert_index]
        target_weighted_infs = {}
        for source_inf, source_weight in weighted_infs.items():
            target_infs = influence_map.get(source_inf, [])
            for target_inf in target_infs:
                target_weighted_infs[target_inf] = source_weight
        pm.skinPercent(target_skincluster, target_vert, transformValue=target_weighted_infs.items())


def copy_weights_vert_order(source_mesh, target_mesh, influence_map=None, mapping_methods=None,
                            source_skincluster=None, target_skincluster=None):
    source_skincluster = source_skincluster or get_skincluster(source_mesh)
    target_skincluster = target_skincluster or get_skincluster(target_mesh)
    source_influences = source_skincluster.influenceObjects()
    target_influences = target_skincluster.influenceObjects()

    def by_skin_cluster_index(source_infs, target_infs, inf_map):
        return update_inf_map_by_skincluster_index(source_infs, target_infs,
                                                   source_skincluster, target_skincluster, inf_map)
    mapping_methods = mapping_methods or [skelutils.update_inf_map_by_label,
                                          skelutils.update_inf_map_by_name,
                                          skelutils.update_inf_map_by_worldspace_position,
                                          by_skin_cluster_index,
                                          skelutils.update_inf_map_by_influence_order]
    if influence_map is None:
        influence_map, unmapped_infs = skelutils.get_influence_map(source_influences,
                                                                   target_influences,
                                                                   mapping_methods)
    _copy_weights_vert_order(source_mesh, target_mesh, influence_map, source_skincluster, target_skincluster)


def copy_weights_vert_order_closest_joint(source_mesh, target_mesh, source_skincluster=None, target_skincluster=None):
    copy_weights_vert_order(source_mesh, target_mesh,
                            mapping_methods=[skelutils.update_inf_map_by_closest_inf],
                            source_skincluster=source_skincluster, target_skincluster=target_skincluster)


def copy_weights_vert_order_inf_order(source_mesh, target_mesh, source_skincluster=None, target_skincluster=None):
    copy_weights_vert_order(source_mesh, target_mesh,
                            mapping_methods=[skelutils.update_inf_map_by_influence_order],
                            source_skincluster=source_skincluster, target_skincluster=target_skincluster)


def update_inf_map_by_skincluster_index(source_influences, target_influences,
                                        source_skincluster, target_skincluster, influence_map=None):
    influence_map = influence_map or {}
    source_inf_to_index = dict([(inf, get_influence_index(inf, source_skincluster)) for inf in source_influences])
    target_inf_to_index = dict([(inf, get_influence_index(inf, target_skincluster)) for inf in target_influences])
    unmapped_target_infs = target_influences[:]
    for target_inf in target_influences:
        target_index = target_inf_to_index[target_inf]
        for source_inf in source_influences:
            if source_inf_to_index[source_inf] == target_index:
                skelutils.append_target_to_influence_map(influence_map, source_inf, target_inf)
                unmapped_target_infs.remove(target_inf)
                break
    return influence_map, unmapped_target_infs


def get_bind_pose_from_skinned_mesh(skinned_mesh):
    skin_cluster = get_skincluster(skinned_mesh)
    return get_bind_pose_from_skincluster(skin_cluster)


def get_bind_pose_from_skincluster(skin_cluster):
    try:
        return skin_cluster.inputs(type=pm.nt.DagPose)[0]
    except IndexError:
        return


def get_skinned_meshes_from_selection():
    sel = pm.selected()
    return [x for x in sel if get_skincluster(x)]


def get_first_skinned_mesh_from_selection():
    sel = pm.selected()
    for each in sel:
        if get_skincluster(each):
            return each


def duplicate_triangulate_mesh(skinned_mesh, dup_namespace=None, dup_parent=None):
    dup_namespace = dup_namespace or pm.namespaceInfo(currentNamespace=True)
    with nsutils.preserve_namespace(dup_namespace):
        dup_skinned_mesh_tri = nsutils.duplicate_to_namespace(
            skinned_mesh, dup_namespace=dup_namespace, dup_parent=dup_parent)[0]
        pm.polyTriangulate(dup_skinned_mesh_tri, ch=True)
        pm.delete(dup_skinned_mesh_tri, constructionHistory=True)
        dup_skin_cluster = bind_mesh_like_mesh(skinned_mesh, dup_skinned_mesh_tri)
        copy_weights(skinned_mesh, dup_skinned_mesh_tri)
    return dup_skinned_mesh_tri, dup_skin_cluster
