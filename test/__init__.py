import unittest

class MayaTestCase(unittest.TestCase):
    """Initializes maya.standalone on initialization.
    This avoids import errors when importing this module outside of a Maya environment.

    Methods to create common Maya nodes for testing.
    Deletes all nodes created with MayaTestCase on tearDown to avoid creating a new scene after each test.
    """
    def __init__(self, *args):
        super(MayaTestCase, self).__init__(*args)
        import maya.standalone as mayastandalone
        mayastandalone.initialize()
        import pymel.core as pm
        self.pm = pm

    def setUp(self):
        super(MayaTestCase, self).setUp()
        self.scene_nodes = []

    def tearDown(self):
        super(MayaTestCase, self).tearDown()
        self.pm.delete(self.scene_nodes)
        self.pm.select(clear=True)

    def create_transform_node(self):
        xform_node = self.pm.createNode('transform')
        self.scene_nodes.append(xform_node)
        return xform_node

    def create_joint(self, **joint_kwargs):
        joint = self.pm.joint(**joint_kwargs)
        self.scene_nodes.append(joint)
        return joint

    def create_cube(self, **cube_kwargs):
        cube = self.pm.polyCube(**cube_kwargs)[0]
        self.scene_nodes.append(cube)
        return cube