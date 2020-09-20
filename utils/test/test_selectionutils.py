import flottitools.test as flottitest
import flottitools.utils.selectionutils as su


class TestConvertSelectionToVerts(flottitest.MayaTestCase):
    def make_and_get_cube_and_verts(self):
        test_cube = self.create_cube()
        self.pm.select(test_cube.vtx, replace=True)
        expected_verts = self.pm.selected(fl=True)
        return test_cube, expected_verts

    def test_returns_verts_from_selected_object(self):
        test_cube, expected_verts = self.make_and_get_cube_and_verts()

        self.pm.select(test_cube, replace=True)
        result = su.convert_selection_to_verts()
        self.assertListEqual(result, expected_verts)

    def test_ignores_selection_if_sel_is_passed_in(self):
        test_cube, expected_verts = self.make_and_get_cube_and_verts()
        dummy_cube = self.create_cube()
        self.pm.select(dummy_cube, replace=True)

        result = su.convert_selection_to_verts([test_cube])
        self.assertListEqual(result, expected_verts)

    def test_multiple_selected_objects(self):
        test_cube1, expected_verts1 = self.make_and_get_cube_and_verts()
        test_cube2, expected_verts2 = self.make_and_get_cube_and_verts()
        expected_verts = expected_verts1 + expected_verts2
        self.pm.select([test_cube1, test_cube2], replace=True)

        result = su.convert_selection_to_verts()
        self.assertListEqual(result, expected_verts)

    def test_faces_converted_to_verts(self):
        test_cube, expected_verts = self.make_and_get_cube_and_verts()
        self.pm.select(test_cube.f, replace=True)

        result = su.convert_selection_to_verts()
        self.assertListEqual(result, expected_verts)
