import pymel.core as pm
import maya.api.OpenMaya as om

import flottitools.utils.rigutils as rigutils
import flottitools.utils.namespaceutils as namespaceutils


def create_cv_curve(nodes: list[pm.nt.Transform], degree: int = 3, name: str = "new_curve", follow_nodes: bool = False) -> pm.nt.Transform:
    if len(nodes) < 2:
        pm.warning("Need at least 2 nodes to create a curve")
        return None

    points = [node.getTranslation(space="world") for node in nodes]
    curve: pm.nt.Transform = pm.curve(degree=degree, point=points, name=f"{name}_CRV")
    pm.setAttr(f"{curve}.inheritsTransform", 0)
    curve_shape = curve.getShape()

    if follow_nodes:
        for index_num, each_node in enumerate(nodes):
            dmx_node = pm.createNode("decomposeMatrix", name=f"{namespaceutils.get_nice_name(each_node)}_DMX")
            each_node.connectAttr("worldMatrix[0]", dmx_node.inputMatrix, force=True)
            dmx_node.connectAttr("outputTranslate", f"{curve_shape.name()}.controlPoints[{index_num}]", force=True)

    return curve


def create_follow_locator(cv: pm.NurbsCurveCV, parent: pm.nt.Transform) -> pm.nt.Locator:
    locator = pm.createNode(pm.nt.Locator)
    locator.parent(0).rename(name=f"{cv.node().parent(0)}_{cv.index()}_LOC")
    locator.parent(0).setParent(parent)
    locator.parent(0).setTranslation(cv.getPosition(space="world"), space="world")
    locator.connectAttr("worldPosition[0]", cv)
    return locator
    

def create_bezier_curve(nodes: list[pm.nt.Transform], name: str = "new_curve", follow_nodes: bool = False):
    # Create standard curve and convert
    cv_curve = create_cv_curve(nodes=nodes, name=name, degree=1, follow_nodes=False)  # Follow gets broken when spline changed to bezier
    pm.select(cv_curve)
    pm.nurbsCurveToBezier()  # Can't seem to pass anything through this, so must select and clear
    pm.select(clear=True)
    
    if follow_nodes:
        # 4 cvs for start and end
        cv_count = cv_curve.cv.count()
        start_cvs = pm.ls(cv_curve.cv[:1], flatten=True)
        end_cvs = pm.ls(cv_curve.cv[-2:], flatten=True)
        
        [create_follow_locator(each_cv, nodes[0]) for each_cv in start_cvs]
        [create_follow_locator(each_cv, nodes[-1]) for each_cv in end_cvs]
        
        if cv_count > 4:
            mid_cvs = pm.ls(cv_curve.cv[2:-2], flatten=True)
            
            node_index_num = 1
            for index_num, each_cv in enumerate(mid_cvs):
                create_follow_locator(each_cv, nodes[node_index_num])
                if (index_num + 1) % 3 == 0:  # Is index divisible by 3
                    node_index_num += 1

    return cv_curve


def create_ribbon_surface(nodes: list[pm.nt.Transform], name: str = "new_ribbon", follow_controls: list[pm.nt.Transform] = False, 
                          use_fitbspline: bool = True, use_tangents: bool = False) -> tuple[list[pm.nt.Transform], list[pm.nt.Transform], pm.nt.Transform, pm.nt.NurbsCurve]:
    surface_group = pm.createNode(pm.nt.Transform, name=f"{name}_ribbon_{rigutils.SUFFIX_GROUP}")
    
    def create_follow_nodes(follow_name: str, follow_nodes: list[pm.nt.Transform], offset: pm.dt.Vector):
        curve_follow_nodes = []
        for index_num, each_node in enumerate(follow_nodes):
            curve_follow_node = pm.createNode(pm.nt.Transform, name=f"{follow_name}_{index_num}_follow_{rigutils.SUFFIX_GROUP}", parent=surface_group)
            curve_follow_node.setTranslation(each_node.getTranslation(space="world"), space="world")
            curve_follow_node.translateBy(offset, space="world")
            
            curve_follow_nodes.append(curve_follow_node)
        
        return curve_follow_nodes

    follow_nodes = follow_controls if follow_controls else nodes
    curve_a_follow_nodes = create_follow_nodes(follow_name=f"{name}_curve_a", follow_nodes=follow_nodes, offset=pm.dt.Vector(-5, 0, 0))
    curve_b_follow_nodes = create_follow_nodes(follow_name=f"{name}_curve_b", follow_nodes=follow_nodes, offset=pm.dt.Vector(5, 0, 0))
    
    if use_tangents:  ### TODO set up advance tangent controls, may need aim constraints or something
        curve_a = create_bezier_curve(nodes=curve_a_follow_nodes, name=f"{name}_curve_a", follow_nodes=True)
        curve_b = create_bezier_curve(nodes=curve_b_follow_nodes, name=f"{name}_curve_b", follow_nodes=True)
    else:
        curve_a = create_cv_curve(nodes=curve_a_follow_nodes, degree=1, name=f"{name}_curve_a", follow_nodes=True)
        curve_b = create_cv_curve(nodes=curve_b_follow_nodes, degree=1, name=f"{name}_curve_b", follow_nodes=True)
    
    # A fitBspline will force the cvs to match the position of the nodes exactly
    # This can mess up if it's not a clean curve, so best to use with follow controls
    fitb_a, fitb_b = [curve_a], [curve_b]
    if use_fitbspline:
        fitb_a = pm.fitBspline(curve_a, name=f"{name}_curve_a_fitb_CRV")
        fitb_b = pm.fitBspline(curve_b, name=f"{name}_curve_b_fitb_CRV")    
        fitb_a[1].rename(f"{name}_curve_a_FBS")
        fitb_b[1].rename(f"{name}_curve_b_FBS")
    
    surface: pm.nt.Transform = pm.loft(fitb_a[0], fitb_b[0], name=f"{name}_ribbon_SRF", reverseSurfaceNormals=True)        
    surface[1].rename(f"{name}_ribbon_LFT")
    surface = pm.rebuildSurface(surface[0], constructionHistory=True, replaceOriginal=True, rebuildType=0, endKnots=1, keepRange=0, 
                                keepControlPoints=False, keepCorners=False, spansU=len(nodes), spansV=1, degreeU=3, degreeV=3, tolerance=0.01, 
                                fitRebuild=0, direction=2)
    surface[1].rename(f"{name}_ribbon_RBS")
    
    # Create follow curve from surface
    follow_curve_from_surface = pm.shadingNode(pm.nt.CurveFromSurfaceIso, name=f"{name}_ribbon_follow_CFS", asUtility=True)
    follow_curve_from_surface.isoparmValue.set(0.5)
    follow_curve_from_surface.isoparmDirection.set(0)  # U
    surface[0].connectAttr("worldSpace[0]", follow_curve_from_surface.inputSurface, force=True)
    
    rebuild_curve = pm.shadingNode(pm.nt.RebuildCurve, name=f"{namespaceutils.get_nice_name(follow_curve_from_surface)}_RBC", asUtility=True)
    rebuild_curve.spans.set(surface[0].spansU.get())
    follow_curve_from_surface.connectAttr("outputCurve", rebuild_curve.inputCurve, force=True)
    
    follow_curve = pm.createNode(pm.nt.NurbsCurve)
    follow_curve.getTransform().rename(f"{namespaceutils.get_nice_name(follow_curve_from_surface)}_CRV")
    rebuild_curve.connectAttr("outputCurve", f"{follow_curve.name()}.create", force=True)
    
    for each_node in [fitb_a[0], fitb_b[0], surface[0], follow_curve.parent(0)]:
        pm.setAttr(f"{each_node.name()}.inheritsTransform", 0)
    
    for each_node in [curve_a, curve_b, fitb_a[0], fitb_b[0], surface[0], follow_curve.parent(0)]:
        pm.parent(each_node, surface_group)
    
    return curve_a_follow_nodes, curve_b_follow_nodes, surface[0], follow_curve


def get_closest_uv(surface: pm.nt.Transform, node: pm.nt.Transform) -> tuple[float, float]:
    sel = om.MSelectionList()
    sel.add(surface.name())
    dag = sel.getDagPath(0)
    surf = om.MFnNurbsSurface(dag)

    test_point = om.MPoint(node.getTranslation(space="world"))
    uv: tuple[float, float] = surf.closestPoint(test_point, space=om.MSpace.kWorld)[1:]
    return uv


def get_closest_point_on_curve(curve: pm.nt.NurbsCurve, node: pm.nt.Transform) -> list[float]:
    sel = om.MSelectionList()
    sel.add(curve.name())
    dag = sel.getDagPath(0)

    curve = om.MFnNurbsCurve(dag)
    node_point = om.MPoint(node.getTranslation(space="world"))

    assumed_point_on_curve, parameter_point_on_curve = curve.closestPoint(node_point, space=om.MSpace.kWorld)
    actual_closest_point: om.MPoint = curve.getPointAtParam(parameter_point_on_curve, om.MSpace.kWorld)
    
    return [actual_closest_point.x, actual_closest_point.y, actual_closest_point.z]


def create_surface_follicles(surface: pm.nt.Transform, nodes: list[pm.nt.Transform]) -> list[pm.nt.Transform]:
    follicles = []
    for index_num, each_node in enumerate(nodes):
        uv = get_closest_uv(surface, each_node)
        
        nice_name = namespaceutils.get_nice_name(surface)
        
        follicle_shape = pm.createNode(pm.nt.Follicle, name=f"{nice_name}_{index_num}_FLCShape")
        follicle_node = follicle_shape.parent(0)
        follicle_node.rename(f"{nice_name}_{index_num}_FLC")
        
        surface.connectAttr("worldSpace[0]", follicle_shape.inputSurface, force=True)
        surface.connectAttr("worldMatrix[0]", follicle_shape.inputWorldMatrix, force=True)
        
        follicle_shape.connectAttr("outTranslate", follicle_node.translate, force=True)
        follicle_shape.connectAttr("outRotate", follicle_node.rotate, force=True)
        
        follicle_shape.setAttr("parameterU", uv[0])
        follicle_shape.setAttr("parameterV", uv[1])

        follicles.append(follicle_node)
    
    return follicles
