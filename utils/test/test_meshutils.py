import pymel.core as pm

import maya.api.OpenMaya as om
import flottitools.test as mayatest
import flottitools.utils.meshutils as meshutils


class TestGetMeshes(mayatest.MayaTestCase):
    def test_get_meshes_in_scene(self):
        test_cube = self.create_cube()
        result = meshutils.get_meshes_from_scene()
        self.assertListEqual(result, [test_cube])

    def test_does_not_get_other_shapes_in_scene(self):
        test_cube = self.create_cube()
        test_sphere = self.create_sphere()
        test_curve = self.pm.curve(p=[(0, 0, 0), (3, 5, 6), (5, 6, 7), (9, 9, 9)])
        self.scene_nodes.append(test_curve)
        result = meshutils.get_meshes_from_scene()
        self.assertListEqual(result, [test_cube, test_sphere])

    def test_only_returns_nodes_in_list(self):
        test_cubes = [self.create_cube() for _ in range(5)]
        result = meshutils.get_meshes_in_list(test_cubes[:3])
        self.assertListEqual(result, test_cubes[:3])

    def test_node_without_get_shape_method_in_list(self):
        test_cubes = [self.create_cube() for _ in range(5)]
        no_shape_node = self.pm.createNode(self.pm.nt.PlusMinusAverage)
        self.scene_nodes.append(no_shape_node)
        all_nodes = test_cubes + [no_shape_node]
        result = meshutils.get_meshes_in_list(all_nodes)
        self.assertListEqual(result, test_cubes)


class TestGetMeshNodes(mayatest.MayaTestCase):
    def test_get_mesh_nodes_simple(self):
        test_cube = self.create_cube()
        result = meshutils.get_mesh_nodes(test_cube)
        expected = [test_cube.getShape()]
        self.assertEqual(result, expected)

    def test_multiple_mesh_nodes(self):
        test_cube = self.create_cube()
        foo_cube = self.create_cube()
        expected = [test_cube.getShape(), foo_cube.getShape()]
        foo_cube.getShape().setParent(test_cube, r=True, s=True)
        result = meshutils.get_mesh_nodes(test_cube)
        self.assertEqual(result, expected)

    def test_returns_empty_list_if_no_shape_nodes(self):
        test_node = self.create_transform_node()
        self.assertEqual(meshutils.get_mesh_nodes(test_node), [])

    def test_returns_empty_list_if_no_mesh_nodes(self):
        test_cube = self.create_cube()
        test_curve = self.pm.curve(p=[(0, 0, 0), (3, 5, 6), (5, 6, 7), (9, 9, 9)])
        self.scene_nodes.append(test_curve)
        test_curve.getShape().setParent(test_cube, r=True, s=True)
        result = meshutils.get_mesh_nodes(test_cube)
        self.assertListEqual(result, [test_cube.getShape()])


class TestGetNGons(mayatest.MayaTestCase):
    def test_get_ngons(self):
        test_cube = self.create_cube()
        pm.select(test_cube, r=True)
        # mel command I copy/pasted that generates a couple ngons
        pm.mel.eval(
            'delete `polyMoveVertex -ch 1 |pCube1|pCubeShape1.vtx[0]`; polySplit -ch 1 -sma 180 -ep 4 1 -fp 0 -1.278728 0.029147 29.713072 -ep 1 0.57896 |pCube1|pCubeShape1;  select -cl;')
        result = meshutils.get_ngons(test_cube)
        expected = [test_cube.f[0], test_cube.f[1]]
        self.assertEqual(result, expected)


class TestGetFacesWithMissingUVS(mayatest.MayaTestCase):
    def test_get_missing_uv_faces(self):
        test_cube = self.create_cube()
        pm.polyMapDel(test_cube.uvs[4:6])
        result = meshutils.get_faces_with_missing_uvs(test_cube)
        expected = [test_cube.f[1], test_cube.f[2], test_cube.f[3]]
        self.assertEqual(result, expected)


class TestOverlappingVertices(mayatest.MayaTestCase):
    def test_get_all_overlapping_vertices_from_mesh_name(self):
        test_cube = self.create_cube()
        pm.move(test_cube.vtx[0], (0, 0, 0), absolute=True)
        pm.move(test_cube.vtx[1], (0, 0, 0), absolute=True)
        pm.move(test_cube.vtx[7], (0, 0, 0), absolute=True)
        pm.move(test_cube.vtx[4], (0, 0, 0), absolute=True)
        result = meshutils.get_overlapping_vertices_from_mesh_name(test_cube.getShape().name())
        result.sort()
        expected = [test_cube.vtx[0].name(), test_cube.vtx[1].name(), test_cube.vtx[4].name(), test_cube.vtx[7].name()]
        expected.sort()
        self.assertListEqual(result, expected)

    def test_accuracy(self):
        test_cube = self.create_cube()
        pm.move(test_cube.vtx[0], (0, 0, 0), absolute=True)
        pm.move(test_cube.vtx[1], (.001, .001, .001), absolute=True)
        result = meshutils.get_overlapping_vertices(test_cube, 1)
        expected = [test_cube.vtx[0], test_cube.vtx[1]]
        self.assertListEqual(result, expected)

    def test_accuracy2(self):
        test_cube = self.create_cube()
        pm.move(test_cube.vtx[0], (0, 0, 0), absolute=True)
        pm.move(test_cube.vtx[1], (.001, .0, .0), absolute=True)
        result = meshutils.get_overlapping_vertices(test_cube, 3)
        expected = []
        self.assertListEqual(result, expected)


class TestGetVertexColors(mayatest.MayaTestCase):
    def test_no_color_skipped(self):
        test_cube = self.create_cube()
        result = meshutils.get_vertex_colors_from_mesh_name(
            test_cube.nodeName(), skip_color_values=[])
        default_color = (-1, -1, -1, -1)
        expected = dict([(0, default_color), (1, default_color), (2, default_color), (3, default_color),
                         (4, default_color), (5, default_color), (6, default_color), (7, default_color)])
        self.assertDictEqual(result, expected)

    def test_returns_empty_if_all_verts_default_color(self):
        test_cube = self.create_cube()
        result = meshutils.get_vertex_colors_from_mesh_name(test_cube.nodeName())
        expected = {}
        self.assertDictEqual(result, expected)

    def test_returns_empty_if_all_vert_colors_are_one(self):
        test_cube = self.create_cube()
        test_color = (1, 1, 1, 1)
        test_cube.vtx[0].setColor(test_color)
        result = meshutils.get_vertex_colors_from_mesh_name(
            test_cube.nodeName(), skip_color_values=(meshutils.NO_VERTEX_COLOR, om.MColor((1, 1, 1, 1))))
        expected = {}
        self.assertDictEqual(result, expected)

    def test_one_vert_not_acceptable(self):
        test_cube = self.create_cube()
        # polyColorPerVertex - r 1 - g 1 - b 1 - a 1 - cdo;
        # polyColorPerVertex - rem
        # pm.polyColorPerVertex(pm.selected(), remove=True)
        test_color = (1, 0, 1, 0)
        test_cube.vtx[0].setColor(test_color)
        result = meshutils.get_vertex_colors_from_mesh_name(test_cube.nodeName())
        expected = dict([(0, test_color)])
        self.assertDictEqual(result, expected)

    def test_with_namespace(self):
        test_cube = self.create_cube()
        dummy_cubes = [self.create_cube() for i in range(3)]
        dummy_cubes[2].setParent(dummy_cubes[1])
        dummy_cubes[1].setParent(dummy_cubes[0])
        dummy_cubes[2].rename('foo')
        test_cube.rename('foo')
        result = meshutils.get_vertex_colors_from_mesh_name(
            test_cube.name(), skip_color_values=[])
        default_color = (-1, -1, -1, -1)
        expected = dict([(0, default_color), (1, default_color), (2, default_color), (3, default_color),
                         (4, default_color), (5, default_color), (6, default_color), (7, default_color)])
        self.assertDictEqual(result, expected)

    def test_get_colors_from_mesh(self):
        test_cube = self.create_cube()
        result = meshutils.get_vertex_colors_from_mesh_node(
            test_cube, skip_color_values=[])
        default_color = (-1, -1, -1, -1)
        expected = dict([(0, default_color), (1, default_color), (2, default_color), (3, default_color),
                         (4, default_color), (5, default_color), (6, default_color), (7, default_color)])
        self.assertDictEqual(result, expected)

    def test_get_from_node_one_shape_node(self):
        test_cube = self.create_cube()
        result = meshutils.get_vertex_colors_from_mesh_node(
            test_cube.getShape(), skip_color_values=[])
        default_color = (-1, -1, -1, -1)
        expected = dict([(0, default_color), (1, default_color), (2, default_color), (3, default_color),
                         (4, default_color), (5, default_color), (6, default_color), (7, default_color)])
        self.assertDictEqual(result, expected)

    def test_get_from_node_several_shape_nodes(self):
        test_cube = self.create_cube()
        dummy_cubes = [self.create_cube() for i in range(3)]
        [self.pm.parent(dc.getShape(), test_cube, r=True, s=True) for dc in dummy_cubes]
        result = meshutils.get_vertex_colors_from_node(
            test_cube, skip_color_values=[])
        default_color = (-1, -1, -1, -1)
        expected = dict([(0, default_color), (1, default_color), (2, default_color), (3, default_color),
                         (4, default_color), (5, default_color), (6, default_color), (7, default_color)])
        shapes = test_cube.getShapes()
        expected = {shapes[0]: expected, shapes[1]: expected, shapes[2]: expected, shapes[3]: expected}
        self.assertDictEqual(result, expected)

    def test_skippable_is_not_m_color(self):
        test_cube = self.create_cube()
        test_color = (1, 1, 1, 1)
        test_cube.vtx[0].setColor(test_color)
        result = meshutils.get_vertex_colors_from_mesh_node(
            test_cube, skip_color_values=(meshutils.NO_VERTEX_COLOR, (1, 1, 1, 1)))
        expected = {}
        self.assertDictEqual(result, expected)


class TestGetMeshPairsByName(mayatest.MayaTestCase):
    def test_basic(self):
        test_cube_a = self.create_cube()
        test_ns = self.create_namespace('foo')
        self.pm.namespace(set=test_ns)
        test_cube_b = self.create_cube()
        result = meshutils.get_mesh_pairs_by_name([test_cube_a], [test_cube_b])
        self.assertListEqual(result, [(test_cube_a, test_cube_b)])

    def test_multiple_meshes_does_not_mutate_args(self):
        test_cube_a1 = self.create_cube(name='foo')
        test_cube_a2 = self.create_cube(name='bar')
        test_cube_a3 = self.create_cube(name='spam')
        root_cubes = [test_cube_a1, test_cube_a2, test_cube_a3]
        test_ns = self.create_namespace('foons')
        self.pm.namespace(set=test_ns)
        test_cube_b1 = self.create_cube(name='foo')
        test_cube_b2 = self.create_cube(name='bar')
        test_cube_b3 = self.create_cube(name='spam')
        ns_cubes = [test_cube_b1, test_cube_b2, test_cube_b3]
        result = meshutils.get_mesh_pairs_by_name(root_cubes, ns_cubes)
        expected = list(zip(root_cubes, ns_cubes))
        self.assertListEqual(result, expected)