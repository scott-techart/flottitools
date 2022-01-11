import os
import tempfile
import unittest

import flottitools.drag_to_maya_scene_setup as flottisetup


class TestWriteToMayaUsersetup(unittest.TestCase):
    test_lines = ['0\n', '1\n', '2\n', '3\n']
    start_tag = '# start '
    end_tag = '# end '
    version = 'v.test'
    version_identifier = ' :: '
    start_line = start_tag + version_identifier + version + '\n'
    end_line = end_tag + version_identifier + version + '\n'

    def setUp(self):
        super(TestWriteToMayaUsersetup, self).setUp()
        self.tmpfile = 'blah'
        # self.tmpfile = tempfile.TemporaryFile(mode='w+', suffix='.py')
        self.tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix='.py')
        # Have to close the file after writing to it so that the method's i/o functions will work.
        self.tmpfile.close()

    def tearDown(self):
        super(TestWriteToMayaUsersetup, self).tearDown()
        os.remove(self.tmpfile.name)

    def test_writes_if_start_and_end_tags_not_found(self):
        with open(self.tmpfile.name, 'w') as tmpfile:
            tmpfile.writelines(self.test_lines)
        expected = self.test_lines + [self.start_line, self.end_line]

        flottisetup.inject_flottisetup_to_maya_usersetup(self.tmpfile.name, None, self.version, self.start_tag, self.end_tag)
        with open(self.tmpfile.name, 'r') as tmpfile:
            result = tmpfile.readlines()
        self.assertListEqual(expected, result)

    def test_no_op_when_start_and_end_tags_match(self):
        test_lines = self.test_lines + ['\n', '\n', '\n', self.start_line, self.end_line]
        with open(self.tmpfile.name, 'w') as tmpfile:
            tmpfile.writelines(test_lines)

        flottisetup.inject_flottisetup_to_maya_usersetup(self.tmpfile.name, None, self.version, self.start_tag, self.end_tag)
        with open(self.tmpfile.name, 'r') as tmpfile:
            result = tmpfile.readlines()
        self.assertListEqual(test_lines, result)

    def test_updates_with_new_version(self):
        test_lines = self.test_lines + ['\n', '\n', '\n', self.start_line, self.end_line]
        with open(self.tmpfile.name, 'w') as tmpfile:
            tmpfile.writelines(test_lines)

        expected_start_line = self.start_tag + self.version_identifier + flottisetup.FLOTTI_ARTTOOLS_VERSION + '\n'
        expected_end_line = self.end_tag + self.version_identifier + flottisetup.FLOTTI_ARTTOOLS_VERSION + '\n'
        expected = self.test_lines + ['\n', '\n', '\n', expected_start_line, expected_end_line]

        flottisetup.inject_flottisetup_to_maya_usersetup(self.tmpfile.name, [],
                                                         flottisetup.FLOTTI_ARTTOOLS_VERSION,
                                                         self.start_tag, self.end_tag)
        with open(self.tmpfile.name, 'r') as tmpfile:
            result = tmpfile.readlines()
        self.assertListEqual(expected, result)

    def test_replaces_content(self):
        test_lines = self.test_lines + ['\n', '\n', '\n',
                                        self.start_tag + self.version_identifier + ' v1.test' + '\n',
                                        'test content\n',
                                        self.end_tag + self.version_identifier + ' v1.test' + '\n']
        with open(self.tmpfile.name, 'w') as tmpfile:
            tmpfile.writelines(test_lines)

        expected = self.test_lines + ['\n', '\n', '\n',
                                      self.start_line,
                                      'expected content\n',
                                      self.end_line]

        flottisetup.inject_flottisetup_to_maya_usersetup(self.tmpfile.name, ['expected content\n'],
                                                      self.version, self.start_tag, self.end_tag)
        with open(self.tmpfile.name, 'r') as tmpfile:
            result = tmpfile.readlines()
        self.assertListEqual(expected, result)


class TestGetFlottiVersion(unittest.TestCase):
    start_tag = 'start tag'
    end_tag = 'end tag'
    version = 'v.test'
    version_identifier = ' :: '
    start_line = start_tag + version_identifier + version
    end_line = end_tag + version_identifier + version
    test_list = ['0', '1', start_line, '3', '4', end_line, '6', '7']

    def test_returns_correct_version_from_start_line(self):
        result = flottisetup._get_flotti_version_from_index(self.test_list, 2, self.version_identifier)
        self.assertEqual(self.version, result)

    def test_returns_correct_version_from_end_line(self):
        result = flottisetup._get_flotti_version_from_index(self.test_list, 5, self.version_identifier)
        self.assertEqual(self.version, result)

    def test_returns_none_if_no_version_identifier(self):
        result = flottisetup._get_flotti_version_from_index(self.test_list, 2, ' ** ')
        self.assertIsNone(None, result)


class TestGetFlottiStartAndEndIndices(unittest.TestCase):
    start_tag = 'start tag'
    end_tag = 'end tag'
    test_list = ['0', '1', start_tag, '3', '4', end_tag, '6', '7']

    def test_returns_start_and_end_indices(self):
        start_index_result, end_index_result = flottisetup._get_flotti_start_and_end_indices(
            self.test_list, self.start_tag, self.end_tag)
        self.assertEqual(2, start_index_result)
        self.assertEqual(5, end_index_result)

    def test_missing_end_tag(self):
        test_list = self.test_list[:]
        test_list.remove(self.end_tag)
        start_index_result, end_index_result = flottisetup._get_flotti_start_and_end_indices(
            test_list, self.start_tag, self.end_tag)
        self.assertEqual(2, start_index_result)
        self.assertEqual(None, end_index_result)

    def test_missing_start_tag(self):
        test_list = self.test_list[:]
        test_list.remove(self.start_tag)
        start_index_result, end_index_result = flottisetup._get_flotti_start_and_end_indices(
            test_list, self.start_tag, self.end_tag)
        self.assertEqual(None, start_index_result)
        self.assertEqual(4, end_index_result)

    def test_missing_both(self):
        test_list = self.test_list[:]
        test_list.remove(self.start_tag)
        test_list.remove(self.end_tag)
        start_index_result, end_index_result = flottisetup._get_flotti_start_and_end_indices(
            test_list, self.start_tag, self.end_tag)
        self.assertEqual(None, start_index_result)
        self.assertEqual(None, end_index_result)

    def test_messy_end(self):
        test_list = self.test_list[:]
        test_list[2] = self.start_tag + ' foo'
        test_list[5] = self.end_tag + ' foo'
        start_index_result, end_index_result = flottisetup._get_flotti_start_and_end_indices(
            test_list, self.start_tag, self.end_tag)
        self.assertEqual(2, start_index_result)
        self.assertEqual(5, end_index_result)


class TestUpdateFlottiSetupLines(unittest.TestCase):
    start_tag = 'start tag'
    end_tag = 'end tag'
    version = 'vtest.0'
    version_identifier = ' :: '
    start_line = start_tag + version_identifier + version + '\n'
    end_line = end_tag + version_identifier + version + '\n'
    test_list = ['0', '1', start_line, '3', '4', end_line, '6', '7']

    def test_noop_if_version_matches(self):
        expected = self.test_list
        result = flottisetup._update_flotti_setup_lines(self.test_list, [], self.start_tag, self.end_tag,
                                                        self.version, self.version_identifier)
        self.assertListEqual(expected, result)

    def test_modifies_start_and_end_line_with_new_version(self):
        new_version = 'v2.0'
        expected = self.test_list[:]
        expected[2] = self.start_tag + self.version_identifier + new_version + '\n'
        expected[5] = self.end_tag + self.version_identifier + new_version + '\n'
        result = flottisetup._update_flotti_setup_lines(self.test_list, ['3', '4'],
                                                        self.start_tag, self.end_tag,
                                                        new_version, self.version_identifier)
        self.assertListEqual(expected, result)

    def test_modifies_content_between_start_end(self):
        new_version = 'v2.0'
        new_ssesetup_lines = ['new1', 'new2', 'new3']
        new_start_line = self.start_tag + self.version_identifier + new_version + '\n'
        new_end_line = self.end_tag + self.version_identifier + new_version + '\n'
        expected = ['0', '1', new_start_line]
        expected.extend(new_ssesetup_lines)
        expected.extend([new_end_line, '6', '7'])
        result = flottisetup._update_flotti_setup_lines(self.test_list, new_ssesetup_lines,
                                                        self.start_tag, self.end_tag,
                                                        new_version, self.version_identifier)
        self.assertListEqual(expected, result)

    def test_does_not_mutate_current_lines(self):
        expected = self.test_list[:]
        result = flottisetup._update_flotti_setup_lines(self.test_list, ['foo', 'bar'], 'foo', 'bar',
                                                        'vfoo', self.version_identifier)
        self.assertListEqual(expected, self.test_list)