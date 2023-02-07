"""Tests for lofting.py."""
import unittest

from hull import Hull


class TestLofting(unittest.TestCase):

    def test01_init(self):
        h = Hull()

    def test02_parse_dimension(self):
        h = Hull()
        self.assertEqual(h.parse_dimension('-'), None)
        self.assertEqual(h.parse_dimension('1'), 1.0)
        self.assertEqual(h.parse_dimension('1.0'), 1.0)
        self.assertEqual(h.parse_dimension('1.000000'), 1.0)
        self.assertEqual(h.parse_dimension('1-00-0'), 12.0)
        self.assertEqual(h.parse_dimension('1-02-0'), 14.0)
        self.assertEqual(h.parse_dimension('1-02-0+'), 14.0625)
        self.assertEqual(h.parse_dimension('1-02-1'), 14.125)
        self.assertEqual(h.parse_dimension('1-02-01'), 14.0125)
        self.assertEqual(h.parse_dimension('1-02-05'), 14.0625)
        self.assertEqual(h.parse_dimension('1-02-09'), 14.1125)
        self.assertEqual(h.parse_dimension('Butt3"'), 3.0)
        self.assertEqual(h.parse_dimension('WL5"'), 5.0)
