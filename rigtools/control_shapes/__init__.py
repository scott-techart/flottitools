"""
A simple example of a control shape manager in Maya contained in one file for easier access.
It can be used for loading, saving, copying, etc. control shapes.
This file is used for demonstration purposes, to be followed along with in this blog post
http://bindpose.com/creating-maya-control-shape-manager
https://gist.github.com/vshotarov/c9f92bea49a19576c91a73fdf701e6fb#file-controlshapemanagerfull-py
"""
import os
import json
import re
import functools

from maya import cmds as mc, OpenMaya as om


SHAPE_LIBRARY_PATH = os.path.dirname(__file__)
SHELF_NAME = "Shape Exporter"


def validatePath(path=None):
    '''Checks if the file already exists and provides a dialog to overwrite or not'''
    if os.path.isfile(path):
        confirm = mc.confirmDialog(title='Overwrite file?',
                                   message='The file ' + path + ' already exists.Do you want to overwrite it?',
                                   button=['Yes', 'No'],
                                   defaultButton='Yes',
                                   cancelButton='No',
                                   dismissString='No')
        if confirm == "No":
            mc.warning("The file " + path + " was not saved")
            return 0
    return 1


def loadData(path=None):
    '''Loads raw JSON data from a file and returns it as a dict'''
    if os.path.isfile(path):
        f = open(path, "r")
        data = json.loads(f.read())
        f.close()
        return data
    else:
        mc.error("The file " + path + " doesn't exist")


def saveData(path=None,
             data=None):
    '''Saves a dictionary as JSON in a file'''
    if validatePath(path):
        f = open(path, "w")
        f.write(json.dumps(data, sort_keys=1, indent=4, separators=(",", ":")))
        f.close()
        return 1
    return 0


def getKnots(crvShape=None):
    mObj = om.MObject()
    sel = om.MSelectionList()
    sel.add(crvShape)
    sel.getDependNode(0, mObj)

    fnCurve = om.MFnNurbsCurve(mObj)
    tmpKnots = om.MDoubleArray()
    fnCurve.getKnots(tmpKnots)

    return [tmpKnots[i] for i in range(tmpKnots.length())]


def getShape(crv=None):
    '''Returns a dictionary containing all the necessery information for rebuilding the passed in crv.'''
    crvShapes = validateCurve(crv)

    crvShapeList = []

    for crvShape in crvShapes:
        crvShapeDict = {
            "points": [],
            "knots": [],
            "form": mc.getAttr(crvShape + ".form"),
            "degree": mc.getAttr(crvShape + ".degree"),
            "colour": mc.getAttr(crvShape + ".overrideColor")
        }
        points = []

        for i in range(mc.getAttr(crvShape + ".controlPoints", s=1)):
        	points.append(mc.getAttr(crvShape + ".controlPoints[%i]" % i)[0])

        crvShapeDict["points"] = points
        crvShapeDict["knots"] = getKnots(crvShape)

        crvShapeList.append(crvShapeDict)

    return crvShapeList


def setShape(crv, crvShapeList):
    '''Creates a new shape on the crv transform, using the properties in the crvShapeDict.'''
    crvShapes = validateCurve(crv)

    oldColour = mc.getAttr(crvShapes[0] + ".overrideColor")
    mc.delete(crvShapes)

    for i, crvShapeDict in enumerate(crvShapeList):
        tmpCrv = mc.curve(p=crvShapeDict["points"], k=crvShapeDict["knots"], d=crvShapeDict["degree"], per=bool(crvShapeDict["form"]))
        newShape = mc.listRelatives(tmpCrv, s=1)[0]
        mc.parent(newShape, crv, r=1, s=1)

        mc.delete(tmpCrv)
        newShape = mc.rename(newShape, crv + "Shape" + str(i + 1).zfill(2))

        mc.setAttr(newShape + ".overrideEnabled", 1)

        if "colour" in crvShapeDict.keys():
            setColour(newShape, crvShapeDict["colour"])
        else:
            setColour(newShape, oldColour)


def validateCurve(crv=None):
    '''Checks whether the transform we are working with is actually a curve and returns it's shapes'''
    if mc.nodeType(crv) == "transform" and mc.nodeType(mc.listRelatives(crv, c=1, s=1)[0]) == "nurbsCurve":
        crvShapes = mc.listRelatives(crv, c=1, s=1)
    elif mc.nodeType(crv) == "nurbsCurve":
        crvShapes = mc.listRelatives(mc.listRelatives(crv, p=1)[0], c=1, s=1)
    else:
        mc.error("The object " + crv + " passed to validateCurve() is not a curve")
    return crvShapes


def loadFromLib(shape=None):
    '''Loads the shape data from the shape file in the SHAPE_LIBRARY_PATH directory'''
    path = os.path.join(SHAPE_LIBRARY_PATH, shape + ".json")
    data = loadData(path)
    return data


def saveToLib(crv=None,
              shapeName=None):
    '''Saves the shape data to a shape file in the SHAPE_LIBRARY_PATH directory'''
    crvShape = getShape(crv=crv)
    path = os.path.join(SHAPE_LIBRARY_PATH, re.sub("\s", "", shapeName) + ".json")
    for shapeDict in crvShape:
        shapeDict.pop("colour", None)
    saveData(path, crvShape)


def setColour(crv, colour):
    '''Sets the overrideColor of a curve'''
    if mc.nodeType(crv) == "transform":
        crvShapes = mc.listRelatives(crv)
    else:
        crvShapes = [crv]
    for crv in crvShapes:
        mc.setAttr(crv + ".overrideColor", colour)


def getColour(crv):
    '''Returns the overrideColor of a curve'''
    if mc.nodeType(crv) == "transform":
        crv = mc.listRelatives(crv)[0]
    return mc.getAttr(crv + ".overrideColor")


def getAvailableControlShapes():
    '''Returns a list of the available control shapes in the specified library. Each element
    of the list is a tuple containing the label (name) of the controlShape and a reference
    to the command to assign that shape via functools.partial'''
    lib = SHAPE_LIBRARY_PATH
    return [(x.split(".")[0], functools.partial(assignControlShape, x.split(".")[0])) for x in os.listdir(lib)]


def getAvailableColours():
    '''Returns a list of the available 32 colours for overrideColor in maya. Each element
    of the list is a tuple containig the label, reference to the command which assigns the
    colour and the name of an image to be used as an icon'''
    return [("index" + str(i).zfill(2), functools.partial(assignColour, i), "shapeColour" + str(i).zfill(2) + ".png") for i in range(32)]


def assignColour(*args):
    '''Assigns args[0] as the overrideColor of the selected curves'''
    for each in mc.ls(sl=1, fl=1):
        setColour(each, args[0])


def assignControlShape(*args):
    '''Assigns args[0] as the shape of the selected curves'''
    sel = mc.ls(sl=1, fl=1)
    for each in sel:
        setShape(each, loadFromLib(args[0]))
    mc.select(sel)


def saveCtlShapeToLib(*args):
    '''Saves the selected shape in the defined control shape library'''
    result = mc.promptDialog(title="Save Control Shape to Library",
                             m="Control Shape Name",
                             button=["Save", "Cancel"],
                             cancelButton="Cancel",
                             dismissString="Cancel")
    if result == "Save":
        name = mc.promptDialog(q=1, t=1)
        saveToLib(mc.ls(sl=1, fl=1)[0], name)


def mirrorCtlShapes(*args):
    '''Mirrors the selected control's shape to the other control on the other side'''
    sel = mc.ls(sl=1, fl=1)
    for ctl in sel:
        if ctl[0] not in ["L", "R"]:
            continue
        search = "R_"
        replace = "L_"
        if ctl[0] == "L":
            search = "L_"
            replace = "R_"
        shapes = getShape(ctl)
        for shape in shapes:
            shape.pop("colour")
        setShape(ctl.replace(search, replace), shapes)
        _flipCtlShape(ctl.replace(search, replace))
    mc.select(sel)


def copyCtlShape(*args):
    '''Copies the selected control's shape to a global variable for pasting'''
    global ctlShapeClipboard
    ctlShapeClipboard = getShape(mc.ls(sl=1, fl=1)[0])
    for ctlShape in ctlShapeClipboard:
        ctlShape.pop("colour")


def pasteCtlShape(*args):
    '''Assigns the control shape from the ctlShapeClipboard global variable
    to the selected controls'''
    sel = mc.ls(sl=1, fl=1)
    for each in sel:
        setShape(each, ctlShapeClipboard)
    mc.select(sel)


def flipCtlShape(*args):
    '''Flips the selected control shapes to the other side in all axis'''
    sel = mc.ls(sl=1, fl=1)
    for each in sel:
        _flipCtlShape(each)
    mc.select(sel)


def flipCtlShapeX(*args):
    '''Flips the selected control shapes to the other side in X'''
    sel = mc.ls(sl=1, fl=1)
    for each in sel:
        _flipCtlShape(each, [-1, 1, 1])
    mc.select(sel)


def flipCtlShapeY(*args):
    '''Flips the selected control shapes to the other side in Y'''
    sel = mc.ls(sl=1, fl=1)
    for each in sel:
        _flipCtlShape(each, [1, -1, 1])
    mc.select(sel)


def flipCtlShapeZ(*args):
    '''Flips the selected control shapes to the other side in Z'''
    sel = mc.ls(sl=1, fl=1)
    for each in sel:
        _flipCtlShape(each, [1, 1, -1])
    mc.select(sel)


def _flipCtlShape(crv=None, axis=[-1, -1, -1]):
    '''Scales the points of the crv argument by the axis argument. This function is not meant to be
    called directly. Look at the flipCtlShape instead.'''
    shapes = getShape(crv)
    newShapes = []
    for shape in shapes:
        for i, each in enumerate(shape["points"]):
            shape["points"][i] = [each[0] * axis[0], each[1] * axis[1], each[2] * axis[2]]
        newShapes.append(shape)
    setShape(crv, newShapes)
    mc.select(crv)
