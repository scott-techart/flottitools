import os
import pathlib
import unittest

import pymel.core as pm

import flottitools.utils.pathutils as pathutils
import flottitools.test as mayatest


class TestGetMeshMayaFiles(mayatest.MayaTempDirTestCase):
    def test_get_scene_path(self):
        scene_path = self.tmp_dir_root.joinpath('foo.ma')
        pm.saveAs(scene_path)
        result = pathutils.get_scene_path()
        self.assertEqual(scene_path, result)
        os.remove(scene_path)

    def test_returns_none(self):
        pm.newFile()
        self.assertIsNone(pathutils.get_scene_path())


class TestGetRelativePathToFolderName(unittest.TestCase):
    def test_get_path_relative_to_source(self):
        test_path = pathlib.Path(
            r'C:\foo\bar\source\spam\eggs\fake.ma')
        expected = pathlib.Path(
            r'spam\eggs\fake.ma')
        result = pathutils.get_path_relative_to_folder_name(test_path, 'source')
        self.assertEqual(result, expected)

    def test_not_absolute_path(self):
        test_path = pathlib.Path(
            r'C:\foo\source\bar\spam\eggs\fake.ma')
        expected = pathlib.Path(
            r'bar\spam\eggs\fake.ma')
        result = pathutils.get_path_relative_to_folder_name(test_path, 'source')
        self.assertEqual(result, expected)

    def test_return_none_if_folder_name_not_in_path(self):
        test_path = pathlib.Path(
            r'C:\poo/bar/spam/eggs/fake.ma')
        result = pathutils.get_path_relative_to_folder_name(test_path, 'foo')
        self.assertIsNone(result)

    def test_not_case_sensitive(self):
        test_path = pathlib.Path(
            r'C:\Foo\bAr\sOuRcE\sPaM\eGgS\fAkE.Ma')
        expected = pathlib.Path(
            r'sPaM\eGgS\fAkE.Ma')
        result = pathutils.get_path_relative_to_folder_name(test_path, 'source')
        self.assertEqual(result, expected)
