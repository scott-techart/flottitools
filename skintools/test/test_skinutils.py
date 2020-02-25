import flottitools.test as mayatest
import skinning.skinutils as skinutils


class TestGetSkinCluster(mayatest.MayaTestCase):
    def test_get_skin_cluster_from_cube(self):
        cube = self.create_cube()
        joint = self.create_joint()
        skin_cluster = self.pm.skinCluster(joint, cube)
        result = skinutils. get_skincluster(cube)
        self.assertEqual(result, skin_cluster)