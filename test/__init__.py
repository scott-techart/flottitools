import os
import pathlib
import shutil
import tempfile
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
        self.scene_namespaces = []

    def tearDown(self):
        super(MayaTestCase, self).tearDown()
        self._clean_scene()

    def _clean_scene(self):
        try:
            self.pm.delete(self.scene_nodes)
        except self.pm.general.MayaNodeError:
            # trying to delete a node that doesn't exist anymore.
            self._careful_delete()
        self.pm.namespace(set=':')
        self._delete_all_namespaces()
        self.pm.select(clear=True)

    def _delete_all_namespaces(self):
        all_ns = self.pm.listNamespaces(recursive=True)
        for ns in all_ns:
            try:
                self.pm.namespace(removeNamespace=ns, deleteNamespaceContent=True)
            except RuntimeError:
                pass

    def _careful_delete(self):
        to_delete = [x for x in self.scene_nodes if x.exists()]
        self.pm.delete(to_delete)

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

    def create_sphere(self, **sphere_kwargs):
        sphere = self.pm.polySphere(**sphere_kwargs)[0]
        self.scene_nodes.append(sphere)
        return sphere

    def create_skinned_cube(self, joint_count=5, test_cube=None, **skin_kwargs):
        skin_kwargs.setdefault('maximumInfluences', 4)
        test_cube = test_cube or self.create_cube()
        test_joints = [self.create_joint(position=(i, i, i), absolute=True) for i in range(joint_count)]
        skin_cluster = self.pm.skinCluster(test_joints, test_cube, **skin_kwargs)
        self.scene_nodes.append(skin_cluster)
        return test_cube, test_joints, skin_cluster

    def create_namespace(self, namespace):
        ns = self.pm.namespace(add=namespace)
        self.scene_namespaces.append(ns)
        return ns


class MayaTempDirTestCase(MayaTestCase):
    tmp_dir_root = None

    @classmethod
    def setUpClass(cls):
        cls.tmp_dir_root = pathlib.Path(tempfile.mkdtemp())

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp_dir_root, ignore_errors=False, onerror=onerror)


def onerror(func, path, exc_info):
    """
    Error handler for ``shutil.rmtree``.

    If the error is due to an access error (read only file)
    it attempts to add write permission and then retries.

    If the error is for another reason it re-raises the error.

    Usage : ``shutil.rmtree(path, onerror=onerror)``
    """
    import stat
    # Is the error an access error?
    if not os.access(path, os.W_OK):
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise
