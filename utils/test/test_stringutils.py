import unittest

import SSEMaya.Utilities.stringutils as stringutils


class TestReplaceAppendSuffix(unittest.TestCase):
    def test_replace_suffix(self):
        test_name = 'foo_bar_spam'
        result = stringutils.replace_suffix(test_name, 'eggs')
        expected = 'foo_bar_eggs'
        self.assertEqual(expected, result)

    def test_append_suffix(self):
        test_name = 'foo_bar_spam'
        result = stringutils.append_suffix(test_name, 'eggs')
        expected = 'foo_bar_spam_eggs'
        self.assertEqual(expected, result)

    def test_replace_suffix_name_has_no_suffix_appends_instead(self):
        test_name = 'foobarspam'
        result = stringutils.replace_suffix(test_name, 'eggs')
        expected = 'foobarspam_eggs'
        self.assertEqual(expected, result)

    def test_no_double_underscore(self):
        test_name = 'foo_bar_spam'
        result = stringutils.append_suffix(test_name, '_eggs')
        expected = 'foo_bar_spam_eggs'
        self.assertEqual(expected, result)

    def test_no_trailing_underscore(self):
        test_name = 'foo_bar_spam'
        result = stringutils.append_suffix(test_name, '_eggs_')
        expected = 'foo_bar_spam_eggs'
        self.assertEqual(expected, result)
